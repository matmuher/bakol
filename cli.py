import sys
from core.engine import Bakol
from core.listener import Listener

def main():
    if len(sys.argv) < 2:
        print("Usage: python bakol.py <path_to_audio_file>")
        return

    audio_path = sys.argv[1]
    
    # Initialize Engine
    bakol = Bakol()
    listener = Listener(bakol)
    
    print(f"--- Analyzing first 30s of: {audio_path} ---")
    
    try:
        timeline = listener.analyze_file(audio_path, max_seconds=30)
        
        # Basic Visualization
        for segment in timeline:
            start = segment['start']
            end = segment['end']
            chord = segment['chord']
            
            # Create a simple visual bar based on duration
            duration = end - start
            bar = "=" * int(duration * 2)
            print(f"[{start:05.2f}s - {end:05.2f}s] {chord:<5} |{bar}")
            
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()
