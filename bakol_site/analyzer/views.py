import os
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.engine import Bakol
from core.listener import Listener

# Initialize core once
bakol = Bakol()
listener = Listener(bakol)

def index(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('track'):
        # 1. Save the file
        track = request.FILES['track']
        fs = FileSystemStorage()
        filename = fs.save(track.name, track)
        file_url = fs.url(filename)
        file_path = fs.path(filename)

        # 2. Call the Core
        # We limit to 60s for the web demo to avoid timeouts
        chords = listener.analyze_file(file_path, max_seconds=60)

        # 3. Prepare data for template
        context['chords'] = chords
        context['file_url'] = file_url

    return render(request, 'index.html', context)
