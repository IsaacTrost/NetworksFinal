from utils import *
from block import Block
from election import Election
from vote import Vote
from node import Node
import itertools
import json

from end_of_election import EndOfElection
from random import shuffle

class Peer():
    def __init__(self, name, port, tracker_ip = None, tracker_port = None):
        self.nodes = {}
        self.log_lock = threading.Lock()
        self.log = open(f"{name}.log", "a")
        self.write_log(f"{name} initialized\n1234567890.\n")
        self.log.write(f"{name} initialized.\n")
        self.node_list_lock = threading.Lock()
        self.chain_headers = []
        self.port = port
        self.counter = itertools.count() 
        self.new_votes = PriorityQueue()
        self.new_elections = PriorityQueue()
        self.new_ended_elections = PriorityQueue()
        self.open_elections = {}
        self.orphan_pool = {}
        self.blocks = {}
        self.all_things = {}
        self.biggest_chain = None
        self.data_lock = threading.Lock()
        self.send_lock = threading.Lock()
        threading.Thread(target=self.accept_connections, daemon=True).start()
        if tracker_ip and tracker_port:
            print(f"Connecting to tracker at {tracker_ip}:{tracker_port}")
            self.start_connection(tracker_ip, tracker_port)
            
        

    def write_log(self, message):
        """
        Logs a message to the log file.
        """
        with self.log_lock:
            self.log.write(f"{time.time()}: {message}\n")
            self.log.flush()
    def mine(self):
        """
        Starts the mining process.
        """
        self.write_log("Starting mining process...\n")
        threading.Thread(target=self.mining).start()
        self.write_log("Mining process started.\n")

    def mining(self):
        """
        Mines a block.
        """
        while True:

            print("Mining...")
            max_header = None
            max_work = 0
            for head in self.chain_headers:
                if head.total_work > max_work:
                    max_work = head.total_work
                    max_header = head
            index = 0
            prev_hash = b'\x00' * 32
            old_longest = self.biggest_chain
            self.move_to_ended()
            objects = self.get_objects()
            print("  objects: ", objects)
            merkle_root = self.get_merkle_root(objects)
            if max_header is not None:
                prev_hash = max_header.hash # case where this is the first block in the chain
                index = max_header.index + 1
            difficulty = self.getDifficulty(max_header)
            timestamp = int(time.time()).to_bytes(8, byteorder='big')
            nonce = 0
            print(nonce)
            while True:
                while nonce < 2**32:
                    if nonce % 1000000 == 0:
                        print(f"Mining block {index} with nonce {nonce}")
                        if self.biggest_chain != old_longest:
                            print("Chain changed, stopping mining")
                            break
                    block_header = b''.join([index.to_bytes(4, byteorder='big'), prev_hash, merkle_root, timestamp, difficulty.to_bytes(4, byteorder='big'), nonce.to_bytes(4, byteorder='big')])
                    header_hash = hashy(block_header)
                    if check_proof_of_work(header_hash, difficulty):
                        print(f"Found a block: {header_hash}")
                        block = Block(index, header_hash, prev_hash, merkle_root, int.from_bytes(timestamp, byteorder='big'), difficulty, nonce, max_header, data=objects)
                        self.handle_block(block.get_sendable(), None, False)
                        break
                        
                    nonce += 1
                if nonce != 2**32:
                    break
                timestamp = int(time.time()).to_bytes(8, byteorder='big')
        
    def get_merkle_root(self, objects):
        """
        Gets the merkle root of the objects.
        """
        # a bit janky, but it works
        block = Block(0, b'', b'', b'', 0, 0, 0, None, objects)
        return block.get_merkle_root()
        
    def get_objects(self):
        """
        Gets the objects to be included in the block.
        """
        # TODO: Throw some sanity checks on the votes and elections
        with self.data_lock:
            objects = []
            total_size = 0
            new_ended_elections = []
            while total_size < MAX_BLOCK_SIZE and not self.new_ended_elections.empty():
                thing = self.new_ended_elections.get()
                item = thing[-1]
                if not item.new:
                    continue

                sizey = item.len
                if sizey + total_size > MAX_BLOCK_SIZE:
                    self.new_ended_elections.put(thing)
                    break
                new_ended_elections.append(item)
                total_size += sizey
            shuffle(new_ended_elections)
            for item in new_ended_elections:
                objects.append(item)
            
            new_elections = []
            while total_size < MAX_BLOCK_SIZE and not self.new_elections.empty():
                thing = self.new_elections.get()
                item = thing[-1]
                if not item.new:
                    continue
                sizey = item.len
                if sizey + total_size > MAX_BLOCK_SIZE:
                    self.new_elections.put(thing)
                    break
                new_elections.append(item)
                total_size += sizey
            shuffle(new_elections)
            for item in new_elections:
                objects.append(item)

            new_votes = []
            while total_size < MAX_BLOCK_SIZE and not self.new_votes.empty():
                thing = self.new_votes.get()
                item = thing[-1]
                if not item.new:
                    continue
                sizey = item.len
                if sizey + total_size > MAX_BLOCK_SIZE:
                    self.votes.put(thing)
                    break
                new_votes.append(item)
                total_size += item

            shuffle(new_votes)
            for item in new_votes:
                objects.append(item)
        print(f"Total size: {total_size}")
        return objects[:2**MAX_LEVELS]
            
                
    def start_connection(self, ip, port):
        try:
            new_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            node = Node(ip, port, new_connection)
            new = self.add_node(node)
            if not new:
                print(f"Node already exists: {ip}:{port}")
                return
            # new_connection.bind(('', self.port))  # Bind to self.port
            new_connection.connect((ip, port))
            msg = INIT.to_bytes(2, byteorder='big') + self.port.to_bytes(2, byteorder='big')
            self.send_message(msg, node)
            response = new_connection.recv(4096 * 8) 
            leny = int.from_bytes(response[:2], byteorder='big')
            print(response[2:2+leny])
            node_list = json.loads(response[2:2+leny].decode('utf-8'))
            for node_info in node_list:
                ip = node_info.get("ip")
                port = node_info.get("port")
                
                if ip and port:
                    self.start_connection(ip, port)

            self.write_log(f"Node list received: {node_list}\n")
            print("here 4")
            threading.Thread(target=self.talk_to_node, args=(new_connection, False, node), daemon=True).start()
        except Exception as e:
            print("failed to connect", e)
            self.write_log(f"Failed to connect to tracker: {e}\n")
            raise e

    def add_node(self, node):
        """
        Adds a node to the tracker.
        """
        # janky check to make sure we dont add ourselves
        if node.address == (socket.gethostbyname(socket.gethostname()), self.port) or node.address == ("localhost", self.port) or node.address == ("127.0.0.1", self.port):
            self.write_log("Attempted to add self as a node. Ignoring.\n")
            return False
        if node.address in self.nodes:
            self.write_log(f"Node already exists: {node}\n")
            return False
        self.nodes[node.address] = node
        self.write_log(f"Node added: {node}\n")
        return True
    
    def remove_node(self, node):
        """
        Removes a node from the tracker.
        """
        if node in self.nodes:
            self.nodes.remove(node)
            self.write_log(f"Node removed: {node}\n")
        else:
            self.write_log(f"Node not found: {node}\n")

    def accept_connections(self):
        """
        Accepts connections from nodes.
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
        """
        if initial:
            initial_message = connection.recv(1024)
            self.write_log(f"Initial message from node: {initial_message}\n")
            print("Initial message from node:", initial_message)
            leny = int.from_bytes(initial_message[:2], byteorder='big')
            initial_message = initial_message[2:2+leny]
            valid, porty = self.verify_node_connection(initial_message)
            node = None
            if valid:
                self.write_log(f"Connection verified: {connection}\n")
                node_list = [{"ip": n[0], "port": n[1]} for n in self.nodes]
                print(node_list)
                node = Node(connection.getpeername()[0], porty, connection)
                msg = json.dumps(node_list).encode('utf-8')
                self.send_message(msg, node)
                with self.node_list_lock:
                    self.add_node(node)
            else:
                self.write_log(f"Connection failed: {connection}\n")
                return
        else:
            self.broadcast(None, GET_LONGEST_CHAIN, (0).to_bytes(4, byteorder='big'))
        # Send the list of nodes in JSON format to the connected node
        

        while True:
            fragment = b''
            try:
                connection.settimeout(1)
                message = connection.recv(1024*8)
                if message == b'':
                    #connection was closed by peer
                    self.write_log(f"Connection closed by peer: {node}\n")
                    break
                self.write_log(f"Message from node: {message}\n")
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
        Sends a vote to the tracker.
        """
        self.handle_vote(vote.jsonify().encode('utf-8'), None)
        
    def send_election(self, election):
        """
        Sends an election to the tracker.
        """
        self.handle_election(election.jsonify().encode('utf-8'), None)

    def handle_message(self, message, node):
        """
        Handles messages from nodes.
        """
        try:
            typey = int.from_bytes(message[:2], byteorder='big')
            if typey == BLOCK:
                self.write_log(f"Block message received: {message}\n") 
                self.handle_block(message[2:], node)
            elif typey == VOTE:
                self.handle_vote(message[2:], node)
            elif typey == INIT:
                self.write_log(f"Init message received: {message} {node.address}\n")
                # Handle init message here
            elif typey == ELECTION:
                self.handle_election(message[2:], node)
            elif typey == LONGEST_CHAIN:
                self.receive_longest_chain(message[2:], node)
            elif typey == GET_LONGEST_CHAIN:
                self.write_log(f"Get longest chain message received: {message}\n")
                self.get_longest_chain(message[2:], node)
                # Handle get longest chain message here. Return the heeaders for the longest chain
            elif typey == GET_BLOCK:
                self.write_log(f"Get block message received: {message}\n")
                with self.data_lock:
                    if message[2:] in self.blocks:
                        block = self.blocks[message[2:]]
                        # Send the block to the node
                        self.send_message(BLOCK.to_bytes(2, byteorder='big') + block.get_sendable(), node)
                    else:
                        self.write_log(f"Block not found: {len(message[2:])} {message[2:]}\n")
                        for key in self.blocks:
                            self.write_log(f"   Block in chain: {len(key)} {key} ")
                        # Send an error message to the node
                        self.send_error(node, "Block not found")
            elif typey == GET_ELECTION:
                self.write_log(f"Get election message received: {message}\n")
                self.get_election(message[2:], node)
                # Handle get election message here. Return the election for the given name, along with the votes, and the merkle trees to prove it.
            elif typey == ERROR_RESPONSE:
                self.write_log(f"Error response received: {message[2:].decode('utf-8')}\n")
                print(f"Error response received: {message[2:].decode('utf-8')}")
                return
            else:
                self.write_log(f"Unknown message type: {message}\n")
        except json.JSONDecodeError:
            self.write_log(f"Failed to decode message: {message}\n")
        except KeyError as e:
            self.write_log(f"Malformed message: {e}\n")
    def send_message(self, message, node):
        """
        Sends a message to the node.
        """
        if node is None:
            self.write_log("Node is None, not sending message\n")
            return
        with self.send_lock:
            leny = len(message)
            node.connection.send(leny.to_bytes(2, byteorder='big') + message)
            self.write_log(f"Message sent to node {node}: {message}\n")
    def receive_longest_chain(self, message, node):
        """
        Handles receive longest chain messages from nodes. Check it for correctness, and see if we need to switch chains (if so, we need to grab the data for all the nodes we dont have)
        """ 
        #pull out chunks of 84 byte sections
        #these should be in the normal header format
        with self.data_lock:
            for i in range(0, len(message), 84):
                # Extract the block header
                block_header = message[i:i+84]
                index = int.from_bytes(block_header[:4], byteorder='big') 
                # Exract the rest of the block eader fields
                prev_hash = block_header[4:36]  # 32 bytes for previous hash
                this_hash = hashy(block_header[:84]) # hashing the header
                if this_hash in self.blocks:
                    # this block is already in our chain, so we can skip it
                    continue
                self.request_block(this_hash, node)
            

    def get_longest_chain(self, message, node):
        """
        Handles get longest chain messages from nodes. Implement this in the actual node.
        """
        # finding the node with the greatest total work
        max_work = 0
        max_node = None
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
            self.write_log(f"Longest chain sent to node {node}: {result}\n")


    def handle_vote(self, message, node):
        """
        Handles vote messages from nodes. Implement this in the actual node.
        """
        vote = Vote(message)
        # Request the longest chain to find the election
        diff = 0
        chain_header = None
        self.write_log(f"Vote message received: {vote}\n")
        with self.data_lock:
            print("got vote data lock")
            election = None
            if vote.election_hash in self.open_elections: 
                election = self.open_elections[vote.election_hash]
            else:
                self.write_log(f"Vote for ended or non-existent election: {vote.election_hash}\n")
            res = self.check_vote(vote, election, time.time() + 20) 
            print("checked vote")
            if not res:
                self.write_log(f"Vote failed: {res}\n")
                return
            
            gas = 1
            election.used_keys[vote.public_key] = vote.choice
            self.all_things[hashy(vote.jsonify())] = (gas, vote) # theoritical GAS ammount, unimplemented
            self.new_votes.put((gas, next(self.counter), vote))
            print("put vote in queue")
            self.broadcast(node, VOTE, message)

        
    def handle_election(self, message, node):
        """
        Handles election messages from nodes. Implement this in the actual node.
        """
        election = Election(message)
        with self.data_lock:
            if election.hashy in self.open_elections:
                self.write_log(f"Election already exists: {election.name}\n")
                return
            if election.end_time < time.time():
                self.write_log(f"Election has already ended: {election.name}\n")
                return
            gas = 1
            self.open_elections[election.hashy] = election
            self.all_things[hashy(election.jsonify())] = (gas, election) # theoritical GAS ammount, unimplemented
            self.new_elections.put((gas, next(self.counter), election))
            self.write_log(f"Election added: {election.name}\n")
            # Broadcast the election to all nodes
            self.broadcast(node, ELECTION, message)
    
    def check_vote(self, vote, election, time):
        """
        Checks if a vote is valid.
        MUST BE CALLED WITH THE DATA LOCK HELD
        """
        if vote.public_key in election.used_keys:
            self.write_log(f"Vote from used public key: {vote.public_key}\n")
            return False
        
        if election is None:
            if election in self.active_elections:
                election = self.active_elections[election]
            else:
                self.write_log(f"Vote for non-existent election: {vote.election_hash}\n")
                return False
        if vote.public_key not in election.public_keys:
            self.write_log(f"Vote from non-existent public key: {vote.public_key}\n")
            return False
        if vote.choice not in election.choices:
            self.write_log(f"Vote for non-existent choice: {vote.choice}\n")
            return
        if not vote.check_sig():
            self.write_log(f"Vote signature verification failed: {vote.signature}\n")
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
            if len(self.chain_headers) == 0 and index == 0:
                found = True
            if this_hash in self.blocks:
                self.write_log(f"Duplicate block received: {message}\n")
                # WE FOUND A DUPLICATE, BREAK IT UP.
                return
            for header in self.chain_headers:
                thing = header
                print("BLOCK INFO\n\n\n")
                print(header.hash, prev_hash, thing.index, index)
                print("\n\n\n")
                while header.index < index - 1:
                    thing = thing.previous_block
                if thing.index == index - 1 and thing.hash == prev_hash:
                    # this is the chain we are on
                    parent = thing
                    found = True
                

                    
            if not found:
                self.write_log(f"Orphan block received: {message}\n")
                if prev_hash not in self.orphan_pool:
                    self.orphan_pool[prev_hash] = []
                if message not in self.orphan_pool[prev_hash]:
                    self.orphan_pool[prev_hash].append(message)
                self.request_block(prev_hash, node)
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
        block_data = message[84:]
        # Extract the votes and elections from the block data. It is a concatanation of json encoded forms of the votes and elections
        json_data = block_data.decode('utf-8') 
        print("json data: ", json_data)
        if json_data == "":
            json_data = "{}"
        # Parse the JSON data to extract votes and elections
        objects = json.loads(json_data) 
        
        # Parse each object in the block data
        data = []
        for key in objects:
            try:
                # Attempt to parse as a Vote
                data.append(Vote(objects[key]))
            except Exception:
                pass  # Not a valid Vote, try parsing as an Election
            try:
                # Attempt to parse as an Election
                data.append(Election(objects[key]))
            except Exception:
                pass
            try:
                # Attempt to parse as an EndOfElection
                data.append(EndOfElection(objects[key]))
            except Exception:
                print("Invalid object in block: ", objects[key])
                self.write_log(f"Invalid object in block: {objects[key]}\n")
        block = Block(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent, data=data)
        # checking the merkle root
        if block.merkle_root != block.get_merkle_root():
            self.write_log(f"Invalid merkle root: {block.merkle_root} != {block.get_merkle_root()}\n")
            print("invalid merkle root")
            self.send_error(node, "Invalid merkle root")
            return
        ##Checking for rule violations:
        # Difficulty check
        if difficulty != self.getDifficulty(parent):
            self.write_log(f"Difficulty mismatch: {difficulty} != {self.getDifficulty(parent)}\n")
            print("invalid difficulty")
            self.send_error(node, "Invalid difficulty")
            return
        
        # checking the POW
        if not check_proof_of_work(header_hash, difficulty):
            self.write_log(f"Invalid proof of work: {header_hash}\n")
            print("invalid PPOW")
            self.send_error(node, "Invalid proof of work")
            return

        #checking the timestamp
        if not self.check_timestamp(parent, timestamp):
            self.write_log(f"Invalid timestamp: {timestamp}\n")
            self.send_error(node, "Invalid timestamp")
            return

        if not self.check_sigs(block, parent):
            self.write_log("Invalid signatures in block\n")
            self.send_error(node, "Invalid signatures")
            return


        # Remove the parent from self.chain_headers and replace with this node
        print("block approved, adding it to the chain")
        if parent == self.biggest_chain:
            self.biggest_chain = block
            self.remove_new(block)
            self.write_log(f"Chain extended: {block}\n")
        elif block.total_work > parent.total_work:
            self.biggest_chain = block
            self.recompute_new(block)
            self.write_log(f"Chain changed: {block}\n")
        try:
            self.chain_headers.remove(parent)
        except ValueError:
            pass

        self.chain_headers.append(block)
        self.blocks[header_hash] = block
        self.broadcast(node, BLOCK, message)

        if header_hash in self.orphan_pool:
            for orphan in self.orphan_pool[header_hash]:
                self.verify_block(orphan, block, None)
    def send_error(self, node, message):
        """
        Sends an error message to the node.
        """
        if node is None:
            return
        self.send_message(ERROR_RESPONSE.to_bytes(2, byteorder='big') + message.encode('utf-8'), node)
        node.good = False
        self.write_log(f"Error sent to node {node}: {message}\n")

    def request_block(self, hashy, node):
        """
        Requests a block from the node.
        """
        # Send a request to the node for the block with the given hash
        request_message = GET_BLOCK.to_bytes(2, byteorder='big') + hashy
        self.send_message(request_message, node) 
        self.write_log(f"Requesting block {hashy} from node {node}\n")

    def remove_new(self, block):
        """ 
        remove the transactions in the block from the new_elections and new_votes queues
        THE DATA LOCK MUST BE HELD WHEN CALLING THIS FUNCTION
        """

       
        for key in block.elections:
            election = block.elections[key]
            election.new = False
            if hashy(election.jsonify()) in self.all_things:
                self.all_things[election.jsonify()].new = False
            else:
                self.all_things[hashy(election.jsonify())] = election

        for key in block.votes:
            vote = block.votes[key]
            vote.new = False
            if hashy(vote.jsonify()) in self.all_things:
                self.all_things[vote.jsonify()].new = False
                block.votes[key] = vote
            else:
                self.all_things[hashy(vote.jsonify())] = vote
        for key in block.election_ends:
            end = block.election_ends[key]
            end.new = False
            if hashy(end.jsonify()) in self.all_things:
                self.all_things[end.jsonify()].new = False
            else:
                self.all_things[hashy(end.jsonify())] = end
    
    def recompute_new(self, block):
        """
        recomputes the new_elections and new_votes queues, for when we switch chains
        THE DATA LOCK MUST BE HELD WHEN CALLING THIS FUNCTION
        """
        self.open_elections = {}
        # going through self.all_things and setting new to True for all things that are in the new_elections and new_votes queues
        for key in self.all_things:
            thing = self.all_things[key]
            thing.new = True
        # going backwards, starting from block, and makring all the things in the block as not new
        current_block = block
        while current_block is not None:
            for key in current_block.elections:
                election = current_block.elections[key]
                self.open_elections[election.hashy] = election
                election.new = False
                if hashy(election.jsonify()) in self.all_things:
                    self.all_things[election.jsonify()].new = False
                else:
                    self.all_things[hashy(election.jsonify())] = election
            for key in current_block.votes:
                vote = current_block.votes[key]
                vote.new = True
                if hashy(vote.jsonify()) in self.all_things:
                    self.all_things[vote.jsonify()].new = False
                    current_block.votes[key] = vote
                else:
                    self.all_things[hashy(vote.jsonify())] = vote
            for key in current_block.election_ends:
                end = current_block.election_ends[key]
                end.new = False
                if end.election_hash in self.open_elections:
                    del self.open_elections[end.election_hash]
                if hashy(end.jsonify()) in self.all_things:
                    self.all_things[end.jsonify()].new = False
                else:
                    self.all_things[hashy(end.jsonify())] = end
            current_block = current_block.previous_block

        # recomputing new_elections and new_votes based on this new information
        self.new_elections = PriorityQueue()
        self.new_votes = PriorityQueue()
        self.new_ended_elections = PriorityQueue() # not dealing with this here, before we ever use these objects, we will clean out open_elections
        for key in self.all_things:
            thing = self.all_things[key]
            if isinstance(thing, Election) and thing.new:
                self.new_elections.put((thing.timestamp, thing))
            elif isinstance(thing, Vote) and thing.new:
                self.new_votes.put((thing.timestamp, thing))
            else:
                self.write_log(f"Invalid object in recompute_new: {thing}\n")
                continue
    
    def move_to_ended(self):
        """
        Moves the election to the ended elections queue.
        """
        with self.data_lock:
            for key in self.open_elections:
                election = self.open_elections[key]
                if election.end_time < time.time():
                    self.move_election_to_ended(election)
                    del self.open_elections[key]
                    self.write_log(f"Election ended: {election.name}\n")
                    results = {}
                    thing = self.biggest_chain
                    already_done = False
                    while thing is not None:
                        

                        if election.hashy in thing.election_ends:
                            already_done = True
                            break

                        if election.hashy in thing.elections:
                            election = thing.elections[election.hashy]
                            break

                        if election.hashy in thing.votes:
                            for vote in thing.votes[election.hashy]:
                                if vote.choice not in results:
                                    results[vote.choice] = 0
                                results[vote.choice] += 1
                                
                        thing = thing.previous_block
                    if not already_done:
                        self.new_ended_elections.put((election.end_time, next(self.counter), EndOfElection({"election_hash": election.hashy, "results": results})))

    def broadcast(self, sender, typey, message):
        """
        Broadcasts a message to all nodes.
        """
        
        message = typey.to_bytes(2, byteorder='big') + message
        message = len(message).to_bytes(2, byteorder='big') + message
        print("Broadcasting message:", message)
        with self.send_lock:
            for addr, node in self.nodes.items():
                # Check if the node is not the sender
                if node != sender:
                    try:
                        print("Sending message to node:", node.address)
                        node.connection.send(message)
                    except Exception as e:
                        self.write_log(f"Failed to send message to {node}: {e}\n")
                        self.remove_node(node)

    def verify_node_connection(self, initial_message):
        """
        This one makes sure that the connection request is valid, baiscly checking the format of the message
        """
        try:
            if initial_message[:2] == INIT.to_bytes(2, byteorder='big'):
                print("Init message received")
                return True, int.from_bytes(initial_message[2:4], byteorder='big')
            return False, None
        except Exception as e:
            self.write_log(f"Failed to verify node connection: {e}\n")
            return False, 0 
    
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
        print(difficulties)
        print(timestamps)
        if len(timestamps) > 1:
            timestamps.sort(reverse=True)
            time_differences = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
            time_differences = [td if td != 0 else 1 for td in time_differences]
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
    
    def check_sigs(self, block, parent):
        """
        Checks the signatures in the block, as well as ensuring that the vote is a valid one for this chain.
        Runs in O(n) time, where n is the number of blocks on the chain, as it has to go back to try to find the election.
        """
        try:
            for vote in block.votes:
                votes = block.votes[vote]
                election_hash = votes[0].election_hash
                election = None
                if election_hash in block.elections:
                    election = block.elections[vote.election_hash]
                else:
                    this = parent
                    while this is not None:
                        if election_hash in this.elections:
                            election = this.elections[election_hash]
                            break
                        else:
                            this = this.previous_block
                if election is None:
                    self.write_log(f"Election not found: {election_hash}\n")
                    return False
                res = self.check_vote(vote, election, block.timestamp)
                if not res:
                    self.write_log(f"Vote signature verification failed: {vote.signature}\n")
                    return False
            for key in block.election_ends:
                end = block.election_ends[key]
                this = parent
                totals = {}
                while this is not None:
                    if end.election_hash in block.votes:
                        for vote in block.votes[end.election_hash]:
                            if vote.choice not in totals:
                                totals[vote.choice] = 0
                            totals[vote.choice] += 1
                    if end.election_hash in this.elections:
                        election = this.elections[end.election_hash]
                        break
                    else:
                        this = this.previous_block
                if election is None:
                    self.write_log(f"Election not found: {end.election_hash}\n")
                    return False
                # Check if the election is still open
                if election.end_time > block.timestamp:
                    self.write_log(f"Election is still open: {election.name}\n")
                    return False
                # Check if the election has been tampered with
                summy_incoming = 0
                for key in end.results:
                    summy_incoming += end.results[key]
                    if end.results[key] != 0 and key not in totals:
                        self.write_log(f"Election tampered with: {key}\n")
                        return False
                summy_real = 0
                for key in totals:
                    summy_real += totals[key]
                    if totals[key] != 0: 
                        if key not in end.results:
                            self.write_log(f"Election tampered with: {key}\n")
                            return False
                        if totals[key] != end.results[key]:
                            self.write_log(f"Election tampered with: {totals[key]} != {end.results[key]}\n")
                            return False
                    
                    
                if summy_real != summy_incoming:
                    self.write_log(f"Election tampered with: {summy_real} != {summy_incoming}\n")
                    return False
                
        except Exception as e:
            raise e
        return True
    
    def get_election(self, election_hash, node=None):
        """"""""" 
        Takes in the election identifier; starts at current block (self.biggest_chain);
        returns election and its votes IF found
        """
        current_block = self.biggest_chain
        while current_block is not None:
            if election_hash in current_block.elections:
                election = current_block.elections[election_hash]
                votes = []
            
                # search for votes in current and previous block
                search = current_block
                while search is not None:
                    if election_hash in search.votes:
                        for vote in search.votes[election_hash]:
                            votes.append(vote)
                    search = search.previous_block

                # need to send back election data if a node is given
                if node:
                    election_proof = current_block.get_merkle_proof(list(current_block.elections.keys()).index(election_hash))

                    vote_proofs = []
                    for vote in votes:
                        vote_block = self.biggest_chain
                        vote_proof = None
                        while vote_block is not None:
                            if election_hash in vote_block.votes:
                                for i, v in enumerate(vote_block.votes[election_hash]):
                                    if v.public_key == vote.public_key:
                                         # Calculate index in the block's data
                                        vote_index = len(vote_block.elections) + i
                                        vote_proof = vote_block.get_merkle_proof(vote_index)
                                        break
                            if vote_proof:
                                break
                            vote_block = vote_block.previous_block

                        vote_proofs.append({
                            "vote": vote.jsonify(),
                            "proof": vote_proof,
                            "block_hash": vote_block.hashy if vote_block else None
                        })
                    
                    # Prepare response with election, votes, and Merkle proofs
                    election_data = {
                        "election": election.jsonify(),
                        "election_proof": election_proof,
                        "block_hash": current_block.hashy,
                        "votes": vote_proofs
                    }
                        
                    response = json.dumps(election_data).encode('utf-8')
                    election_response = 9
                    self.send_message(election_response.to_bytes(2, byteorder='big') + response, node)
                    
                return election, votes
                
            current_block = current_block.previous_block
            
        # Election not found
        if node:
            self.send_error(node, f"Election not found: {election_hash}")
            
        self.write_log(f"Election not found: {election_hash}\n")
        return None
                    
