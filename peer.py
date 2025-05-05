from utils import *
from block import Block
from election import Election
from vote import Vote
from node import Node
import itertools
import json
import threading
import time
import socket
import base64

from end_of_election import EndOfElection
from random import shuffle

PING = 10
PONG = 11

class Peer():
    def __init__(self, name, port, tracker_ip = None, tracker_port = None):
        """
        Initializes the Peer class.
        This will immidiatly start to connect to the network, trying to find the tracker if ip is provided (if not, this is the tracker)
        args:
        - name: The name of the peer (for logging)
        - port: The port to listen on
        - tracker_ip: The ip of the tracker to connect to (if this is the tracker, this should be None)
        - tracker_port: The port of the tracker to connect to (if this is the tracker, this should be None)

        returns:
        - None
        """
        self.nodes = {} # used to store current connections, more complex processing will be needed for larger networks, but right now we just talk to everyone.
        self.log_lock = threading.Lock() # lock for the log file
        self.log = open(f"{name}.log", "a") # log file
        self.log.write(f"{name} INITIALIZE.\n\n")


        self.node_list_lock = threading.Lock() # lock for the node list, so more than one thread dont race
        self.chain_headers = [] # list of current chain headers (any node that is not a parent of another node that we know)
        self.port = port # the port
        self.name = name # the name of the peer

        self.new_votes = {} # these are the votes that we have recieved and verified, but are not in a block on the longest chain yet
        self.new_elections = {} # these are the elections that we have recieved and verified, but are not in a block on the longest chain yet
        self.new_ended_elections = {} # these are end of election events, critical for determining security and preventing nodes from dropping votes when reporting results
        self.open_elections = {} # elections that we think are ongoing. This may contain some recently ended elections, so still check
        self.orphan_pool = {} # orphan pool
        self.blocks = {} # all blocks and their hashes. This is storing pointers. Memory overhead for this is pretty light. Still, some trimming of stubs and untaken branches could be good
        self.all_things = {} # hashes of every object we have seen, used to recalculate the new arrays when we switch chains
        self.biggest_chain = None # the node with the most work
        self.data_lock = threading.Lock() # lock for the data (all of the data structures here)
        self.send_lock = threading.Lock() # lock to prevent two threads from sending at the same time. More fine-grained per node could be good, but this should suffice
        threading.Thread(target=self.accept_connections, daemon=True).start() # starting the thread to accept connections
        self.is_tracker = False # if this is the tracker or not 
        if tracker_ip and tracker_port:
            # print(f"Connecting to tracker at {tracker_ip}:{tracker_port}")
            self.start_connection(tracker_ip, tracker_port) # connecting to the tracker
        else:
            self.is_tracker = True # if we are the tracker, we need to accept connections
            
        threading.Thread(target=self.ping_loop, daemon=True).start()

    def write_log(self, message):
        """
        Logs a message to the log file. Lock to prevent race conditions on the file
        args:
        - message: The message to log
        """
        with self.log_lock:
            self.log.write(f"{time.time()}: {message}\n")
            self.log.flush()
    def mine(self):
        """
        Starts the mining process.
        """
        self.should_mine = True
        self.write_log("Starting mining process...\n")
        threading.Thread(target=self.mining).start()
    def stop_mining(self):
        """
        Stops the mining process.
        """
        try:
            self.should_mine = False
            self.write_log("Stopping mining process...\n")
        except Exception as e:
            self.write_log(f"Error stopping mining process: {e}\n")
    def mining(self):
        """
        Mines a block.
        This will run a loop, and is responsible for cleanup of open_elections (since it is the only thing that uses it)

        """
        while self.should_mine:
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
            difficulty = self.getDifficulty(biggest_chain) # gets the difficulty of the block
            timestamp = int(time.time()).to_bytes(8, byteorder='big')
            nonce = 0
            while nonce < 2**32: # max for 4 byte num
                if nonce % 10000000 == 0:
                    self.write_log(f"Mining block {index} with nonce {nonce}")
                    if self.biggest_chain != old_longest or not self.should_mine: # new block was recieved, need to break and start over
                        break
                block_header = b''.join([index.to_bytes(4, byteorder='big'), prev_hash, merkle_root, timestamp, difficulty.to_bytes(4, byteorder='big'), nonce.to_bytes(4, byteorder='big')])
                header_hash = hashy(block_header)
                if check_proof_of_work(header_hash, difficulty): #checks if the hash we just made will work
                    # print(f"Found a block: {header_hash}")
                    block = Block(index, header_hash, prev_hash, merkle_root, int.from_bytes(timestamp, byteorder='big'), difficulty, nonce, biggest_chain, data=objects)
                    self.handle_block(block.get_sendable(), None, False)
                    break
                
                nonce += 1
                
        
    def get_merkle_root(self, objects):
        """
        Gets the merkle root of the objects.

        args:
        - objects: The objects to be included in the block, must be json serializable (vote, election, end of election)
        """
        # a bit janky, but it works
        block = Block(0, b'', b'', b'', 0, 0, 0, None, objects)
        return block.get_merkle_root()
        
    def get_objects(self):
        """
        Gets the objects to be included in the block.
        We allways prioritize the ended elections, then the new elections, then the votes.
        A more mature implemention would include gas or some sort of fee to incentivize the miners to include certain transactions, but this is not implemented yet.
        """
        # TODO: Throw some sanity checks on the votes and elections, ensuring that they are not expired
        with self.data_lock:
            objects = []
            total_size = 0
            new_ended_elections = []
            # we allways prioritize the ended elections, then the new elections, then the votes
            for key in self.new_ended_elections:
                item = self.new_ended_elections[key]

                sizey = item.len
                if sizey + total_size > MAX_BLOCK_SIZE:
                    break
                new_ended_elections.append(item)
                total_size += sizey
            shuffle(new_ended_elections) # shuffling so that what are hashing will be different than other nodes, if we have the same transactions
            for item in new_ended_elections:
                objects.append(item)
            
            new_elections = []
            del_list = []
            for key in self.new_elections:
                item = self.new_elections[key]
                if item.end_time < time.time(): # time passed since we saw this, so it may not be good anymore
                    self.write_log(f"Election has already ended: {item.name}\n")
                    del_list.append(key)
                    continue
                sizey = item.len
                if sizey + total_size > MAX_BLOCK_SIZE:
                    break
                new_elections.append(item)
                total_size += sizey
            for key in del_list:
                del self.new_elections[key]
            shuffle(new_elections)
            for item in new_elections:
                objects.append(item)
            del_list = []
            new_votes = []
            for key in self.new_votes:
                item = self.new_votes[key]
                sizey = item.len
                if item.election_hash not in self.open_elections: # check if the election is still open
                    self.write_log(f"Vote for ended or non-existent election: {item.election_hash}\n")
                    del_list.append(key)
                    continue
                if sizey + total_size > MAX_BLOCK_SIZE:
                    break
                new_votes.append(item)
                total_size += sizey
            for key in del_list:
                del self.new_votes[key]
            shuffle(new_votes)
            for item in new_votes:
                objects.append(item)
        print(f"Total size: {total_size}")
        return objects[:2**MAX_LEVELS]
            
                
    def start_connection(self, ip, port):
        """
        This is used by nodes that are sending the first message and establishing a connection to another node.
        This gets the target nodes list of other known nodes, so we can learn the whole network
        args:
        - ip: The ip of the node to connect to
        - port: The port of the node to connect to
        """
        try:
            # opening the socket
            new_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # creating and adding the node
            node = Node(ip, port, new_connection)
            # this checks for duplicates and self refrences.
            new = self.add_node(node)
            if not new:
                # print(f"Node already exists: {ip}:{port}")
                return
            
            # connecting to the node
            new_connection.connect((ip, port))
            # sending the initial message
            msg = INIT.to_bytes(2, byteorder='big') + self.port.to_bytes(2, byteorder='big')
            self.send_message(msg, node)

            #getting and parsing the node list response
            response = new_connection.recv(4096 * 8) 
            leny = int.from_bytes(response[:2], byteorder='big')
            # print(response[2:2+leny])
            try:
                node_list = json.loads(response[2:2+leny].decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print("Failed to decode node list:", e)
                self.write_log(f"Failed to decode node list: {e}\n")
                return
            
            # connecting to all the other nodes (if they are new)
            for node_info in node_list:
                ip = node_info.get("ip")
                port = node_info.get("port")
                
                if ip and port:
                    self.start_connection(ip, port)

            self.write_log(f"Node list received: {node_list}\n")
            # starting a deticated thread to talk to the node
            threading.Thread(target=self.talk_to_node, args=(new_connection, False, node), daemon=True).start()
        except Exception as e:
            print("failed to connect", e)
            self.write_log(f"Failed to connect to node: {e}\n")

    def add_node(self, node):
        """
        Adds a node to the tracker.
        """
        with self.node_list_lock:
            # janky check to make sure we dont add ourselves
            if node.address == (socket.gethostbyname(socket.gethostname()), self.port) or node.address == ("localhost", self.port) or node.address == ("127.0.0.1", self.port):
                return False
            # check to make sure we dont add duplicates
            if node.address in self.nodes:
                return False
            self.nodes[node.address] = node
            self.write_log(f"Node added: {node}\n")
        return True
    
    def remove_node(self, node):
        """
        Removes a node from the tracker.
        """
        with self.node_list_lock:
            if node in self.nodes:
                del self.nodes[node]
                self.write_log(f"Node removed: {node}\n")
            else:
                self.write_log(f"Node not found: {node}\n")

    def accept_connections(self):
        """
        Accepts connections from nodes, spinning off a thread for each one.
        """
        while True:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', self.port))
            server_socket.listen(MAX_CONNECTIONS)
            connection, _ = server_socket.accept()
            self.write_log(f"Connection accepted: {connection}\n")
            threading.Thread(target=self.talk_to_node, args=(connection,)).start()
        
    def talk_to_node(self, connection, initial = True, node = None):
        """
        Talks to a node.
        args:
        - connection: The connection to the node
        - initial: If this is the initial connection (used to send the node list)
        - node: The node object (used to send messages back to the node, needed if intial is false)
        """
        if initial:
            initial_message = connection.recv(1024)
            leny = int.from_bytes(initial_message[:2], byteorder='big')
            initial_message = initial_message[2:2+leny]
            # checks the first message, ensuring its good
            valid, porty = self.verify_node_connection(initial_message)
            node = None
            if valid:
                # sending the node list
                node_list = [{"ip": n[0], "port": n[1]} for n in self.nodes]
                node = Node(connection.getpeername()[0], porty, connection)
                msg = json.dumps(node_list).encode('utf-8')
                self.send_message(msg, node)
                self.add_node(node)
            else:
                self.write_log(f"Connection failed: {connection}\n")
                return
        else:
            # otherwise, we want the longest chain, as we are new.
            self.send_message(GET_LONGEST_CHAIN.to_bytes(2, byteorder='big') + (0).to_bytes(4, byteorder='big'), node)
        # Send the list of nodes in JSON format to the connected node
        

        while True:
            # loop to receive and process messages from the node
            fragment = b''
            try:
                connection.settimeout(1)
                message = connection.recv(1024*8)
                if message == b'':
                    #connection was closed by peer
                    self.write_log(f"Connection closed by peer: {node}\n")
                    break
                message = fragment + message
                leny = int.from_bytes(message[:2], byteorder='big')
                print("Message length:", leny, len(message[2:]))
                while len(message[2:]) >= leny and leny > 0:
                    self.handle_message(message[2:leny+2], node) 
                    message = message[leny+2:]
                    leny = int.from_bytes(message[:2], byteorder='big')
                fragment = message
            except socket.timeout:
                node.lastSeen += 1
                

    def send_vote(self, vote):
        """
        Sends a vote to the network. Called by whatever instianted this node. Used to send votes to the network.
        args:
        - vote: The vote to send
        """
        self.handle_vote(vote.jsonify().encode('utf-8'), None)
        
    def send_election(self, election):
        """
        Sends an election to the network.  
        args:
        - election: The election to send
        """
        self.handle_election(election.jsonify().encode('utf-8'), None)

    def handle_message(self, message, node):
        """
        Handles messages from nodes.
        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        try:
            typey = int.from_bytes(message[:2], byteorder='big')
            #if typey == BLOCK:

            # Reset lastSeen counter whenever we get any message
            node.lastSeen = 0
            
            if typey == PING:
                # Reply with pong
                pong_message = PONG.to_bytes(2, byteorder='big')
                self.send_message(pong_message, node)
            elif typey == PONG:
                # Do nothing, lastSeen already reset
                pass
            elif typey == BLOCK:
                self.handle_block(message[2:], node)
            elif typey == VOTE:
                self.handle_vote(message[2:], node)
            elif typey == INIT:
                pass # we ignore more init messages from the same node
                # Handle init message here
            elif typey == ELECTION:
                self.handle_election(message[2:], node)
            elif typey == LONGEST_CHAIN:
                self.receive_longest_chain(message[2:], node)
            elif typey == GET_LONGEST_CHAIN:
                self.get_longest_chain(message[2:], node)
                # Handle get longest chain message here. Return the heeaders for the longest chain
            elif typey == GET_BLOCK:
                self.get_block(message[2:], node) 
            elif typey == GET_ELECTION_RES:
                self.get_election(message[2:], node)
                # Handle get election message here. Return the election for the given name, along with the votes, and the merkle trees to prove it.
            elif typey == ELECTION_RES:
                self.handle_election_res(message[2:], node)
                return
            elif typey == ERROR_RESPONSE:
                print(f"Error response received: {message[2:].decode('utf-8')}")
                return
            elif typey == GET_ACTIVE_ELECTIONS:
                self.get_active_election(node)
            elif typey == ACTIVE_ELECTIONS:
                self.handle_active_elections(message[2:], node)
            else:
                self.write_log(f"Unknown message type: {message[:2]}\n")
        # checks so I dont have to put these in every one (i still do sometimes though)
        except json.JSONDecodeError:
            self.write_log(f"Failed to decode message: {message}\n")
        except KeyError as e:
            self.write_log(f"Malformed message: {e}\n")
    
    def get_active_election(self, node):
        """
        Handles get active election messages from nodes. This will return the list of active elections to the node.
        args:
        - node: The node that sent the message
        """
        with self.data_lock:
            result = []
            for key in self.open_elections:
                result.append(self.open_elections[key].jsonify())
            # smashing results together so its one big binary string
            result = {"elections": result}
            # send the result back to the node
            self.send_message(ACTIVE_ELECTIONS.to_bytes(2, byteorder='big') + json.dumps(result).encode('utf-8'), node)
            self.write_log(f"Active elections sent to node {node}\n")
    
    def handle_active_elections(self, message, node):
        """
        Handles active election messages from nodes. This will update the list of active elections with the data from the node.
        Only the light nodes need to deal with this, as they are the ones that will be sending this message.
        """
        pass

    def get_block(self, message, node):
        """
        Handles get block messages from nodes.
        Tries to get the block based on the provided hash, and returns the data to the sender.
        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        with self.data_lock:
            if message in self.blocks:
                block = self.blocks[message]
                # Send the block to the node
                self.send_message(BLOCK.to_bytes(2, byteorder='big') + block.get_sendable(), node)
            else:
                self.write_log(f"Get block request failed: Block not found: {len(message[2:])} {message[2:]}\n")
                # Send an error message to the node
                self.send_error(node, "Block not found")
    def send_message(self, message, node):
        """
        Sends a message to the node. Does number of bytes in the message + the message
        args:
        - message: The message to send
        - node: The node to send the message to
        """
        if node is None:
            return
        with self.send_lock:
            leny = len(message)
            node.connection.send(leny.to_bytes(2, byteorder='big') + message)
    def receive_longest_chain(self, message, node):
        """
        Handles receive longest chain messages from nodes. Check it for correctness, and see if we need to switch chains (if so, we need to grab the data for all the nodes we dont have)
        We are just going to request all of the data for all of the data from the node, then do the full checks
        
        args:
        - message: The message to handle
        - node: The node that sent the message
        """ 
        #pull out chunks of 84 byte sections
        #these should be in the normal header format
        with self.data_lock:
            for i in range(len(message) - 84, -1, -84):
                # Extract the block header
                block_header = message[i:i+84]
                # Exract the rest of the block eader fields
                this_hash = hashy(block_header[:84]) # hashing the header
                if this_hash in self.blocks:
                    # this block is already in our chain, so we can skip it
                    continue
                self.request_block(this_hash, node)
            

    def get_longest_chain(self, message, node):
        """
        Handles get longest chain messages from nodes. Starts from index specified, but this should useally be 0 to get the whole chain.


        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        # finding the node with the greatest total work
        idx = int.from_bytes(message[:4], byteorder='big')
        with self.data_lock:
            current = self.biggest_chain
            result = []
            while current is not None and current.index >= idx:
                header = current.get_header()
                result.append(header)
                current = current.previous_block
            # smashing results together so its one big binary string
            result = b''.join(result)
            # send the result back to the node
            self.send_message(LONGEST_CHAIN.to_bytes(2, byteorder='big') + result, node)
            self.write_log(f"Longest chain sent to node {node}\n")


    def handle_election_res(self, message, node):
        """
        NOT IMPLEMENTED IN THE FULL NODE, AS THEY HAVE ALL THE DATA
        """
        pass
    def handle_vote(self, message, node):
        """
        Handles vote messages from nodes. Implement this in the actual node.
        This will check the vote, and if it is valid, add it to the election.
        It is critical that elections are not duplicate, as these checks on used keys is how we decide if to reject a vote or not and prevent duplicates.

        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        vote = Vote(message)
        self.write_log(f"Vote message received: {vote.jsonify()}\n")
        with self.data_lock:
            election = None
            if vote.election_hash in self.open_elections: 
                election = self.open_elections[vote.election_hash]
            else:
                self.write_log(f"Vote for ended or non-existent election: {vote.election_hash}\n")

            res = self.check_vote(vote, election, time.time() + 20) # makes sure it will be valid for long enough that we could mine theoretically

            if not res:
                self.write_log(f"VOTE FAILED CHECKS: {vote.jsonify()}\n")
                return
            
            gas = 1
            self.write_log(f"[ ] Vote added: {vote.jsonify()}\n")
            election.used_keys[vote.public_key] = vote.choice # mark the key as used
            self.all_things[hashy(vote.jsonify())] = (gas, vote) # theoritical GAS ammount, unimplemented
            self.new_votes[hashy(vote.jsonify())] = vote # add the vote to the new votes so we can throw it on a block
            self.broadcast(node, VOTE, message) # if its good, we spread it to the rest of the network

        
    def handle_election(self, message, node):
        """
        Handles election messages from nodes. Implement this in the actual node.
        Checks are less intense here, mostly just checking for duplicates and if the election is still open.

        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        election = Election(message)
        self.write_log(f"Election message received: {election.jsonify()}\n")
        with self.data_lock:
            if election.hashy in self.open_elections:
                self.write_log(f"X Election already exists: {election.name}\n")
                return
            if election.end_time < time.time():
                self.write_log(f"X Election has already ended: {election.name}\n")
                return
            gas = 1
            self.open_elections[election.hashy] = election
            self.all_things[hashy(election.jsonify())] = (gas, election) # theoritical GAS ammount, unimplemented
            self.new_elections[hashy(election.jsonify())] =  election
            self.write_log(f"[ ] Election added: {election.name}\n")
            # Broadcast the election to all nodes
            self.broadcast(node, ELECTION, message)
    
    def check_vote(self, vote, election, time):
        """
        Checks if a vote is valid.
        MUST BE CALLED WITH THE DATA LOCK HELD
        This checks:
        - The vote is not a duplicate (if it is, we wont broadcast)
        - The vote is for a valid public key for that election (if it is not, we wont broadcast)
        - The vote is for a valid choice for that election (if it is not, we wont broadcast)
        - The vote has a valid signature (if it is not, we wont broadcast)

        The valid election check is handeled by the caller, as this function needs the election object.


        args:
        - vote: The vote to check
        - election: The election to check against
        - time: The current time
        """
        # check if the key is not used
        if vote.public_key in election.used_keys:
            self.write_log(f"X Vote from used public key: {vote.public_key}\n")
            return False
        
        # check if the public key is in the election
        if vote.public_key not in election.public_keys:
            self.write_log(f"X Vote from non-existent public key: {vote.public_key}\n")
            return False
        
        # check if the choice is in the election
        if vote.choice not in election.choices:
            self.write_log(f"X Vote for non-existent choice: {vote.choice}\n")
            return
        
        # check that the signature is valid
        if not vote.check_sig():
            self.write_log(f"X Vote signature verification failed: {vote.signature}\n")
            return False
        return True

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
        this_hash = hashy(message[:84]) # hashing the header
        parent = None
        found = False
        thing = None
        with self.data_lock:
            # if this is the genisis block, we need to add it to the chain
            if index == 0:
                found = True
            # otherwise, we need to find the parent block
            if this_hash in self.blocks:
                self.write_log(f"INF: Duplicate block received: {message}\n")
                # WE FOUND A DUPLICATE, BREAK IT UP.
                return
            if prev_hash in self.blocks:
                # we found the parent block, so we can add this block to the chain
                parent = self.blocks[prev_hash]
                found = True
                thing = parent
                

            # throwing it in the orphan pool, we can check it later once we get the chain it goes on.    
            if not found:
                self.write_log(f"INF: Orphan block received: {message}\n")
                if prev_hash not in self.orphan_pool:
                    self.orphan_pool[prev_hash] = []
                if message not in self.orphan_pool[prev_hash]:
                    self.orphan_pool[prev_hash].append(message)
                # request the parent block from the node
                self.request_block(prev_hash, node)
                return
            # if we found the parent, we can do the rest of verification
            self.verify_block(message, thing, node)
        
        
    def verify_block(self, message, parent, node):
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

        args:
        - message: The message to handle
        - node: The node that sent the message
        - parent: The parent block of this block
        """
        # pull out index (first 4 bytes)
        index = int.from_bytes(message[:4], byteorder='big') 
        # Exract the rest of the block header fields
        prev_hash = message[4:36]  # 32 bytes for previous hash
        merkle_root = message[36:68]  # 32 bytes for merkle root
        timestamp = int.from_bytes(message[68:76], byteorder='big')  # 8 bytes for timestamp
        difficulty = int.from_bytes(message[76:80], byteorder='big') # 4 bytes for difficulty
        nonce = int.from_bytes(message[80:84], byteorder='big')  # 4 bytes for nonce
        block_header = message[:84]
        header_hash = hashy(block_header)


        # Extract the votes and elections from the block data. It is a concatanation of json encoded forms of the votes and elections
        block_data = message[84:]
        json_data = block_data.decode('utf-8') 
        if json_data == "":
            json_data = "{}"
        # Parse the JSON data to extract votes and elections
        objects = json.loads(json_data) 
        
        # Parse each object in the block data
        data = []
        for key in objects:
            if "type" not in objects[key]:
                self.write_log(f"X Malformed object in block data: {objects[key]}\n")
                return
            obj = objects[key]
            if obj["type"] == "vote":
                data.append(Vote(obj))
            elif obj["type"] == "election":
                data.append(Election(obj))
            elif obj["type"] == "end_of_election":
                data.append(EndOfElection(obj))
            else:
                self.write_log(f"X Unknown object type in block data: {obj['type']}\n")
                return
        # Create a new block object
        block = Block(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent, data=data)
        # checking the merkle root
        if block.merkle_root != block.get_merkle_root():
            self.write_log(f"X Invalid merkle root: {block.merkle_root} != {block.get_merkle_root()}\n")
            self.send_error(node, "Invalid merkle root")
            return
        ##Checking for rule violations:
        # Difficulty check (goes from the parent, since that is where the minor calculates it)
        if difficulty != self.getDifficulty(parent):
            self.write_log(f"X Difficulty mismatch: {difficulty} != {self.getDifficulty(parent)}\n")
            print("invalid difficulty")
            self.send_error(node, "Invalid difficulty")
            return
        
        # checking the POW
        if not check_proof_of_work(header_hash, difficulty):
            self.write_log(f"X Invalid proof of work: {header_hash}\n")
            self.send_error(node, "Invalid proof of work")
            return

        #checking the timestamp
        if not self.check_timestamp(parent, timestamp):
            self.write_log(f"X Invalid timestamp: {timestamp}\n")
            self.send_error(node, "Invalid timestamp")
            return

        # checking the signatures (also checks other app correctness things with the elections and votes)
        if not self.check_sigs(block, parent):
            self.write_log("X Invalid signatures in block\n")
            self.send_error(node, "Invalid signatures")
            return


        # Remove the parent from self.chain_headers and replace with this node
        self.write_log(f"Block verified: Index: {block.index}, Difficulty: {block.difficulty}, Objects: {json.dumps([obj.jsonify() for obj in block.data])}\n")
        if parent == self.biggest_chain:
            self.biggest_chain = block
            self.remove_new(block) # simple check to update the new queues
            self.write_log(f"INF: Chain extended\n")
        elif block.total_work > self.biggest_chain.total_work:
            self.biggest_chain = block
            self.recompute_new(block) # more through check, goea back throug the whole chain
            self.write_log(f"INF: Longest chain changed\n")
        try:
            self.chain_headers.remove(parent)
        except ValueError:
            pass

        
        self.chain_headers.append(block)
        self.blocks[header_hash] = block
        self.broadcast(node, BLOCK, message)

        # checking if this was the parent to any orphans, if so we can process those.
        if header_hash in self.orphan_pool:
            for orphan in self.orphan_pool[header_hash]:
                self.write_log(f"INF: Orphan block parent found: {orphan}\n")
                self.verify_block(orphan, block, None)
            del self.orphan_pool[header_hash]
    def send_error(self, node, message):
        """
        Sends an error message to the node.
        args:
        - node: The node to send the message to
        - message: The message to send
        """
        if node is None:
            return
        self.send_message(ERROR_RESPONSE.to_bytes(2, byteorder='big') + message.encode('utf-8'), node)
        node.good = False
        self.write_log(f"Error sent to node {node}: {message}\n")

    def request_block(self, hashy, node):
        """
        Requests a block from the node.

        args:
        - hashy: The hash of the block to request
        - node: The node to request the block from
        """
        # Send a request to the node for the block with the given hash
        request_message = GET_BLOCK.to_bytes(2, byteorder='big') + hashy
        self.send_message(request_message, node) 
        self.write_log(f"Requesting block {hashy} from node {node}\n")

    def remove_new(self, block):
        """ 
        remove the transactions in the block from the new_elections and new_votes queues. Use if the new block is just an extension of the current chain
        THE DATA LOCK MUST BE HELD WHEN CALLING THIS FUNCTION
        args:
        - block: The block to remove the transactions from
        """

       # checking this block, and if any of our transactions are in there, we remove them.
        for key in block.elections:
            election = block.elections[key]
            election.new = False
            # do this so we get accurate totals if we do have to do a big shift
            if hashy(election.jsonify()) in self.all_things:
                self.all_things[hashy(election.jsonify())][1].new = False
            else:
                self.all_things[hashy(election.jsonify())] = (0, election)
            if hashy(election.jsonify()) in self.new_elections:
                del self.new_elections[hashy(election.jsonify())]
        for key in block.votes:
            votes = block.votes[key]
            for vote in votes:
                vote.new = False
                if hashy(vote.jsonify()) in self.all_things:
                    self.all_things[hashy(vote.jsonify())][1].new = False
                else:
                    self.all_things[hashy(vote.jsonify())] = (0, vote)
                if hashy(vote.jsonify()) in self.new_votes:
                    del self.new_votes[hashy(vote.jsonify())]
        for key in block.election_ends:
            end = block.election_ends[key]
            end.new = False
            if hashy(end.jsonify()) in self.all_things:
                self.all_things[hashy(end.jsonify())][1].new = False
            else:
                self.all_things[hashy(end.jsonify())] = (0, end)
            if hashy(end.jsonify()) in self.new_ended_elections:
                del self.new_ended_elections[hashy(end.jsonify())]
    
    def recompute_new(self, block):
        """
        recomputes the new_elections and new_votes queues, for when we switch chains. Goes back through the whole chain, and sees what objects were not added
        THE DATA LOCK MUST BE HELD WHEN CALLING THIS FUNCTION
        """
        self.open_elections = {}
        # going through self.all_things and setting new to True for all things that are in the new_elections and new_votes queues
        for key in self.all_things:
            gas, thing = self.all_things[key]
            thing.new = True
        # going backwards, starting from block, and makring all the things in the block as not new
        current_block = block
        while current_block is not None:
            # for every election in the block, we need to mark it as not new
            for key in current_block.elections:
                election = current_block.elections[key]
                self.open_elections[election.hashy] = election
                election.new = False
                if hashy(election.jsonify()) in self.all_things:
                    self.all_things[hashy(election.jsonify())][1].new = False
                else:
                    self.all_things[hashy(election.jsonify())] = (0, election)
            # for every vote in the block, we need to mark it as not new
            for key in current_block.votes:
                votes = current_block.votes[key]
                for vote in votes:
                    vote.new = True
                    if hashy(vote.jsonify()) in self.all_things:
                        self.all_things[hashy(vote.jsonify())][1].new = False
                    else:
                        self.all_things[hashy(vote.jsonify())] = (0, vote)
            # for every end of election in the block, we need to mark it as not new
            for key in current_block.election_ends:
                end = current_block.election_ends[key]
                end.new = False
                if end.election_hash in self.open_elections:
                    del self.open_elections[end.election_hash]
                if hashy(end.jsonify()) in self.all_things:
                    self.all_things[hashy(end.jsonify())][1].new = False
                else:
                    self.all_things[hashy(end.jsonify())] = (0, end)
            current_block = current_block.previous_block

        # recomputing new_elections and new_votes based on this new information
        self.new_elections = {}
        self.new_votes = {}
        self.new_ended_elections = {}
        self.open_elections = {}
        # building back up everything that is new
        for key in self.all_things:
            thing = self.all_things[key][1]
            if isinstance(thing, Election):
                if thing.new:
                    self.new_elections[hashy(thing.jsonify())] = thing
                    if thing.end_time < time.time():
                        self.open_elections[thing.hashy] = thing
            elif isinstance(thing, EndOfElection):
                if thing.new:
                    if not self.all_things[thing.election_hash][1].new: # we dont want to add the end if the start was never added. If it is a thing we need to do, we can do it during processing.
                        self.new_ended_elections[hashy(thing.jsonify())] = thing
            elif isinstance(thing, Vote):
                if thing.new:
                    self.new_votes[hashy(thing.jsonify())] = thing
            else:
                self.write_log(f"X Invalid object in recompute_new: {thing}\n")
                continue
    
    def move_to_ended(self):
        """
        Moves the election to the ended elections queue.
        This is called by the minor, and is used to check if any elections have ended.
        It checks the end time of the election, and if it has passed and the election was on the chain, it moves it to the ended elections queue.
        """
        with self.data_lock:
            keys_to_remove = [] # tracking what to remove from the open elections
            for key in self.open_elections:
                election = self.open_elections[key]
                if election.end_time < time.time():
                    keys_to_remove.append(key) # we will remove this later
                    self.write_log(f"X Election ended: {election.name}\n")
                    results = {} # track results so we can put them on the blockchain
                    thing = self.biggest_chain # we will loop backwards from here
                    already_done = False # if we have already added this election end to the chain
                    found_election = None # confirming the election actually exists
                    while thing is not None:
                        self.write_log(thing.votes)
                        if election.hashy in thing.election_ends:
                            already_done = True
                            break

                        if election.hashy in thing.votes:
                            for vote in thing.votes[election.hashy]:
                                if vote.choice not in results:
                                    results[vote.choice] = 0
                                results[vote.choice] += 1
                        if election.hashy in thing.elections:
                            found_election = thing.elections[election.hashy]
                            break    
                        thing = thing.previous_block
                    if found_election is None: #never on the chain
                        self.write_log(f"X Election not found: {election.name}, likely never added to chain\n")
                        continue
                    if not already_done: # we have not added this election end to the chain yet
                        self.write_log(f"INF: election {election.hashy} results: " + str(results) + "\n")
                        election_end = EndOfElection({"election_hash": base64.b64encode(election.hashy).decode('utf-8'), "results": results})
                        self.new_ended_elections[hashy(election_end.jsonify())] = election_end 
            for key in keys_to_remove:
                del self.open_elections[key]

    def broadcast(self, sender, typey, message):
        """
        Broadcasts a message to all nodes.
        This results in n^2 messages being sent, where n is the number of nodes for updates.
        This is impracticle with huge numbers of nodes, so parsing down the neighboring node list would help with that

        args:
        - sender: The node that sent the message
        - typey: The type of message to send
        - message: The message to send
        """
         
        message = typey.to_bytes(2, byteorder='big') + message
        message = len(message).to_bytes(2, byteorder='big') + message
        with self.send_lock:
            del_list = []
            for addr, node in self.nodes.items():
                # Check if the node is not the sender
                if node != sender:
                    try:
                        # print("Sending message to node:", node.address)
                        node.connection.send(message)
                    except Exception as e:
                        self.write_log(f"X Failed to send message to {node}: {e}, removing\n")
                        del_list.append(addr)
            for addr in del_list:
                self.remove_node(addr)


    def verify_node_connection(self, initial_message):
        """
        This one makes sure that the connection request is valid, baiscly checking the format of the message

        args:
        - initial_message: The message to check
        """
        try:
            if initial_message[:2] == INIT.to_bytes(2, byteorder='big'):
                print("Init message received")
                return True, int.from_bytes(initial_message[2:4], byteorder='big')
            return False, None
        except Exception as e:
            self.write_log(f"X Failed to verify node connection: {e}\n")
            return False, 0 
    
    def getDifficulty(self, block):
        """
        Calculates the difficulty of the block based on the last 10 blocks.
        Will check the check average frequency of the last 10 blocks, as well as their difficulties. 
        Time to mine scales with 1/difficulty, so we can use that to calculate the new difficulty.

        args:
        - block: The block to check
        """
        # Calculate the frequency of the last 10 blocks (excluding the current one)
        timestamps = []
        current_block = block
        difficulties = []
        for _ in range(11):
            if current_block is None:
                break
            timestamps.append(current_block.timestamp)
            difficulties.append(current_block.difficulty)
            current_block = current_block.previous_block
        
        difficulty = 0
        if len(timestamps) > 1:
            timestamps.sort(reverse=True)
            time_differences = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
            time_differences = [td if td != 0 else 1 for td in time_differences]
            average_frequency = sum(time_differences) / len(time_differences)
            average_difficulty = sum(difficulties[:-1]) / len(difficulties[:-1]) # we need one extra timestamp to get all the times, so we trim off the corosponding difficulty
            # Calculate the new difficulty, targeting block every 30 seconds, assume that time to mine scales with 1/difficulty
            difficulty = int(average_difficulty * (TIME_TARGET/average_frequency))
            if difficulty < 1:
                difficulty = 1
            elif difficulty > 2**32 - 1:
                difficulty = 2**32 - 1
            elif difficulty > block.difficulty * CLAMP: # limiting change to 20% for every block
                difficulty = int(block.difficulty * CLAMP)
            elif difficulty < block.difficulty * 1/CLAMP:
                difficulty = int(block.difficulty * 1/CLAMP)
            return difficulty

        else:
            return DEFAULT_DIFFICULTY
        
    def check_timestamp(self, block, timestamp):
        """
        Checks if the timestamp is valid.
        This checks:
        - The timestamp is not in the future (more than 2 minutes)
        - The timestamp is not before the median of the last 6 blocks (if they exist)

        args:
        - block: The block to check against
        - timestamp: The timestamp to check
        """
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
        # Check if the timestamp is before the median timestamp
        if timestamp < median_timestamp:
            return False
        
        # Check if the timestamp is more than 2 minutes in the future
        if timestamp > time.time() + 120:
            return False
        return True
    
    def check_sigs(self, block, parent):
        """
        Checks the signatures in the block, as well as ensuring that the vote is a valid one for this chain.
        Runs in O(n) time, where n is the number of blocks on the chain, as it has to go back to try to find the election.

        args:
        - block: The block to check
        - parent: The parent block of this block
        """
        try:
            
            for election_hash in block.votes:
                for vote in block.votes[election_hash]:
                    election = None
                    # if its in this block, thats cool
                    if vote.election_hash in block.elections:
                        election = block.elections[vote.election_hash]
                    # if not, we have to go looking for it
                    else:
                        this = parent
                        while this is not None:
                            if vote.election_hash in this.elections:
                                election = this.elections[election_hash]
                                break
                            else:
                                this = this.previous_block
                    # if we never found it, we have a problem
                    if election is None:
                        self.write_log(f"X Election not found: {election_hash}\n")
                        return False
                    # check the vote, ensure the sig is good and everything
                    res = self.check_vote(vote, election, block.timestamp)
                    if not res:
                        self.write_log(f"X Vote signature verification failed: {vote.signature}\n")
                        return False
            for key in block.election_ends:
                end = block.election_ends[key]
                this = parent
                totals = {}
                election = None
                # check to make sure the results said here accuratly reflect the votes in the block and on the rest of the chain.
                while this is not None:
                    if end.election_hash in this.votes:
                        for vote in this.votes[end.election_hash]:
                            if vote.choice not in totals:
                                totals[vote.choice] = 0
                            totals[vote.choice] += 1
                    if end.election_hash in this.elections:
                        election = this.elections[end.election_hash]
                        break
                    else:
                        this = this.previous_block
                if election is None:
                    self.write_log(f"X Election not found: {end.election_hash}\n")
                    return False
                # Check if the election is still open
                if election.end_time > block.timestamp:
                    self.write_log(f"X Election is still open: {election.name}, cannot put end on it\n")
                    return False
                # Check if the election has been tampered with
                summy_incoming = 0
                self.write_log(f"INF: End of election results: {end.results}\n")
                self.write_log(f"INF: Totals: {totals}\n")
                for key in end.results:
                    summy_incoming += end.results[key]
                    if end.results[key] != 0 and key not in totals:
                        self.write_log(f"Election tampered with: 1 {key}\n")
                        return False
                summy_real = 0
                for key in totals:
                    summy_real += totals[key]
                    if totals[key] != 0: 
                        if key not in end.results:
                            self.write_log(f"X Election tampered with: 2 {key}\n")
                            return False
                        if totals[key] != end.results[key]:
                            self.write_log(f"X Election tampered with: 3 {totals[key]} != {end.results[key]}\n")
                            return False
                    
                    
                if summy_real != summy_incoming:
                    self.write_log(f"Election tampered with: {summy_real} != {summy_incoming}\n")
                    return False
                
        except Exception as e:
            raise e
        return True
    
    def get_election(self, election_hash, node):
        """"""""" 
        Takes in the election identifier; starts at current block (self.biggest_chain);
        returns election and its votes IF found

        args:
        - election_hash: The hash of the election to get
        - node: The node to send the message to
        """
        current_block = self.biggest_chain
        election_dict = {}
        start = {}
        votes = []
        end = {}
        while current_block is not None:
            if election_hash in current_block.election_ends:
                endy = current_block.election_ends[election_hash]
                end["election_end"] = endy.get_json_dict()
                end["block"] = base64.b64encode(current_block.hash).decode('utf-8')
                end["proof"] = current_block.get_merkle_proof(hashy(endy.jsonify()))

            if election_hash in current_block.votes:
                votes_block = current_block.votes[election_hash]
                for vote in votes_block:
                    vote_inst = {}
                    vote_inst["vote"] = vote.get_json_dict()
                    vote_inst["block"] = base64.b64encode(current_block.hash).decode('utf-8')
                    vote_inst["proof"] = current_block.get_merkle_proof(hashy(vote.jsonify()))
                    votes.append(vote_inst)
            
            if election_hash in current_block.elections:
                election = current_block.elections[election_hash]
                start["election"] = election.get_json_dict()
                start["block"] = base64.b64encode(current_block.hash).decode('utf-8')
                start["proof"] = current_block.get_merkle_proof(election_hash)
                break
            current_block = current_block.previous_block
            
        # Election not found
        if current_block is None:
            self.send_error(node, f"Election not found: {election_hash}")
        election_dict["start"] = start
        election_dict["votes"] = votes
        election_dict["end"] = end
        # Send the election data to the node
        self.send_message(ELECTION_RES.to_bytes(2, byteorder='big') + election_hash + json.dumps(election_dict).encode('utf-8'), node)
        return election_dict
    
    def ping_loop(self):
        """
        Simple periodic ping to all nodes
        """
        while True:
            time.sleep(60)  # Ping once per minute
            
            with self.node_list_lock:
                for addr, node in list(self.nodes.items()):
                    try:
                        # Send ping
                        ping_message = PING.to_bytes(2, byteorder='big')
                        self.send_message(ping_message, node)
                    except Exception as e:
                        # Remove failed nodes
                        self.write_log(f"Ping failed for {addr}: {e}\n")
                        self.remove_node(addr)
            