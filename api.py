from flask import Flask, request, jsonify
from flask_cors import CORS
from node import Node  # Adjust if needed
import time

app = Flask(__name__)
CORS(app)

# Initialize the node 
node = Node(name="Node 1", port=5000)

@app.route('/api/node-info', methods=['GET'])
def get_node_info():
    return jsonify({
        "name": node.name,
        "address": node.host,
        "port": node.port
    })

@app.route('/api/elections', methods=['GET'])
def get_elections():
    # Returns the list of elections and their candidates
    elections = node.blockchain.get_elections()
    return jsonify(elections)

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    try:
        tx = node.create_transaction(
            election_id=data["election_id"],
            candidate_id=data["candidate_id"],
            private_key=data["private_key"],
            timestamp=data.get("timestamp", int(time.time()))
        )
        node.broadcast_transaction(tx)
        return jsonify({"message": "Vote submitted and broadcasted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        results = node.blockchain.get_results()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)

