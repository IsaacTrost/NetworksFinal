from utils import *
class Vote:
    """
    Simple class to represent a vote.
    """
    def __init__(self, message):
        try:
            data = json.loads(message)
            election_hash = data["election_hash"]
            choice = data["choice"]
            public_key = data["public_key"]
            signature = data["signature"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid vote message format: {e}")
        self.election_hash = election_hash
        self.choice = choice
        self.public_key = public_key
        self.signature = signature
        self.new = True
    
    def jsonify(self):
        """
        Converts the vote to JSON format.
        """
        return json.dumps({
            "election_hash": self.election_hash,
            "choice": self.choice,
            "public_key": self.public_key,
            "signature": self.signature,
        })

    def check_sig(self):
        """
        Checks the signature of the vote.
        Assumes the signature is over (election_hash + choice) using the provided public_key.
        """
        

        try:
            # Prepare the message that was signed
            message = (self.election_hash + self.choice).encode('utf-8')
            # Load the public key (assume PEM format)
            public_key = serialization.load_der_public_key(base64.b64decode(self.public_key))
            # Decode the signature 
            signature_bytes = base64.b64decode(self.signature)
            # Verify the signature
            public_key.verify(
                signature_bytes,
                message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            return False
