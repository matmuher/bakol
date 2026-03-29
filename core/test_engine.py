import pytest
from engine import Bakol

@pytest.fixture
def b():
    return Bakol()

@pytest.mark.parametrize("input_note, expected_id", [
    ("C", 0),
    ("C#", 1),
    ("Db", 1),
    ("Eb", 3),
    ("F#", 6),
    ("Gb", 6),
    ("B", 11),
    ("Cb", 11),
])
def test_get_id(b, input_note, expected_id):
    assert b.get_id(input_note) == expected_id

@pytest.mark.parametrize("chords, expected_tonic", [
    (['A#', 'Gm', 'D#', 'F', 'Cm'], 'A#'),
    (['C', 'F', 'G', 'Am'], 'C'),
    (['G', 'C', 'D', 'Em'], 'G'),
    (['Gm', 'Dm', 'Gm', 'Dm', 'D#', 'Cm', 'D'], 'A#'),
    (['D#', 'F', 'A#', 'Gm'], 'A#'),
])
def test_identify_tonic(b, chords, expected_tonic):
    assert b.identify_tonic(chords) == expected_tonic

@pytest.mark.parametrize("chords, target, expected", [
    (['A#', 'Gm', 'D#', 'F'], 'C', ['C', 'Am', 'F', 'G']),
    (['D', 'A', 'Bm', 'G'], 'C', ['C', 'G', 'Am', 'F']),
])
def test_transpose_to_tonic(b, chords, target, expected):
    assert b.transpose_to_tonic(chords, target) == expected

def test_invalid_chord(b):
    with pytest.raises(ValueError):
        b.parse_chord("X#")
