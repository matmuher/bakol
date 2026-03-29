import librosa
import numpy as np
import warnings

# Suppress system-level deprecation noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def analyze_file(self, file_path, num_chords):
            y, sr = librosa.load(file_path)
            
            # Use n_chroma=12 (default) to get our 12 semitone bins.
            # We remove n_bins and bins_per_octave as they were redundant/incorrect.
            chroma = librosa.feature.chroma_cqt(
                y=y, 
                sr=sr, 
                hop_length=256,
                n_chroma=self.bakol.SEMITONES
            )
            
            segments = np.array_split(chroma, num_chords, axis=1)
            return [self._detect_chord(np.mean(seg, axis=1)) for seg in segments]

    def _detect_chord(self, chroma_vector):
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
