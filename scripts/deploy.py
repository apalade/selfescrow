from brownie import accounts, selfescrow

def main(from_address):
    acct_from = accounts.load('acct_from')
    acct_to = accounts.load('acct_to')
    acct_owner = accounts.load('acct_owner')
    selfescrow.deploy(acct_from.address, 
        acct_to.address, 100, 0, 
        {'from': acct_owner})