import os
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pygame
import yt_dlp
from pathlib import Path

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
SONGS_DIR = os.path.join(os.path.dirname(__file__), 'songs')
SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), 'schedules.json')
os.makedirs(SONGS_DIR, exist_ok=True)

# Initialize pygame mixer for audio playback
pygame.mixer.init()
current_volume = 0.7  # Default volume (0.0 to 1.0)
pygame.mixer.music.set_volume(current_volume)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Lock for thread-safe operations
playback_lock = threading.Lock()
current_playing = None


def load_schedules():
    """Load schedules from JSON file"""
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, 'r') as f:
            return json.load(f)
    return []


def save_schedules(schedules):
    """Save schedules to JSON file"""
    with open(SCHEDULES_FILE, 'w') as f:
        json.dump(schedules, f, indent=2)


def play_song(song_path, repeat=False):
    """Play a song using pygame mixer"""
    global current_playing
    with playback_lock:
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            full_path = os.path.join(SONGS_DIR, song_path)
            if os.path.exists(full_path):
                pygame.mixer.music.load(full_path)
                loops = -1 if repeat else 0  # -1 means infinite loop
                pygame.mixer.music.play(loops=loops)
                current_playing = song_path
                print(f"Playing: {song_path} (repeat: {repeat})")
            else:
                print(f"Song not found: {full_path}")
        except Exception as e:
            print(f"Error playing song: {e}")


def schedule_job(schedule_id, hour, minute, song, repeat):
    """Schedule a song to play at specific time"""
    job_id = f"schedule_{schedule_id}"
    
    # Remove existing job if it exists
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job
    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(
        play_song,
        trigger=trigger,
        id=job_id,
        args=[song, repeat],
        replace_existing=True
    )


def reload_all_schedules():
    """Reload all schedules from file and update scheduler"""
    schedules = load_schedules()
    for schedule in schedules:
        if schedule.get('enabled', True):
            schedule_job(
                schedule['id'],
                schedule['hour'],
                schedule['minute'],
                schedule['song'],
                schedule.get('repeat', False)
            )


# API Routes

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/songs', methods=['GET'])
def get_songs():
    """Get list of all songs"""
    songs = []
    for filename in os.listdir(SONGS_DIR):
        if filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            filepath = os.path.join(SONGS_DIR, filename)
            songs.append({
                'name': filename,
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath)
            })
    return jsonify(songs)


@app.route('/api/songs/upload', methods=['POST'])
def upload_song():
    """Upload a song file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = file.filename
        filepath = os.path.join(SONGS_DIR, filename)
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})


@app.route('/api/songs/<path:filename>', methods=['DELETE'])
def delete_song(filename):
    """Delete a song file"""
    filepath = os.path.join(SONGS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'message': 'Song deleted successfully'})
    return jsonify({'error': 'Song not found'}), 404


@app.route('/api/songs/youtube', methods=['POST'])
def download_youtube():
    """Download a song from YouTube"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(SONGS_DIR, '%(title)s.%(ext)s'),
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Change extension to mp3
            filename = os.path.splitext(os.path.basename(filename))[0] + '.mp3'
            
        return jsonify({'message': 'Song downloaded successfully', 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Get all schedules"""
    schedules = load_schedules()
    return jsonify(schedules)


@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    data = request.json
    schedules = load_schedules()
    
    # Generate new ID
    new_id = max([s['id'] for s in schedules], default=0) + 1
    
    new_schedule = {
        'id': new_id,
        'name': data.get('name', 'Untitled'),
        'hour': data['hour'],
        'minute': data['minute'],
        'song': data['song'],
        'repeat': data.get('repeat', False),
        'enabled': data.get('enabled', True)
    }
    
    schedules.append(new_schedule)
    save_schedules(schedules)
    
    # Schedule the job
    if new_schedule['enabled']:
        schedule_job(new_id, new_schedule['hour'], new_schedule['minute'], 
                    new_schedule['song'], new_schedule['repeat'])
    
    return jsonify(new_schedule)


@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing schedule"""
    data = request.json
    schedules = load_schedules()
    
    for i, schedule in enumerate(schedules):
        if schedule['id'] == schedule_id:
            schedules[i].update(data)
            save_schedules(schedules)
            
            # Update the scheduled job
            if schedules[i]['enabled']:
                schedule_job(schedule_id, schedules[i]['hour'], schedules[i]['minute'],
                           schedules[i]['song'], schedules[i].get('repeat', False))
            else:
                job_id = f"schedule_{schedule_id}"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
            
            return jsonify(schedules[i])
    
    return jsonify({'error': 'Schedule not found'}), 404


@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    schedules = load_schedules()
    schedules = [s for s in schedules if s['id'] != schedule_id]
    save_schedules(schedules)
    
    # Remove the scheduled job
    job_id = f"schedule_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    return jsonify({'message': 'Schedule deleted successfully'})


@app.route('/api/playback/play', methods=['POST'])
def play_now():
    """Play a song immediately"""
    data = request.json
    song = data.get('song')
    repeat = data.get('repeat', False)
    
    if not song:
        return jsonify({'error': 'No song specified'}), 400
    
    play_song(song, repeat)
    return jsonify({'message': 'Playing song', 'song': song})


@app.route('/api/playback/stop', methods=['POST'])
def stop_playback():
    """Stop current playback"""
    global current_playing
    with playback_lock:
        pygame.mixer.music.stop()
        current_playing = None
    return jsonify({'message': 'Playback stopped'})


@app.route('/api/playback/pause', methods=['POST'])
def pause_playback():
    """Pause current playback"""
    with playback_lock:
        pygame.mixer.music.pause()
    return jsonify({'message': 'Playback paused'})


@app.route('/api/playback/resume', methods=['POST'])
def resume_playback():
    """Resume paused playback"""
    with playback_lock:
        pygame.mixer.music.unpause()
    return jsonify({'message': 'Playback resumed'})


@app.route('/api/playback/volume', methods=['POST'])
def set_volume():
    """Set playback volume"""
    global current_volume
    data = request.json
    volume = data.get('volume', 70)
    
    # Convert percentage to 0.0-1.0 range
    current_volume = volume / 100.0
    pygame.mixer.music.set_volume(current_volume)
    
    return jsonify({'message': 'Volume set', 'volume': volume})


@app.route('/api/playback/status', methods=['GET'])
def get_status():
    """Get current playback status"""
    global current_playing, current_volume
    return jsonify({
        'playing': pygame.mixer.music.get_busy(),
        'current_song': current_playing,
        'volume': int(current_volume * 100)
    })


if __name__ == '__main__':
    # Load all schedules on startup
    reload_all_schedules()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

