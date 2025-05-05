import argparse
import subprocess
import time
import os
import signal

def main():
    parser = argparse.ArgumentParser(description="Test blockchain forking scenario.")
    parser.add_argument('--num-observers', type=int, default=1, help='Number of normal observer peers.')
    parser.add_argument('--tracker-port', type=int, default=5000, help='Tracker port.')
    parser.add_argument('--duration', type=int, default=120, help='Approximate test duration in seconds.')

    args = parser.parse_args()

    processes = []
    tracker_ip = "localhost" # Assuming local test
    base_port = args.tracker_port + 1

    # Define node configurations
    nodes_config = []
    # Tracker
    nodes_config.append({
        "type": "tracker", "port": args.tracker_port, "name": "Tracker",
        "cmd": ["python3", "tracker.py", "--port", str(args.tracker_port)]
    })
    for i in range(args.num_observers):
        base_port = base_port + 1
        name = f"Observer{i}"
        nodes_config.append({
            "type": "observer", "port": base_port, "name": name,
            "cmd": ["python3", "peer_good.py", "--port", str(base_port), # Assuming peer_good runs a normal Peer
                    "--tracker-ip", tracker_ip, "--tracker-port", str(args.tracker_port), name]
        })
    # Miner 1 (Holds 10)
    nodes_config.append({
        "type": "forking", "port": base_port, "name": "Miner1", "hold": 10,
        "cmd": ["python3", "forking_node.py", "--port", str(base_port),
                "--tracker-ip", tracker_ip, "--tracker-port", str(args.tracker_port),
                "--hold-count", "10", "Miner1"]
    })
    base_port += 1
    # Miner 2 (Holds 20)
    nodes_config.append({
        "type": "forking", "port": base_port, "name": "Miner2", "hold": 20,
        "cmd": ["python3", "forking_node.py", "--port", str(base_port),
                "--tracker-ip", tracker_ip, "--tracker-port", str(args.tracker_port),
                "--hold-count", "20", "Miner2"]
    })
    base_port += 1
    # Observer Peers
    
    # Transaction Sender
    nodes_config.append({
        "type": "sender", "port": base_port, "name": "Sender",
        "cmd": ["python3", "simple_sender.py", "--port", str(base_port),
                "--tracker-ip", tracker_ip, "--tracker-port", str(args.tracker_port), "Sender"]
    })

    try:
        # Start all nodes
        print("Starting nodes...")
        for config in nodes_config:
            print(f"  Starting {config['name']} on port {config['port']}...")
            # Redirect stdout/stderr to separate files for easier debugging
            log_filename = f"{config['name']}.log"
            if os.path.exists(log_filename):
                 os.remove(log_filename) # Clear old log
            log_file = open(log_filename, 'w')
            proc = subprocess.Popen(config["cmd"], stdout=log_file, stderr=subprocess.STDOUT)
            processes.append({"proc": proc, "log_file": log_file, "name": config['name']})
            time.sleep(1) # Stagger startup slightly

        print(f"\nNetwork running. Miner1 holds 10, Miner2 holds 20.")
        print(f"Monitoring for approximately {args.duration} seconds...")
        print("Check the *.log files for node behavior, especially observers.\n")

        # Let the simulation run
        time.sleep(args.duration)

        print("\nTest duration finished. Stopping nodes...")

    finally:
        # Stop all processes
        print("Terminating processes...")
        for p_info in processes:
            try:
                p_info["proc"].terminate()
            except ProcessLookupError:
                pass # Process already finished

        # Wait a bit and force kill if necessary
        time.sleep(3)
        for p_info in processes:
            if p_info["proc"].poll() is None: # If still running
                try:
                    print(f"  Force killing {p_info['name']} (PID {p_info['proc'].pid})")
                    p_info["proc"].kill()
                except ProcessLookupError:
                    pass
            # Close log file handles
            if p_info["log_file"]:
                p_info["log_file"].close()

        print("\nProcesses stopped.")
        print("Review the generated .log files (Miner1.log, Miner2.log, ObserverX.log, Sender.log, Tracker.log).")


if __name__ == "__main__":
    main()