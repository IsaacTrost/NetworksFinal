from flask import Flask, request, jsonify
import json
import time
import hashlib
import threading
import uuid
from werkzeug.serving import make_server
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Import your blockchain implementation
# from peer import Peer
# from utils import ThisNode

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# This would be your blockchain node instance
# node = Peer("api_node", "tracker_ip", tracker_port)

# Mock data for testing - replace with actual blockchain data in production
mock_elections = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Student Council President",
        "description": "Election for the 2023-2024 Student Council President",
        "candidates": [
            {"id": 1, "name": "Alex Johnson", "party": "Student Progress Party"},
            {"id": 2, "name": "Taylor Smith", "party": "Campus Reform Coalition"},
            {"id": 3, "name": "Jordan Lee", "party": "University Voice Alliance"},
            {"id": 4, "name": "Morgan Rivera", "party": "Independent"}
        ],
        "status": "active",
        "closeTime": (time.time() + 86400) * 1000  # 24 hours from now
    }
]

mock_tally = {
    "550e8400-e29b-41d4-a716-446655440000": {
        "1": 145,
        "2": 132,
        "3": 118,
        "4": 97
    }
}

mock_blocks = [
    {
        "index": 0,
        "hash": "000000b642f2b3808707121a89f1b8c3f1bbb1d60e2066b7f9a0b57a46e694ab",
        "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "timestamp": int(time.time()) - 3600,
        "difficulty": 16,
        "nonce": 42,
        "transactions": []
    }
]

# Add more mock blocks
for i in range(1, 20):
    prev_block = mock_blocks[i-1]
    new_block = {
        "index": i,
        "hash": hashlib.sha256(f"block{i}".encode()).hexdigest(),
        "prev_hash": prev_block["hash"],
        "merkle_root": hashlib.sha256(f"merkle{i}".encode()).hexdigest(),
        "timestamp": int(time.time()) - (3600 - i*180),  # Each block 3 minutes apart
        "difficulty": 16 + (i % 5),  # Vary difficulty slightly
        "nonce": 100 + i*10,
        "transactions": [
            {
                "election_id": "550e8400-e29b-41d4-a716-446655440000",
                "voter_pk_hash": hashlib.sha256(f"voter{j}".encode()).hexdigest(),
                "candidate_id": (j % 4) + 1,
                "timestamp": int(time.time()) - (3600 - i*180 - j),
                "signature": f"sig{i}{j}"
            } for j in range(1, i+1)
        ]
    }
    mock_blocks.append(new_block)

# API Routes

