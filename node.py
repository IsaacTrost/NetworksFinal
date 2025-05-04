from utils import *

class Node:
    """
    Simple class to represent a node in the network.
    """
    def __init__(self, ip, port, connection):
        self.address = (ip, port)
        self.connection = connection
        self.good = True
        self.lastSeen = 0
    