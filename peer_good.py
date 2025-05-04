import argparse
from peer import Peer
import time
def main():
    parser = argparse.ArgumentParser(description="Start a well-behaved peer node.")
    parser.add_argument('--port', type=int, required=True, help='Port number for this peer to listen on')
    parser.add_argument('--tracker-ip', type=str, required=False, help='Tracker IP address')
    parser.add_argument('name', type=str, help='Name of the peer')
    parser.add_argument('--tracker-port', type=int, required=False, help='Tracker port number')
    args = parser.parse_args()

    print(f"Starting peer '{args.name}' on port {args.port}, connecting to tracker at {args.tracker_ip}:{args.tracker_port}")
    peer = Peer(args.name, port=args.port, tracker_ip=args.tracker_ip, tracker_port=args.tracker_port)
    time.sleep(3)  # Give some time for the peer to initialize
    peer.mine()

    # Keep the process alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down peer.")

if __name__ == "__main__":
    main()