import click
import colorlog
import logging
import os
import time
import json
from requests.exceptions import ConnectionError, HTTPError

from web3 import Web3
from web3.exceptions import ContractLogicError

import pandas as pd


handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def read_env_file(file_path):
    if not os.path.exists(file_path):
        return {}
    
    env_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_dict[key.strip()] = value.strip()
    return env_dict

# Чтение переменных из файла .env
env_variables = read_env_file('./.env')


class Airdrop:
    web3=None
    airdrop = None
    private_key = None
    public_address = None
    contract_names = {}
    nonce = None
    
    def __init__(self, provider, _airdrop_address, _old_token_address, _new_token_address, _private_key):
        _airdrop_address = Web3.toChecksumAddress(_airdrop_address)
        _old_token_address = Web3.toChecksumAddress(_old_token_address)
        _new_token_address = Web3.toChecksumAddress(_new_token_address)
        
        if not _private_key.startswith('0x'):
            _private_key = '0x' + _private_key
        print(f"Web3({provider})")
        self.web3 = Web3(Web3.HTTPProvider(provider))
        if not self.web3.isConnected():
            raise Exception("Web3 is not connected to the network")
        self.airdrop = self.load_contract(_airdrop_address, "contracts/build/contracts/Airdrop.json")
        self.old_token = self.load_contract(_old_token_address, "contracts/build/contracts/OldPancakeIBEP2E.json")
        self.new_token = self.load_contract(_new_token_address, "contracts/build/contracts/PancakeIBEP2E.json")
        self.private_key = _private_key
        self.public_address = self.web3.eth.account.privateKeyToAccount(self.private_key).address

    def get_airdrop_balance(self):
        print(f"Balance of {self.airdrop.address}: {self.new_token.functions.balanceOf(self.airdrop.address).call()}")
        return self.new_token.functions.balanceOf(self.airdrop.address).call()
        
    def load_contract(self, _address, _abi_path):
        with open(_abi_path, 'r') as file:
            contract_data = json.load(file)
            abi = contract_data['abi']
            self.contract_names[_address] = contract_data['contractName']
        return self.web3.eth.contract(address=_address, abi=abi)

    def send_transaction(self, contract, func_name, *args):
        if self.nonce is None:
            self.nonce = self.web3.eth.getTransactionCount(self.public_address)           

        nonce = self.nonce
        
        tx_hash = None
        gas_price = self.web3.eth.gas_price
        try:
            transaction = getattr(contract.functions, func_name)(*args).buildTransaction({
                'nonce': nonce,
                'from':self.public_address,
                'gasPrice': int(gas_price * 1.5)
            })
            signed_tx = self.web3.eth.account.signTransaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            self.nonce += 1

        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f'{self.contract_names[contract.address]}.{func_name}{args}: {error_message} from: {self.public_address}')

        if tx_hash:
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, {'timeout': 240000})
            #print(f'{self.contract_names[contract.address]}.{func_name}{args}: Transaction {tx_hash.hex()}')
            return tx_hash
        return None

    def airdrop_to(self, _address):
        _address = Web3.toChecksumAddress(_address)
        user_balance_old = self.old_token.functions.balanceOf(_address).call()
        if user_balance_old > 0:
            user_balance_new = self.new_token.functions.balanceOf(_address).call()

            nonce = self.web3.eth.getTransactionCount(self.public_address)

            print(f"... balances before: {user_balance_old}/{user_balance_new}", end='', flush=True)

            tx = self.send_transaction(self.airdrop, "airdrop", _address, self.old_token.address, self.new_token.address)

            user_balance_old = self.old_token.functions.balanceOf(_address).call()
            user_balance_new = self.new_token.functions.balanceOf(_address).call()

            print(f", balances after: {user_balance_old}/{user_balance_new}", end='', flush=True)


            if tx:
                print(f', tx: {tx.hex()}', end='', flush=True)
        else:
            print("... not need",end='')
        print("\n")

def load_holders(file_path):    
    df = pd.read_csv(file_path)
    addresses = df['HolderAddress'].tolist()
    return addresses


