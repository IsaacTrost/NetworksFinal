from flask import Flask, request, jsonify
from flask_cors import CORS
from light_node import LightNode
import time

# Need changes to match tracker set up 
TRACKER_IP = "127.0.0.1"
TRACKER_PORT = 8000
NODE_NAME = "WebNode"
NODE_PORT = 5000

app = Flask(__name__)
CORS(app)

# Initialize a LightNode
node = LightNode(name=NODE_NAME, port=NODE_PORT, tracker_ip=TRACKER_IP, tracker_port=TRACKER_PORT)

@app.route('/api/node-info', methods=['GET'])
def get_node_info():
    return jsonify({
        "name": node.name,
        "address": "localhost",
        "port": node.port
    })

@app.route('/api/elections', methods=['GET'])
def get_elections():
    elections = []
    for block in node.blocks.values():
        for election_hash, election in block.elections.items():
            elections.append({
                "name": election.name,
                "choices": election.choices,
                "hash": election_hash.hex(),
                "total_votes": election.total_votes,
                "end_time": election.end_time,
                "winner": election.winner
            })
    return jsonify(elections)

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    try:
        vote_data = {
            "election_name": data["election_id"],
            "choice": data["candidate_id"],
            "public_key": "placeholder",  # Replace with actual if signing is done server-side
            "signature": "placeholder"   # Replace with actual if signing is done server-side
        }
        vote_json = str(vote_data).replace("'", '"')
        node.handle_vote(vote_json.encode(), node)
        return jsonify({"message": "Vote broadcasted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        election_results = {}
        for block in node.blocks.values():
            for election_hash, election in block.elections.items():
                candidate_tally = {}
                for vote in election.votes:
                    choice = vote.get("choice")
                    if choice:
                        candidate_tally[choice] = candidate_tally.get(choice, 0) + 1

                election_results[election.name] = {
                    "winner": election.winner,
                    "total_votes": election.total_votes,
                    "per_candidate": candidate_tally
                }
        return jsonify(election_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    NODE_PORT = 6000
    FLASK_PORT = 5000
    node = LightNode(name="WebNode", port=NODE_PORT, tracker_ip=TRACKER_IP, tracker_port=TRACKER_PORT)
    app.run(port=FLASK_PORT, debug=True)


