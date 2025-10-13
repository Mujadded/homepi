import os
import json
import threading
import subprocess
import shutil
import psutil
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pygame
import yt_dlp
from pathlib import Path
from mutagen import File as MutagenFile

# Pi HAT modules
try:
    import sensor_manager
    import display_manager
    HAT_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Pi HAT modules not available: {e}")
    HAT_AVAILABLE = False

# Security system modules
try:
    import security_manager
    import car_recognizer
    SECURITY_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Security modules not available: {e}")
    SECURITY_AVAILABLE = False

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
SONGS_DIR = os.path.join(os.path.dirname(__file__), 'songs')
SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), 'schedules.json')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(SONGS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Initialize pygame mixer for audio playback
# Set audio driver to ALSA to avoid PulseAudio issues
os.environ['SDL_AUDIODRIVER'] = 'alsa'
try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"⚠ Warning: Audio initialization failed: {e}")
    print("  Trying alternative audio driver...")
    os.environ['SDL_AUDIODRIVER'] = 'dsp'
    try:
        pygame.mixer.init()
    except:
        print("  Audio playback may not work. Please check audio configuration.")

current_volume = 0.7  # Default volume (0.0 to 1.0)
try:
    pygame.mixer.music.set_volume(current_volume)
except:
    print("  Could not set volume - audio may not be available")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Lock for thread-safe operations
playback_lock = threading.Lock()
current_playing = None
current_playing_start_time = None
current_song_duration = None

# Health monitoring
last_bluetooth_check = None
bluetooth_connected = False
system_warnings = []


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


def get_audio_duration(filepath):
    """Get duration of audio file in seconds"""
    try:
        audio = MutagenFile(filepath)
        if audio and audio.info:
            return audio.info.length
    except:
        pass
    return None


def play_song(song_path, repeat=False, volume=None):
    """Play a song using pygame mixer"""
    global current_playing, current_volume, current_playing_start_time, current_song_duration
    with playback_lock:
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            full_path = os.path.join(SONGS_DIR, song_path)
            if os.path.exists(full_path):
                # Get duration
                current_song_duration = get_audio_duration(full_path)
                
                # Set volume if specified, otherwise keep current
                if volume is not None:
                    pygame.mixer.music.set_volume(volume / 100.0)
                
                pygame.mixer.music.load(full_path)
                loops = -1 if repeat else 0  # -1 means infinite loop
                pygame.mixer.music.play(loops=loops)
                current_playing = song_path
                current_playing_start_time = datetime.now()
                print(f"Playing: {song_path} (repeat: {repeat}, volume: {volume if volume else 'default'}, duration: {current_song_duration}s)")
                
                # Update display manager if available
                if HAT_AVAILABLE:
                    display_manager.update_playback_state(
                        playing=True,
                        current_song=song_path,
                        position=0,
                        duration=current_song_duration if current_song_duration else 0
                    )
            else:
                print(f"Song not found: {full_path}")
        except Exception as e:
            print(f"Error playing song: {e}")


def schedule_job(schedule_id, hour, minute, song, repeat, volume=None, days_of_week=None):
    """Schedule a song to play at specific time"""
    job_id = f"schedule_{schedule_id}"
    
    # Remove existing job if it exists
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job with day of week filter if specified
    trigger_kwargs = {'hour': hour, 'minute': minute}
    if days_of_week:
        # days_of_week is a list like ['mon', 'wed', 'fri']
        trigger_kwargs['day_of_week'] = ','.join(days_of_week)
    
    trigger = CronTrigger(**trigger_kwargs)
    scheduler.add_job(
        play_song,
        trigger=trigger,
        id=job_id,
        args=[song, repeat, volume],
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
                schedule.get('repeat', False),
                schedule.get('volume'),
                schedule.get('days_of_week')
            )
    
    # Update display manager if available
    if HAT_AVAILABLE:
        display_manager.update_schedules(schedules)


