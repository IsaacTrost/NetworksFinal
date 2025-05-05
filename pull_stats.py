import argparse
import time
import statistics
import matplotlib.pyplot as plt
import threading
import sys
import socket
import json

# Assuming LightNode is in light_node.py and Peer/utils are accessible
from utils import * # Import message types like GET_LONGEST_CHAIN, LONGEST_CHAIN, INIT, ERROR

def get_peer_list_from_tracker(tracker_ip, tracker_port, listen_port):
    """Connects to the tracker to get a list of peers."""
    print(f"Connecting to tracker at {tracker_ip}:{tracker_port} to get peer list...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((tracker_ip, tracker_port))
            # Send INIT message (type 0) with our listening port
            msg = INIT.to_bytes(2, byteorder='big') + listen_port.to_bytes(2, byteorder='big')
            msg = len(msg).to_bytes(2, byteorder='big') + msg
            print("Sending INIT message to tracker...", msg)
            sock.sendall(msg)

            # Receive the peer list response
            response = sock.recv(4096 * 8) # Adjust buffer size if needed
            if not response:
                print("Error: No response from tracker.")
                return None

            # Assuming tracker response format: len (2 bytes) + json_list
            list_len = int.from_bytes(response[:2], byteorder='big')
            peer_list_json = response[2:2+list_len].decode('utf-8')
            peer_list = json.loads(peer_list_json)
            print(f"Received peer list: {peer_list}")
            return peer_list
    except Exception as e:
        print(f"Error connecting to tracker or getting peer list: {e}")
        return None

def fetch_chain_directly(peer_ip, peer_port, listen_port):
    """Connects directly to a peer and requests the longest chain."""
    print(f"Connecting directly to peer {peer_ip}:{peer_port} to fetch chain...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(30) # Set a timeout for socket operations
            sock.connect((peer_ip, peer_port))

            # 1. Send INIT message (pretend to be a peer connecting)
            init_msg = INIT.to_bytes(2, byteorder='big') + listen_port.to_bytes(2, byteorder='big')
            init_msg = len(init_msg).to_bytes(2, byteorder='big') + init_msg
            print("Sending INIT message...", init_msg)
            sock.sendall(init_msg)
            # Peers might send back their peer list upon INIT, we can ignore it for now
            # Or read it to prevent blocking issues if the peer expects a read
            try:
                _ = sock.recv(4096 * 8, socket.MSG_DONTWAIT) # Try non-blocking read
            except BlockingIOError:
                pass # No initial response, that's fine

            # 2. Send GET_LONGEST_CHAIN message
            get_chain_msg = GET_LONGEST_CHAIN.to_bytes(2, byteorder='big')
            get_chain_msg = len(get_chain_msg).to_bytes(2, byteorder='big') + get_chain_msg
            print("Sending GET_LONGEST_CHAIN request...")
            sock.sendall(get_chain_msg)

            # 3. Receive the response
            print("Waiting for LONGEST_CHAIN response...")
            # Peers should send: type (2 bytes) + chain_data
            response_header = sock.recv(4)
            if not response_header:
                print("Error: No response header from peer.")
                return None

            msg_type = int.from_bytes(response_header[2:], byteorder='big')
            print(f"Received message type: {msg_type}")

            if msg_type == LONGEST_CHAIN:
                # Read the rest of the data (potentially large)
                chain_data = b""
                while True:
                    try:
                        # Set a shorter timeout for subsequent reads
                        sock.settimeout(5)
                        chunk = sock.recv(4096 * 8)
                        if not chunk:
                            break # Connection closed or end of data
                        chain_data += chunk
                    except socket.timeout:
                        print("Socket timeout waiting for more chain data, assuming complete.")
                        break
                    except Exception as e:
                        print(f"Error receiving chain data chunk: {e}")
                        break # Stop reading on error
                print(f"Received {len(chain_data)} bytes of chain data.")
                return chain_data
            elif msg_type == ERROR:
                 # Read error message: len (2 bytes) + message
                 error_len_bytes = sock.recv(2)
                 if not error_len_bytes: return None
                 error_len = int.from_bytes(error_len_bytes, byteorder='big')
                 error_msg_bytes = sock.recv(error_len)
                 if not error_msg_bytes: return None
                 error_msg = error_msg_bytes.decode('utf-8')
                 print(f"Peer responded with ERROR: {error_msg}")
                 return None
            else:
                print(f"Error: Received unexpected message type {msg_type} instead of LONGEST_CHAIN.")
                return None

    except socket.timeout:
        print("Error: Socket timed out connecting or waiting for response from peer.")
        return None
    except ConnectionRefusedError:
        print(f"Error: Connection refused by peer {peer_ip}:{peer_port}.")
        return None
    except Exception as e:
        print(f"Error fetching chain directly from peer: {e}")
        raise e
        return None


def parse_chain_data(chain_data):
    """Parses the concatenated block headers into a list of dicts."""
    blocks = []
    if not chain_data or len(chain_data) % 84 != 0:
        print(f"Error: Invalid chain data length ({len(chain_data)} bytes). Not divisible by 84.")
        return []

    print(f"Parsing {len(chain_data) // 84} block headers...")
    for i in range(0, len(chain_data), 84):
        header = chain_data[i:i + 84]
        try:
            index = int.from_bytes(header[:4], byteorder='big')
            prev_hash = header[4:36] # Keep as bytes
            merkle_root = header[36:68] # Keep as bytes
            timestamp = int.from_bytes(header[68:76], byteorder='big')
            difficulty = int.from_bytes(header[76:80], byteorder='big')
            nonce = int.from_bytes(header[80:84], byteorder='big')
            blocks.append({
                "index": index,
                "timestamp": timestamp,
                "difficulty": difficulty,
                "prev_hash": prev_hash,
                # Add other fields if needed
            })
        except Exception as e:
            print(f"Error parsing header at offset {i}: {e}")
            continue

    # Sort blocks by index just in case they weren't perfectly ordered
    blocks.sort(key=lambda b: b["index"])
    return blocks

def analyze_and_plot(blocks):
    """Calculates stats and plots graphs from parsed block data."""
    if len(blocks) < 2:
        print("Not enough blocks to analyze time differences.")
        # Still print/plot difficulty if at least one block exists
        if len(blocks) == 1:
             print("\n--- Blockchain Statistics ---")
             print(f"Total Blocks Analyzed: {len(blocks)}")
             print(f"Difficulty of Block 0: {blocks[0]['difficulty']}")
             print("---------------------------\n")
             plt.figure(figsize=(12, 6))
             plt.plot([blocks[0]['index']], [blocks[0]['difficulty']], marker='o', linestyle='', markersize=6, color='green', label='Difficulty')
             plt.title("Block Difficulty (Only 1 Block)")
             plt.xlabel("Block Index")
             plt.ylabel("Difficulty")
             plt.legend()
             plt.grid(True)
             plt.tight_layout()
             plt.show()
        return

    indices = [b["index"] for b in blocks]
    timestamps = [b["timestamp"] for b in blocks]
    difficulties = [b["difficulty"] for b in blocks]

    # Calculate time differences
    time_diffs = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
    block_indices_for_diffs = indices[1:] # Indices corresponding to time_diffs

    # --- Print Statistics ---
    print("\n--- Blockchain Statistics ---")
    print(f"Total Blocks Analyzed: {len(blocks)}")

    if time_diffs:
        print("\nBlock Time Statistics:")
        print(f"  Average Time Between Blocks: {statistics.mean(time_diffs):.2f} seconds")
        try:
            print(f"  Median Time Between Blocks: {statistics.median(time_diffs):.2f} seconds")
        except statistics.StatisticsError:
             print("  Median Time Between Blocks: N/A (needs >= 1 diff)")
        print(f"  Minimum Time Between Blocks: {min(time_diffs):.2f} seconds")
        print(f"  Maximum Time Between Blocks: {max(time_diffs):.2f} seconds")
        try:
            print(f"  Std Dev of Block Times: {statistics.stdev(time_diffs):.2f} seconds")
        except statistics.StatisticsError:
            print("  Std Dev of Block Times: N/A (needs >= 2 diffs)")


    if difficulties:
        print("\nDifficulty Statistics:")
        print(f"  Average Difficulty: {statistics.mean(difficulties):.2f}")
        try:
            print(f"  Median Difficulty: {statistics.median(difficulties):.2f}")
        except statistics.StatisticsError:
             print("  Median Difficulty: N/A (needs >= 1 block)")
        print(f"  Minimum Difficulty: {min(difficulties)}")
        print(f"  Maximum Difficulty: {max(difficulties)}")
        try:
            print(f"  Std Dev of Difficulty: {statistics.stdev(difficulties):.2f}")
        except statistics.StatisticsError:
            print("  Std Dev of Difficulty: N/A (needs >= 2 blocks)")
    print("---------------------------\n")


    # Plot 1: Time Differences Between Blocks
    if time_diffs:
        plt.figure(figsize=(12, 6))
        plt.plot(block_indices_for_diffs, time_diffs, marker='o', linestyle='-', markersize=4, label='Block Time')
        # Add a line for the target block time if available (e.g., 30s)
        TARGET_BLOCK_TIME = 30 # Assuming this is your target
        plt.axhline(y=TARGET_BLOCK_TIME, color='r', linestyle='--', label=f'Target ({TARGET_BLOCK_TIME}s)')
        plt.title("Time Between Consecutive Blocks")
        plt.xlabel("Block Index")
        plt.ylabel("Time Difference (seconds)")
        plt.legend()
        plt.grid(True)

    # Plot 2: Difficulty Over Time (Block Index)
    if difficulties:
        plt.figure(figsize=(12, 6))
        plt.plot(indices, difficulties, marker='.', linestyle='-', markersize=4, color='green', label='Difficulty')
        plt.title("Block Difficulty Over Time")
        plt.xlabel("Block Index")
        plt.ylabel("Difficulty")
        plt.legend()
        plt.grid(True)
        # Use log scale for y-axis if difficulty varies widely
        # plt.yscale('log')

    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Connect directly to a peer to fetch and analyze blockchain statistics.")
    # Port for this script to potentially listen on (used in INIT msg)
    parser.add_argument('--listen-port', type=int, default=5011, help='Ephemeral port number this script uses for INIT')
    parser.add_argument('--tracker-ip', type=str, required=True, help='Tracker IP address')
    parser.add_argument('--tracker-port', type=int, required=True, help='Tracker port number')
    # Optional: Specify a peer directly
    parser.add_argument('--peer-ip', type=str, help='Specific Peer IP address to connect to')
    parser.add_argument('--peer-port', type=int, help='Specific Peer port number to connect to')

    args = parser.parse_args()

    peer_ip = args.peer_ip
    peer_port = args.peer_port

    # If peer not specified, get list from tracker
    if not peer_ip or not peer_port:
        peer_list = get_peer_list_from_tracker(args.tracker_ip, args.tracker_port, args.listen_port)
        if not peer_list:
            print("Could not get peer list from tracker. Exiting.")
            sys.exit(1)
        # Select the first peer from the list (or implement random/better selection)
        if not peer_list:
             print("Tracker returned an empty peer list. Exiting.")
             sys.exit(1)
        selected_peer = peer_list[0]
        peer_ip = selected_peer.get("ip")
        peer_port = selected_peer.get("port")
        if not peer_ip or not peer_port:
             print("Selected peer from tracker has invalid IP/Port. Exiting.")
             sys.exit(1)
        print(f"Selected peer {peer_ip}:{peer_port} from tracker.")

    # Fetch chain data directly from the selected peer
    chain_data = fetch_chain_directly(peer_ip, peer_port, args.listen_port)

    if chain_data is None:
        print("Failed to fetch chain data from peer.")
        sys.exit(1)

    print("Chain data received. Parsing and analyzing...")
    parsed_blocks = parse_chain_data(chain_data)

    if parsed_blocks:
        analyze_and_plot(parsed_blocks)
    else:
        print("No valid blocks found in the received data.")

    print("Analysis complete. Exiting.")
    sys.exit(0)


if __name__ == "__main__":
    main()