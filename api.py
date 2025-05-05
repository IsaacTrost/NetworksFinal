from flask import Flask, send_from_directory, jsonify, request
import os
from flask_cors import CORS
from flask_socketio import SocketIO
from vote import submit_vote, get_results
from voter_node import VoterNode

app = Flask(__name__, static_folder='campus-voting/ui/build', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create a global node instance
node = VoterNode()

@app.route('/api/node-info', methods=['GET'])
def get_node_info():
    return jsonify({
        "name": node.name,
        "chain_length": len(node.blockchain),
        "peers": node.peers
    })

@app.route('/api/vote', methods=['POST'])
def vote():
    data = request.json
    voter = data.get("voter")
    candidate = data.get("candidate")
    success, message = submit_vote(node, voter, candidate)
    return jsonify({"success": success, "message": message})

@app.route('/api/results', methods=['GET'])
def results():
    return jsonify(get_results(node))

@app.route('/')
@app.route('/<path:path>')
def serve(path=''):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

