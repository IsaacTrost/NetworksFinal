from utils import *
from election import Election
from vote import Vote
from end_of_election import EndOfElection
import json

class Block:
    """
    Simple class to represent a block in the blockchain.
    """
    def __init__(self, index, out_hash, previous_hash, merkle_root, timestamp, difficulty, nonce, parent = None, data = []):
        assert isinstance(index, int), "Index must be an integer"
        assert isinstance(previous_hash, bytes), "Previous hash must be bytes"
        assert isinstance(merkle_root, bytes), "Merkle root must be bytes"
        assert isinstance(timestamp, int), "Timestamp must be int"
        assert isinstance(difficulty, int), "Difficulty must be an integer"
        assert isinstance(nonce, int), "Nonce must be an integer"

        self.previous_block = parent
        self.total_work = difficulty
        if(parent is not None):
            self.total_work += parent.total_work
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.elections = {}
        self.votes = {}
        self.election_ends = {}
        self.merkle_root = merkle_root
        self.nonce = nonce
        self.data = data
        transactions = []
        for data in self.data:
            transactions.append(data.jsonify())

        # First, hash all transactions if they aren't already hashed
        self.leaves = [hashy(tx) for tx in transactions]
        while len(self.leaves) < 2**MAX_LEVELS:
            self.leaves.append(b'\x00' * 32)
        
        for item in self.data:
            if type(item) == Vote:
                if item.election_hash not in self.votes:
                    self.votes[item.election_hash] = []
                self.votes[item.election_hash].append(item)
            elif type(item) == Election:
                self.elections[hashy(item.jsonify())] = item
            elif type(item) == EndOfElection:
                self.election_ends[item.election_hash] = item
            else:
                raise ValueError(f"Invalid data type in block: {type(item)}")
            
            

        self.hash = out_hash 
        self.difficulty = difficulty
    def get_header(self):
        return b''.join([
            self.index.to_bytes(4, byteorder='big'),
            self.previous_hash,
            self.merkle_root,
            self.timestamp.to_bytes(8, byteorder='big'),
            self.difficulty.to_bytes(4, byteorder='big'),
            self.nonce.to_bytes(4, byteorder='big'),
        ]) 
    
    def get_sendable(self):
        """
        Returns the block in a format that can be sent over the network.
        """
        # Creating the header
        header = self.get_header() 
        # Creating the body (transactions in the block)
        body = {}
        count = 0
        for data in self.data:
            body[count] = data.get_json_dict()
            count += 1
        return header + json.dumps(body).encode('utf-8')
    

    def create_merkle_tree(self):
        """
        Creates a Merkle Tree from a list of transactions and returns the root hash.
        
        Args:
            transactions: List of transactions (assumed to be in bytes)
        Returns:
            bytes: The merkle tree, represented as a binary tree array
        """
        # print("ends:", self.election_ends)
        # print("elections: ", self.elections)
        # print("votes: ", self.votes)
        leaves = self.leaves 
        
        # If odd number of transactions, duplicate the last one
        while len(leaves) < 2**MAX_LEVELS:
            leaves.append(b'\x00' * 32)
        tree = []
        tree.append(leaves)
        # Build tree bottom-up
        while len(leaves) > 1:
            next_level = []
            # Process pairs of nodes
            for i in range(0, len(leaves), 2):
                # Concatenate the pair of hashes and hash them together
                combined = leaves[i] + leaves[i + 1]
                next_level.append(hashy(combined))
            leaves = next_level
            tree.append(leaves)

        return tree
    
    def get_merkle_root(self):
        """
        Convenience method to get just the merkle root from a list of transactions.
        
        Args:
            transactions: List of transactions
        Returns:
            bytes: The merkle root hash
        """
        return self.create_merkle_tree()[-1][0]
    
    def verify_merkle_proof(self, transaction, proof):
        """
        Verifies that a transaction is included in the Merkle tree.
        
        Args:
            transaction: The transaction to verify (in bytes)
            proof: List of (hash, is_left) tuples forming the proof path
            merkle_root: The expected Merkle root hash
        Returns:
            bool: True if the proof is valid
        """
        proof = self.parse_merkle_proof(proof)
        current_hash = hashy(transaction.jsonify())
        
        for proof_hash, is_left in proof:
            if is_left:
                current_hash = hashy(proof_hash + current_hash)
            else:
                current_hash = hashy(current_hash + proof_hash)
        
        return current_hash == self.merkle_root
    
    def parse_merkle_proof(self, proof):
        """
        Parses a Merkle proof from a string to a list of (hash, is_left) tuples.
        
        Args:
            proof: The Merkle proof as a string
        Returns:
            list: The parsed proof as a list of (hash, is_left) tuples
        """
        if isinstance(proof, str):
            proof = json.loads(proof)
        
        parsed_proof = []
        for hashy, left in proof:
            if isinstance(hashy, str):
                # If the item is a string, it's a hash
                parsed_proof.append((base64.b64decode(hashy), left))
            else:
                # If it's not a string, it's a boolean
                parsed_proof.append((hashy, left))
        return parsed_proof 
        
    
    def get_merkle_proof(self, target_tx):
        """
        Generates a Merkle proof for a specific transaction.
        
        Args:
            transactions: List of all transactions
            target_tx: Hash of object (bytes)
        Returns:
            list: The proof as a list of (hash, is_left) tuples
        """
        target_tx_index = self.leaves.index(target_tx)
        if target_tx_index == -1:
            raise ValueError("Transaction not found in the block")
         
            
        tree = self.create_merkle_tree()
        
        # Track the position of our target transaction
        current_index = target_tx_index
        proof = []
        
        for level in tree[:-1]:
            # print("Current index:", current_index)
            # print("Level:", level)
            if current_index % 2 == 1:
                proof.append((base64.b64encode(level[current_index - 1]).decode('utf-8'), True))  # Isleft is true because 1 means we are the right side, and the hash we are adding is left
            else:
                proof.append((base64.b64encode(level[current_index + 1]).decode('utf-8'), False))
            current_index = current_index // 2
        return proof
    

    