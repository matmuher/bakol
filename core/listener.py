import librosa
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def get_fixed_windows(self, duration, window_size=0.1):
        """Creates a list of (start, end) timestamps."""
        return [(i, i + window_size) for i in np.arange(0, duration, window_size)]

    def analyze_file(self, file_path, max_seconds=30):
        # 1. Load only the first N seconds
        y, sr = librosa.load(file_path, duration=max_seconds)
        
        # 2. Compute Chromagram
        # We use a finer hop_length to get better time resolution
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
        
        # Calculate time per chroma column (frame)
        times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
        
        # 3. Define Windows (Fixed Grid for now)
        total_duration = librosa.get_duration(y=y, sr=sr)
        windows = self.get_fixed_windows(total_duration, window_size=1.0)
        
        results = []
        for start, end in windows:
            # Find the indices in the chroma matrix that correspond to this time window
            idx = np.where((times >= start) & (times < end))[0]
            if len(idx) == 0:
                continue
                
            # Average the chroma across the window
            segment_chroma = np.mean(chroma[:, idx], axis=1)
            chord = self._detect_chord(segment_chroma)
            
            results.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "chord": chord
            })
            
        return self._merge_adjacent(results)

    def _detect_chord(self, chroma_vector):
        """Uses dot product against Bakol templates (unchanged logic)."""
        best_chord = ""
        max_similarity = -1
        
        if np.max(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.max(chroma_vector)

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
        """Combines consecutive identical chords into single blocks."""
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
