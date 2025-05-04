
from utils import *

import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

class Verifier:
    def __init__(self, difficulty_bits=16):
        self.difficulty_bits = difficulty_bits

    def check_proof_of_work(self, hash_result: bytes) -> bool:
        bits = ''.join(f'{byte:08b}' for byte in hash_result)
        return bits.startswith('0' * self.difficulty_bits)

    def verify_signature(self, pubkey_pem: bytes, signature: bytes, message: bytes) -> bool:
        try:
            pubkey = serialization.load_pem_public_key(pubkey_pem)
            pubkey.verify(
                signature,
                message,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    def build_merkle_root(self, tx_hashes: list[bytes]) -> bytes:
        if not tx_hashes:
            return b'\x00' * 32
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            tx_hashes = [
                hashlib.sha256(tx_hashes[i] + tx_hashes[i + 1]).digest()
                for i in range(0, len(tx_hashes), 2)
            ]
        return tx_hashes[0]


