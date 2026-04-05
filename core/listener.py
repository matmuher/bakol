import librosa
import numpy as np
import warnings
from collections import Counter

# Suppress audio-loading noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def analyze_file(self, file_path, num_chords=None, max_seconds=30, window_size=1.0):
        """
        The complete pipeline for chord analysis with Harmonic Circle filtering.
        """
        # 1. Load Audio & Extract Chroma
        y, sr = librosa.load(file_path, duration=max_seconds)
        total_duration = librosa.get_duration(y=y, sr=sr)
        
        # Constant-Q Transform (CQT) is better than FFT for musical notes
        chroma = librosa.feature.chroma_cqt(
            y=y, sr=sr, hop_length=512, n_chroma=self.bakol.SEMITONES
        )
        times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)

        # 2. Define Windows
        if num_chords:
            # Test Mode: Split into exact parts for verification
            win_len = total_duration / num_chords
            windows = [(i * win_len, (i + 1) * win_len) for i in range(num_chords)]
            is_test = True
        else:
            # Production Mode: Fixed 1.0s (or custom) grid
            windows = [(i, i + window_size) for i in np.arange(0, total_duration, window_size)]
            is_test = False

        # 3. Raw Detection Loop
        raw_results = []
        for start, end in windows:
            idx = np.where((times >= start) & (times < end))[0]
            if len(idx) == 0:
                continue
            
            # Identify the best matching chord template
            mean_chroma = np.mean(chroma[:, idx], axis=1)
            chord = self._detect_chord(mean_chroma)
            
            raw_results.append({
                "start": round(start, 2), 
                "end": round(end, 2), 
                "chord": chord
            })

        # 4. Post-Processing Logic
        if is_test:
            # Return raw data for unit tests to verify exact detection
            return raw_results
        
        # Apply Harmonic Circle Filtering to fix E-Em style outliers
        corrected = self._harmonic_correction(raw_results)
        
        # Merge identical adjacent chords for a clean timeline
        return self._merge_adjacent(corrected)

    def _harmonic_correction(self, results):
        """
        Music Theory Filter:
        1. Finds the Global Tonic (The 'Home' key).
        2. Maps the 7 legal Diatonic chords for that key.
        3. Snaps out-of-tune detections (like Em in A Major) to the nearest legal chord.
        """
        if not results: return []

        # 1. Identify the Global Tonic
        # We count roots to find the 'Center of Gravity'
        all_roots = [r['chord'].replace('m', '') for r in results if r['chord'] != 'N/A']
        if not all_roots: return results
        tonic_root = Counter(all_roots).most_common(1)[0][0]

        # 2. Determine if the song is likely Major or Minor
        # If more than 50% of the tonic detections are minor, we treat the key as Minor
        tonic_instances = [r['chord'] for r in results if r['chord'].replace('m', '') == tonic_root]
        is_minor_key = (tonic_instances.count(f"{tonic_root}m") > len(tonic_instances) / 2)
        global_tonic = f"{tonic_root}{'m' if is_minor_key else ''}"

        # 3. Build the 'Legal Chords' Map (The Diatonic Scale)
        circle = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
        t_idx = circle.index(tonic_root)

        # Dictionary: { Root: Quality }
        # Example for A Major: {'A': '', 'B': 'm', 'C#': 'm', 'D': '', 'E': '', 'F#': 'm'}
        if not is_minor_key:
            safe_map = {
                circle[t_idx]: "",           # I   (A)
                circle[(t_idx + 2) % 12]: "m", # ii  (Bm)
                circle[(t_idx + 4) % 12]: "m", # iii (C#m)
                circle[(t_idx - 1) % 12]: "", # IV  (D)
                circle[(t_idx + 1) % 12]: "", # V   (E)
                circle[(t_idx + 3) % 12]: "m", # vi  (F#m)
            }
        else:
            # Key of E Minor: {E:m, G:'', A:m, B:m, C:'', D:''}
            safe_map = {
                circle[t_idx]: "m",          # i   (Em)
                circle[(t_idx + 1) % 12]: "", # III (G)
                circle[(t_idx - 1) % 12]: "m", # iv  (Am)
                circle[(t_idx + 2) % 12]: "m", # v   (Bm)
                circle[(t_idx - 2) % 12]: "", # VI  (C)
                circle[(t_idx - 1) % 12]: "", # VII (D)
            }

        # 4. The "Snap" Logic
        corrected = []
        for res in results:
            chord = res['chord']
            root = chord.replace('m', '')
            
            if root in safe_map:
                # Root is in the key! Force the quality to be 'in tune'
                # This fixes the Em -> E glitch automatically
                required_quality = safe_map[root]
                corrected.append({**res, "chord": f"{root}{required_quality}"})
            else:
                # Out-of-key root (e.g., Cm in the key of A)
                # Snap it to the Tonic or the nearest neighbor
                corrected.append({**res, "chord": global_tonic})
                
        return corrected

    def _detect_chord(self, chroma_vector):
        """Standard Template Matching logic."""
        if np.max(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.max(chroma_vector)

        best_chord = "N/A"
        max_similarity = -1

        for i in range(self.bakol.SEMITONES):
            for quality, intervals in self.bakol.CHORD_OFFSETS.items():
                template = np.zeros(self.bakol.SEMITONES)
                for interval in intervals:
                    template[interval] = 1
                
                template = np.roll(template, i)
                similarity = np.dot(chroma_vector, template)
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    root = self.bakol.CHROMATIC[i]
                    best_chord = f"{root}{quality}"
        return best_chord

    def _merge_adjacent(self, results):
        """Joins identical consecutive chords."""
        if not results:
            return []
            
        merged = []
        current = results[0].copy()
        
        for next_res in results[1:]:
            if next_res['chord'] == current['chord']:
                current['end'] = next_res['end']
            else:
                merged.append(current)
                current = next_res.copy()
        
        merged.append(current)
        return merged