def backup_schedules():
    """Create a backup of schedules file"""
    try:
        if os.path.exists(SCHEDULES_FILE):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f'schedules_{timestamp}.json')
            shutil.copy2(SCHEDULES_FILE, backup_file)
            print(f"Backup created: {backup_file}")
            
            # Clean old backups (keep last 7 days)
            cleanup_old_backups()
            return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False


def cleanup_old_backups():
    """Remove backups older than 7 days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=7)
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('schedules_') and filename.endswith('.json'):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    print(f"Removed old backup: {filename}")
    except Exception as e:
        print(f"Cleanup failed: {e}")


def restore_from_backup(backup_filename):
    """Restore schedules from a backup"""
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, SCHEDULES_FILE)
            reload_all_schedules()
            return True
        return False
    except Exception as e:
        print(f"Restore failed: {e}")
        return False


def get_system_health():
    """Get system health metrics"""
    global system_warnings
    system_warnings = []
    
    health = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'temperature': get_cpu_temperature(),
        'uptime': get_uptime(),
        'bluetooth_connected': check_bluetooth_connection(),
        'warnings': system_warnings
    }
    
    # Add environmental sensor data if available
    if HAT_AVAILABLE:
        sensor_data = sensor_manager.get_sensor_data()
        health['room_temperature'] = sensor_data.get('temperature')
        health['room_humidity'] = sensor_data.get('humidity')
        health['sensor_available'] = sensor_data.get('sensor_available', False)
    else:
        health['room_temperature'] = None
        health['room_humidity'] = None
        health['sensor_available'] = False
    
    # Check for warnings
    if health['cpu_percent'] > 80:
        system_warnings.append('High CPU usage')
    if health['memory_percent'] > 80:
        system_warnings.append('High memory usage')
    if health['disk_percent'] > 90:
        system_warnings.append('Low disk space')
    if health['temperature'] and health['temperature'] > 75:
        system_warnings.append('High CPU temperature')
    if not health['bluetooth_connected']:
        system_warnings.append('Bluetooth speaker disconnected')
    
    health['warnings'] = system_warnings
    return health


def get_cpu_temperature():
    """Get CPU temperature (Raspberry Pi specific)"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000.0
            return round(temp, 1)
    except:
        return None


def get_uptime():
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            return int(uptime_seconds)
    except:
        return None