@app.route('/api/elections', methods=['GET'])
def get_elections():
    # In production, fetch from your blockchain
    # elections = node.get_elections()
    return jsonify(mock_elections)

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.json
    
    # Validate request
    required_fields = ['election_id', 'private_key', 'candidate_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # In production, this would:
    # 1. Sign the vote with the private key
    # 2. Submit to the blockchain
    # 3. Return the transaction hash
    
    # For now, just simulate a successful submission
    tx_hash = hashlib.sha256(json.dumps(data).encode()).hexdigest()
    
    # Update mock tally for testing
    election_id = data['election_id']
    candidate_id = str(data['candidate_id'])
    
    if election_id in mock_tally:
        if candidate_id in mock_tally[election_id]:
            mock_tally[election_id][candidate_id] += 1
        else:
            mock_tally[election_id][candidate_id] = 1
    else:
        mock_tally[election_id] = {candidate_id: 1}
    
    # Emit WebSocket event for real-time updates
    socketio.emit('tally_update', mock_tally[election_id], namespace='/ws/tally', room=election_id)
    
    return jsonify({"success": True, "tx_hash": tx_hash})

@app.route('/api/tally', methods=['GET'])
def get_tally():
    election_id = request.args.get('election_id')
    if not election_id:
        return jsonify({"error": "Missing election_id parameter"}), 400
    
    # In production, calculate tally from blockchain
    # tally = node.calculate_tally(election_id)
    
    if election_id not in mock_tally:
        return jsonify({}), 200
    
    return jsonify(mock_tally[election_id])

@app.route('/api/blocks', methods=['GET'])
def get_blocks():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    # Calculate pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # In production, fetch from blockchain
    # blocks = node.get_blocks(start_idx, end_idx)
    
    paginated_blocks = mock_blocks[start_idx:end_idx]
    paginated_blocks.reverse()  # Most recent first
    
    return jsonify({
        "blocks": paginated_blocks,
        "total": len(mock_blocks),
        "page": page,
        "limit": limit
    })

@app.route('/api/blocks/<int:block_index>', methods=['GET'])
def get_block_by_index(block_index):
    # In production, fetch from blockchain
    # block = node.get_block_by_index(block_index)
    
    if block_index < 0 or block_index >= len(mock_blocks):
        return jsonify({"error": "Block not found"}), 404
    
    return jsonify({"block": mock_blocks[block_index]})

@app.route('/api/search', methods=['GET'])
def search():
    hash_query = request.args.get('hash')
    if not hash_query:
        return jsonify({"error": "Missing hash parameter"}), 400
    
    # Search for block by hash
    for block in mock_blocks:
        if block["hash"] == hash_query:
            return jsonify({"type": "block", "block": block})
    
    # Search for transaction by hash
    for block in mock_blocks:
        for tx in block.get("transactions", []):
            tx_hash = hashlib.sha256(json.dumps(tx).encode()).hexdigest()
            if tx_hash == hash_query:
                return jsonify({
                    "type": "transaction", 
                    "transaction": tx,
                    "block_index": block["index"]
                })
    
    return jsonify({"error": "No results found"}), 404

@app.route('/api/status', methods=['GET'])
def get_status():
    # In production, get from blockchain node
    # status = {
    #     "currentHeight": node.get_current_height(),
    #     "peerCount": len(node.nodes),
    #     "difficulty": node.get_current_difficulty(),
    #     "lastBlockTime": node.get_last_block_time(),
    #     "hashRate": node.get_hash_rate()
    # }
    
    latest_block = mock_blocks[-1]
    
    status = {
        "currentHeight": latest_block["index"],
        "peerCount": 3,  # Mock peer count
        "difficulty": latest_block["difficulty"],
        "lastBlockTime": latest_block["timestamp"] * 1000,  # Convert to milliseconds
        "hashRate": 15.7  # Mock hash rate in MH/s
    }
    
    return jsonify(status)

# WebSocket routes
@socketio.on('connect', namespace='/ws/blockchain')
def blockchain_connect():
    print("Client connected to blockchain updates")
    
    # Send initial status
    latest_block = mock_blocks[-1]
    status = {
        "currentHeight": latest_block["index"],
        "peerCount": 3,
        "difficulty": latest_block["difficulty"],
        "lastBlockTime": latest_block["timestamp"] * 1000,
        "hashRate": 15.7
    }
    
    emit('BLOCKCHAIN_STATUS', {"type": "BLOCKCHAIN_STATUS", "payload": status})

@socketio.on('connect', namespace='/ws/tally')
def tally_connect():
    election_id = request.args.get('election_id')
    if election_id:
        print(f"Client connected to tally updates for election {election_id}")
        # Join a room for this election
        socketio.server.enter_room(request.sid, election_id, namespace='/ws/tally')
        
        # Send initial tally
        if election_id in mock_tally:
            emit('message', mock_tally[election_id])

# Background task to simulate new blocks being mined
def simulate_blockchain_activity():
    block_index = len(mock_blocks)
    while True:
        time.sleep(30)  # New block every 30 seconds
        
        # Create a new block
        prev_block = mock_blocks[-1]
        new_block = {
            "index": block_index,
            "hash": hashlib.sha256(f"block{block_index}".encode()).hexdigest(),
            "prev_hash": prev_block["hash"],
            "merkle_root": hashlib.sha256(f"merkle{block_index}".encode()).hexdigest(),
            "timestamp": int(time.time()),
            "difficulty": 16 + (block_index % 5),
            "nonce": 100 + block_index*10,
            "transactions": []
        }
        
        # Add some random transactions
        num_tx = min(block_index, 5)
        for j in range(num_tx):
            tx = {
                "election_id": "550e8400-e29b-41d4-a716-446655440000",
                "voter_pk_hash": hashlib.sha256(f"voter{uuid.uuid4()}".encode()).hexdigest(),
                "candidate_id": (j % 4) + 1,
                "timestamp": int(time.time()) - j,
                "signature": f"sig{block_index}{j}"
            }
            new_block["transactions"].append(tx)
            
            # Update mock tally
            candidate_id = str(tx["candidate_id"])
            election_id = tx["election_id"]
            if election_id in mock_tally:
                if candidate_id in mock_tally[election_id]:
                    mock_tally[election_id][candidate_id] += 1
                else:
                    mock_tally[election_id][candidate_id] = 1
            
            # Emit tally update
            socketio.emit('message', mock_tally[election_id], namespace='/ws/tally', room=election_id)
        
        mock_blocks.append(new_block)
        block_index += 1
        
        # Emit new block notification
        socketio.emit('message', {"type": "NEW_BLOCK", "payload": new_block}, namespace='/ws/blockchain')
        
        print(f"Simulated new block: {new_block['index']}")

if __name__ == '__main__':
    # Start blockchain simulation in background
    simulation_thread = threading.Thread(target=simulate_blockchain_activity, daemon=True)
    simulation_thread.start()
    
    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
