import hashlib
import json
import requests
from time import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

'''
Block structure
- index
- timestamp
- transactions: list of transactions
-   transaction 1：sender/recipient/amount
-   transaction 2：...
-   transaction 3：...
- proof: the number satisfied with hash requirement
- previous_hash hash value of previous block
'''

class BlockChain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.nodes = set()
        self.new_block(proof=100, previous_hash='1') # Create the genesis block

    def register_node(self, address: str) -> None:
        # http://localhost:500 -> localhost:5000
        parsed = urlparse(address) 
        self.nodes.add(parsed.netloc)

    def new_block(self, proof: int, previous_hash: Optional[str]=None) -> Dict[str, Any]:
        block = {'index': len(self.chain) + 1,
                 'timestamp': time(),
                 'transactions': self.transactions,
                 'proof': proof,
                 'previous_hash': previous_hash or self.hash(self.chain[-1])}
        # Clear the transactions packaged by the block
        self.transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        self.transactions.append({'sender': sender,
                                  'recipient': recipient,
                                  'amount': amount})
        # The index of the block which transactions will be packages
        return self.last_block['index'] + 1

    def valid_chain(self, chain: List[Dict[str, Any]]) -> bool:
        prev_block = chain[0]
        ci = 1
        while ci < len(chain):
            block = chain[ci]
            # Check hash of previous block
            if block['previous_hash'] != self.hash(prev_block):
                return False
            # Check POS is correct
            if not self.valid_proof(prev_block['proof'], block['proof']):
                return False
            prev_block = block
            ci += 1
        return True

    def pos(self, last_proof: int) -> int: # proof of work
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    def resolve_conficts(self) -> bool:
        new_chain = None
        max_length = len(self.chain)
        print(self.nodes)
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            print(response.url)
            print(response.status_code)
            if response.status_code == 200:
                j_data = response.json()
                length = j_data['length']
                chain = j_data['chain']
                if (length > max_length) and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        else:
            return False

    @staticmethod
    def valid_proof(prev_proof, proof):
        guess = f'{prev_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # Number of zeros determine the complexity
        return guess_hash[:2] == '00'

    @staticmethod
    def hash(block):
        block_bytes = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_bytes).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]
