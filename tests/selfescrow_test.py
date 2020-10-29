import pytest
import brownie

VALUE = 100
FEE = 1


@pytest.fixture
def selfescrow_contract_no_fee(selfescrow, accounts):
    # deploy the contract with the initial value as a constructor argument
    yield selfescrow.deploy(
        accounts[1],
        accounts[2],
        VALUE,
        0,
        {'from': accounts[0]})

@pytest.fixture
def selfescrow_contract(selfescrow, accounts):
    # deploy the contract with the initial value as a constructor argument
    yield selfescrow.deploy(
        accounts[1],
        accounts[2],
        VALUE,
        FEE,
        {'from': accounts[0]})



def test_initial_state(selfescrow_contract, accounts):
    # Check if the constructor of the contract is set up properly
    assert selfescrow_contract.party_from() == accounts[1]
    assert selfescrow_contract.party_to() == accounts[2]
    assert selfescrow_contract.value() == VALUE
    assert selfescrow_contract.fee() == FEE
    assert selfescrow_contract.released() == 0
    assert selfescrow_contract.collected() == 0
    assert not selfescrow_contract.funded()
    assert selfescrow_contract.balance() == 0


def test_closed(selfescrow_contract, accounts, chain):
    chain.sleep(31536000)   # Fast forward 1 year
    selfescrow_contract.close({'from': accounts[0]})
    
    with brownie.reverts("E_CLOSED"):
        selfescrow_contract.fund({'from': accounts[2]})
    with brownie.reverts("E_CLOSED"):
        selfescrow_contract.release(0, {'from': accounts[2]})
    with brownie.reverts("E_CLOSED"):
        selfescrow_contract.collect(0, {'from': accounts[2]})
    with brownie.reverts("E_CLOSED"):
        selfescrow_contract.close({'from': accounts[2]})

def test_fund(selfescrow_contract, accounts):
    with brownie.reverts("E_INVALID_ORIGIN"):
        selfescrow_contract.fund({'from': accounts[2]})
    with brownie.reverts("E_INVALID_VALUE"):
        selfescrow_contract.fund({'from': accounts[1], 
                                  'amount': VALUE / 2})
    
    old_balance = accounts[0].balance()
    selfescrow_contract.fund({'from': accounts[1], 
                              'amount': VALUE + FEE})
    with brownie.reverts("E_ALREADY"):
        selfescrow_contract.fund({'from': accounts[1], 
                                  'amount': VALUE + FEE})
    assert accounts[0].balance() == old_balance + FEE
    

def test_release(selfescrow_contract, accounts):
    with brownie.reverts("E_INVALID_ORIGIN"):
        selfescrow_contract.release(0, {'from': accounts[2]})
    with brownie.reverts("E_NOT_FUNDED"):
        selfescrow_contract.release(1, {'from': accounts[1]})
    selfescrow_contract.fund({'from': accounts[1], 
                              'amount': VALUE + FEE})
    with brownie.reverts("E_INVALID_VALUE"):
        selfescrow_contract.release(0, {'from': accounts[1]})
        
    with brownie.reverts("E_TOO_MUCH"):
        selfescrow_contract.release(VALUE + FEE, {'from': accounts[1]})
    selfescrow_contract.release(VALUE / 2, {'from': accounts[1]})    
    assert selfescrow_contract.released() == VALUE / 2
    selfescrow_contract.release(VALUE / 2, {'from': accounts[1]})    
    assert selfescrow_contract.released() == VALUE
    with brownie.reverts("E_TOO_MUCH"):
        selfescrow_contract.release(1, {'from': accounts[1]})

def test_collect(selfescrow_contract, accounts):
    with brownie.reverts("E_INVALID_ORIGIN"):
        selfescrow_contract.collect(0, {'from': accounts[1]})
        
    with brownie.reverts("E_NOT_FUNDED"):
        selfescrow_contract.collect(1, {'from': accounts[2]})
        
    selfescrow_contract.fund({'from': accounts[1], 
                              'amount': VALUE + FEE})
    with brownie.reverts("E_INVALID_VALUE"):
        selfescrow_contract.collect(0, {'from': accounts[2]})
   
    # Testing the release/collect cycle
    old_balance = accounts[2].balance()
    selfescrow_contract.release(VALUE / 2, {'from': accounts[1]})
    selfescrow_contract.collect(VALUE / 2, {'from': accounts[2]})
    assert selfescrow_contract.collected() == VALUE / 2
    assert accounts[2].balance() == old_balance + VALUE / 2

    # Already collected everything available
    with brownie.reverts("E_TOO_MUCH"):
        selfescrow_contract.collect(1, {'from': accounts[2]})
    
    # Release the rest
    selfescrow_contract.release(VALUE / 2, {'from': accounts[1]})
    selfescrow_contract.collect(VALUE / 2, {'from': accounts[2]})    
    assert selfescrow_contract.collected() == VALUE
    with brownie.reverts("E_TOO_MUCH"):
        selfescrow_contract.collect(1, {'from': accounts[2]})

def test_close(selfescrow_contract, accounts, chain):
    
    with brownie.reverts("E_INVALID_ORIGIN"):
        selfescrow_contract.close({'from': accounts[1]})
    with brownie.reverts("E_INVALID_ORIGIN"):
        selfescrow_contract.close({'from': accounts[2]})
    with brownie.reverts("E_TOO_SOON"):
        selfescrow_contract.close({'from': accounts[0]})
    
    selfescrow_contract.fund({'from': accounts[1], 
                              'amount': VALUE + FEE})
    chain.sleep(31536000)   # Fast forward 1 year
    to_close = selfescrow_contract.value() - selfescrow_contract.collected()
    old_balance = accounts[0].balance()
    selfescrow_contract.close({'from': accounts[0]})
    assert accounts[0].balance() == \
                old_balance + to_close
                
    
        
"""
    # set the value to 10
    selfescrow_contract.set(10, {'from': accounts[0]})
    assert selfescrow_contract.storedData() == 10  # Directly access storedData

    # set the value to -5
    selfescrow_contract.set(-5, {'from': accounts[0]})
    assert selfescrow_contract.storedData() == -5
"""