def check_bluetooth_connection():
    """Check if Bluetooth speaker is connected"""
    global last_bluetooth_check, bluetooth_connected
    
    try:
        # Run bluetoothctl to check connected devices
        result = subprocess.run(
            ['bluetoothctl', 'info'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Check if any device is connected
        bluetooth_connected = 'Connected: yes' in result.stdout
        last_bluetooth_check = datetime.now()
        return bluetooth_connected
    except:
        return False


def auto_reconnect_bluetooth():
    """Attempt to reconnect Bluetooth speaker"""
    try:
        print("Attempting Bluetooth auto-reconnect...")
        subprocess.run(
            ['bash', os.path.join(os.path.dirname(__file__), 'quick-bluetooth-fix.sh')],
            timeout=30
        )
        return True
    except Exception as e:
        print(f"Auto-reconnect failed: {e}")
        return False


def schedule_daily_backup():
    """Schedule daily backup at 3 AM"""
    scheduler.add_job(
        backup_schedules,
        trigger=CronTrigger(hour=3, minute=0),
        id='daily_backup',
        replace_existing=True
    )
    print("Daily backup scheduled for 3:00 AM")


def schedule_health_check():
    """Schedule health check every 5 minutes"""
    def health_check():
        health = get_system_health()
        if not health['bluetooth_connected']:
            print("Bluetooth disconnected, attempting reconnect...")
            auto_reconnect_bluetooth()
    
    scheduler.add_job(
        health_check,
        trigger='interval',
        minutes=5,
        id='health_check',
        replace_existing=True
    )
    print("Health check scheduled every 5 minutes")


# API Routes

@app.route('/')
def index():
    """Serve the main page"""
    response = send_from_directory('static', 'index.html')
    # Add cache-busting headers to force browser refresh
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/security')
def security():
    """Serve the security page"""
    response = send_from_directory('static', 'security.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/songs', methods=['GET'])
def get_songs():
    """Get list of all songs with duration"""
    songs = []
    for filename in os.listdir(SONGS_DIR):
        if filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            filepath = os.path.join(SONGS_DIR, filename)
            duration = get_audio_duration(filepath)
            songs.append({
                'name': filename,
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath),
                'duration': duration
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
    """Delete a song file and all schedules using it"""
    filepath = os.path.join(SONGS_DIR, filename)
    if os.path.exists(filepath):
        # Delete the song file
        os.remove(filepath)
        
        # Delete all schedules using this song
        schedules = load_schedules()
        schedules_to_delete = [s for s in schedules if s['song'] == filename]
        
        # Remove scheduled jobs
        for schedule in schedules_to_delete:
            job_id = f"schedule_{schedule['id']}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
        
        # Keep only schedules that don't use this song
        updated_schedules = [s for s in schedules if s['song'] != filename]
        save_schedules(updated_schedules)
        
        deleted_count = len(schedules_to_delete)
        message = f'Song deleted successfully'
        if deleted_count > 0:
            message += f' (also deleted {deleted_count} schedule{"s" if deleted_count > 1 else ""} using this song)'
        
        return jsonify({
            'message': message,
            'deleted_schedules': deleted_count
        })
    return jsonify({'error': 'Song not found'}), 404


@app.route('/api/songs/youtube', methods=['POST'])
def download_youtube():
    """Download a song from YouTube (single video only, no playlists)"""
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
            'no_warnings': False,
            # Prevent playlist downloads - only single video
            'noplaylist': True,
            # Use cookies and headers to avoid 403 errors
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Extract audio only
            'extract_audio': True,
            # Prefer youtube music if available
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            # Socket timeout for large files (2 hours = 7200 seconds)
            'socket_timeout': 7200,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First extract info to check if it's a playlist
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if 'entries' in info:
                return jsonify({
                    'error': 'Playlist detected! Please use a single video URL, not a playlist link.'
                }), 400
            
            # Prepare expected filename
            expected_filename = ydl.prepare_filename(info)
            expected_mp3 = os.path.splitext(os.path.basename(expected_filename))[0] + '.mp3'
            expected_mp3_path = os.path.join(SONGS_DIR, expected_mp3)
            
            # Check if MP3 already exists
            if os.path.exists(expected_mp3_path):
                return jsonify({
                    'message': 'Song already exists in library',
                    'filename': expected_mp3,
                    'already_exists': True
                })
            
            # Clean up any incomplete downloads (mp4, webm, etc.)
            # This happens if previous download timed out
            base_filename = os.path.splitext(os.path.basename(expected_filename))[0]
            for ext in ['.mp4', '.webm', '.m4a', '.part', '.ytdl', '.temp']:
                incomplete_file = os.path.join(SONGS_DIR, base_filename + ext)
                if os.path.exists(incomplete_file):
                    print(f"Removing incomplete download: {incomplete_file}")
                    os.remove(incomplete_file)
            
            # Now download the single video
            print(f"Starting download: {info.get('title', 'Unknown')}")
            info = ydl.extract_info(url, download=True)
            print(f"Download finished, extracting audio...")
            filename = ydl.prepare_filename(info)
            # Change extension to mp3
            filename = os.path.splitext(os.path.basename(filename))[0] + '.mp3'
            print(f"Download complete: {filename}")
            
        return jsonify({'message': 'Song downloaded successfully', 'filename': filename})
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            return jsonify({
                'error': 'YouTube blocked the download. Try updating yt-dlp: ./venv/bin/pip install --upgrade yt-dlp'
            }), 500
        return jsonify({'error': f'Download failed: {error_msg}'}), 500
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
        'enabled': data.get('enabled', True),
        'volume': data.get('volume'),  # Per-schedule volume
        'days_of_week': data.get('days_of_week')  # e.g., ['mon', 'wed', 'fri']
    }
    
    schedules.append(new_schedule)
    save_schedules(schedules)
    
    # Schedule the job
    if new_schedule['enabled']:
        schedule_job(new_id, new_schedule['hour'], new_schedule['minute'], 
                    new_schedule['song'], new_schedule['repeat'],
                    new_schedule.get('volume'), new_schedule.get('days_of_week'))
    
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
                           schedules[i]['song'], schedules[i].get('repeat', False),
                           schedules[i].get('volume'), schedules[i].get('days_of_week'))
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
    global current_playing, current_playing_start_time, current_song_duration
    with playback_lock:
        pygame.mixer.music.stop()
        current_playing = None
        current_playing_start_time = None
        current_song_duration = None
        
        # Update display manager if available
        if HAT_AVAILABLE:
            display_manager.update_playback_state(playing=False, current_song=None)
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
    """Get current playback status with progress"""
    global current_playing, current_volume, current_playing_start_time, current_song_duration
    
    try:
        is_playing = pygame.mixer.music.get_busy()
    except pygame.error:
        # Mixer not initialized - treat as not playing
        is_playing = False
    
    position = 0
    duration = 0
    
    if is_playing and current_playing_start_time and current_song_duration:
        # Calculate current position
        elapsed = (datetime.now() - current_playing_start_time).total_seconds()
        position = min(elapsed, current_song_duration)
        duration = current_song_duration
    
    return jsonify({
        'playing': is_playing,
        'current_song': current_playing,
        'volume': int(current_volume * 100),
        'position': position,
        'duration': duration
    })


@app.route('/api/health', methods=['GET'])
def health_status():
    """Get system health status"""
    return jsonify(get_system_health())


@app.route('/api/backups', methods=['GET'])
def list_backups():
    """List all available backups"""
    backups = []
    try:
        for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if filename.startswith('schedules_') and filename.endswith('.json'):
                filepath = os.path.join(BACKUP_DIR, filename)
                backups.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })
    except Exception as e:
        print(f"Error listing backups: {e}")
    return jsonify(backups)


