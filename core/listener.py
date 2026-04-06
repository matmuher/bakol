import librosa
import numpy as np
import warnings
from collections import Counter

warnings.filterwarnings("ignore", category=DeprecationWarning, module="audioread")

class Listener:
    def __init__(self, bakol):
        self.bakol = bakol

    def analyze_file(self, file_path, num_chords=None, max_seconds=30, window_size=1.0, latency_offset=-0.15, use_correction=True):
        y, sr = librosa.load(file_path, duration=max_seconds)
        total_duration = librosa.get_duration(y=y, sr=sr)
        
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512, n_chroma=self.bakol.SEMITONES)
        times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)

        if num_chords:
            win_len = total_duration / num_chords
            windows = [(i * win_len, (i + 1) * win_len) for i in range(num_chords)]
        else:
            windows = [(i, i + window_size) for i in np.arange(0, total_duration, window_size)]

        raw_results = []
        for start, end in windows:
            idx = np.where((times >= start) & (times < end))[0]
            if len(idx) == 0: continue
            mean_chroma = np.mean(chroma[:, idx], axis=1)
            chord = self._detect_chord(mean_chroma)
            raw_results.append({"start": start, "end": end, "chord": chord})

        processed = self._harmonic_correction(raw_results) if use_correction else raw_results
        merged = self._merge_adjacent(processed)

        final_timeline = []
        for item in merged:
            shifted_start = item['start'] + latency_offset
            final_timeline.append({
                "chord": item['chord'],
                "start": max(0, round(shifted_start, 2))
            })

        for i in range(len(final_timeline) - 1):
            final_timeline[i]['end'] = final_timeline[i+1]['start']
            
        if final_timeline:
            final_timeline[0]['start'] = 0.0
            final_timeline[-1]['end'] = total_duration

        return final_timeline

    def get_core_progression(self, full_chords, top_n=4):
        """Identifies the top N most frequent chords in order of first appearance."""
        if not full_chords: return []
        
        # Count occurrences (frequency)
        stats = Counter([c['chord'] for c in full_chords])
        top_chords = [chord for chord, count in stats.most_common(top_n)]
        
        # Re-order based on first appearance in the original timeline
        ordered_core = []
        found = set()
        for segment in full_chords:
            chord = segment['chord']
            if chord in top_chords and chord not in found:
                ordered_core.append(chord)
                found.add(chord)
        return ordered_core

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
            safe_map = {circle[t_idx]: "", circle[(t_idx+2)%12]: "m", circle[(t_idx+4)%12]: "m", circle[(t_idx-1)%12]: "", circle[(t_idx+1)%12]: "", circle[(t_idx+3)%12]: "m"}
        else:
            safe_map = {circle[t_idx]: "m", circle[(t_idx+1)%12]: "", circle[(t_idx-1)%12]: "m", circle[(t_idx+2)%12]: "m", circle[(t_idx-2)%12]: "", circle[(t_idx-3)%12]: ""}

        corrected = []
        for res in results:
            root = res['chord'].replace('m', '')
            if root in safe_map:
                corrected.append({**res, "chord": f"{root}{safe_map[root]}"})
            else:
                corrected.append({**res, "chord": global_tonic})
        return corrected

    def _detect_chord(self, chroma_vector):
        if np.max(chroma_vector) > 0: chroma_vector /= np.max(chroma_vector)
        best_chord, max_similarity = "N/A", -1
        for i in range(self.bakol.SEMITONES):
            for quality, intervals in self.bakol.CHORD_OFFSETS.items():
                template = np.zeros(self.bakol.SEMITONES); [template.__setitem__(v, 1) for v in intervals]
                template = np.roll(template, i)
                similarity = np.dot(chroma_vector, template)
                if similarity > max_similarity:
                    max_similarity, best_chord = similarity, f"{self.bakol.CHROMATIC[i]}{quality}"
        return best_chord

    def _merge_adjacent(self, results):
        if not results: return []
        merged = [results[0].copy()]
        for next_res in results[1:]:
            if next_res['chord'] == merged[-1]['chord']: merged[-1]['end'] = next_res['end']
            else: merged.append(next_res.copy())
        return merged
