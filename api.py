from flask import Flask, send_from_directory, jsonify, request
import os
import json
import time
import hashlib
import threading
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Import your blockchain node implementation
# from peer import Peer

app = Flask(__name__, static_folder='ui/build')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# This would be your blockchain node instance
# node = None  # Will be initialized when starting the server

# API Routes

@app.route('/api/node-info', methods=['GET'])
def get_node_info():
    # In production, get this from your node
    # return jsonify({
    #     "name": node.name,
    #     "address": node.address[0],
    #     "port": node.address[1]
    # })
    
    # Mock data for testing
    return jsonify({
        "name": "Node-1",
        "address": "127.0.0.1",
        "port": 8000
    })

# Include all the API routes from the previous example here
# ...

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

def start_ui_server(node_instance=None, port=5000):
    """
    Start the UI server for a blockchain node.
    
    Args:
        node_instance: The blockchain node instance
        port: The port to run the server on
    """
    global node
    node = node_instance
    
    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # For testing without a node instance
    start_ui_server(port=5000)
