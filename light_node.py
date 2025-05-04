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


    pass