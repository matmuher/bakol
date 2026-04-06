import os
import sys
import librosa
import soundfile as sf
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings # <--- ADD THIS IMPORT

# Path fix for core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.engine import Bakol
from core.listener import Listener

bakol = Bakol()
listener = Listener(bakol)

def index(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('track'):
        track = request.FILES['track']
        fs = FileSystemStorage()
        
        # 1. Save temp file
        temp_name = fs.save("temp_" + track.name, track)
        temp_path = fs.path(temp_name)

        try:
            # 2. Crop Audio
            max_sec = 30
            y, sr = librosa.load(temp_path, duration=max_sec)
            
            cropped_filename = "cropped_" + track.name
            # settings.MEDIA_ROOT now works because of the import above
            cropped_path = os.path.join(settings.MEDIA_ROOT, cropped_filename)
            
            sf.write(cropped_path, y, sr)

            # 3. Analyze
            chords = listener.analyze_file(cropped_path, max_seconds=max_sec)

            context['chords'] = chords
            context['file_url'] = fs.url(cropped_filename)
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return render(request, 'index.html', context)
