import cryptography
import hashlib
import socket
import json
import threading

import utils

MAX_CONNECTIONS = 50


class Tracker(utils.ThisNode):

    def handle_block(self, message, node):
        """
        Handles block messages from nodes.
        """
        self.log.write(f"Handling block message: {message}\n")
        # Extract the first 4 bytes as the index
        block_index = int.from_bytes(message['block_data'][:4], byteorder='big')
        # Check if the block is a duplicate
        block_hash = hashlib.sha256(message['block_data']).hexdigest()
        for chain in self.chain_headers:
            if block_index < len(chain) and chain[block_index] == block_hash:
                self.log.write(f"Duplicate block detected: {block_hash}\n")
                return

        # Confirm the block's previous hash
        previous_hash = message['block_data'][4:36].hex()
        target_chain = None
        for chain in self.chain_headers:
            if block_index == 0 or (block_index - 1 < len(chain) and chain[block_index - 1] == previous_hash):
            target_chain = chain
            break

        if target_chain is None:
            self.log.write(f"Block does not match any chain: {block_hash}\n")
            return

        # Add the block to the appropriate chain
        if block_index == len(target_chain):
            target_chain.append(block_hash)
            self.log.write(f"Block added to chain: {block_hash}\n")
        else:
            self.log.write(f"Orphan block detected: {block_hash}\n")
            orphan_chain = target_chain[:block_index] + [block_hash]
            self.chain_headers.append(orphan_chain)
        # Process the block message here
        pass
    def handle_transaction(self, message, node):
        """
        Handles transaction messages from nodes.
        """
        self.log.write(f"Handling transaction message: {message}\n")
        # Process the transaction message here
        pass

    




        
        


        
        