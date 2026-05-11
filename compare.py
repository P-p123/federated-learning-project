from centralized_model import run_centralized
import subprocess
import time

def run_federated():
    start = time.time()

    # Run federated server
    subprocess.run(["python", "server.py"])

    end = time.time()

    return {
        "training_time": end - start
    }

if __name__ == "__main__":
    print("Running Centralized Model...")
    central = run_centralized()

    print("Running Federated Model...")
    federated = run_federated()

    print("\n===== RESULTS =====")
    print("Centralized:", central)
    print("Federated:", federated)