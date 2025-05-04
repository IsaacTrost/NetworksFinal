from utils import *
import time
import json

class Election:
    """
    Simple class to represent an election.
    """
    def __init__(self, message):
        try:
            data = json.loads(message)
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
        self.timestamp = int(time.time())
        self.end_time = end_time
        self.new = True
        self.hashy = hashy(self.jsonify().encode('utf-8'))
        self.len = len(self.jsonify())

    
    def jsonify(self):
        """
        Converts the election to JSON format.
        """
        return json.dumps({
            "name": self.name,
            "choices": self.choices,
            "public_keys": self.public_keys,
            "end_time": self.end_time
        })