# 📚 HomePi Documentation Guide

## Quick Navigation

### 🚀 Getting Started
- **[README.md](README.md)** - Main project overview and setup
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup guide

### 📝 All Features & Updates
- **[CHANGELOG.md](CHANGELOG.md)** - Complete list of all features and improvements

### 🔵 Bluetooth Setup
- **[BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md)** - General Bluetooth speaker setup
- **[PIPEWIRE_BLUETOOTH.md](PIPEWIRE_BLUETOOTH.md)** - Specific guide for PipeWire systems

### 📦 Installation Files
- **requirements.txt** - Python dependencies

---

## 📖 What to Read

### If you're NEW:
1. Read **README.md** - Understand what HomePi is
2. Follow **QUICKSTART.md** - Get up and running
3. If using Bluetooth: **BLUETOOTH_SETUP.md**

### If you're UPDATING:
1. Read **CHANGELOG.md** - See all new features
2. Look for "Installation" sections
3. Copy required files and restart

### If you have PROBLEMS:
1. Check **CHANGELOG.md** "Troubleshooting" section
2. Check **BLUETOOTH_SETUP.md** if Bluetooth issues
3. Look at service logs: `sudo journalctl -u homepi.service -f`

---

## 🎯 Quick Links by Topic

### Installation
- Fresh install → README.md
- Quick setup → QUICKSTART.md
- Bluetooth → BLUETOOTH_SETUP.md

### Features
- All features → CHANGELOG.md
- Track durations → CHANGELOG.md (Section 5)
- Progress bar → CHANGELOG.md (Section 6)
- End times → CHANGELOG.md (Section 7)
- Cascade delete → CHANGELOG.md (Section 8)

### Troubleshooting
- General issues → CHANGELOG.md (Troubleshooting section)
- Bluetooth issues → BLUETOOTH_SETUP.md
- PipeWire specific → PIPEWIRE_BLUETOOTH.md

---

## 📂 File Structure

```
homepi/
├── DOCS.md              ← You are here
├── README.md            ← Project overview
├── QUICKSTART.md        ← Quick setup
├── CHANGELOG.md         ← All features (read this!)
├── BLUETOOTH_SETUP.md   ← Bluetooth guide
├── PIPEWIRE_BLUETOOTH.md ← PipeWire guide
├── requirements.txt     ← Dependencies
├── app.py              ← Backend
├── static/
│   └── index.html      ← Frontend
├── songs/              ← Your music
└── backups/            ← Schedule backups
```

---

## 💡 Tips

- **CHANGELOG.md is your friend** - It has everything!
- Bluetooth issues? Check both Bluetooth docs
- Always read warnings before deleting songs
- Check the health dashboard regularly
- Backups are automatic (3 AM daily)

---

## 🎉 That's It!

You now have:
- ✅ 6 documentation files (down from 13!)
- ✅ Everything organized by purpose
- ✅ Clear navigation
- ✅ One place for all features (CHANGELOG.md)

Happy scheduling! 🎵

