struct Escrow:
    id: public(uint256)
    party_from: public(address)
    party_to: public(address)
    value: public(uint256)
    fee: public(uint256)
    released: public(uint256)
    collected: public(uint256)
    funded: public(bool)
    closed: public(bool)
    closing_time: uint256

owner: address
escrows: map(uint256, Escrow)
    
@internal
def _check_is_open():
    assert not self.closed, "E_CLOSED"

@internal
def _check_is_funded():
    assert self.funded, "E_NOT_FUNDED"
    
@internal
def _check_sender_is(expected: address, sender: address):
    assert sender == expected, "E_INVALID_ORIGIN"

@external
def __init__(_party_from: address, _party_to: address, _value: uint256, _fee: uint256):
    self.party_from = _party_from
    self.party_to = _party_to
    self.value = _value
    self.fee = _fee
    self.released = 0
    self.collected = 0
    self.funded = False
    self.closed = False
    self.owner = msg.sender
    self.closing_time =  block.timestamp + 31536000   # 1 year


@external
@payable
def fund():
    self._check_is_open()
    self._check_sender_is(msg.sender, self.party_from)
    
    # Check that we are receiving the expected amount
    assert not self.funded, "E_ALREADY"
    assert self.value + self.fee == msg.value, "E_INVALID_VALUE"
    
    # If we have any fee to collect, go ahead
    if self.fee > 0:
        send(self.owner, self.fee)
        
    # We are funded
    self.funded = True


@external    
def release(_to_release: uint256):
    self._check_is_open()
    self._check_sender_is(msg.sender, self.party_from)
    self._check_is_funded() 
    
    # Check that we received a valid value to release
    assert _to_release > 0, "E_INVALID_VALUE"
    assert self.released + _to_release <= self.value, "E_TOO_MUCH"
    
    self.released += _to_release


@external
def collect(_to_collect: uint256):
    self._check_is_open()
    self._check_sender_is(msg.sender, self.party_to)
    self._check_is_funded() 
    
    # Check that we received a valid value to collect
    assert _to_collect > 0, "E_INVALID_VALUE"
    assert self.collected + _to_collect <= self.released, "E_TOO_MUCH"

    send(self.party_to, _to_collect)
    self.collected += _to_collect


@external
def close():
    self._check_is_open()
    self._check_sender_is(msg.sender, self.owner)
    
    # Only allow to close after the expiration date
    assert self.closing_time <= block.timestamp, "E_TOO_SOON"

    # Whatever hasn't been collected within the deadline
    # send it back to the owner of the contract
    remaining: uint256 = (self.value - self.collected)
    if self.funded and remaining > 0: 
        send(self.owner, remaining)
    
    self.closed = True