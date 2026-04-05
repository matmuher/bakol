import pytest
import os
import warnings
# Silence the audioread deprecation noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

from engine import Bakol
from audio_gen import AudioGen
from listener import Listener

@pytest.fixture
def tools():
    b = Bakol()
    return b, AudioGen(b), Listener(b)
def test_audio_detection_loop(tools, tmp_path):
    bakol, gen, listener = tools
    wav_file = os.path.join(tmp_path, "test_loop.wav")
    
    input_sequence = [("C", ""), ("A", "m"), ("G", ""), ("D#", "")]
    expected_output = ["C", "Am", "G", "D#"]
    
    wave_data = gen.generate_sequence_wave(input_sequence)
    gen.save_wav(wave_data, wav_file)
    
    detected_segments = listener.analyze_file(wav_file)
    # Extract just the chord strings for comparison
    detected_chords = [s['chord'] for s in detected_segments]
    
    assert detected_chords == expected_output

@pytest.mark.parametrize("root, quality, expected", [
    ("F#", "", "F#"),
    ("B", "m", "Bm"),
    ("C#", "", "C#"),
])
def test_single_chord_accuracy(tools, tmp_path, root, quality, expected):
    bakol, gen, listener = tools
    wav_file = os.path.join(tmp_path, "single.wav")
    
    wave_data = gen.generate_sequence_wave([(root, quality)])
    gen.save_wav(wave_data, wav_file)
    
    detected = listener.analyze_file(wav_file, 1)
    # Check the 'chord' key in the first segment
    assert detected[0]['chord'] == expected