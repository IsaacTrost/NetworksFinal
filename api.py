from flask import Flask, request, jsonify
from flask_cors import CORS
from light_node import LightNode
import time

# CONFIGURE THESE TO MATCH YOUR TRACKER SETUP
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
    # This assumes you are tracking elections via block headers
    elections = []
    for block in node.blocks.values():
        for election_hash, election in block.elections.items():
            elections.append({
                "name": election.name,
                "choices": election.choices,
                "hash": election_hash.hex()
            })
    return jsonify(elections)

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    try:
        vote_data = {
            "election_name": data["election_id"],
            
            "choice": data["candidate_id"],
            "public_key": data["public_key"],
            "signature": data["signature"]
        }
        vote_json = str(vote_data).replace("'", '"')
        node.handle_vote(vote_json.encode(), node)
        return jsonify({"message": "Vote broadcasted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        # Gather results from longest chain
        election_results = {}
        for block in node.blocks.values():
            for election_hash, election in block.elections.items():
                election_results[election.name] = {
                    "winner": election.winner,
                    "total_votes": election.total_votes
                }
        return jsonify(election_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    NODE_PORT = 6000
    FLASK_PORT = 5000
    node = LightNode(name="WebNode", port=NODE_PORT, tracker_ip="127.0.0.1", tracker_port=8000)
    app.run(port=FLASK_PORT, debug=True)

