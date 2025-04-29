import cryptography
import hashlib
import socket
import json
import threading
import time

MAX_CONNECTIONS = 50
DEFAULT_DIFFICULTY = 16
INIT = 0
VOTE = 1
BLOCK = 2
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
    def __init__(self, index, previous_hash, timestamp, data, hashy, work, difficulty, previous_block=None):
        self.previous_block = previous_block
        self.total_work = work
        if(previous_block is not None):
            self.total_work += previous_block.total_work
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
        self.votes = []
        self.new_elections = []
        self.active_elections = []
        self.orphan_blocks = []
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
        total_size = 0
        while total_size < MAX_BLOCK_SIZE:
            pass
            
                


            
        

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
                self.handle_transaction(message[2:], node)
            else:
                self.log.write(f"Unknown message type: {message}\n")
        except json.JSONDecodeError:
            self.log.write(f"Failed to decode message: {message}\n")
        except KeyError as e:
            self.log.write(f"Malformed message: {e}\n")
    
    def handle_block(self, message, node):
        """
        Handles block messages from nodes. Implement this in the actual node.
        """
        pass
    def handle_transaction(self, message, node):
        """
        Handles transaction messages from nodes. Implement this in the actual node.
        """
        self.log.write(f"Handling transaction message: {message}\n")
        # Process the transaction message here
        pass

    def broadcast(self, sender, message):
        """
        Broadcasts a message to all nodes.
        """
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
