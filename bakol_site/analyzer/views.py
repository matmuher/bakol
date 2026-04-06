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
        
        # 1. Save original upload as a temp file
        temp_name = fs.save("temp_" + track.name, track)
        temp_path = fs.path(temp_name)

        try:
            # 2. Crop Audio using librosa
            max_sec = 30
            y, sr = librosa.load(temp_path, duration=max_sec)
            
            # Define name and path for the cropped file
            cropped_filename = "cropped_" + track.name
            cropped_path = os.path.join(settings.MEDIA_ROOT, cropped_filename)
            
            # Write the cropped buffer to the media folder
            sf.write(cropped_path, y, sr)

            # 3. Analyze the cropped file
            # use_correction=True handles the harmonic filtering
            chords_timeline = listener.analyze_file(
                cropped_path, 
                max_seconds=max_sec, 
                use_correction=True,
                latency_offset=-0.5
            )

            # 4. Extract Core Progression
            core_list = listener.get_core_progression(chords_timeline, top_n=4)
            core_display = " → ".join(core_list)

            # 5. Prepare Context
            context['chords'] = chords_timeline
            context['core_chords'] = core_display
            context['file_url'] = fs.url(cropped_filename)

        except Exception as e:
            print(f"Error: {e}")
            context['error'] = f"Analysis failed: {str(e)}"
        finally:
            # Cleanup the original temp file to save space
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return render(request, 'index.html', context)
