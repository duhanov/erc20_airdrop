PRIVATE_KEY=$(cat .secret)
INITIAL_BALANCE=100000000000000000000

ganache-cli --fork https://bsc-dataseed.binance.org/ --account "0x$PRIVATE_KEY,$INITIAL_BALANCE"
# -p 8545
# --networkId 56