@app.route('/api/backups/create', methods=['POST'])
def create_backup():
    """Create a manual backup"""
    if backup_schedules():
        return jsonify({'message': 'Backup created successfully'})
    return jsonify({'error': 'Backup failed'}), 500


@app.route('/api/backups/restore', methods=['POST'])
def restore_backup():
    """Restore from a backup"""
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'No backup filename provided'}), 400
    
    if restore_from_backup(filename):
        return jsonify({'message': 'Backup restored successfully'})
    return jsonify({'error': 'Restore failed'}), 500


@app.route('/api/bluetooth/reconnect', methods=['POST'])
def reconnect_bluetooth():
    """Manually trigger Bluetooth reconnection"""
    if auto_reconnect_bluetooth():
        return jsonify({'message': 'Bluetooth reconnection initiated'})
    return jsonify({'error': 'Reconnection failed'}), 500


@app.route('/api/sensors', methods=['GET'])
def get_sensor_data():
    """Get environmental sensor data (temperature, humidity)"""
    if HAT_AVAILABLE:
        return jsonify(sensor_manager.get_sensor_data())
    else:
        return jsonify({
            'temperature': None,
            'humidity': None,
            'pressure': None,
            'last_update': None,
            'sensor_available': False
        })


# ============================================
# Security System Routes
# ============================================

