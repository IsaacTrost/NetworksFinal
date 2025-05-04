from utils import *
from election import Election
from vote import Vote
class Block:
    """
    Simple class to represent a block in the blockchain.
    """
    def __init__(self, index, hashy, previous_hash, merkle_root, timestamp, difficulty, nonce, parent = None, data = []):
        self.previous_block = parent
        self.total_work = difficulty
        if(parent is not None):
            self.total_work += parent.total_work
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.elections = {}
        self.votes = {}
        self.merkle_root = merkle_root
        self.nonce = nonce
        for item in data:
            if type(item) == Vote:
                if item.election_name not in self.votes:
                    self.votes[item.election_name] = []
                self.votes[item.election_name].append(item)
            elif type(item) == Election:
                self.elections[item.name] = item
            else:
                raise ValueError(f"Invalid data type in block: {type(item)}")
            
            

        self.hash = hashy
        self.difficulty = difficulty
    def get_header(self):
        return b''.join([
            self.index.to_bytes(4, byteorder='big'),
            self.previous_hash,
            self.merkle_root,
            self.timestamp.to_bytes(8, byteorder='big'),
            self.difficulty.to_bytes(4, byteorder='big'),
            self.nonce.to_bytes(4, byteorder='big'),
            self.hash
        ]) 
    
    def get_sendable(self):
        """
        Returns the block in a format that can be sent over the network.
        """
        # Creating the header
        header =  self.get_header() 
        # Creating the body (transactions in the block)
        body = b''
        for election in self.elections:
            body += self.elections[election].jsonify().encode('utf-8')
        for vote in self.votes:
            body += self.votes[vote].jsonify().encode('utf-8')
        return header + body
    
    def get_election_peices(self, name):
        """
        Returns the election pieces for the given election name.
        """
        res = ""
        if name in self.elections:
            res += json.dumps({
                "election": self.elections[name].jsonify(),
                "merkle_proof": self.get_merkle_proof(list(self.elections.keys()).index(name))
            })
        if name in self.votes:
            for vote in self.votes[name]:
                res += json.dumps({
                    "vote": vote.jsonify(),
                    "merkle_proof": self.get_merkle_proof(list(self.votes.keys()).index(name) + len(self.elections))
                })
    def create_merkle_tree(self):
        """
        Creates a Merkle Tree from a list of transactions and returns the root hash.
        
        Args:
            transactions: List of transactions (assumed to be in bytes)
        Returns:
            bytes: The merkle tree, represented as a binary tree array
        """
        transactions = []
        for election in self.elections:
            transactions.append(self.elections[election].jsonify().encode('utf-8'))
        for vote in self.votes:
            transactions.append(self.votes[vote].jsonify().encode('utf-8'))
            
        # First, hash all transactions if they aren't already hashed
        leaves = [hashy(tx) for tx in transactions]
        
        # If odd number of transactions, duplicate the last one
        while len(leaves) < 2**MAX_LEVELS:
            leaves.append(b'\x00' * 32)
        tree = leaves
        # Build tree bottom-up
        while len(leaves) > 1:
            next_level = []
            # Process pairs of nodes
            for i in range(0, len(leaves), 2):
                # Concatenate the pair of hashes and hash them together
                combined = leaves[i] + leaves[i + 1]
                next_level.append(hashy(combined))
            leaves = next_level
            tree = leaves + tree

        return tree
    
    def get_merkle_root(self):
        """
        Convenience method to get just the merkle root from a list of transactions.
        
        Args:
            transactions: List of transactions
        Returns:
            bytes: The merkle root hash
        """
        return self.create_merkle_tree()[0]
    
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
        if type(proof) != list:
            proof = self.parse_merkle_proof(proof)
        current_hash = hashy(transaction)
        
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
        proof_list = json.loads(proof)
        parsed_proof = []
        for item in proof_list:
            hash_part = bytes.fromhex(item["hash"])
            is_left = item["is_left"]
            parsed_proof.append((hash_part, is_left))
        return parsed_proof
    
    def get_merkle_proof(self, target_tx_index):
        """
        Generates a Merkle proof for a specific transaction.
        
        Args:
            transactions: List of all transactions
            target_tx_index: Index of the transaction to prove
        Returns:
            list: The proof as a list of (hash, is_left) tuples
        """

        transactions = []
        for election in self.elections:
            transactions.append(self.elections[election].jsonify().encode('utf-8'))
        for vote in self.votes:
            transactions.append(self.votes[vote].jsonify().encode('utf-8'))
        if not transactions:
            return []
            
        # First, hash all transactions
        nodes = [hashy(tx) for tx in transactions]
        
        # If odd number of transactions, duplicate the last one
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        
        # Track the position of our target transaction
        current_index = target_tx_index
        proof = []
        
        while len(nodes) > 1:
            next_level = []
            
            for i in range(0, len(nodes), 2):
                if i + 1 >= len(nodes):
                    next_level.append(nodes[i])
                    continue
                    
                # If this pair includes our target transaction
                if i == current_index - (current_index % 2):
                    # Add the sibling to our proof
                    proof_hash = nodes[i + 1] if current_index % 2 == 0 else nodes[i]
                    is_left = current_index % 2 == 0
                    proof.append((proof_hash, is_left))
                
                combined = nodes[i] + nodes[i + 1]
                next_level.append(hashy(combined))
            
            nodes = next_level
            current_index = current_index // 2
            
            if len(nodes) % 2 == 1 and len(nodes) > 1:
                nodes.append(nodes[-1])
        
        return proof
    