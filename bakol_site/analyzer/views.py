import os
import sys
import librosa
import soundfile as sf
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import tempfile

# Path fix for core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile

from .models import UserTrack
from .utils import calculate_hash
from core.engine import Bakol
from core.listener import Listener

# Initialize the analysis engine
bakol = Bakol()
listener = Listener(bakol)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username:
            user, created = User.objects.get_or_create(username=username)
            request.session['simple_user_id'] = user.id
            return redirect('index')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def index(request, track_id=None):
    user_id = request.session.get('simple_user_id')
    if not user_id:
        return redirect('login')
    
    current_user = get_object_or_404(User, id=user_id)
    user_files = UserTrack.objects.filter(user=current_user).order_by('-created_at')
    
    context = {
        'user_files': user_files,
        'user': current_user,
        'active_id': track_id,
        'chords': None,
    }

    # --- 1. Handle File Uploads with CROPPING ---
    if request.method == 'POST' and request.FILES.get('track'):
        track = request.FILES['track']
        
        if not track.name.lower().endswith('.mp3'):
            context['error'] = "Only MP3 files are supported."
            return render(request, 'index.html', context)

        # We check the hash of the ORIGINAL file to prevent duplicates
        file_hash = calculate_hash(track)
        existing = UserTrack.objects.filter(user=current_user, hash=file_hash).first()
        
        if existing:
            return redirect('index_with_track', track_id=existing.id)

        try:
            # SAVE TO TEMP TO READ
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
                for chunk in track.chunks():
                    temp_mp3.write(chunk)
                temp_path = temp_mp3.name

            # CROP USING LIBROSA
            max_sec = 30
            y, sr = librosa.load(temp_path, duration=max_sec)
            
            # WRITE CROPPED TO A NEW TEMP FILE (AS WAV FOR BEST COMPATIBILITY)
            cropped_filename = f"cropped_{track.name.split('.')[0]}.wav"
            temp_cropped_path = os.path.join(tempfile.gettempdir(), cropped_filename)
            sf.write(temp_cropped_path, y, sr)

            # SAVE TO DATABASE
            new_track = UserTrack(
                user=current_user,
                filename=track.name,
                hash=file_hash
            )
            
            # Read the cropped file back to save it into the FileField
            with open(temp_cropped_path, 'rb') as f:
                new_track.file.save(cropped_filename, ContentFile(f.read()), save=True)

            # CLEANUP TEMPS
            os.remove(temp_path)
            os.remove(temp_cropped_path)

            return redirect('index_with_track', track_id=new_track.id)

        except Exception as e:
            context['error'] = f"Upload/Crop failed: {str(e)}"
            return render(request, 'index.html', context)

    # --- 2. Handle Chord Analysis ---
    if track_id:
        selected_track = get_object_or_404(UserTrack, id=track_id, user=current_user)
        try:
            # Analysis is fast because the file is already 30s
            chords_timeline = listener.analyze_file(selected_track.file.path, max_seconds=30)
            core_list = listener.get_core_progression(chords_timeline)
            diatonic_options = listener.get_diatonic_options(chords_timeline)

            context.update({
                'chords': chords_timeline,
                'core_list': core_list,
                'diatonic_options': diatonic_options,
                'file_url': selected_track.file.url,
                'active_id': selected_track.id
            })
        except Exception as e:
            context['error'] = f"Analysis failed: {str(e)}"

    return render(request, 'index.html', context)

def delete_track(request, track_id):
    user_id = request.session.get('simple_user_id')
    if not user_id:
        return redirect('login')
        
    track = get_object_or_404(UserTrack, id=track_id, user_id=user_id)
    if track.file and os.path.isfile(track.file.path):
        os.remove(track.file.path)
    track.delete()
    return redirect('index')