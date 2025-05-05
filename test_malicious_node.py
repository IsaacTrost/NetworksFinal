# filepath: /home/wisaac/school/CSEE4119_computer_networks/NetworksFinal/malicious_node.py
from peer import Peer
from election import Election
from vote import Vote
import base64
import json
from utils import *
from block import Block
# ... other necessary imports ...
import random
import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import copy # For deep copying objects before tampering

class MaliciousNode(Peer):
    def __init__(self, name, port, tracker_ip=None, tracker_port=None, attack_mode="none"):
        super().__init__(name, port, tracker_ip, tracker_port)
        self.attack_mode = attack_mode
        self.write_log(f"Initialized MaliciousNode in mode: {self.attack_mode}")
        # Add any state needed for specific attacks
        self.stashed_block = None # For holding back blocks

    def mining(self, pre_adj = 0, post_adj = 0):
        self.write_log("ATTACK: Attempting to mine with fake PoW pre_adj {pre_adj} post_adj {post_adj}")
        # Find a nonce that meets a *very low* difficulty, but create block
        # header claiming the *correct* (high) difficulty.

        index = 0
        prev_hash = b'\x00' * 32
        with self.data_lock:
            biggest_chain = self.biggest_chain
        old_longest = self.biggest_chain # for if there are updates mid mining below, we want to break and work on the new longer chain
        self.move_to_ended() # cleans up the open elections, and moves them to the ended elections, and generates end of election events
        objects = self.get_objects() # gets the objects that will be included in the block
        merkle_root = self.get_merkle_root(objects) # gets the merkle root of the objects
        if biggest_chain is not None:
            prev_hash = biggest_chain.hash # case where this is the first block in the chain
            index = biggest_chain.index + 1
        difficulty = self.getDifficulty(biggest_chain) - pre_adj # gets the difficulty of the block
        timestamp = int(time.time()).to_bytes(8, byteorder='big')
        nonce = 0
        while nonce < 2**32: # max for 4 byte num
            if nonce % 10000000 == 0:
                self.write_log(f"Mining block {index} with nonce {nonce}")
                if self.biggest_chain != old_longest: # new block was recieved, need to break and start over
                    break
            block_header = b''.join([index.to_bytes(4, byteorder='big'), prev_hash, merkle_root, timestamp, difficulty.to_bytes(4, byteorder='big'), nonce.to_bytes(4, byteorder='big')])
            header_hash = hashy(block_header)
            if check_proof_of_work(header_hash, difficulty-post_adj): #checks if the hash we just made will work
                if post_adj > 0 and check_proof_of_work(header_hash, difficulty):
                    continue
                # print(f"Found a block: {header_hash}")
                block = Block(index, header_hash, prev_hash, merkle_root, int.from_bytes(timestamp, byteorder='big'), difficulty, nonce, biggest_chain, data=objects)
                self.broadcast(None, BLOCK, block.get_sendable()) # broadcast the block to the network
                self.verify_block(block.get_sendable(), old_longest, None) # verify the block
                break
            
            nonce += 1
    
    def send_election(self, election):
        """
        Send an election to the network.
        """
        self.write_log(f"Sending election: {election.jsonify()}")
        self.broadcast(None, ELECTION, election.jsonify().encode('utf-8'))
    def send_vote(self, vote):
        """
        Send a vote to the network.
        """
        self.write_log(f"Sending vote: {vote.jsonify()}")
        self.broadcast(None, VOTE, vote.jsonify().encode('utf-8'))


private_keys = []
public_keys = []
public_keys_b64 = []
election_name = "election"
def setUp():
    # Generate test keys for multiple voters
    
    
    # Create 3 key pairs
    for i in range(4):
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
        "public_keys": public_keys_b64[:3],
        "end_time": election_end_time
    }
    
    election_json = json.dumps(election_data)
    return Election(election_json)
    
def create_vote(election, voter_index, choice):
    """Helper method to create a signed vote"""
    
    private_key = private_keys[voter_index]
    public_key_b64 = public_keys_b64[voter_index]
    
    # Sign the message
    signature_b64 = Vote.sign(private_key, election.hashy, choice)
    election_hash = base64.b64encode(election.hashy).decode('utf-8')
    vote_data = {
        "election_hash": election_hash,
        "choice": choice,
        "public_key": public_key_b64,
        "signature": signature_b64
    }
    vote_json = json.dumps(vote_data)
    
    return Vote(vote_json)

if __name__ == "__main__":
    victim_node = Peer("VictimNode", 5000)
    node = MaliciousNode("MaliciousNode", 5001, tracker_ip="localhost", tracker_port=5000)
    victim_node.write_log("TEST: Testing valid block\n")
    node.mining(pre_adj=0, post_adj=0)  # Normal mining
    time.sleep(1)  # Wait for the block to be mined
    victim_node.write_log("TEST: Pre adjustment low attack\n")
    node.mining(pre_adj=10, post_adj=0)  
    time.sleep(1)  # Wait for the block to be mined
    victim_node.write_log("TEST: Post adjustment low attack\n")
    node.mining(pre_adj=0, post_adj=100)  
    time.sleep(1)  # Wait for the block to be mined
    
    ele = setUp()
    node.send_election(ele)
    victim_node.write_log("TEST: Testing valid vote\n")
    vote1 = create_vote(ele, 0, "A")
    vote2 = create_vote(ele, 1, "B")
    node.send_vote(vote1)
    node.send_vote(vote2)
    time.sleep(1)  # Wait for the votes to be sent
    victim_node.write_log("TEST: Testing duplicate vote\n")
    dup_vote = create_vote(ele, 0, "B")
    node.send_vote(dup_vote)

    time.sleep(1)  # Wait for the votes to be sent
    victim_node.write_log("TEST: Testing vote with invalid signature\n")
    vote_invalid = create_vote(ele, 2, "A")
    signature_list = list(vote_invalid.signature)
    signature_list[5] = chr(ord(signature_list[5]) + 1)
    vote_invalid.signature = ''.join(signature_list)
    node.send_vote(vote_invalid)

    time.sleep(1)  # Wait for the votes to be sent
    victim_node.write_log("TEST: Testing vote with pkey not in election\n")
    vote4 = create_vote(ele, 3, "A")
    node.send_vote(vote4)


    time.sleep(20)


    