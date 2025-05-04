import json

class EndOfElection:
    def __init__(self, message):
        data = message if isinstance(message, dict) else json.loads(message)
        self.election_hash = data["election_hash"]  # hash of the election
        self.results = data["results"]         # {choice: count, ...}
        self.new = True

    def jsonify(self):
        return json.dumps({
            "type": "end_of_election",
            "election_hash": self.election_hash,
            "results": self.results
        })

    