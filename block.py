from hashlib import sha256

import json

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    @staticmethod
    def fromDict(blockDict):
        block = Block(blockDict['index'], blockDict['transactions'], blockDict['timestamp'], blockDict['previous_hash'], blockDict['nonce'])
        block.hash = blockDict['hash']
        return block

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def __str__(self):
        return f"index:{self.index}, timestamp:{self.timestamp}, previous_hash:{self.previous_hash}"

    def __repr__(self):
        return str(self)