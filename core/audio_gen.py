import numpy as np
from scipy.io.wavfile import write

class AudioGen:
    SAMPLE_RATE = 44100
    
    def __init__(self, bakol):
        self.bakol = bakol
        self.base_freqs = {
            name: 440.0 * (2.0 ** ((i - 9) / self.bakol.SEMITONES)) 
            for i, name in enumerate(self.bakol.CHROMATIC)
        }

    def _generate_tone(self, freq, duration, volume=0.3):
        t = np.linspace(0, duration, int(self.SAMPLE_RATE * duration), False)
        return volume * np.sin(2 * np.pi * freq * t)

    def create_chord_wave(self, root_name, quality='', duration=4.0):
        root_id = self.bakol.get_id(root_name)
        
        # Pull the offsets directly from the engine's recipe using the key ('', 'm', etc.)
        intervals = self.bakol.CHORD_OFFSETS[quality]
        
        chord_wave = np.zeros(int(self.SAMPLE_RATE * duration))
        for interval in intervals:
            note_name = self.bakol.CHROMATIC[(root_id + interval) % self.bakol.SEMITONES]
            freq = self.base_freqs[note_name]
            chord_wave += self._generate_tone(freq, duration)
            
        return chord_wave

    def generate_sequence_wave(self, sequence):
        # sequence is now a list of (root, quality)
        waves = [self.create_chord_wave(r, q) for r, q in sequence]
        return np.concatenate(waves)

    def save_wav(self, wave_data, filename):
        max_val = np.max(np.abs(wave_data))
        if max_val > 0:
            wave_data = (wave_data / max_val * 32767).astype(np.int16)
        write(filename, self.SAMPLE_RATE, wave_data)
