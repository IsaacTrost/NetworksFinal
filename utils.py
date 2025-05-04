import hashlib

import socket
import json
import threading
import time
from queue import PriorityQueue
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
import base64

MAX_CONNECTIONS = 50
DEFAULT_DIFFICULTY = 65536
INIT = 1
VOTE = 2
BLOCK = 3
ELECTION = 4
LONGEST_CHAIN = 5
GET_LONGEST_CHAIN = 6
GET_BLOCK = 7
GET_ELECTION = 8
ERROR_RESPONSE = 9
MAX_BLOCK_SIZE = 1024 * 1024
TARGET = 2**32
MAX_LEVELS = 8
START_ZEROS = 3
def hashy(data):
    """
    Hashes the data using SHA-256.
    """
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()

def check_proof_of_work(hash_result, difficulty):
    """
    Checks if the hash of the data has the required number of leading zeros.
    """
    # Check if the bottom 3 bytes are 0
    if hash_result[:START_ZEROS] != b'\x00' * START_ZEROS:
        return False

    # Check if 2^32 - difficulty is less than the next 8 bytes
    target = TARGET - difficulty
    next_4_bytes = int.from_bytes(hash_result[START_ZEROS:START_ZEROS + 4], byteorder='big')
    return next_4_bytes < target
