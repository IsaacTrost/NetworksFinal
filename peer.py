import utils
import argparse
MAX_CONNECTIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 50= 50


class Peer(utils.ThisNode):
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
        hashy = utils.hashy(message[:84]) # hashing the header
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
        header_hash = utils.hash(block_header)
        block_body = message[84:]
        ##Checking for rule violations:
        # Difficulty check
        if difficulty != self.getDifficulty(parent):
            self.log.write(f"Difficulty mismatch: {difficulty} != {self.getDifficulty(parent)}\n")
            node.connection.send(b"Invalid difficulty")
            node.good = False
            return
        
        # checking the POW
        if not utils.check_proof_of_work(header_hash, difficulty):
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
        block = utils.BlockHeader(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent)
        try:
            self.chain_headers.remove(parent)
        except ValueError:
            pass

        self.chain_headers.append(block)
        self.broadcast(node, message)

        if header_hash in self.orphan_blocks:
            for orphan in self.orphan_blocks[header_hash]:
                self.verify_block(orphan, block, None)

if __name__ == "__main__":
    # get user input to get the IP and port of the tracker, and the name of this peer
    parser = argparse.ArgumentParser(description="Start a peer node.")
    parser.add_argument("--tracker-ip", type=str, required=True, help="IP address of the tracker")
    parser.add_argument("--tracker-port", type=int, required=True, help="Port of the tracker")
    parser.add_argument("--peer-name", type=str, required=True, help="Name of this peer")
    args = parser.parse_args()

    tracker_ip = args.tracker_ip
    tracker_port = args.tracker_port
    peer_name = args.peer_name
    # Example usage
    tracker = Peer(peer_name)
    # Add nodes, handle messages, etc.
    pass