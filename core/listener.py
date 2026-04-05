import librosa
import numpy as np
import warnings

# Suppress audio-loading noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def analyze_file(self, file_path, num_chords=None, max_seconds=30, window_size=1.0):
        """
        Pure Fixed-Grid Analysis. 
        Slices the audio into uniform windows and identifies the dominant chord in each.
        """
        # 1. Load Audio
        y, sr = librosa.load(file_path, duration=max_seconds)
        total_duration = librosa.get_duration(y=y, sr=sr)

        # 2. Extract Features (Chromagram)
        # Using CQT for musical frequency alignment (maps frequencies to the 12 semitones)
        chroma = librosa.feature.chroma_cqt(
            y=y, sr=sr, hop_length=512, n_chroma=self.bakol.SEMITONES
        )
        times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)

        # 3. Define Windows
        if num_chords:
            # Test Mode: Force exact divisions (used by pytest)
            win_len = total_duration / num_chords
            windows = [(i * win_len, (i + 1) * win_len) for i in range(num_chords)]
            should_merge = False
        else:
            # Production Mode: Standard 1.0s slices
            windows = [(i, i + window_size) for i in np.arange(0, total_duration, window_size)]
            should_merge = True

        # 4. Processing
        results = []
        for start, end in windows:
            # Get all chroma frames within this time slice
            idx = np.where((times >= start) & (times < end))[0]
            if len(idx) == 0:
                continue
            
            # Identify the chord based on the average energy in this window
            mean_chroma = np.mean(chroma[:, idx], axis=1)
            chord = self._detect_chord(mean_chroma)
            
            results.append({
                "start": round(start, 2), 
                "end": round(end, 2), 
                "chord": chord
            })

        # 5. Final Merge (Optional but usually necessary for readability)
        # Only merges if the string is identical (e.g., 'A', 'A' -> 'A')
        return self._merge_adjacent(results) if should_merge else results

    def _detect_chord(self, chroma_vector):
        """Pure template matching logic."""
        if np.max(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.max(chroma_vector)

        best_chord = "N/A"
        max_similarity = -1

        for i in range(self.bakol.SEMITONES):
            for quality, intervals in self.bakol.CHORD_OFFSETS.items():
                # Build the binary template for this chord
                template = np.zeros(self.bakol.SEMITONES)
                for interval in intervals:
                    template[interval] = 1
                
                # Shift template to current root note
                template = np.roll(template, i)
                
                # Compute similarity (dot product)
                similarity = np.dot(chroma_vector, template)
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    root = self.bakol.CHROMATIC[i]
                    best_chord = f"{root}{quality}"
        
        return best_chord

    def _merge_adjacent(self, results):
        """Only combines identical strings. No 'intelligent' smoothing."""
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
