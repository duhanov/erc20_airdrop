import click
import colorlog
import logging
import time
import json

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

class Airdrop:
    web3=None
    airdrop = None
    private_key = None
    public_address = None
    
    def __init__(self, _airdrop_address, _old_token_address, _new_token_address, _private_key):
        _airdrop_address = Web3.toChecksumAddress(_airdrop_address)
        _old_token_address = Web3.toChecksumAddress(_old_token_address)
        _new_token_address = Web3.toChecksumAddress(_new_token_address)

        
        if not _private_key.startswith('0x'):
            _private_key = '0x' + _private_key

        self.web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        if not self.web3.isConnected():
            raise Exception("Web3 is not connected to the network")
        self.airdrop = self.load_contract(_airdrop_address, "contracts/build/contracts/Airdrop.json")
        self.old_token = self.load_contract(_old_token_address, "contracts/build/contracts/PancakeIBEP2E.json")
        self.new_token = self.load_contract(_new_token_address, "contracts/build/contracts/NewToken.json")
        self.private_key = _private_key
        self.public_address = self.web3.eth.account.privateKeyToAccount(self.private_key).address

    def load_contract(self, _address, _abi_path):
        print(f"load_contract({_address})")
        with open(_abi_path, 'r') as file:
            contract_data = json.load(file)
            abi = contract_data['abi']
        return self.web3.eth.contract(address=_address, abi=abi)

    def send_transaction(self, contract, func_name, *args):
        nonce = self.web3.eth.getTransactionCount(self.public_address)
        tx_hash = None
        gas_price = self.web3.eth.gas_price
        try:
            transaction = getattr(contract.functions, func_name)(*args).buildTransaction({
                'nonce': nonce,
                'gasPrice': gas_price
            })
            signed_tx = self.web3.eth.account.signTransaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f'ContractLogicError: {error_message}')

        if tx_hash:
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            print(f'{func_name}({args}): Transaction {tx_hash.hex()}: {tx_receipt}')

    def airdrop_to(self, _address):
        print(f"airdrop_to{_address}")
        _address = Web3.toChecksumAddress(_address)
        user_balance_old = self.old_token.functions.balanceOf(_address).call()
        if user_balance_old > 0:
            user_balance_new = self.new_token.functions.balanceOf(_address).call()

            nonce = self.web3.eth.getTransactionCount(self.public_address)

            print(f"airdrop {user_balance_old}/{user_balance_new} to {_address}")

            self.send_transaction(self.airdrop, "airdrop", _address, self.old_token.address, self.new_token.address)

            user_balance_old = self.old_token.functions.balanceOf(_address).call()
            user_balance_new = self.new_token.functions.balanceOf(_address).call()

            print(f"new balances: {user_balance_old}/{user_balance_new} to {_address}")


def load_holders(file_path):    
    df = pd.read_csv(file_path)

    # Вывод данных из CSV файла
    print("Data from CSV file:")
    print(df)

    # Пример доступа к данным
    addresses = df['HolderAddress'].tolist()


    return addresses

def get_balances(addresses, dnt_address):
    
    balances = []

    dnt = web3.eth.contract(address=dnt_address, abi=DNT_ABI)
    decimals = dnt.functions.decimals().call()
    n = 0
    for address in addresses:
        n += 1
        if n > 3:
            break
        checksum_address = Web3.toChecksumAddress(address)
        balance = dnt.functions.balanceOf(checksum_address).call()
        formatted_balance = balance / (10 ** decimals)

        print(f"{checksum_address}: {formatted_balance}")
        balances.append([checksum_address, balance, formatted_balance])

        time.sleep(0.2)
    return balances



airdrop = Airdrop(
    _airdrop_address = "0x6F74b332Ab9b4e87cb174b2dCf85bDced58C7841",
    _old_token_address = "0x1EDa1f347fcf2bE121458938c6601C0b88E79B69",
    _new_token_address = "0xa47AA0E94110ce431b52D3b8339a47b8C23BdC61",
    _private_key = "0xb69130e1cad456c818bb72bdd8b3ff5c53a132a5f7028b8f8a18b0f326e341db"
)


#old_token_owner = airdrop.old_token.functions.owner().call()
airdrop.send_transaction(airdrop.old_token, "transferOwner", airdrop.airdrop.address)
airdrop.airdrop_to("0x14ef5b599f1cc8f33879e9c3890fae07e96f339c")
airdrop.send_transaction(airdrop.airdrop, "transferContractOwner", airdrop.old_token.address, airdrop.public_address)


# переводим права контракта старого токена на контракт airdrop
#airdrop.airdrop_to("0x14ef5b599f1cc8f33879e9c3890fae07e96f339c")


@click.command()
@click.option('--holders_file', prompt='CSV file path', default='holders.csv', help='The path to the CSV file.')
@click.option('--airdrop_contract', prompt='Airdrop contract', help='The address of Airdrop contract.')
@click.option('--from_contract', prompt='DNT old contract address', help='The address of the old DNT contract.')
@click.option('--to_contract', prompt='New contract address', help='The address of the New contract.')
@click.option('--private_key', prompt='Private key', help='The private key for calls to contracts')
def main(holders_file, airdrop_contract, from_contract, to_contract, private_key):

    start_time = time.time()

    addresses = load_holders(holders_file)
    print(f"addresses: {len(addresses)}")
    #balances = get_balances(addresses, from_contract)

    #non_zero_balances = [bal for bal in balances if bal[1] > 0]
    #non_zero_balances.sort(key=lambda x: x[1], reverse=True)

    #print(f"non_zero_balances: {len(non_zero_balances)}")
    #for item in non_zero_balances:
    #    print(f"{item[0]} {item[1]} {item[2]}")
    #print(f"non_zero_balances: {len(non_zero_balances)}")


#    airdrop = Airdrop(_airdrop_address = airdrop_contract, _old_token_address = from_contract, _new_token_address = to_contract, _private_key = private_key)
    airdrop = Airdrop(_airdrop_address = "0xf92b32e3c01f58d594126b7acef29d9f2837fba8", _old_token_address = "0x2516B65b454127EE43711FAefe24cb95b5efaAa6", _new_token_address = "0xf7fdE5a1356bB466053ACaBfFbA8059C748DC9B7", _private_key = "0xb69130e1cad456c818bb72bdd8b3ff5c53a132a5f7028b8f8a18b0f326e341db")
    n = 0
    for address in addresses:
        n += 1
        if n > 3:
            break
        airdrop.airdrop_to(address)

    end_time = time.time()

    execution_time = end_time - start_time
    hours, remainder = divmod(execution_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Execution time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")


if __name__ == '__main__':
    main()