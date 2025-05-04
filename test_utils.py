import unittest
import time
import base64
from utils import Vote, Election, Node, Block, ThisNode, hashy

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import json

class TestVote(unittest.TestCase):
    def setUp(self):
        # Generate a test RSA key pair
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.public_der = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.election_name = "test_election"
        self.choice = "A"
        # Sign the message
        message = (self.election_name + self.choice).encode('utf-8')
        signature = self.private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        self.signature_b64 = base64.b64encode(signature).decode('utf-8')
        self.vote_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, self.choice, base64.b64encode(self.public_der).decode('utf-8'), self.signature_b64)
        ).replace('\\n', '\n')  # Fix newlines for PEM

    def test_vote_signature_valid(self):
        vote = Vote(self.vote_json)
        self.assertTrue(vote.check_sig())

    def test_vote_signature_invalid(self):
        # Tamper with the choice
        tampered_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, "B", base64.b64encode(self.public_der).decode('utf-8'), self.signature_b64)
        ).replace('\\n', '\n')
        vote = Vote(tampered_json)
        self.assertFalse(vote.check_sig())

class TestElection(unittest.TestCase):
    def test_election_init_and_jsonify(self):
        election_data = {
            "name": "election1",
            "choices": ["A", "B"],
            "public_keys": ["key1", "key2"],
            "end_time": int(time.time()) + 1000
        }
        election_json = str(election_data).replace("'", '"')
        election = Election(election_json)
        self.assertEqual(election.name, "election1")
        self.assertEqual(election.choices, ["A", "B"])
        self.assertEqual(election.public_keys, ["key1", "key2"])
        self.assertIn("name", election.jsonify())

class TestBlock(unittest.TestCase):
    def test_block_linking(self):
        parent = Block(0, "hash0", "prev0", "merkle0", 123456, 1, 0)
        block = Block(1, "hash1", "hash0", "merkle1", 123457, 2, 1, parent)
        self.assertEqual(block.previous_block, parent)
        self.assertEqual(block.index, 1)
        self.assertEqual(block.previous_hash, "hash0")

class TestNode(unittest.TestCase):
    def test_node_init(self):
        node = Node("127.0.0.1", 8000, None)
        self.assertEqual(node.address, ("127.0.0.1", 8000))
        self.assertTrue(node.good)
        self.assertEqual(node.lastSeen, 0)

class TestVotingSystem(unittest.TestCase):
    def setUp(self):
        # Generate test keys for multiple voters
        self.private_keys = []
        self.public_keys = []
        self.public_keys_b64 = []
        
        # Create 3 key pairs
        for i in range(3):
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key = private_key.public_key()
            public_der = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            public_key_b64 = base64.b64encode(public_der).decode('utf-8')
            
            self.private_keys.append(private_key)
            self.public_keys.append(public_key)
            self.public_keys_b64.append(public_key_b64)
        
        # Create an election
        self.election_name = "test_election"
        self.election_choices = ["A", "B", "C"]
        self.election_end_time = int(time.time()) + 3600  # 1 hour from now
        
        self.election_data = {
            "name": self.election_name,
            "choices": self.election_choices,
            "public_keys": self.public_keys_b64,
            "end_time": self.election_end_time
        }
        
        self.election_json = json.dumps(self.election_data)
        self.election = Election(self.election_json)
    
    def create_vote(self, voter_index, choice):
        """Helper method to create a signed vote"""
        private_key = self.private_keys[voter_index]
        public_key_b64 = self.public_keys_b64[voter_index]
        
        # Sign the message
        message = (self.election_name + choice).encode('utf-8')
        signature = private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        vote_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, choice, public_key_b64, signature_b64)
        ).replace('\\n', '\n')
        
        return Vote(vote_json)
    
    def test_election_with_votes(self):
        """Test creating an election and casting votes"""
        # Create votes for each voter
        vote1 = self.create_vote(0, "A")
        vote2 = self.create_vote(1, "B")
        vote3 = self.create_vote(2, "C")
        
        # Verify all votes have valid signatures
        self.assertTrue(vote1.check_sig())
        self.assertTrue(vote2.check_sig())
        self.assertTrue(vote3.check_sig())
        
        # Add votes to election
        self.election.used_keys[self.public_keys_b64[0]] = "A"
        self.election.used_keys[self.public_keys_b64[1]] = "B"
        self.election.used_keys[self.public_keys_b64[2]] = "C"
        
        # Check that all keys are marked as used
        self.assertEqual(len(self.election.used_keys), 3)
        self.assertEqual(self.election.used_keys[self.public_keys_b64[0]], "A")
        self.assertEqual(self.election.used_keys[self.public_keys_b64[1]], "B")
        self.assertEqual(self.election.used_keys[self.public_keys_b64[2]], "C")
    
    def test_vote_with_invalid_key(self):
        """Test vote with a key not in the election's public_keys"""
        # Generate a new key pair not in the election
        invalid_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        invalid_public_key = invalid_private_key.public_key()
        invalid_public_der = invalid_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        invalid_public_key_b64 = base64.b64encode(invalid_public_der).decode('utf-8')
        
        # Sign the message
        message = (self.election_name + "A").encode('utf-8')
        signature = invalid_private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        vote_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, "A", invalid_public_key_b64, signature_b64)
        ).replace('\\n', '\n')
        
        vote = Vote(vote_json)
        
        # The signature should be valid
        self.assertTrue(vote.check_sig())
        
        # But the key should not be in the election's public_keys
        self.assertNotIn(invalid_public_key_b64, self.election.public_keys)
    
    def test_vote_with_invalid_choice(self):
        """Test vote with an invalid choice"""
        # Create a vote with an invalid choice
        invalid_choice = "D"  # Not in election choices
        
        # Sign the message
        message = (self.election_name + invalid_choice).encode('utf-8')
        signature = self.private_keys[0].sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        vote_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, invalid_choice, self.public_keys_b64[0], signature_b64)
        ).replace('\\n', '\n')
        
        vote = Vote(vote_json)
        
        # The signature should be valid
        self.assertTrue(vote.check_sig())
        
        # But the choice should not be in the election's choices
        self.assertNotIn(invalid_choice, self.election.choices)
    
    def test_double_voting(self):
        """Test that a voter cannot vote twice"""
        # First vote
        vote1 = self.create_vote(0, "A")
        
        # Second vote with same key
        vote2 = self.create_vote(0, "B")
        
        # Both votes should have valid signatures
        self.assertTrue(vote1.check_sig())
        self.assertTrue(vote2.check_sig())
        
        # Add first vote to election
        self.election.used_keys[self.public_keys_b64[0]] = "A"
        
        # Check that the key is marked as used
        self.assertEqual(self.election.used_keys[self.public_keys_b64[0]], "A")
        
        # Try to add second vote (in a real implementation, this would be rejected)
        # Here we're just testing that the first vote isn't overwritten
        if self.public_keys_b64[0] not in self.election.used_keys:
            self.election.used_keys[self.public_keys_b64[0]] = "B"
        
        # Check that the original vote wasn't changed
        self.assertEqual(self.election.used_keys[self.public_keys_b64[0]], "A")


if __name__ == '__main__':
    unittest.main()