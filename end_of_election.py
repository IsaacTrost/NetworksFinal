import json
import base64

class EndOfElection:
    def __init__(self, message):
        """
        Initializes the EndOfElection object with the given message.
        The message can be a JSON string or a dictionary.
        
        The expected format is:
        {
            "election_hash": "<base64_encoded_election_hash>",
            "results": {
                "<choice1>": <count1>,
                "<choice2>": <count2>,
                ...
            }
        }
        """
        data = message if isinstance(message, dict) else json.loads(message)
        self.election_hash_b64 = data["election_hash"]  # hash of the election
        self.election_hash = base64.b64decode(self.election_hash_b64)
        self.results = data["results"]         # {choice: count, ...}
        self.new = True
        self.len = len(self.jsonify())

    def jsonify(self):
        return json.dumps(self.get_json_dict())
    
    def get_json_dict(self):
        return {
            "type": "end_of_election",
            "election_hash": self.election_hash_b64,
            "results": self.results
        }
        

    