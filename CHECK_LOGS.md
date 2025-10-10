# How to Check HomePi Logs

## 🔍 Main Application Logs

### View Live Logs (recommended):
```bash
sudo journalctl -u homepi.service -f
```
Press `Ctrl+C` to stop

### View Last 100 Lines:
```bash
sudo journalctl -u homepi.service -n 100
```

### View Today's Logs:
```bash
sudo journalctl -u homepi.service --since today
```

### View Last Hour:
```bash
sudo journalctl -u homepi.service --since "1 hour ago"
```

### View with Timestamps:
```bash
sudo journalctl -u homepi.service -f --no-pager
```

---

## 📊 Other Service Logs

### Watchdog Logs:
```bash
cat /tmp/homepi-watchdog.log
```

### Bluetooth Auto-Connect:
```bash
cat /tmp/bluetooth-autoconnect.log
```

### System Logs:
```bash
sudo journalctl -xe
```

---

## 🐛 Debug YouTube Downloads

### 1. Start watching logs in one terminal:
```bash
sudo journalctl -u homepi.service -f
```

### 2. Then try downloading in browser

### 3. You'll see output like:
```
[youtube] Extracting URL: https://...
[youtube] xxxxx: Downloading webpage
[youtube] xxxxx: Downloading android player API JSON
[download] Destination: /home/user/homepi/songs/Song Name.webm
[download]  45.0% of 150.00MiB at 2.5MiB/s ETA 00:30
[download] 100% of 150.00MiB in 00:01:20
[ExtractAudio] Destination: /home/user/homepi/songs/Song Name.mp3
Deleting original file /home/user/homepi/songs/Song Name.webm
```

---

## 🔧 If Still Timing Out

The issue is likely **Nginx or reverse proxy timeout**, not the app itself.

### Check if you're using a reverse proxy:
```bash
sudo systemctl status nginx
sudo systemctl status apache2
```

### If using Nginx, increase timeout:
```bash
sudo nano /etc/nginx/sites-available/default
```

Add these lines in the `location /` block:
```nginx
proxy_read_timeout 3600s;
proxy_connect_timeout 3600s;
proxy_send_timeout 3600s;
```

Then restart:
```bash
sudo systemctl restart nginx
```

### If using Apache, increase timeout:
```bash
sudo nano /etc/apache2/sites-available/000-default.conf
```

Add:
```apache
Timeout 3600
ProxyTimeout 3600
```

Then restart:
```bash
sudo systemctl restart apache2
```

---

## 💡 Quick Diagnostics

### 1. Check if HomePi is running:
```bash
sudo systemctl status homepi.service
```

### 2. Check recent errors:
```bash
sudo journalctl -u homepi.service --since "10 minutes ago" | grep -i error
```

### 3. Test download directly (bypass browser):
```bash
cd ~/homepi
source venv/bin/activate
curl -X POST http://localhost:5000/api/songs/youtube \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=YOUR_VIDEO_ID"}'
```

### 4. Check yt-dlp version:
```bash
source ~/homepi/venv/bin/activate
pip show yt-dlp
```

### 5. Update yt-dlp if old:
```bash
source ~/homepi/venv/bin/activate
pip install --upgrade yt-dlp
```

---

## 🚀 Increase Timeouts Even More

If you need even longer timeout for very large files, edit `app.py`:

```python
# Change from:
'socket_timeout': 1800,  # 30 minutes

# To:
'socket_timeout': 7200,  # 2 hours
```

Then restart:
```bash
sudo systemctl restart homepi.service
```

---

## 📝 Full Debug Session

```bash
# Terminal 1 - Watch logs
sudo journalctl -u homepi.service -f

# Terminal 2 - Test download
cd ~/homepi
source venv/bin/activate
python3 << 'EOF'
import yt_dlp
url = "YOUR_YOUTUBE_URL_HERE"
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'test_download.%(ext)s',
    'socket_timeout': 7200,
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
EOF
```

This tests yt-dlp directly without the web interface.

---

## 🎯 Common Issues & Solutions

### Issue: "Download timed out"
**Cause:** Reverse proxy timeout  
**Fix:** Increase nginx/apache timeout (see above)

### Issue: "403 Forbidden"
**Cause:** YouTube blocking  
**Fix:** Update yt-dlp: `pip install --upgrade yt-dlp`

### Issue: "Connection reset"
**Cause:** Network issue or file too large  
**Fix:** 
1. Check internet connection
2. Increase timeout in app.py
3. Try smaller file first

### Issue: No error, just hangs
**Cause:** Timeout somewhere in the stack  
**Fix:** Check ALL timeouts:
- App timeout (app.py)
- Nginx timeout (if used)
- Browser timeout (already removed)
- Firewall timeout

---

## 📊 Example Log Output

### Success:
```
[youtube] dQw4w9WgXcQ: Downloading webpage
[download] Destination: songs/Song.webm
[download] 100% of 50.0MiB in 00:30
[ExtractAudio] Destination: songs/Song.mp3
INFO: Song downloaded successfully
```

### Timeout:
```
[download] 45% of 200.0MiB at 1.2MiB/s ETA 02:15
ERROR: Download timeout
```

### Network Error:
```
[download] 75% of 100.0MiB
ERROR: [Errno 104] Connection reset by peer
```

---

## 💡 Pro Tip

For very large files, consider downloading on the Pi directly via SSH:

```bash
cd ~/homepi/songs
source ../venv/bin/activate
yt-dlp -x --audio-format mp3 "YOUR_YOUTUBE_URL"
```

This bypasses the web interface entirely and logs show progress.

