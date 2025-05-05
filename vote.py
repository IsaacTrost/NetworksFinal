from utils import *
import json 
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
import base64

class Vote:
    """
    Simple class to represent a vote.
    """
    def __init__(self, message):
        """
        Initializes the Vote object with the given message.
        The message can be a JSON string or a dictionary.

        args:
        - message: JSON string or dictionary containing the vote data.
        The expected format is:
        {
            "election_hash": "<base64_encoded_election_hash>",
            "choice": "<choice>",
            "public_key": "<base64_encoded_public_key>",
            "signature": "<base64_encoded_signature>"
        }
        """

        data = message if isinstance(message, dict) else json.loads(message)
        election_hash = data["election_hash"]
        choice = data["choice"]
        public_key = data["public_key"]
        signature = data["signature"]
        
        self.election_hash_b64 = election_hash
        self.election_hash = base64.b64decode(election_hash)
        self.choice = choice
        self.public_key = public_key
        self.signature = signature
        self.new = True
        self.len = len(self.jsonify())
    
    def jsonify(self):
        """
        Converts the vote to JSON format.
        """
        return json.dumps(self.get_json_dict())

    def get_json_dict(self):
        """
        Returns the vote as a dictionary.
        """
        return {
            "type": "vote",
            "election_hash": self.election_hash_b64,
            "choice": self.choice,
            "public_key": self.public_key,
            "signature": self.signature,
        } 
    @staticmethod
    def sign(private_key, election_hash, choice):
        """
        Signs the vote using the provided private key.
        Assumes the signature is over (election_hash + choice).
        """
        # Prepare the message to sign
        message = (election_hash + choice.encode('utf-8'))
        print(f"VOTE Message to sign: {message}")
        
        # Sign the message
        signature = private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Encode the signature in base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return signature_b64
    def check_sig(self):
        """
        Checks the signature of the vote.
        The signature should be over (election_hash + choice) using the provided public_key.
        """
        try:
            # Prepare the message that was signed
            message = (self.election_hash + self.choice.encode('utf-8'))
            print(f"VOTE Message to verify: {message}")
            # Load the public key (assume PEM format)
            public_key = serialization.load_der_public_key(base64.b64decode(self.public_key))
            print("CURVE:", self.public_key)
            # Decode the signature 
            signature_bytes = base64.b64decode(self.signature)
            # Verify the signature
            print("checking")
            public_key.verify(
                signature_bytes,
                message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
