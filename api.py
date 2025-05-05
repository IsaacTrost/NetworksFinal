from flask import Flask, request, jsonify
from flask_cors import CORS
from peer_light import LightNode
from election import Election
import time
import threading
from vote import Vote
import base64
import json

# Need changes to match tracker set up 
TRACKER_IP = "127.0.0.1"
TRACKER_PORT = 5000
NODE_NAME = "WebNode"
NODE_PORT = 5000

app = Flask(__name__)
CORS(app)

# Initialize a LightNode
node = LightNode(name=NODE_NAME, port=NODE_PORT, tracker_ip=TRACKER_IP, tracker_port=TRACKER_PORT)

def refresh_node_periodically():
    while True:
        node.refreash_elections()
        time.sleep(2)

refresh_thread = threading.Thread(target=refresh_node_periodically, daemon=True)
refresh_thread.start()

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
    with node.data_lock:
        for election in node.active_elections:
            elections.append({
                "name": election.name,
                "choices": election.choices,
                "hash": base64.b64encode(election.hashy).decode(),
                "total_votes": election.total_votes,
                "end_time": election.end_time,
            })
    return jsonify(elections)

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    try:
        private_key = base64.b64decode(data["private_key"])
        election_id = base64.b64decode(data["election_id"])
        candidate_id = base64.b64decode(data["candidate_id"])
        sig = Vote.sign(private_key, election_id, candidate_id)
        vote_data = {
            "election_hash": data["election_id"],
            "choice": data["candidate_id"],
            "public_key": data["public_key"],  # Replace with actual if signing is done server-side
            "signature": sig   # Replace with actual if signing is done server-side
        }
        vote = Vote(vote_data)
        node.handle_vote(vote, None)
        return jsonify({"message": "Vote broadcasted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/results', methods=['GET'])
def get_results():
    hashy = request.get_json().get("election_hash")
    if not hashy:
        return jsonify({"error": "Election hash is required."}), 400
    hashy = base64.b64decode(hashy)
    election = node.request_election(hashy)
    if not type(election) == Election:
        return jsonify({"error": "Election not found."}), 404
    per_candidate = {}
    for choice in election.choices:
        per_candidate[choice] = 0
    for vote in election.used_keys.values():
        choice = vote
        if choice in election.choices:
            per_candidate[choice] += 1
        else:
            return jsonify({"error": "Election choices are not lining up"}), 400


    election_results = {
        "name": election.name,
        "choices": election.choices,
        "total_votes": election.total_votes,
        "end_time": election.end_time,
        "winner": election.winner,
        "per_candidate": {}
    }
    return jsonify(election_results)
@app.route('/api/election', methods=['POST'])
def create_election():
    data = request.get_json()
    try:
        name = data["name"]
        choices = data["choices"]
        public_keys = data["public_keys"]
        end_time = data["end_time"]
        election_data = {
            "name": name,
            "choices": choices,
            "public_keys": public_keys,
            "end_time": end_time
        }
        election = Election(election_data)
        node.send_election(election)
        return jsonify({"message": "Election broadcasted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    NODE_PORT = 6000
    FLASK_PORT = 5000
    node = LightNode(name="WebNode", port=NODE_PORT, tracker_ip=TRACKER_IP, tracker_port=TRACKER_PORT)
    app.run(port=FLASK_PORT, debug=True)


