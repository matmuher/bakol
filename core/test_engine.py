from engine import BakolEngine

def test_bakol_precision():
    engine = BakolEngine()

    # Sequence 1: Mostly minor chords (Gm, Dm, Cm) 
    # With 6-chord logic, this should now pull toward A# 
    # because Gm, Dm, Cm, D# are all in the A# family.
    prog1 = ['Gm', 'Dm', 'Gm', 'Dm', 'D#', 'Cm', 'D']
    tonic1 = engine.identify_tonic(prog1)
    print(f"Sequence 1 Tonic: {tonic1}") 
    # Note: 'D' (Major) is technically outside A# major, but the 
    # other 4 chords will force the A# result.
    
    # Sequence 2: Standard A# Major
    prog2 = ['D#', 'F', 'A#', 'Gm']
    tonic2 = engine.identify_tonic(prog2)
    print(f"Sequence 2 Tonic: {tonic2}")

    assert tonic1 == 'A#'
    assert tonic2 == 'A#'
    
    # Final Normalization Test
    normalized = engine.normalize_to_tonic(prog1, target_tonic='C')
    print(f"Normalized Sequence 1: {normalized}")
    # Expected: Gm -> Am, Dm -> Em, D# -> F, Cm -> Dm
    
    print("✅ Logic successfully unified both sequences under A#!")

if __name__ == "__main__":
    test_bakol_precision()