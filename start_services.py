import subprocess
import signal
import sys
import time

def main():
    print("Starting Controller Service...")
    controller_process = subprocess.Popen(
        [sys.executable, "-m", "controller_service.main"]
    )

    print("Starting Game Service...")
    game_process = subprocess.Popen(
        [sys.executable, "-m", "game_service.main"]
    )

    def signal_handler(sig, frame):
        print("\nStopping services...")
        controller_process.terminate()
        game_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("Services started. Press Ctrl+C to stop.")
    
    try:
        controller_process.wait()
        game_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
