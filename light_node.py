from peer import Peer
from utils import hashy

class LightNode(Peer):
    """
    Lightweight node that extends Peer class but doesn't maintain the full blockchain.
    Doesn't store full chain.
    """

    def __init__(self, name, port, tracker_ip=None, tracker_port=None):
        # Initialize with parent class but modify behavior
        super().__init__(name, port, tracker_ip, tracker_port)
        self.write_log("Initializing as lightweight node")
        
        # We don't need to store the full blockchain
        self.chain_headers = []
        self.blocks = {}
        self.biggest_chain = None
        
    def mine(self):
        """Override mining to do nothing in lightweight node"""
        self.write_log("Mining disabled in lightweight node")
        return

    def handle_block(self, message, node, new=True):
        """
        Override to only store block headers, not full blocks
        """
        # Extract header information (first 84 bytes)
        header = message[:84]
        index = int.from_bytes(header[:4], byteorder='big')
        prev_hash = header[4:36]
        merkle_root = header[36:68]
        timestamp = int.from_bytes(header[68:76], byteorder='big')
        difficulty = int.from_bytes(header[76:80], byteorder='big')
        nonce = int.from_bytes(header[80:84], byteorder='big')
        header_hash = hashy(header)
        
        self.write_log(f"Received block header: index={index}, hash={header_hash.hex()}")
        
        # Check if we already have this header
        with self.data_lock:
            if header_hash in self.blocks:
                return
            
            # Find parent
            parent = None
            if index == 0:  # Genesis block
                parent = None
            else:
                for h in self.chain_headers:
                    if h.hash == prev_hash:
                        parent = h
                        break
            
            # If parent not found, store as orphan
            if parent is None and index > 0:
                if prev_hash not in self.orphan_pool:
                    self.orphan_pool[prev_hash] = []
                self.orphan_pool[prev_hash].append(message)
                return
            
            # Verify proof of work
            if not check_proof_of_work(header_hash, difficulty):
                self.write_log(f"Invalid proof of work")
                return
            
            # Create lightweight block (header only)
            block = Block(index, header_hash, prev_hash, merkle_root, timestamp, difficulty, nonce, parent)
            
            # Update chain
            self.chain_headers.append(block)
            self.blocks[header_hash] = block
            
            # Update biggest chain if needed
            if parent == self.biggest_chain or (self.biggest_chain is None and index == 0):
                self.biggest_chain = block
            elif block.total_work > (self.biggest_chain.total_work if self.biggest_chain else 0):
                self.biggest_chain = block
            
            # Process orphans
            if header_hash in self.orphan_pool:
                orphans = self.orphan_pool[header_hash]
                del self.orphan_pool[header_hash]
                for orphan in orphans:
                    self.handle_block(orphan, None, False)
            
            # Forward the header to peers
            if new:
                self.broadcast(node, BLOCK, header)
    
    def get_block(self, block_hash):
        """Request a specific block from peers when needed"""
        for _, node in self.nodes.items():
            try:
                self.send_message(GET_BLOCK.to_bytes(2, byteorder='big') + block_hash, node)
                return True
            except:
                continue
        return False
