from peer import Peer
from utils import *
from block import Block
from election import Election
from vote import Vote
from end_of_election import EndOfElection
import json
import argparse
import random
class LightNode(Peer):
    """
    Lightweight node that extends Peer class but doesn't maintain the full blockchain.
    Doesn't store full chain.
    """

    def __init__(self, name, port, tracker_ip=None, tracker_port=None):
        # Initialize with parent class but modify behavior
        super().__init__(name, port, tracker_ip, tracker_port)
        self.write_log("Initializing as lightweight node")
        self.election_reses = {}
        self.election_reses_lock = threading.Lock()

        
        
    def mine(self):
        """Override mining to do nothing in lightweight node"""
        self.write_log("Mining disabled in lightweight node")
        return
    def mining(self):
        """Override mining to do nothing in lightweight node"""
        self.write_log("Mining disabled in lightweight node")
        return
    
    def get_block(self, message, node):
        """
        Tosses an error back to the sender, as we dont carry the data.
        """
        self.write_log("Received block request, but this is a lightweight node. Ignoring.")
        # Send an error message back to the sender
        self.send_error("This is a lightweight node, no data available", node)
    
    def receive_longest_chain(self, message, node):
        """
        Handles incoming messages from other nodes.
        The light version is just going to mindlessly pass them on without doing any checks.
        This should keep the p2p network running, but does not require us to do any work (since this node wont mine, it does not matter)
        """
        with self.data_lock:
            for i in range(len(message) - 84, -1, -84):
                # Extract the block header
                block_header = message[i:i + 84]
                index = int.from_bytes(block_header[:4], byteorder='big')
                prev_hash = block_header[4:36]
                parent = None
                if prev_hash not in self.blocks and index != 0:
                    self.write_log(f"Block {index} not in chain, exiting")
                    return
                if index != 0:
                    parent = self.blocks[prev_hash]
                
                self.check_header(block_header, parent)

    def handle_vote(self, message, node):
        """
        Handles incoming vote messages.
        The light version is just going to mindlessly pass them on without doing any checks.
        This should keep the p2p network running, but does not require us to do any work (since this node wont mine, it does not matter)
        """
        self.broadcast(node, VOTE, message)
        self.write_log("Vote received, broadcasting") 

    def handle_election(self, message, node):
        """
        Handles incoming election messages.
        The light version is just going to mindlessly pass them on without doing any checks.
        This should keep the p2p network running, but does not require us to do any work (since this node wont mine, it does not matter)
        """
        print(message, ELECTION)
        self.broadcast(node, ELECTION, message)
        self.write_log("Election received, broadcasting")
    


    def handle_block(self, message, node, new=True):
        """
        Handles incoming block messages.
        The light version is just going to mindlessly pass them on without doing any checks.
        This should keep the p2p network running, but does not require us to do any work (since this node wont mine, it does not matter)
        """
        with self.data_lock:
            # Extract the block header
            block_header = message[:84]
            index = int.from_bytes(block_header[:4], byteorder='big')
            prev_hash = block_header[4:36]
            parent = None
            if prev_hash not in self.blocks and index != 0:
                self.write_log(f"Block {index} not in chain, exiting")
                return
            if index != 0:
                parent = self.blocks[prev_hash]
            
            added = self.check_header(block_header, parent)
            if added:
                self.write_log(f"Added block {index} to chain")
                self.broadcast(node, BLOCK, message)

    def check_header(self, header, parent):
        """
        Check the header of a block.
        """
        # Check if the header is valid
        if len(header) != 84:
            self.write_log("Invalid header length")
            return False
        # Check if the hash is valid
        header_hash = hashy(header)
        
        if header_hash in self.blocks:
            self.write_log("Header already in chain")
            return False
        index = int.from_bytes(header[:4], byteorder='big')
        prev_hash = header[4:36]
        merkle_root = header[36:68]
        timestamp = int.from_bytes(header[68:76], byteorder='big')
        difficulty = int.from_bytes(header[76:80], byteorder='big')
        nonce = int.from_bytes(header[80:84], byteorder='big')
        if index != 0 and parent is None:
            self.write_log("Parent not in chain")
            return False
        if not check_proof_of_work(header_hash, difficulty):
            self.write_log("Invalid proof of work")
            return False
        if difficulty != self.getDifficulty(parent):
            self.write_log("Invalid difficulty")
            return False
        if not self.check_timestamp(parent, timestamp):
            self.write_log("Invalid timestamp")
            return False
        self.write_log("Header is valid")
        block = Block(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent)
        self.blocks[header_hash] = block
        if parent == self.biggest_chain:
            self.write_log("Header is in the biggest chain")
            self.biggest_chain = block
        elif block.total_work > self.biggest_chain.total_work:
            self.write_log("Header is in a bigger chain")
            self.biggest_chain = block
        try:
            self.chain_headers.remove(parent)
        except ValueError:
            pass
        self.chain_headers.append(block)
        return True
    
    def request_election(self, election_hash):
        """
        Request an election from the tracker.
        Picks up to 5 random nodes, and sends them a request for the election.
        Each will send their proofs for the election back. We will use the first that has the election end, or the first
        assuming none of them do. If something does not check out, we will move to the next one.
        
        args:
            election_hash: The hash of the election to request.
        
        returns:
            None, actual processing will be done once we get the message back.
        """
        self.write_log(f"Requesting election {election_hash} from tracker")
        # Pick up to 5 random nodes
        with self.node_list_lock:
            nodes = list(self.nodes.keys())
            if len(nodes) > 5:
                nodes = random.sample(nodes, 5)
            for node in nodes:
                # Send a request to each node
                self.send_message(GET_ELECTION_RES.to_bytes(2, byteorder='big') + election_hash, self.nodes[node])
        results = []
        for _ in range(10):
            # Wait for the response
            with self.election_reses_lock:
                if election_hash in self.election_reses and len(self.election_reses[election_hash]) == len(nodes):
                    results = self.election_reses[election_hash]
                    del self.election_reses[election_hash]
                    break
            time.sleep(1)
        if election_hash in self.election_reses:
            results = self.election_reses[election_hash]
        if len(results) == 0:
            self.write_log(f"Election {election_hash} not found")
            return "election not found"
        max_votes = 0
        best_election = None
        for result in results:
            if best_election is not None:
                self.write_log(f"best so far: {best_election.used_keys}")
            else:
                self.write_log(f"best so far: None")
            vote_totals = {}
            json_data = None
            try:
                json_data = json.loads(result)
            except json.JSONDecodeError:
                self.write_log(f"Error decoding election result: {result}")
                continue
            try:
                # handling the start
                start = json_data["start"]
                election = Election(start["election"])
                for choice in election.choices:
                    vote_totals[choice] = 0
                election_proof = start["proof"]
                election_block = base64.b64decode(start["block"])
                if election_block not in self.blocks:
                    self.write_log(f"Election block {election_block} not in chain")
                    continue
                election_block = self.blocks[election_block]
                valid = election_block.verify_merkle_proof(election, election_proof)
                if not valid:
                    self.write_log(f"Election proof not valid")
                    continue

                # handling the votes
                votes = json_data["votes"]
                for vote in votes:
                    vote_obj = Vote(vote["vote"])
                    vote_proof = vote["proof"]
                    vote_block = base64.b64decode(vote["block"])
                    if vote_block not in self.blocks:
                        self.write_log(f"Vote block {vote_block} not in chain")
                        continue
                    vote_block = self.blocks[vote_block]
                    valid = vote_block.verify_merkle_proof(vote_obj, vote_proof)
                    if not valid:
                        self.write_log(f"Vote proof not valid")
                        continue
                    vote_good = self.check_vote(vote_obj, election, time.time())
                    if not vote_good:
                        self.write_log(f"Vote {vote_obj} not valid")
                        continue
                    vote_totals[vote_obj.choice] += 1
                    election.used_keys[vote_obj.public_key] = vote_obj.choice


                end = json_data["end"]
                election.winner = max(vote_totals, key=vote_totals.get)
                election.total_votes = sum(vote_totals.values())
                if end != {}:
                    # handling the end
                    end_obj = EndOfElection(end["election_end"])
                    end_proof = end["proof"]
                    end_block = base64.b64decode(end["block"])
                    if end_block not in self.blocks:
                        self.write_log(f"End block {end_block} not in chain")
                        continue
                    end_block = self.blocks[end_block]
                    valid = end_block.verify_merkle_proof(end_obj, end_proof)
                    if not valid:
                        self.write_log(f"End proof not valid")
                        continue
                    election.finished = True
                    
                    return election
                else:
                    if sum(vote_totals.values()) > max_votes:
                        max_votes = sum(vote_totals.values())
                        best_election = election
                         
            except KeyError:
                self.write_log(f"Error processing election result: {json_data}")
                continue
        return best_election

    def handle_election_res(self, message, node):
        self.write_log(message)
        election_hash = message[:32]
        with self.election_reses_lock:
            if election_hash not in self.election_reses:
                self.election_reses[election_hash] = []
            self.election_reses[election_hash].append(message[32:])
            if len(self.election_reses[election_hash]) == 5:
                self.write_log(f"Got all election results for {election_hash}")
            else:
                self.write_log(f"Got election result for {election_hash}, waiting for more")

    

    
    

        
if __name__ == "__main__":
    # Example usage
    parser = argparse.ArgumentParser(description="Start a LightNode.")
    parser.add_argument("name", type=str, help="Name of the LightNode")
    parser.add_argument("--port", type=int, required=True, help="Port number for the LightNode")
    parser.add_argument("--tracker-ip", type=str, required=True, help="IP address of the tracker")
    parser.add_argument("--tracker-port", type=int, required=True, help="Port number of the tracker")

    args = parser.parse_args()

    node = LightNode(args.name, args.port, args.tracker_ip, args.tracker_port)
    while True:
        # Keep the node running
        pass

