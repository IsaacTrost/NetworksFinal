import time
import threading
from peer import Peer
from utils import * # Assuming BLOCK type is defined here
from block import Block # Assuming Block class is defined here
from election import Election
from vote import Vote
from end_of_election import EndOfElection

class ForkingNode(Peer):
    def __init__(self, name, port, tracker_ip=None, tracker_port=None, hold_count=0):
        """
        Initializes a ForkingNode.
        Args:
            hold_count (int): Number of blocks to mine and hold before releasing.
                              If 0, behaves like a normal peer.
        """
        super().__init__(name, port, tracker_ip, tracker_port)
        self.hold_count = hold_count
        self.held_blocks = []
        self.release_lock = threading.Lock()
        self.is_releasing = False
        # Flag to ensure mining thread starts only once if run directly
        self._mining_started_by_main = False
        self.write_log(f"Initialized ForkingNode. Will hold {self.hold_count} blocks before releasing.")
    
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
        self.held_blocks.append(block)
        if len(self.held_blocks) > self.hold_count:
            for held_block in self.held_blocks:
                self.broadcast(None, BLOCK, held_block.get_sendable()) 
            self.write_log(f"INF: Releasing held blocks: {len(self.held_blocks)}\n")
            self.stop_mining()

        # checking if this was the parent to any orphans, if so we can process those.
        if header_hash in self.orphan_pool:
            for orphan in self.orphan_pool[header_hash]:
                self.write_log(f"INF: Orphan block parent found: {orphan}\n")
                self.verify_block(orphan, block, None)
            del self.orphan_pool[header_hash]
        
    def handle_message(self, message, node):
        """
        Handles messages from nodes.
        args:
        - message: The message to handle
        - node: The node that sent the message
        """
        try:
            typey = int.from_bytes(message[:2], byteorder='big')
            if typey == BLOCK:
                # we are ignoring blocks that come in
                pass
                # self.handle_block(message[2:], node)
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
                pass # not doing this, as that would show our blocks
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
            else:
                self.write_log(f"Unknown message type: {message[:2]}\n")
        # checks so I dont have to put these in every one (i still do sometimes though)
        except json.JSONDecodeError:
            self.write_log(f"Failed to decode message: {message}\n")
        except KeyError as e:
            self.write_log(f"Malformed message: {e}\n")



    def handle_vote(self, message, node):
        
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
            self.new_votes[hashy(vote.jsonify())] = vote # add the vote
    
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
            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start a forking node.")
    parser.add_argument('--port', type=int, required=True, help='Port number for this peer to listen on')
    parser.add_argument('--tracker-ip', type=str, required=False, help='Tracker IP address')
    parser.add_argument('name', type=str, help='Name of the peer')
    parser.add_argument('--tracker-port', type=int, required=False, help='Tracker port number')
    parser.add_argument('--hold-count', type=int, default=0, help='Number of blocks to hold before releasing')
    args = parser.parse_args()

    print(f"Starting ForkingNode '{args.name}' on port {args.port}, connecting to tracker at {args.tracker_ip}:{args.tracker_port}")
    node = ForkingNode(args.name, port=args.port, tracker_ip=args.tracker_ip, tracker_port=args.tracker_port, hold_count=args.hold_count)

    # Start the mining process (which handles holding logic internally)
    node.mine()
    node._mining_started_by_main = True # Mark that main started it

    # Keep the main thread alive to allow background threads to run
    try:
        while True:
            # Optional: Add checks here, e.g., if mining thread died unexpectedly
            time.sleep(60)
    except KeyboardInterrupt:
        print(f"\nShutting down ForkingNode '{args.name}'...")
        # Add any specific shutdown logic for ForkingNode if needed
        # node.shutdown() # If Peer has a shutdown method