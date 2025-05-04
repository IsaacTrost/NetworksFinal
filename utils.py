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
INIT = 0
VOTE = 1
BLOCK = 2
ELECTION = 3
GET_LONGEST_CHAIN = 4
GET_BLOCK = 5
GET_ELECTION = 6
MAX_BLOCK_SIZE = 1024 * 1024
TARGET = 2**32
MAX_LEVELS = 8

def hashy(data):
    """
    Hashes the data using SHA-256.
    """
    return hashlib.sha256(data).digest()

def check_proof_of_work(hash_result, difficulty):
    """
    Checks if the hash of the data has the required number of leading zeros.
    """
    # Check if the bottom 3 bytes are 0
    if hash_result[:3] != b'\x00\x00\x00':
        return False

    # Check if 2^32 - difficulty is less than the next 8 bytes
    target = TARGET - difficulty
    next_4_bytes = int.from_bytes(hash_result[4:8], byteorder='big')
    return next_4_bytes < target
