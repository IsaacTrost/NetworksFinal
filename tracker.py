from election import Election
from vote import Vote
from peer import Peer
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import utils
import base64
import json
import time
private_keys = []
public_keys = []
public_keys_b64 = []
election_name = "election"
def setUp():
    # Generate test keys for multiple voters
    
    
    # Create 3 key pairs
    for i in range(3):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        public_key_b64 = base64.b64encode(public_der).decode('utf-8')
        
        private_keys.append(private_key)
        public_keys.append(public_key)
        public_keys_b64.append(public_key_b64)
    
    # Create an election
    election_name = "test_election"
    election_choices = ["A", "B", "C"]
    election_end_time = int(time.time()) + 3600  # 1 hour from now
    
    election_data = {
        "name": election_name,
        "choices": election_choices,
        "public_keys": public_keys_b64,
        "end_time": election_end_time
    }
    
    election_json = json.dumps(election_data)
    return Election(election_json)
    
def create_vote(election, voter_index, choice):
    """Helper method to create a signed vote"""
    
    private_key = private_keys[voter_index]
    public_key_b64 = public_keys_b64[voter_index]
    
    # Sign the message
    message = (election_name + choice).encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    vote_json = (
        '{"election_name": "%s", "choice": "%s", "public_key": "%s", "signature": "%s"}'
        % (election_name, choice, public_key_b64, signature_b64)
    ).replace('\\n', '\n')
    
    return Vote(vote_json)

if __name__ == "__main__":
    # Example usage
    tracker = Peer("tracker", port=5000)
    ele = setUp()
    vote1 = create_vote(ele, 0, "A")
    vote2 = create_vote(ele, 1, "A")
    vote3 = create_vote(ele, 2, "A")
    print(ele.jsonify())
    tracker.send_election(ele)
    tracker.mine()
    time.sleep(20)
    tracker.send_vote(vote1)
    tracker.send_vote(vote2)
