import sys
import argparse
from core.engine import Bakol
from core.listener import Listener

def main():
    parser = argparse.ArgumentParser(description="Bakol AI: Music Chord Analysis")
    parser.add_argument("file", help="Path to audio file")
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--window", type=float, default=1.0, help="Grid size in seconds")
    
    args = parser.parse_args()
    
    bakol = Bakol()
    listener = Listener(bakol)
    
    print(f"--- Analyzing: {args.file} ({args.seconds}s) ---")
    
    try:
        timeline = listener.analyze_file(args.file, max_seconds=args.seconds, window_size=args.window)
        for seg in timeline:
            duration = seg['end'] - seg['start']
            bar = "=" * int(duration * 2)
            print(f"[{seg['start']:05.2f}s - {seg['end']:05.2f}s] {seg['chord']:<5} |{bar}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
