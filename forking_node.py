import time
import threading
from peer import Peer
from utils import * # Assuming BLOCK type is defined here
from block import Block # Assuming Block class is defined here

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
        self.write_log(f"Initialized ForkingNode. Will hold {self.hold_count} blocks before releasing.")

    def add_block(self, block):
        """
        Overrides add_block to potentially hold the block instead of broadcasting.
        Only holds blocks that *this node* mined itself.
        """
        # Check if the block was mined by this node (simple check based on recent mining)
        # A more robust check might involve comparing miner ID if blocks store it.
        # For this simulation, we assume if we just mined it, it's ours.
        # The base add_block logic handles chain validation and adding to self.blocks

        # Perform standard validation and chain addition first
        added_successfully = super().add_block(block)

        if not added_successfully:
            return False # Block was invalid or duplicate, don't hold/release

        # Check if holding is enabled and if we should hold *this* block
        # We only hold blocks we mined. We assume a block added right after
        # mining loop finishes is ours. This is imperfect but works for simulation.
        # A better way would be to modify the mine() loop directly.
        # Let's modify mine() instead for clarity.

        # Return True as the block was added to the local chain structure
        return True


    def mine(self):
        """
        Overrides the mining loop to hold blocks instead of broadcasting immediately.
        """
        if self.hold_count <= 0:
            # If not holding, use the normal mining behavior
            super().mine()
            return

        # Custom mining loop for holding blocks
        self.write_log("Starting holding mining process...")
        self.mining_active = True
        try:
            while self.mining_active and len(self.held_blocks) < self.hold_count:
                parent_block = self.get_head()
                if not parent_block:
                    self.write_log("Cannot mine without parent block. Waiting...")
                    time.sleep(5)
                    continue

                difficulty = self.getDifficulty(parent_block)
                data = self.get_objects() # Get transactions
                merkle_root = self.create_merkle_tree_from_data(data)
                index = parent_block.index + 1
                timestamp = int(time.time())
                nonce = 0
                target_reached = False

                self.write_log(f"Mining block {index} with difficulty {difficulty} (Target: {self.hold_count} held blocks)")

                start_time = time.time()
                while self.mining_active and len(self.held_blocks) < self.hold_count:
                    header_prefix = b''.join([
                        index.to_bytes(4, 'big'), parent_block.hashy, merkle_root,
                        timestamp.to_bytes(8, 'big'), difficulty.to_bytes(4, 'big'),
                        nonce.to_bytes(4, 'big')
                    ])
                    hash_result = hashy(header_prefix)

                    if check_proof_of_work(hash_result, difficulty):
                        new_block = Block(index, parent_block.hashy, merkle_root, timestamp,
                                          difficulty, nonce, data, parent_block)
                        new_block.hashy = hash_result

                        # Add locally first (using base class method to update chain state)
                        if super().add_block(new_block):
                            self.write_log(f"Successfully mined and validated block {index}. Holding it.")
                            with self.release_lock:
                                self.held_blocks.append(new_block)
                            target_reached = True
                            break # Exit inner nonce loop, proceed to next block
                        else:
                            # Should not happen if mined correctly, but handle anyway
                            self.write_log(f"ERROR: Mined block {index} failed local validation. Discarding.")
                            target_reached = False # Ensure we don't break outer loop incorrectly
                            break # Exit inner nonce loop, retry mining block index

                    nonce += 1
                    # Add a small sleep/yield if CPU usage is too high
                    if nonce % 100000 == 0: time.sleep(0.001)
                    if nonce > 2**32: # Safety break for nonce
                         self.write_log(f"Nonce overflow for block {index}. Retrying.")
                         timestamp = int(time.time()) # Update timestamp and retry
                         nonce = 0


                if not self.mining_active:
                    self.write_log("Mining stopped externally.")
                    break # Exit outer mining loop

                if not target_reached:
                    # If inner loop exited without finding nonce (e.g., nonce overflow handled)
                    # continue the outer loop to retry mining the same index
                    continue

            # End of outer mining loop (either stopped or reached hold_count)
            if len(self.held_blocks) >= self.hold_count:
                self.write_log(f"Reached target of {self.hold_count} held blocks. Releasing burst.")
                self.release_held_blocks()

        except Exception as e:
            self.write_log(f"ERROR in holding mining loop: {e}")
        finally:
            self.mining_active = False
            self.write_log("Holding mining process finished.")


    def release_held_blocks(self):
        """Broadcasts all held blocks sequentially."""
        with self.release_lock:
            if self.is_releasing or not self.held_blocks:
                return
            self.is_releasing = True
            blocks_to_release = list(self.held_blocks) # Copy list
            self.held_blocks.clear() # Clear original list

        self.write_log(f"Releasing {len(blocks_to_release)} held blocks...")
        for i, block in enumerate(blocks_to_release):
            self.write_log(f"Broadcasting held block {block.index} ({i+1}/{len(blocks_to_release)})...")
            # Use the broadcast method from the base Peer class
            self.broadcast(block.get_sendable(), BLOCK, None)
            time.sleep(0.1) # Small delay between broadcasts to avoid overwhelming network buffers

        self.write_log("Finished releasing held blocks.")
        self.is_releasing = False

    # Optional: Override handle_block if specific "ignore" logic is needed,
    # but relying on standard chain validation is generally better for testing resilience.
    # def handle_block(self, message_data, node):
    #     if self.name == "Miner2" and node.name == "Miner1": # Example: Identify sender
    #          self.write_log("Miner2 ignoring block from Miner1 during holding phase.")
    #          return
    #     super().handle_block(message_data, node)
