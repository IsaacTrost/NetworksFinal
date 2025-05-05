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
DEFAULT_DIFFICULTY = 128 
INIT = 1
VOTE = 2
BLOCK = 3
ELECTION = 4
LONGEST_CHAIN = 5
GET_LONGEST_CHAIN = 6
GET_BLOCK = 7
GET_ELECTION_RES = 8
ELECTION_RES = 9
ERROR_RESPONSE = 10
MAX_BLOCK_SIZE = 1024 * 1024
TARGET = 2**32
MAX_LEVELS = 8
START_ZEROS = 2
CLAMP = 1.2
def hashy(data):
    """
    Hashes the data using SHA-256.
    """
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()

def check_proof_of_work(hash_result, difficulty):
    """
    Checks if the hash meets the difficulty requirement.
    A higher difficulty means a lower target, making it harder.
    Doubling difficulty roughly halves the probability (doubles expected time).
    """
    # Ensure difficulty is at least 1 to avoid division by zero and ensure target is <= TARGET
    if difficulty < 1:
        # Or raise an error, depending on how difficulty is managed
        return False

    # 1. Check for the fixed number of leading zero bytes (constant factor)
    if hash_result[:START_ZEROS] != b'\x00' * START_ZEROS:
        return False

    # 2. Calculate the target based on difficulty (variable factor)
    # Target is inversely proportional to difficulty.
    # Use integer division. TARGET is 2**32.
    target = TARGET // difficulty

    # 3. Extract the relevant part of the hash as an integer
    next_4_bytes = int.from_bytes(hash_result[START_ZEROS:START_ZEROS + 4], byteorder='big', signed=False)

    # 4. Check if the hash part is less than the target
    return next_4_bytes < target
