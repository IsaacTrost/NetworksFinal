import hashlib

import socket
import json
import threading
import time
from queue import PriorityQueue
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
import base64

MAX_CONNECTIONS = 50
DEFAULT_DIFFICULTY = 16
INIT = 0
VOTE = 1
BLOCK = 2
ELECTION = 3
MAX_BLOCK_SIZE = 1024 * 1024
TARGET = 2**32

#TODO: Add the orphan pool, transactions list, and chain verification
#TODO: Add a way to get a new node up to speed with the chain
def hashy(data):
    """
    Hashes the data using SHA-256.
    """
    return hashlib.sha256(data).hexdigest()

def check_proof_of_work(data, difficulty):
    """
    Checks if the hash of the data has the required number of leading zeros.
    """
    hash_result = hash(data)
    # Check if the bottom 3 bytes are 0
    if hash_result[:4] != b'\x00\x00\x00':
        return False

    # Check if 2^32 - difficulty is less than the next 8 bytes
    target = TARGET - difficulty
    next_8_bytes = int.from_bytes(hash_result[4:12], byteorder='big')
    return next_8_bytes < target


class Election:
    """
    Simple class to represent an election.
    """
    def __init__(self, message):
        try:
            data = json.loads(message)
            name = data["name"]
            choices = data["choices"]
            public_keys = data["public_keys"]
            end_time = data["end_time"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid election message format: {e}")
        self.name = name
        self.choices = choices
        self.public_keys = public_keys
        self.used_keys = {}
        self.votes = {}
        self.total_votes = 0
        self.finished = False
        self.winner = None
        self.timestamp = int(time.time())
        self.end_time = end_time
    
    def jsonify(self):
        """
        Converts the election to JSON format.
        """
        return json.dumps({
            "name": self.name,
            "choices": self.choices,
            "public_keys": self.public_keys,
        })


class Vote:
    """
    Simple class to represent a vote.
    """
    def __init__(self, message):
        try:
            data = json.loads(message)
            election_name = data["election_name"]
            choice = data["choice"]
            public_key = data["public_key"]
            signature = data["signature"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid vote message format: {e}")
        self.election_name = election_name
        self.choice = choice
        self.public_key = public_key
        self.signature = signature
    
    def jsonify(self):
        """
        Converts the vote to JSON format.
        """
        return json.dumps({
            "election_name": self.election_name,
            "choice": self.choice,
            "public_key": self.public_key,
            "signature": self.signature,
        })

    def check_sig(self):
        """
        Checks the signature of the vote.
        Assumes the signature is over (election_name + choice) using the provided public_key.
        """
        

        try:
            # Prepare the message that was signed
            message = (self.election_name + self.choice).encode('utf-8')
            # Load the public key (assume PEM format)
            public_key = serialization.load_pem_public_key(self.public_key.encode('utf-8'))
            # Decode the signature 
            signature_bytes = base64.b64decode(self.signature)
            # Verify the signature
            public_key.verify(
                signature_bytes,
                message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            return False

class Node:
    """
    Simple class to represent a node in the network.
    """
    def __init__(self, ip, port, connection):
        self.address = (ip, port)
        self.connection = connection
        self.good = True
        self.lastSeen = 0


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
        self.data = data
        self.hash = hashy
        self.difficulty = difficulty
        


class ThisNode():
    def __init__(self, name, tracker_ip, tracker_port):
        self.nodes = {}
        self.log = open(f"{name}.log", "a")
        self.log.write(f"{name} initialized.\n")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(0.5)
        self.node_list_lock = threading.Lock()
        self.chain_headers = []
        self.votes = PriorityQueue()
        self.new_elections = PriorityQueue()
        self.active_elections = {}
        self.orphan_blocks = []
        self.blocks = {}
        if tracker_ip and tracker_port:
            self.start_connection(tracker_ip, tracker_port)
            
        

    def mining(self, block):
        """
        Mines a block.
        """
        max_header = None
        max_work = 0
        for head in self.chain_headers:
            if head.total_work > max_work:
                max_work = head.total_work
                max_header = head
        

        index = 0
        prev_hash = b'\x00' * 32
        objects = self.get_objects()
        merkle_root = self.get_merkle_root(objects)
        if max_header is not None:
            prev_hash = max_header.hash # case where this is the first block in the chain
            index = max_header.index + 1
        difficulty = self.getDifficulty(max_header).to_bytes(4, byteorder='big')
        timestamp = int(time.time()-10).to_bytes(8, byteorder='big')
        nonce = 0
        while True:
            while nonce < 2**32:
                block_header = b''.join([index.to_bytes(4, byteorder='big'), prev_hash, merkle_root, timestamp, difficulty, nonce.to_bytes(4, byteorder='big')])
                header_hash = hashy(block_header)
                if check_proof_of_work(header_hash, difficulty):
                    #TODO: logic for finding a valid block
                    pass
            timestamp = min(time.time(), timestamp + 1)
        

    def get_objects(self):
        """
        Gets the objects to be included in the block.
        """
        objects = []
        total_size = 0
        while total_size < MAX_BLOCK_SIZE and len(self.new_elections) > 0:
            thing = self.new_elections.get()
            item = thing[1]
            sizey = len(item)
            if sizey + total_size > MAX_BLOCK_SIZE:
                self.new_elections.put(thing)
                break
            objects.append(item)
            total_size += sizey
        while total_size < MAX_BLOCK_SIZE and len(self.votes) > 0:
            thing = self.votes.get()
            item = thing[1]
            sizey = len(item)
            if sizey + total_size > MAX_BLOCK_SIZE:
                self.votes.put(thing)
                break
            objects.append(item)
            total_size += item

        return objects
            
                
    def start_connection(self, ip, port):
        try:
            self.server.connect((ip, port))
            new_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_connection.connect((ip, port))
            new_connection.send(INIT.to_bytes(2, byteorder='big'))
            response = self.server.recv(4096)
            node_list = json.loads(response)
            for node_info in node_list:
                ip = node_info.get("ip")
                port = node_info.get("port")
                if ip and port:
                    new = self.add_node(Node(ip, port, new_connection))
                    if new:
                        self.start_connection(ip, port)

            self.log.write(f"Initial node list received from tracker: {node_list}\n")
        except Exception as e:
            self.log.write(f"Failed to connect to tracker: {e}\n")

    def add_node(self, node):
        """
        Adds a node to the tracker.
        """
        if node.address in self.nodes:
            self.log.write(f"Node already exists: {node}\n")
            return False
        self.nodes[node.address] = node
        self.log.write(f"Node added: {node}\n")
        return True
    
    def remove_node(self, node):
        """
        Removes a node from the tracker.
        """
        if node in self.nodes:
            self.nodes.remove(node)
            self.log.write(f"Node removed: {node}\n")
        else:
            self.log.write(f"Node not found: {node}\n")

    def accept_connections(self):
        """
        Accepts connections from nodes.
        """
        while True:
            connection = self.server.accept()
            self.log.write(f"Connection accepted: {connection}\n")
            threading.Thread(target=self.talk_to_node, args=(connection,)).start()
        
    def talk_to_node(self, connection):
        """
        Talks to a node.
        """
        initial_message = connection.recv(1024)
        self.log.write(f"Initial message from node: {initial_message}\n")
        valid, conn = self.verify_node_connection(initial_message)
        node = None
        if valid:
            self.log.write(f"Connection verified: {conn}\n")
            with self.node_list_lock.acquire() as s:
                node = Node(conn[0], conn[1], connection)
                self.add_node(node)
        else:
            self.log.write(f"Connection failed: {conn}\n")
            return
        
        # Send the list of nodes in JSON format to the connected node
        node_list = [{"ip": n.address[0], "port": n.address[1]} for n in self.nodes]
        connection.send(json.dumps({"type": "node_list", "nodes": node_list}).encode('utf-8'))

        while True:
            connection.settimeout(1)
            message = connection.recv(1024)
            if not message:
                node.lastSeen += 1
                continue
            self.log.write(f"Message from node: {message}\n")
            self.handle_message(message, node) 

    def handle_message(self, message, node):
        """
        Handles messages from nodes.
        """
        try:
            typey = message[0:2].from_bytes(byteorder='big')
            if typey == BLOCK:
                self.log.write(f"Block message received: {message}\n") 
                self.handle_block(message[2:], node)
            elif typey == VOTE:
                self.handle_vote(message[2:], node)
            elif typey == INIT:
                self.log.write(f"Init message received: {message}\n")
                # Handle init message here
            elif typey == ELECTION:
                self.handle_election(message[2:], node)
            else:
                self.log.write(f"Unknown message type: {message}\n")
        except json.JSONDecodeError:
            self.log.write(f"Failed to decode message: {message}\n")
        except KeyError as e:
            self.log.write(f"Malformed message: {e}\n")
    
    def handle_vote(self, message, node):
        """
        Handles vote messages from nodes. Implement this in the actual node.
        """
        vote = Vote(message)
        # finding the election that this vote is for
        election = self.active_elections.get(vote.election_name)
        if election is None:
            self.log.write(f"Vote for non-existent or ended election: {vote.election_name}\n")
            return
        if vote.public_key in election.used_keys:
            self.log.write(f"Vote from used public key: {vote.public_key}\n")
            return
        if vote.public_key not in election.public_keys:
            self.log.write(f"Vote from non-existent public key: {vote.public_key}\n")
            return
        if vote.choice not in election.choices:
            self.log.write(f"Vote for non-existent choice: {vote.choice}\n")
            return
        if not vote.check_sig():
            self.log.write(f"Vote signature verification failed: {vote.signature}\n")
            return
        election.used_keys[vote.public_key] = vote.choice
        self.broadcast(node, VOTE, message)
        
    def handle_election(self, message, node):
        """
        Handles election messages from nodes. Implement this in the actual node.
        """
        election = Election(message)
        if election.name in self.active_elections:
            self.log.write(f"Election already exists: {election.name}\n")
            return
        if election.end_time < time.time():
            self.log.write(f"Election has already ended: {election.name}\n")
            return
        self.active_elections[election.name] = election
        self.log.write(f"Election added: {election.name}\n")
        # Broadcast the election to all nodes
        self.broadcast(node, ELECTION, message)
    def handle_block(self, message, node, new = True):
        """
        handles a block message from another node.
        Checks: 
        - Confirms that the blocks hash has the correct proof of work (number of leading zeros)
        - Confirms that the block is not a duplicate (if it is, we wont broadcast)
        - Confirms that the block's previous hash matches the previous block in the chain (some logic here about orphan bkocks and alternate chains)
        -    If we do have an orphan block, we need a worker to query for the prior blocks
        - Confirms that the votes cast in the block have valid signatures, and that the merkle tree is valid
        - COnfirms the the block timestamp is reasonable (compared to the previous blocks, and the current time if this is a new block (not ff from another node))
        - Adds the block to the chain, removing votes from the transaction pool that are encoded here
        - Cleans up, ensuring that we cleared out the orphan pool as much as we can.
        """
        # pull out index (first 4 bytes)
        index = int.from_bytes(message[:4], byteorder='big') 
        # Exract the rest of the block eader fields
        prev_hash = message[4:36]  # 32 bytes for previous hash
        hashy = hashy(message[:84]) # hashing the header
        parent = None
        for header in self.chain_headers:
            thing = header
            while header.index < index - 1:
                if thing.index == index - 1 and thing.hash == prev_hash:
                    # this is the chain we are on
                    parent = thing
                    found = True
                if thing.hash == hashy:
                    # WE FOUND A DUPLICATE, BREAK IT UP.
                    return

                thing = thing.previous_block
                
        if not found:
            self.orphan_pool[prev_hash].append(message)
            #TODO: add a worker to query for the prior blocks
            return
        
        self.verify_block(message, thing, node, new)
        
        
    def verify_block(self, message, parent, node, new = True):
        """
        Verifies a block message from another node.
        Checks: 
        - Confirms that the blocks hash has the correct proof of work (number of leading zeros)
        - Confirms that the block's previous hash matches the previous block in the chain (some logic here about orphan bkocks and alternate chains)
        -    If we do have an orphan block, we need a worker to query for the prior blocks
        - Confirms that the votes cast in the block have valid signatures, and that the merkle tree is valid
        - COnfirms the the block timestamp is reasonable (compared to the previous blocks, and the current time if this is a new block (not ff from another node))
        - Adds the block to the chain, removing votes from the transaction pool that are encoded here
        - Cleans up, ensuring that we cleared out the orphan pool as much as we can.
        """
        # pull out index (first 4 bytes)
        index = int.from_bytes(message[:4], byteorder='big') 
        # Exract the rest of the block eader fields
        prev_hash = message[4:36]  # 32 bytes for previous hash
        merkle_root = message[36:68]  # 32 bytes for merkle root
        timestamp = int.from_bytes(message[68:76], byteorder='big')  # 8 bytes for timestamp
        difficulty = int.from_bytes(message[76:80], byteorder='big') # 4 bytes for difficulty
        nonce = int.from_bytes(message[80:84], byteorder='big')  # 4 bytes for nonce
        block_header = message[:84]
        header_hash = hashy(block_header)
        block_body = message[84:]
        ##Checking for rule violations:
        # Difficulty check
        if difficulty != self.getDifficulty(parent):
            self.log.write(f"Difficulty mismatch: {difficulty} != {self.getDifficulty(parent)}\n")
            node.connection.send(b"Invalid difficulty")
            node.good = False
            return
        
        # checking the POW
        if not check_proof_of_work(header_hash, difficulty):
            self.log.write(f"Invalid proof of work: {header_hash}\n")
            node.connection.send(b"Invalid proof of work")
            node.good = False
            return

        #checking the timestamp
        if not self.check_timestamp(parent, timestamp):
            self.log.write(f"Invalid timestamp: {timestamp}\n")
            node.connection.send(b"Invalid timestamp")
            node.good = False
            return

        if not self.check_sigs(message):
            self.log.write("Invalid signatures in block\n")
            node.connection.send(b"Invalid signatures")
            node.good = False
            return

        #TODO: Implement the above function, and remove signitures from the pool that were seen here.

        # Remove the parent from self.chain_headers and replace with this node
        block = Block(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent)
        try:
            self.chain_headers.remove(parent)
        except ValueError:
            pass

        self.chain_headers.append(block)
        self.broadcast(node, BLOCK, message)

        if header_hash in self.orphan_blocks:
            for orphan in self.orphan_blocks[header_hash]:
                self.verify_block(orphan, block, None)

    def broadcast(self, sender, type, message):
        """
        Broadcasts a message to all nodes.
        """
        message = type.to_bytes(2, byteorder='big') + message
        for addr, node in self.nodes:
            if node != sender:
                try:
                    node.connection.send(message.encode('utf-8'))
                except Exception as e:
                    self.log.write(f"Failed to send message to {node}: {e}\n")
                    self.remove_node(node)

    def verify_node_connection(self, initial_message, connection):
        """
        This one makes sure that the connection request is valid, baiscly checking the format of the message
        """
        try:
            if initial_message[:2] == INIT.to_bytes(2, byteorder='big'):
                return True, connection.getpeername()
            return False, None
        except:
            return False, None
    
    def getDifficulty(self, block):
        # Calculate the frequency of the last 10 blocks (excluding the current one)
        timestamps = []
        current_block = block
        difficulties = []
        for _ in range(6):
            if current_block is None:
                break
            timestamps.append(current_block.timestamp)
            difficulties.append(current_block.difficulty)
            current_block = current_block.previous_block
        difficulty = 0
        if len(timestamps) > 1:
            timestamps.sort(reverse=True)
            time_differences = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
            average_frequency = sum(time_differences) / len(time_differences)
            average_difficulty = sum(difficulties) / len(difficulties)
            # Calculate the new difficulty, targeting block every 30 seconds, assume that time to mine scales with 1/difficulty
            # This is a simple way to do it, but we can make it more complex if needed
            difficulty = int(average_difficulty * (30/average_frequency))
            if difficulty < 1:
                difficulty = 1
            elif difficulty > 2**32 - 1:
                difficulty = 2**32 - 1
            elif difficulty > block.difficulty * 1.5:
                difficulty = int(block.difficulty * 1.5)
            elif difficulty < block.difficulty * 0.5:
                difficulty = int(block.difficulty * 0.5)
            return difficulty

        else:
            return DEFAULT_DIFFICULTY
        
    def check_timestamp(self, block, timestamp):
        #Starging at block, find the median timestamp of the last 6
        timestamps = []
        current_block = block
        for _ in range(6):
            if current_block is None:
                break
            timestamps.append(current_block.timestamp)
            current_block = current_block.previous_block

        if len(timestamps) == 0:
            return True  # No previous blocks to compare against

        timestamps.sort()
        median_timestamp = timestamps[len(timestamps) // 2]

        if timestamp < median_timestamp:
            return False
        
        # Check if the timestamp is more than 2 minutes in the future
        if timestamp > time.time() + 120:
            return False
        return True
    
    def check_sigs(self, message):
        """
        Checks the signatures in the block.
        """
        return True
    
        
