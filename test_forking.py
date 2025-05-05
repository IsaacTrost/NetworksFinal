import argparse
import subprocess
import time
import os
import signal
from forking_node import ForkingNode
from light_node import LightNode
from peer import Peer
from election import Election
from vote import Vote
import threading

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import utils
import base64
import json
import time
from multiprocessing import Process

election_name = "election"
def setUp(name):
    private_keys = []
    public_keys = []
    public_keys_b64 = []
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
    election_name = name
    election_choices = ["A", "B", "C"]
    election_end_time = int(time.time()) + 180  # 1 minute from now
    
    election_data = {
        "name": election_name,
        "choices": election_choices,
        "public_keys": public_keys_b64,
        "end_time": election_end_time
    }
    
    election_json = json.dumps(election_data)
    return Election(election_json), private_keys, public_keys_b64
    
def create_vote(election, voter_index, choice, private_keys, public_keys_b64):
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

def minor1(name, port, tracker_ip, tracker_port):
    """Start a miner node that forks the blockchain."""
    print(f"Starting forking node on port {port}...")
    ele, private_keys, public_keys_b64 = setUp("minor 1 election")
    # create 3 votes
    vote1 = create_vote(ele, 0, "A", private_keys, public_keys_b64)
    vote2 = create_vote(ele, 1, "B", private_keys, public_keys_b64)
    vote3 = create_vote(ele, 2, "C", private_keys, public_keys_b64)

    miner = ForkingNode(name = name, port=port, tracker_ip=tracker_ip, tracker_port=tracker_port, hold_count=10)
    miner.mine()
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down miner.")
        miner.stop()
def minor2(name, port, tracker_ip, tracker_port):
    """Start a miner node that forks the blockchain."""
    print(f"Starting forking node on port {port}...")
    ele, private_keys, public_keys_b64 = setUp("minor 2 election")
    # create 3 votes
    vote1 = create_vote(ele, 0, "A", private_keys, public_keys_b64)
    vote2 = create_vote(ele, 1, "B", private_keys, public_keys_b64)
    vote3 = create_vote(ele, 2, "C", private_keys, public_keys_b64)
    miner = ForkingNode(name = name, port=port, tracker_ip=tracker_ip, tracker_port=tracker_port, hold_count=20)
    miner.mine()
    miner.send_election(ele)
    miner.send_vote(vote1)
    miner.send_vote(vote2)
    miner.send_vote(vote3)
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down miner.")
        miner.stop()

def sender(name, port, tracker_ip, tracker_port):
    """Start a sender node that sends votes to the network."""
    print(f"Starting sender node on port {port}...")
    ele, private_keys, public_keys_b64 = setUp("sender election")
    # create 3 votes
    vote1 = create_vote(ele, 0, "A", private_keys, public_keys_b64)
    vote2 = create_vote(ele, 1, "B", private_keys, public_keys_b64)
    vote3 = create_vote(ele, 2, "C", private_keys, public_keys_b64)
    sender = LightNode(name = name, port=port, tracker_ip=tracker_ip, tracker_port=tracker_port)
    time.sleep(6)
    sender.send_election(ele)
    sender.send_vote(vote1)
    sender.send_vote(vote2)
    sender.send_vote(vote3)
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down sender.")
        sender.stop()
def observer(name, port, tracker_ip, tracker_port):
    """Start a normal observer node."""
    print(f"Starting observer node on port {port}...")
    observer = Peer(name = name, port=port, tracker_ip=tracker_ip, tracker_port=tracker_port)
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down observer.")
        observer.stop()

def tracker(name, port):
    """Start the tracker node."""
    print(f"Starting tracker node on port {port}...")
    tracker = Peer(name = name, port=port)
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down tracker.")
        tracker.stop()

def wait_to_mine(name, port, tracker_ip, tracker_port):
    """Start a miner node that waits for a certain amount of time before mining."""
    print(f"Starting forking node on port {port}...")
    miner = Peer(name = name, port=port, tracker_ip=tracker_ip, tracker_port=tracker_port)
    while True:
        if miner.biggest_chain is not None and miner.biggest_chain.index > 17:
            print(f"Starting mining on {name}...")
            miner.mine()
            break
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down miner.")
        miner.stop()




def main():
    parser = argparse.ArgumentParser(description="Test blockchain forking scenario.")
    parser.add_argument('--num-observers', type=int, default=1, help='Number of normal observer peers.')
    parser.add_argument('--tracker-port', type=int, default=5000, help='Tracker port.')
    parser.add_argument('--duration', type=int, default=300, help='Approximate test duration in seconds.')

    args = parser.parse_args()

    processes = []

    # Start tracker
    tracker_process = Process(target=tracker, args=("tracker", args.tracker_port))
    tracker_process.start()
    processes.append(tracker_process)
    time.sleep(1)  # Give some time for the tracker to initialize

    # Start sender node
    sender_process = Process(target=sender, args=("sender", 5003, "127.0.0.1", args.tracker_port))
    sender_process.start()
    processes.append(sender_process)
    time.sleep(1)  # Give some time for the sender node to initialize

    # Start miner nodes
    miner1_process = Process(target=minor1, args=("miner1", 5001, "127.0.0.1", args.tracker_port))
    miner1_process.start()
    processes.append(miner1_process)
    time.sleep(1)  # Give some time for the miner node to initialize

    miner2_process = Process(target=minor2, args=("miner2", 5002, "127.0.0.1", args.tracker_port))
    miner2_process.start()
    processes.append(miner2_process)
    time.sleep(1)  # Give some time for the miner node to initialize

    # Start observer nodes
    for i in range(args.num_observers):
        observer_process = Process(target=observer, args=(f"observer{i+1}", 5004 + i, "127.0.0.1", args.tracker_port))
        observer_process.start()
        processes.append(observer_process)
    time.sleep(1)  # Give some time for the observer nodes to initialize

    # Start wait-to-mine node
    wait_to_mine_process = Process(target=wait_to_mine, args=("wait_to_mine", 5005 + args.num_observers, "127.0.0.1", args.tracker_port))
    wait_to_mine_process.start()
    processes.append(wait_to_mine_process)
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("Test interrupted.")

    # Terminate all processes
    for process in processes:
        process.terminate()
if __name__ == "__main__":
    main()