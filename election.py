from utils import *
import time
import json

class Election:
    """
    Simple class to represent an election.
    """
    def __init__(self, message):
        """
        Initializes the Election object with the given message.

        The message can be a JSON string or a dictionary.
        The expected format is:
        {
            "name": "<election_name>",
            "choices": ["<choice1>", "<choice2>", ...],
            "public_keys": ["<base64_encoded_public_key1>", "<base64_encoded_public_key2>", ...],
            "end_time": <end_time_in_seconds>
        }
        """
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            name = data["name"]
            choices = data["choices"]
            public_keys = data["public_keys"]
            end_time = data["end_time"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid election message format: {e}")
        self.name = name
        self.choices = choices
        self.public_keys = public_keys
        self.used_keys = {}
        self.votes = {}
        self.total_votes = 0
        self.finished = False
        self.winner = None
        self.end_time = end_time
        self.new = True
        self.hashy = hashy(self.jsonify())
        self.len = len(self.jsonify())

    
    def jsonify(self):
        """
        Converts the election to JSON format.
        """
        return json.dumps(self.get_json_dict())
    
    def get_json_dict(self):
        """
        Returns the election as a dictionary.
        """
        return {
            "type": "election",
            "name": self.name,
            "choices": self.choices,
            "public_keys": self.public_keys,
            "end_time": self.end_time
        }