@app.route('/api/security/status', methods=['GET'])
def get_security_status():
    """Get security system status"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        status = security_manager.get_status()
        # Add debug info
        status['_debug'] = {
            'SECURITY_AVAILABLE': SECURITY_AVAILABLE,
            'module_loaded': 'security_manager' in dir()
        }
        return jsonify(status)
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/security/enable', methods=['POST'])
def enable_security():
    """Enable security detection"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        if security_manager.start_detection():
            return jsonify({'success': True, 'message': 'Detection started'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start detection'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/disable', methods=['POST'])
def disable_security():
    """Disable security detection"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        if security_manager.stop_detection():
            return jsonify({'success': True, 'message': 'Detection stopped'})
        else:
            return jsonify({'success': False, 'message': 'Detection not running'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/detections', methods=['GET'])
def get_detections():
    """Get recent detections"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        detections = security_manager.get_recent_detections(limit)
        return jsonify(detections)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/detections/<int:detection_id>', methods=['GET'])
def get_detection(detection_id):
    """Get specific detection details"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        detections = security_manager.get_recent_detections(1000)  # Get many
        detection = next((d for d in detections if d['id'] == detection_id), None)
        
        if detection:
            return jsonify(detection)
        else:
            return jsonify({'error': 'Detection not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/cars', methods=['GET'])
def get_known_cars():
    """Get list of known cars"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        cars = car_recognizer.get_known_cars()
        return jsonify(cars)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/cars', methods=['POST'])
def add_known_car():
    """Add a known car"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        data = request.json
        car_id = data.get('car_id')
        owner = data.get('owner')
        
        if not car_id or not owner:
            return jsonify({'error': 'car_id and owner required'}), 400
        
        if car_recognizer.add_car_to_database(car_id, owner):
            return jsonify({'success': True, 'message': f'Car {car_id} added'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add car'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/cars/<car_id>', methods=['DELETE'])
def delete_known_car(car_id):
    """Remove a known car"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        if car_recognizer.remove_car_from_database(car_id):
            return jsonify({'success': True, 'message': f'Car {car_id} removed'})
        else:
            return jsonify({'success': False, 'message': 'Car not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/live-feed')
def live_feed():
    """MJPEG live camera stream"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    def generate():
        """Generate MJPEG stream from camera frames"""
        import cv2
        import time
        import camera_manager
        
        print("📹 Live feed stream started")
        frame_count = 0
        
        while True:
            try:
                # Get current frame from camera
                frame = camera_manager.get_frame()
                
                if frame is not None:
                    # Convert RGB to BGR for OpenCV
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Encode frame to JPEG
                    _, jpeg = cv2.imencode('.jpg', bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    # Yield frame in MJPEG format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    
                    frame_count += 1
                    if frame_count % 30 == 0:  # Log every 30 frames (~1 second)
                        print(f"📹 Streamed {frame_count} frames")
                else:
                    print("⚠ No frame available from camera")
                
                time.sleep(0.033)  # ~30 FPS
                
            except GeneratorExit:
                print(f"📹 Live feed stream ended (streamed {frame_count} frames)")
                break
            except Exception as e:
                print(f"Error in live feed: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    from flask import Response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/security/pantilt/move', methods=['POST'])
def move_pantilt():
    """Manual Pan-Tilt control (relative movement)"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import pantilt_controller
        
        data = request.json
        pan_delta = data.get('pan', 0)
        tilt_delta = data.get('tilt', 0)
        speed = data.get('speed', 5)
        
        # Get current position
        current = pantilt_controller.get_position()
        
        # Calculate new absolute position
        new_pan = current['pan'] + pan_delta
        new_tilt = current['tilt'] + tilt_delta
        
        # Move to new position
        pantilt_controller.move_to(new_pan, new_tilt, speed)
        position = pantilt_controller.get_position()
        
        return jsonify({
            'success': True,
            'position': position
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/pantilt/home', methods=['POST'])
def pantilt_home():
    """Move Pan-Tilt to home position"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import pantilt_controller
        
        pantilt_controller.home()
        position = pantilt_controller.get_position()
        
        return jsonify({
            'success': True,
            'position': position
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/training/upload', methods=['POST'])
def upload_training_image():
    """Upload image for training (car, person, family member)"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        label = request.form.get('label')  # 'my_car', 'my_face', 'family_member_name'
        category = request.form.get('category')  # 'car', 'person'
        
        if not label or not category:
            return jsonify({'error': 'label and category required'}), 400
        
        # Save uploaded image
        import os
        from datetime import datetime
        
        training_dir = f'training_data/{category}/{label}'
        os.makedirs(training_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{label}_{timestamp}.jpg'
        filepath = os.path.join(training_dir, filename)
        
        file.save(filepath)
        
        # Count images for this label
        image_count = len([f for f in os.listdir(training_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
        
        return jsonify({
            'success': True,
            'message': f'Image saved for {label}',
            'filepath': filepath,
            'image_count': image_count,
            'needs_more': image_count < 50  # Recommend at least 50 images
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/security/training/labels', methods=['GET'])
def get_training_labels():
    """Get list of training labels and image counts"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import os
        
        labels = {
            'cars': {},
            'persons': {}
        }
        
        # Scan training_data directory
        for category in ['car', 'person']:
            category_dir = f'training_data/{category}'
            if os.path.exists(category_dir):
                for label in os.listdir(category_dir):
                    label_dir = os.path.join(category_dir, label)
                    if os.path.isdir(label_dir):
                        image_count = len([f for f in os.listdir(label_dir) 
                                          if f.endswith(('.jpg', '.jpeg', '.png'))])
                        
                        key = 'cars' if category == 'car' else 'persons'
                        labels[key][label] = {
                            'count': image_count,
                            'ready': image_count >= 50
                        }
        
        return jsonify(labels)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/training/train', methods=['POST'])
def train_model():
    """Train custom recognition model"""
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        data = request.json
        category = data.get('category')  # 'car' or 'person'
        
        if category not in ['car', 'person']:
            return jsonify({'error': 'Invalid category'}), 400
        
        # TODO: Implement actual training
        # For now, return placeholder response
        return jsonify({
            'success': True,
            'message': 'Training started',
            'note': 'Training functionality coming soon. For now, use remote training on laptop.',
            'guide': 'See TRAINING_GUIDE.md for instructions'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Jetson Integration APIs (I/O Device Mode)
# ============================================

@app.route('/api/webhook/detection', methods=['POST'])
def webhook_detection():
    """
    Receive detection results from Jetson Orin
    
    Expected payload:
    {
        "timestamp": "2025-10-12T20:15:30",
        "object_type": "car",
        "confidence": 0.87,
        "bbox": [0.3, 0.2, 0.7, 0.8],
        "car_id": "my_car",
        "action": "open_garage",
        "image_data": "base64_encoded_image"
    }
    """
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import security_manager
        
        data = request.json
        
        # Store detection in local database
        detection_id = security_manager.save_detection_from_webhook(data)
        
        # Execute requested action
        action = data.get('action')
        if action == 'open_garage':
            import flipper_controller
            if flipper_controller.is_enabled():
                flipper_controller.open_garage()
        
        # Send Telegram notification if image provided
        if data.get('image_data'):
            import telegram_notifier
            if telegram_notifier.is_enabled():
                message = f"🚨 {data['object_type'].title()} detected"
                if data.get('car_id'):
                    message += f" ({data['car_id']})"
                message += f"\nConfidence: {data['confidence']:.1%}"
                
                telegram_notifier.send_notification(
                    message=message,
                    image_data=data.get('image_data')
                )
        
        return jsonify({
            'success': True,
            'detection_id': detection_id,
            'message': 'Detection processed'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/camera/frame', methods=['GET'])
def get_camera_frame():
    """
    Get single camera frame for Jetson processing
    Returns base64-encoded JPEG image
    """
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import camera_manager
        
        frame_data = camera_manager.get_single_frame_encoded()
        
        if frame_data:
            return jsonify({
                'success': True,
                'frame': frame_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to capture frame'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pantilt/command', methods=['POST'])
def pantilt_command():
    """
    Execute Pan-Tilt command from Jetson
    
    Payload:
    {
        "action": "move",
        "pan": 15,
        "tilt": -10,
        "speed": 5
    }
    
    Or:
    {
        "action": "home"
    }
    """
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import pantilt_controller
        
        data = request.json
        action = data.get('action')
        
        if action == 'move':
            pan = data.get('pan', 0)
            tilt = data.get('tilt', 0)
            speed = data.get('speed', 5)
            
            # Get current position
            current = pantilt_controller.get_position()
            
            # Calculate new absolute position
            new_pan = current['pan'] + pan
            new_tilt = current['tilt'] + tilt
            
            # Move to new position
            pantilt_controller.move_to(new_pan, new_tilt, speed)
            position = pantilt_controller.get_position()
            
            return jsonify({
                'success': True,
                'position': position
            })
            
        elif action == 'home':
            pantilt_controller.home()
            position = pantilt_controller.get_position()
            
            return jsonify({
                'success': True,
                'position': position
            })
            
        else:
            return jsonify({'error': 'Invalid action. Use "move" or "home"'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/telegram/send', methods=['POST'])
def send_telegram_notification():
    """
    Send Telegram notification from Jetson
    
    Payload:
    {
        "message": "Car detected",
        "image_data": "base64_encoded_image",
        "chat_id": "optional_chat_id"
    }
    """
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import telegram_notifier
        
        if not telegram_notifier.is_enabled():
            return jsonify({'error': 'Telegram not configured'}), 503
        
        data = request.json
        message = data.get('message', 'Notification from HomePi')
        image_data = data.get('image_data')
        chat_id = data.get('chat_id')
        
        result = telegram_notifier.send_notification(
            message=message,
            image_data=image_data,
            chat_id=chat_id
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Notification sent'
            })
        else:
            return jsonify({'error': 'Failed to send notification'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/flipper/trigger', methods=['POST'])
def trigger_flipper_action():
    """
    Trigger Flipper Zero action from Jetson
    
    Payload:
    {
        "action": "garage_open"
    }
    """
    if not SECURITY_AVAILABLE:
        return jsonify({'error': 'Security system not available'}), 503
    
    try:
        import flipper_controller
        
        if not flipper_controller.is_enabled():
            return jsonify({'error': 'Flipper Zero not configured'}), 503
        
        data = request.json
        action = data.get('action')
        
        if action == 'garage_open':
            result = flipper_controller.open_garage()
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Garage command sent'
                })
            else:
                return jsonify({'error': 'Failed to send command'}), 500
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Load all schedules on startup
    reload_all_schedules()
    
    # Setup automated tasks
    schedule_daily_backup()
    schedule_health_check()
    
    # Create initial backup
    backup_schedules()
    
    print("=" * 50)
    print("HomePi Music Scheduler Started")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Schedules loaded: {len(load_schedules())}")
    print("Daily backup: 3:00 AM")
    print("Health check: Every 5 minutes")
    
    # Initialize Pi HAT if available
    if HAT_AVAILABLE:
        print("\n🎩 Initializing Pi HAT...")
        
        # Start sensor thread
        sensor_thread = sensor_manager.start_sensor_thread()
        if sensor_thread:
            print("✓ Environmental sensors active")
        
        # Start display thread (pass schedules and sensor data)
        schedules_list = load_schedules()
        sensor_data_dict = sensor_manager.sensor_data
        display_thread = display_manager.start_display_thread(schedules_list, sensor_data_dict)
        if display_thread:
            print("✓ OLED display active")
        
        # Set up volume control callback for joystick
        def volume_control_callback(action, value=None):
            """Handle volume control from joystick"""
            global current_volume
            if action == 'get':
                return int(current_volume * 100)
            elif action == 'set' and value is not None:
                try:
                    current_volume = value / 100.0
                    pygame.mixer.music.set_volume(current_volume)
                    return value
                except:
                    pass
            return int(current_volume * 100)
        
        display_manager.set_volume_callback(volume_control_callback)
        print("✓ Joystick controls enabled (Up/Down=Brightness, Left/Right=Volume)")
    else:
        print("\n⚠ Pi HAT modules not loaded - running without display/sensors")
    
    # Initialize Security System if available (I/O Mode - No detection loop)
    if SECURITY_AVAILABLE:
        print("\n🔐 Initializing Security System (I/O Mode)...")
        if security_manager.init_security_io_mode():
            print("✓ Security I/O system initialized")
            print("  - Camera: Ready for streaming")
            print("  - Pan-Tilt: Ready for commands")
            print("  - Telegram: Ready for notifications")
            print("  - Flipper: Ready for automation")
            print("  - Database: Ready for caching")
            print("⚠ Detection loop disabled - Jetson Orin handles AI processing")
        else:
            print("⚠ Security system initialization failed")
    else:
        print("\n⚠ Security modules not loaded - running without security system")
    
    print("=" * 50)
    
    # Run the Flask app
    # Note: debug=False for production to avoid state loss on reload
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

