import re

class BakolEngine:
    # Our internal universe: 12 semitones, always favoring Sharps.
    CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self):
        # Dynamically generate the map from the CHROMATIC array
        # This picks only single-letter names (Naturals) like 'C', 'D', 'E'...
        self.letter_map = {name: i for i, name in enumerate(self.CHROMATIC) if len(name) == 1}

    def get_id(self, note_str):
        """Standardizes any input (C#, Db, F) to its 0-11 index."""
        note = note_str.strip().capitalize()
        
        # 1. Direct match check (Fast path for standard sharps/naturals)
        if note in self.CHROMATIC:
            return self.CHROMATIC.index(note)
        
        # 2. Handle Flats (b) or Multi-accidentals using the letter_map as an anchor
        base_letter = note[0]
        if base_letter not in self.letter_map:
            raise ValueError(f"Invalid note base: {base_letter}")
            
        idx = self.letter_map[base_letter]
        # Add 1 for every #, subtract 1 for every b
        idx += note.count('#') - note.count('b')
        return idx % 12

    def parse_chord(self, chord_str):
        """Splits chord into a standardized root ID and a simple 'm' quality."""
        match = re.match(r"([A-G][#b]*)(.*)", chord_str.strip().capitalize())
        if not match: 
            raise ValueError(f"Invalid chord format: {chord_str}")
        
        root_str, quality_str = match.groups()
        root_id = self.get_id(root_str)
        
        # Keep it simple: 'm' means minor, anything else (or empty) is Major
        is_minor = 'm' in quality_str.lower() and 'maj' not in quality_str.lower()
        return root_id, ('m' if is_minor else '')

    def identify_tonic(self, chord_names):
        """Finds the tonic by matching roots+qualities against the 6 diatonic neighbors."""
        parsed = [self.parse_chord(n) for n in chord_names]
        # Offset from Tonic: Expected Quality (Empty=Major, 'm'=Minor)
        family = {0:'', 2:'m', 4:'m', 5:'', 7:'', 9:'m'} 
        
        scores = []
        for t in range(12):
            score = sum(1 for r_id, q in parsed 
                        if (r_id - t) % 12 in family 
                        and family[(r_id - t) % 12] == q)
            scores.append(score)
        
        return self.CHROMATIC[scores.index(max(scores))]

    def normalize_to_tonic(self, chord_names, target_tonic='C'):
        """Transposes and simplifies the chord sequence to a new tonic."""
        current_t_id = self.CHROMATIC.index(self.identify_tonic(chord_names))
        target_t_id = self.get_id(target_tonic)
        shift = (target_t_id - current_t_id) % 12
        
        res = []
        for n in chord_names:
            r_id, q = self.parse_chord(n)
            res.append(f"{self.CHROMATIC[(r_id + shift) % 12]}{q}")
        return res
