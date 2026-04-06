import librosa
import numpy as np
import warnings
from collections import Counter

warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def analyze_file(self, file_path, num_chords=None, max_seconds=30, window_size=1.0):
        # 1. Load Audio & Extract Chroma
        y, sr = librosa.load(file_path, duration=max_seconds)
        total_duration = librosa.get_duration(y=y, sr=sr)
        
        chroma = librosa.feature.chroma_cqt(
            y=y, sr=sr, hop_length=512, n_chroma=self.bakol.SEMITONES
        )
        times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)

        # 2. Define Windows
        if num_chords:
            win_len = total_duration / num_chords
            windows = [(i * win_len, (i + 1) * win_len) for i in range(num_chords)]
            is_test = True
        else:
            windows = [(i, i + window_size) for i in np.arange(0, total_duration, window_size)]
            is_test = False

        # 3. Raw Detection Loop
        raw_results = []
        for start, end in windows:
            idx = np.where((times >= start) & (times < end))[0]
            if len(idx) == 0: continue
            
            mean_chroma = np.mean(chroma[:, idx], axis=1)
            chord = self._detect_chord(mean_chroma)
            
            raw_results.append({
                "start": start, 
                "end": end, 
                "chord": chord
            })

        if is_test: return raw_results
        
        # 4. Post-Processing
        corrected = self._harmonic_correction(raw_results)
        merged = self._merge_adjacent(corrected)

        # 5. WINDOW CENTERING (Option 3 Implementation)
        # We transform the start/end times into "Midpoint" triggers
        final_timeline = []
        for i, item in enumerate(merged):
            # The 'true' time for this chord is the middle of its existence
            midpoint = item['start'] + ((item['end'] - item['start']) / 2)
            
            final_timeline.append({
                "chord": item['chord'],
                "start": round(midpoint, 2),
                "original_start": round(item['start'], 2)
            })

        # Set the 'end' of one chord to be the 'start' (midpoint) of the next
        for i in range(len(final_timeline) - 1):
            final_timeline[i]['end'] = final_timeline[i+1]['start']
            
        if final_timeline:
            final_timeline[-1]['end'] = total_duration

        return final_timeline

    def _harmonic_correction(self, results):
        if not results: return []
        all_roots = [r['chord'].replace('m', '') for r in results if r['chord'] != 'N/A']
        if not all_roots: return results
        tonic_root = Counter(all_roots).most_common(1)[0][0]

        tonic_instances = [r['chord'] for r in results if r['chord'].replace('m', '') == tonic_root]
        is_minor_key = (tonic_instances.count(f"{tonic_root}m") > len(tonic_instances) / 2)
        global_tonic = f"{tonic_root}{'m' if is_minor_key else ''}"

        circle = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
        t_idx = circle.index(tonic_root)

        if not is_minor_key:
            safe_map = {
                circle[t_idx]: "", circle[(t_idx + 2) % 12]: "m",
                circle[(t_idx + 4) % 12]: "m", circle[(t_idx - 1) % 12]: "",
                circle[(t_idx + 1) % 12]: "", circle[(t_idx + 3) % 12]: "m",
            }
        else:
            safe_map = {
                circle[t_idx]: "m", circle[(t_idx + 1) % 12]: "",
                circle[(t_idx - 1) % 12]: "m", circle[(t_idx + 2) % 12]: "m",
                circle[(t_idx - 2) % 12]: "", circle[(t_idx - 3) % 12]: "",
            }

        corrected = []
        for res in results:
            root = res['chord'].replace('m', '')
            if root in safe_map:
                corrected.append({**res, "chord": f"{root}{safe_map[root]}"})
            else:
                corrected.append({**res, "chord": global_tonic})
        return corrected

    def _detect_chord(self, chroma_vector):
        if np.max(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.max(chroma_vector)
        best_chord, max_similarity = "N/A", -1
        for i in range(self.bakol.SEMITONES):
            for quality, intervals in self.bakol.CHORD_OFFSETS.items():
                template = np.zeros(self.bakol.SEMITONES)
                for interval in intervals: template[interval] = 1
                template = np.roll(template, i)
                similarity = np.dot(chroma_vector, template)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_chord = f"{self.bakol.CHROMATIC[i]}{quality}"
        return best_chord

    def _merge_adjacent(self, results):
        if not results: return []
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
