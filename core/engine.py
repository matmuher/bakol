import re

class Bakol:
    CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    SEMITONES = len(CHROMATIC)
    
    # The "Recipe" for building chords
    CHORD_OFFSETS = {
        '': [0, 4, 7],  # Major
        'm': [0, 3, 7]  # Minor
    }

    DIATONIC_FAMILY = {0: '', 2: 'm', 4: 'm', 5: '', 7: '', 9: 'm'}
    
    def __init__(self):
        self.letter_map = {name: i for i, name in enumerate(self.CHROMATIC) if len(name) == 1}

    def get_id(self, note_str):
        note = note_str.strip().capitalize()
        if note in self.CHROMATIC:
            return self.CHROMATIC.index(note)
        
        base_letter = note[0]
        if base_letter not in self.letter_map:
            raise ValueError(f"Invalid note base: {base_letter}")
            
        idx = self.letter_map[base_letter]
        idx += note.count('#') - note.count('b')
        return idx % self.SEMITONES

    def parse_chord(self, chord_str):
        match = re.match(r"([A-G][#b]*)(.*)", chord_str.strip().capitalize())
        if not match: 
            raise ValueError(f"Invalid chord format: {chord_str}")
        
        root_str, quality_str = match.groups()
        root_id = self.get_id(root_str)
        is_minor = 'm' in quality_str.lower() and 'maj' not in quality_str.lower()
        return root_id, ('m' if is_minor else '')

    def identify_tonic(self, chord_names):
        parsed = [self.parse_chord(n) for n in chord_names]
        scores = []
        for t in range(self.SEMITONES):
            score = sum(
                1 for r_id, q in parsed 
                if (r_id - t) % self.SEMITONES in self.DIATONIC_FAMILY 
                and self.DIATONIC_FAMILY[(r_id - t) % self.SEMITONES] == q
            )
            scores.append(score)
        return self.CHROMATIC[scores.index(max(scores))]

    def transpose_to_tonic(self, chord_names, target_tonic='C'):
        current_t_id = self.CHROMATIC.index(self.identify_tonic(chord_names))
        target_t_id = self.get_id(target_tonic)
        shift = (target_t_id - current_t_id) % self.SEMITONES
        
        res = []
        for n in chord_names:
            r_id, q = self.parse_chord(n)
            res.append(f"{self.CHROMATIC[(r_id + shift) % self.SEMITONES]}{q}")
        return res
