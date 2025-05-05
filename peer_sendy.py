from vote import Vote
from light_node import LightNode
from election import Election
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
    print(private_keys, public_keys)
    election_name = "test_election"
    election_choices = ["A", "B", "C"]
    election_end_time = int(time.time()) + 30  # 1 minute from now
    
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
    print("CURVE:", public_key_b64)
    
    # Sign the message
    signature_b64 = Vote.sign(private_key, election.hashy, choice)
    election_hash = base64.b64encode(election.hashy).decode('utf-8')
    print(type(signature_b64))
    print(type(election_hash))
    print(type(public_key_b64))
    print(type(choice))
    vote_data = {
        "election_hash": election_hash,
        "choice": choice,
        "public_key": public_key_b64,
        "signature": signature_b64
    }
    vote_json = json.dumps(vote_data)
    
    return Vote(vote_json)

    

import argparse
import time
def main():
    parser = argparse.ArgumentParser(description="Start a well-behaved peer node.")
    parser.add_argument('--port', type=int, required=True, help='Port number for this peer to listen on')
    parser.add_argument('--tracker-ip', type=str, required=False, help='Tracker IP address')
    parser.add_argument('name', type=str, help='Name of the peer')
    parser.add_argument('--tracker-port', type=int, required=False, help='Tracker port number')
    args = parser.parse_args()

    print(f"Starting peer '{args.name}' on port {args.port}, connecting to tracker at {args.tracker_ip}:{args.tracker_port}")
    peer = LightNode(args.name, port=args.port, tracker_ip=args.tracker_ip, tracker_port=args.tracker_port)
    time.sleep(1)  # Give some time for the peer to initialize
    ele = setUp()
    print(ele.jsonify())
    peer.send_election(ele)
    time.sleep(1)
    vote1 = create_vote(ele, 0, "A")
    vote2 = create_vote(ele, 1, "A")
    vote3 = create_vote(ele, 2, "B")
    peer.send_vote(vote1)
    peer.send_vote(vote2)
    time.sleep(10)
    res = peer.request_election(ele.hashy)
    print("RESULTS:", res)
    time.sleep(40)
    res = peer.request_election(ele.hashy)
    print("RESULTS:", res)
    print(res.winner)
    print(res.used_keys)
    # Keep the process alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down peer.")

if __name__ == "__main__":
    main()