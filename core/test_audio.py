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

import os

def test_audio_detection_loop(tools, tmp_path):
    bakol, gen, listener = tools
    wav_file = os.path.join(tmp_path, "test_loop.wav")

    # Sequence with D# (Non-diatonic to C)
    input_sequence = [("C", ""), ("A", "m"), ("G", ""), ("D#", "")]
    expected_output = ["C", "Am", "G", "D#"]

    wave_data = gen.generate_sequence_wave(input_sequence)
    gen.save_wav(wave_data, wav_file)

    # FIX: use_correction=False allows the engine to 'hear' the D# without snapping it
    detected_segments = listener.analyze_file(
        wav_file, 
        num_chords=len(input_sequence), 
        use_correction=False
    )
    
    detected_chords = [s['chord'] for s in detected_segments]
    assert detected_chords == expected_output

def test_core_progression_extraction(tools, tmp_path):
    bakol, gen, listener = tools
    wav_file = os.path.join(tmp_path, "test_progression.wav")

    # Sequence where C, G, Am, F are frequent, but "B" is just a passing chord
    # Order of first appearance: C -> G -> Am -> F
    input_sequence = [
        ("C", ""), ("G", ""), ("A", "m"), ("F", ""), # Core 4
        ("C", ""), ("G", ""), ("A", "m"), ("F", ""), # Repeat
        ("B", ""), ("C", "")                         # B is rare
    ]
    
    # We expect the Top 4 to be C, G, Am, F in that order.
    # 'B' should be excluded because it only appears once.
    expected_core = ["C", "G", "Am", "F"]

    wave_data = gen.generate_sequence_wave(input_sequence)
    gen.save_wav(wave_data, wav_file)

    # Analyze normally
    detected_segments = listener.analyze_file(
        wav_file, 
        num_chords=len(input_sequence), 
        use_correction=False
    )
    
    # Extract core progression
    core = listener.get_core_progression(detected_segments, top_n=4)

    assert core == expected_core
