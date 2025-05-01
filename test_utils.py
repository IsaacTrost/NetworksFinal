import unittest
import time
import base64
from utils import Vote, Election, Node, Block, ThisNode, hashy

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class TestVote(unittest.TestCase):
    def setUp(self):
        # Generate a test RSA key pair
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
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
            % (self.election_name, self.choice, self.public_pem.replace('\n', '\\n'), self.signature_b64)
        ).replace('\\n', '\n')  # Fix newlines for PEM

    def test_vote_signature_valid(self):
        vote = Vote(self.vote_json)
        self.assertTrue(vote.check_sig())

    def test_vote_signature_invalid(self):
        # Tamper with the choice
        tampered_json = (
            '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
            % (self.election_name, "B", self.public_pem.replace('\n', '\\n'), self.signature_b64)
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

if __name__ == '__main__':
    unittest.main()