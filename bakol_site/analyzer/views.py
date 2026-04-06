import os
import sys
import librosa
import soundfile as sf
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# Path fix for core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.engine import Bakol
from core.listener import Listener

# Initialize engine and listener once at module level
bakol = Bakol()
listener = Listener(bakol)

def index(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('track'):
        track = request.FILES['track']
        fs = FileSystemStorage()
        
        temp_name = fs.save("temp_" + track.name, track)
        temp_path = fs.path(temp_name)

        try:
            # 1. Crop Audio
            max_sec = 30
            y, sr = librosa.load(temp_path, duration=max_sec)
            cropped_filename = "cropped_" + track.name
            cropped_path = os.path.join(settings.MEDIA_ROOT, cropped_filename)
            sf.write(cropped_path, y, sr)

            # 2. Extract Timeline
            chords_timeline = listener.analyze_file(
                cropped_path, 
                max_seconds=max_sec, 
                use_correction=True,
                latency_offset=-0.15
            )

            # 3. Extract Core and Diatonic Options using core routines
            core_list = listener.get_core_progression(chords_timeline, top_n=4)
            diatonic_options = listener.get_diatonic_options(chords_timeline)

            context = {
                'chords': chords_timeline,
                'core_list': core_list,
                'diatonic_options': diatonic_options,
                'file_url': fs.url(cropped_filename),
            }

        except Exception as e:
            context['error'] = str(e)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return render(request, 'index.html', context)
