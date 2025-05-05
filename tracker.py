import subprocess
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Run peer_good.py with specified name and port.")
parser.add_argument("name", help="Name of the peer")  # Make 'name' a positional argument
parser.add_argument("--port", required=True, help="Port number to use")

# Parse arguments
args = parser.parse_args()
name = args.name
port = args.port
print(f"Running peer_good.py with name: {name} and port: {port}")
# Run good_node.py with the provided name and port
subprocess.run(["python3", "peer_good.py", name, "--port", port])
