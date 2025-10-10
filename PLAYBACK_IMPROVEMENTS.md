# Playback & Track Duration Improvements

## 🎯 What Changed

### 1. **Clarified "Repeat" Feature**

**Before:** It wasn't clear what "repeat" meant  
**Now:** Crystal clear with helpful warnings

- **Repeat OFF (default)** = Song plays **once** and stops
- **Repeat ON** = Song **loops forever** until you manually stop it

### How to Use:
- **For normal schedules:** Leave repeat **UNCHECKED** ✅
- **For alarm clocks:** Check repeat if you want it to keep playing until you wake up and stop it

**Example:**
- Morning alarm at 7:00 AM with repeat OFF → Plays once (song ends, then silence)
- Morning alarm at 7:00 AM with repeat ON → Plays on loop forever (keeps repeating until you stop it)

---

### 2. **Track Duration Display**

Every song now shows how long it is!

**In Song List:**
```
🎵 Morning_Vibes.mp3
3.5 MB • ⏱️ 3:24
```

**In Schedule List:**
```
07:00 • 🎵 Morning_Vibes.mp3 • ⏱️ 3:24 • 📅 MON, WED, FRI
```

**Benefits:**
- ✅ See if schedules might overlap
- ✅ Know exactly how long each track is
- ✅ Plan your schedule better

**Example Conflict Detection:**
```
Schedule 1: 07:00 AM - Morning_Vibes.mp3 (3:24) → Ends ~07:03 AM
Schedule 2: 07:05 AM - Workout_Beats.mp3 (4:10) → Starts 07:05 AM

✅ No conflict! 2-minute gap between songs.
```

---

### 3. **Live Playback Progress Bar**

**New Feature:** See exactly where you are in the song!

The "Now Playing" card now shows:
- 🎵 Current song name
- ⏱️ Progress bar (visual)
- ⏰ Current time / Total time (e.g., "1:32 / 3:24")
- 🔊 Volume slider for currently playing song
- ⏹️ Stop button (easily accessible)

**What You See:**
```
┌─────────────────────────────────────┐
│ Now Playing:                        │
│ Morning_Vibes.mp3                   │
│                                     │
│ 1:32 ────────●──────── 3:24        │
│ ████████████░░░░░░░░░░░ 45%        │
│                                     │
│ Playback Volume: [████████] 70%    │
└─────────────────────────────────────┘
```

**Features:**
- Progress updates every 2 seconds
- Adjust volume while playing
- See exactly how much time is left

---

### 4. **Improved Song Controls**

**Before:**
- "▶️ Play" button
- "🔁 Play & Repeat" button

**Now:**
- "▶️ Play Once" button (clearer!)
- "🔁 Loop" button (clearer!)

This makes it obvious:
- "Play Once" → Plays the song one time
- "Loop" → Plays the song on repeat forever

---

## 🚀 Installation

### Update Dependencies

```bash
cd ~/homepi
source venv/bin/activate
pip install mutagen
```

### Copy Updated Files

1. `app.py` (added duration detection)
2. `static/index.html` (added progress bar & duration display)
3. `requirements.txt` (added mutagen library)

### Restart

```bash
sudo systemctl restart homepi.service
```

---

## 📖 How to Use New Features

### View Track Durations

1. Go to web interface
2. Look at song list - durations appear next to each song
3. Look at schedules - durations appear in schedule details

### Monitor Playback Progress

1. Play any song
2. The "Now Playing" card appears automatically
3. Watch the progress bar move
4. See current time vs. total time

### Control Playback Volume

1. While song is playing
2. Use the "Playback Volume" slider in the "Now Playing" card
3. Adjust in real-time without stopping

### Stop Playing Song

1. Click the big **⏹️ Stop** button
2. Or use Pause (⏸️) to pause temporarily

### Check for Schedule Conflicts

**Example:**
```
✅ Good schedule spacing:
- 07:00 - Morning Song (3:24) → ends 07:03
- 07:10 - Next Song (2:15) → starts 07:10
  (7 minute gap - plenty of space!)

⚠️ Potential overlap:
- 07:00 - Long Song (5:30) → ends 07:05:30
- 07:05 - Next Song (3:00) → starts 07:05
  (Second song starts while first is still playing!)
```

---

## 🎯 Best Practices

### For Daily Schedules

- ✅ **DO:** Leave repeat **unchecked**
- ✅ **DO:** Check track durations to avoid overlaps
- ✅ **DO:** Leave 1-2 minute gaps between schedules

**Example Good Schedule:**
```
06:00 AM - Gentle Wake Up (3:24) - Repeat OFF
06:30 AM - Morning Energy (2:45) - Repeat OFF
07:00 AM - Breakfast Vibes (4:12) - Repeat OFF
```

### For Alarms

- ✅ **DO:** Enable repeat if you want it to keep playing
- ✅ **DO:** Test volume levels first
- ✅ **DO:** Make sure you can reach the Stop button!

**Example Alarm:**
```
07:00 AM - WAKE UP ALARM (2:30) - Repeat ON ✅
→ Will play on loop until you manually stop it
```

### For Background Music

- ✅ **DO:** Use longer tracks
- ✅ **DO:** Space them appropriately
- ❌ **DON'T:** Use repeat (unless you want same song forever!)

---

## 📊 Technical Details

### Duration Detection

- Uses **mutagen** library
- Supports: MP3, WAV, OGG, M4A, FLAC
- Reads ID3 tags and audio metadata
- Fallback: Shows "Unknown" if can't detect

### Progress Tracking

- Backend tracks start time + duration
- Frontend calculates position every 2 seconds
- Progress bar updates smoothly
- Time format: M:SS (e.g., 3:24)

### Volume Control

- **Default Volume:** Sets volume for all new playbacks
- **Playback Volume:** Controls currently playing song only
- Both sliders sync automatically

---

## 🐛 Troubleshooting

### Duration shows "Unknown"

**Cause:** File doesn't have metadata or unsupported format

**Fix:**
1. Re-download the file
2. Convert to MP3 with proper encoding
3. Or just ignore - it still plays fine!

### Progress bar doesn't move

**Cause:** Duration couldn't be detected

**Result:** Bar stays at 0%, but song still plays normally

### Schedule times look wrong

**Tip:** Times are in 24-hour format
- 07:00 = 7:00 AM
- 19:00 = 7:00 PM

---

## ✅ Summary

**What You Get:**

1. ✅ **Clear repeat explanation** - No more confusion!
2. ✅ **Track durations everywhere** - Plan your schedules
3. ✅ **Live progress bar** - See where you are in the song
4. ✅ **Playback volume control** - Adjust on the fly
5. ✅ **Better buttons** - "Play Once" vs "Loop"
6. ✅ **Conflict detection** - Spot overlapping schedules

**Now you can:**
- Know exactly how long each song is
- Plan schedules without overlaps
- See playback progress in real-time
- Control volume while playing
- Understand what "repeat" actually does!

Enjoy your improved HomePi! 🎵

