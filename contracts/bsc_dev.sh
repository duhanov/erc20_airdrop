PRIVATE_KEY=$(cat .secret)
INITIAL_BALANCE=100000000000000000000

ganache-cli --account "0x$PRIVATE_KEY,$INITIAL_BALANCE" --networkId 1337
# -p 8545
# --networkId 56