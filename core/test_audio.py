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
    
    # Input format: (Root, Quality) matching Bakol.CHORD_OFFSETS keys
    input_sequence = [("C", ""), ("A", "m"), ("G", ""), ("D#", "")]
    expected_output = ["C", "Am", "G", "D#"]
    
    # Generate the wave data (Logic)
    # Note: I modified create_chord_wave below to accept the quality string
    wave_data = gen.generate_sequence_wave(input_sequence)
    gen.save_wav(wave_data, wav_file)
    
    detected = listener.analyze_file(wav_file, len(input_sequence))
    assert detected == expected_output

@pytest.mark.parametrize("root, quality, expected", [
    ("F#", "", "F#"),
    ("B", "m", "Bm"),
    ("C#", "", "C#"),
])
def test_single_chord_accuracy(tools, tmp_path, root, quality, expected):
    bakol, gen, listener = tools
    wav_file = os.path.join(tmp_path, "single.wav")
    
    # Pass chords as (root, quality) tuples
    wave_data = gen.generate_sequence_wave([(root, quality)])
    gen.save_wav(wave_data, wav_file)
    
    detected = listener.analyze_file(wav_file, 1)
    assert detected[0] == expected