# переводим права контракта старого токена на контракт airdrop
#airdrop.airdrop_to("0x14ef5b599f1cc8f33879e9c3890fae07e96f339c")

env_variables = read_env_file('./.env')

def retry_function_with_exceptions(func, *args, **kwargs):
    while True:
        try:
            func(*args, **kwargs)
            break  # Если функция выполнена успешно, прерываем цикл
        except ConnectionError:
            pass  # Игнорируем ошибку соединения и продолжаем цикл
        except HTTPError:
            pass  # Игнорируем HTTP ошибки и продолжаем цикл
        except Exception as err:
            print(f"ERROR: {err}")
        print(".", end="", flush=True)
        time.sleep(1)  # Пауза перед повторной попыткой


@click.command()

@click.option('--holders_file', prompt='CSV file path with holders', default='holders.csv', help='The path to the CSV file.')
@click.option('--provider', prompt='Blockchain RPC endpoint', default='http://127.0.0.1:8545', help='The url of RPC-provider')
@click.option('--airdrop_contract', prompt='Airdrop contract', default=env_variables.get('AIRDROP_CONTRACT'), help='The address of Airdrop contract.')
@click.option('--from_contract', prompt='Old Token address (for burn)', default=env_variables.get('OLD_TOKEN_CONTRACT'), help='The address of the Old Token contract. (for burn)')
@click.option('--to_contract', prompt='New Token address (for airdrop)', default=env_variables.get('NEW_TOKEN_CONTRACT'), help='The address of the New Token contract. (for airdrop)')
@click.option('--private_key', prompt='Private key of Owner', help='The private key for calls to contracts', default = "read from .secret")
def main(holders_file, provider, airdrop_contract, from_contract, to_contract, private_key):

    start_time = time.time()

    if private_key == "read from .secret":
        private_key_file_path = ".secret"
        if not os.path.exists(private_key_file_path):
            raise FileNotFoundError(f"Private key file {private_key_file_path} not found")

        with open(private_key_file_path, 'r') as file:
            private_key = file.read().strip()


    addresses = load_holders(holders_file)
    print(f"addresses: {len(addresses)}")

    airdrop = Airdrop(
        provider=provider,
        _airdrop_address = airdrop_contract, 
        _old_token_address = from_contract, 
        _new_token_address = to_contract, 
        _private_key = private_key
    )
    
    print(f"Owner: {airdrop.public_address}")
    try:
        print(f"Owner of Old Token: {airdrop.old_token.functions.contractOwner().call()}")
    except:
        print("Can't get OldToken owner")

    airdrop_balance = airdrop.get_airdrop_balance()
    if(airdrop_balance == 0):
        print(f"Airdrop contract balance is 0. Please, top up. {airdrop.airdrop.address}")
        return 
    print(f"Airdrop balance: {airdrop_balance}")
    #oldtoken ownership to contract
    print("Transfer owner OldToken to Airdrop")
    #airdrop.send_transaction(airdrop.old_token, "transferOwner", airdrop.airdrop.address)
    retry_function_with_exceptions(airdrop.send_transaction, airdrop.old_token, "transferOwner", airdrop.airdrop.address)
    

    #Run airdrop for users
    n = 0
    for address in addresses:
        n += 1
        #if n > 3:
        #    break
        print(f"Airdrop {n}/{len(addresses)} {address}", end='', flush=True)
        retry_function_with_exceptions(airdrop.airdrop_to, address)
    #oldtoken ownership to owner
    print("Transfer owner OldToken to Owner")
    retry_function_with_exceptions(airdrop.send_transaction, airdrop.airdrop, "transferContractOwner", airdrop.old_token.address, airdrop.public_address)
    #airdrop.send_transaction(airdrop.airdrop, "transferContractOwner", airdrop.old_token.address, airdrop.public_address)

    end_time = time.time()

    execution_time = end_time - start_time
    hours, remainder = divmod(execution_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Execution time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")


if __name__ == '__main__':
    main()