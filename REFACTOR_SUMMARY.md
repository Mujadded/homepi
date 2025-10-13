# Refactor Summary: I/O Device Mode

## Overview

HomePi has been successfully refactored from a monolithic system to an **I/O-only device architecture**. The Raspberry Pi now focuses exclusively on input/output operations while the Jetson Orin handles all AI processing and detection logic.

---

## What Changed

### Architecture Transformation

**Before:**
```
Raspberry Pi: Camera → Detection → Decision → Action
Jetson Orin: AI Inference Service (passive)
```

**After:**
```
Raspberry Pi: Camera → Stream → Execute Actions (I/O only)
Jetson Orin: Request Frames → Detect → Decide → Command Pi
```

---

## Files Modified

### 1. `app.py`
**Changes:**
- Added 5 new webhook/API endpoints for Jetson integration:
  - `GET /api/camera/frame` - Stream camera frames to Jetson
  - `POST /api/webhook/detection` - Receive detection results from Jetson
  - `POST /api/pantilt/command` - Execute Pan-Tilt commands from Jetson
  - `POST /api/telegram/send` - Send Telegram notifications from Jetson
  - `POST /api/flipper/trigger` - Trigger Flipper Zero actions from Jetson

- Modified security system initialization:
  - Changed from `init_security()` to `init_security_io_mode()`
  - Removed automatic detection loop start
  - Added I/O mode status messages

**Lines Added:** ~240 lines

---

### 2. `security_manager.py`
**Changes:**
- Added `init_security_io_mode()` function:
  - Initializes camera, Pan-Tilt, Flipper, Telegram
  - Does NOT start detection loop
  - Does NOT initialize object_detector

- Deprecated `init_security()` function:
  - Now redirects to `init_security_io_mode()`
  - Logs deprecation warning

- Added `save_detection_from_webhook()` function:
  - Processes detection data from Jetson webhook
  - Decodes and saves base64 images
  - Stores detections in local database

**Lines Added:** ~70 lines

---

### 3. `camera_manager.py`
**Changes:**
- Added `get_single_frame_encoded()` function:
  - Captures single frame
  - Converts RGB to BGR
  - Encodes as JPEG
  - Returns base64 string

**Lines Added:** ~25 lines

---

### 4. `telegram_notifier.py`
**Changes:**
- Modified `send_notification()` function:
  - Added `image_data` parameter
  - Supports base64-encoded images
  - Supports file path images
  - Falls back to text-only if image fails

- Added `_send_photo_bytes_async()` function:
  - Sends photos from BytesIO objects
  - Handles base64-decoded images

**Lines Added:** ~40 lines

---

### 5. `config.json`
**Changes:**
- Added `jetson` configuration section:
  ```json
  "jetson": {
    "url": "http://192.168.0.105:5001",
    "webhook_enabled": true,
    "frame_streaming": true,
    "webhook_url": "http://192.168.0.26:5000/api/webhook/detection"
  }
  ```

- Updated `security` section:
  ```json
  "security": {
    "enabled": true,
    "mode": "io_only",
    "local_detection": false,
    ...
  }
  ```

---

### 6. `API_DOCUMENTATION.md`
**Changes:**
- Added "Raspberry Pi I/O APIs (Jetson Integration)" section
  - Documented all 5 new endpoints
  - Added usage examples
  - Included request/response formats

- Added "Jetson Orin APIs (Expected Implementation)" section
  - Documented expected Jetson endpoints
  - Provided API contract

- Updated "Architecture" section
  - New I/O Device Mode diagram
  - Updated data flow
  - Clarified component responsibilities

- Updated "Configuration" section
  - Added Jetson configuration
  - Added I/O mode flags

**Lines Added:** ~250 lines

---

### 7. `JETSON_INTEGRATION.md` (New File)
**Purpose:** Comprehensive guide for Jetson Orin integration

**Contents:**
- Architecture overview with diagrams
- Complete API contract documentation
- Sample detection loop implementation
- Database synchronization strategy
- Error handling and retry logic
- Configuration examples
- Testing procedures
- Performance considerations
- Troubleshooting guide

**Lines:** ~650 lines

---

## Files Unchanged

The following files remain unchanged and continue to work as before:

- `static/index.html` - Music scheduler UI
- `static/security.html` - Security UI (data source changes but UI stays same)
- `static/security.js` - Minor updates only (if any)
- `pantilt_controller.py` - No changes
- `flipper_controller.py` - No changes
- `camera_manager.py` - Only additions, no modifications
- Music scheduler logic - Completely unchanged

---

## New API Endpoints

### For Jetson to Call (Raspberry Pi)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/camera/frame` | GET | Get camera frame for detection |
| `/api/webhook/detection` | POST | Receive detection results |
| `/api/pantilt/command` | POST | Control Pan-Tilt HAT |
| `/api/telegram/send` | POST | Send Telegram notification |
| `/api/flipper/trigger` | POST | Trigger Flipper Zero action |

### Expected from Jetson (To Implement)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/status` | GET | Health check |
| `/detections` | GET | Query detection history |
| `/detections/{id}` | GET | Get specific detection |

---

## Workflow Changes

### Old Workflow (Monolithic)

1. Raspberry Pi captures frame
2. Raspberry Pi sends frame to Jetson for inference
3. Jetson returns detection results
4. Raspberry Pi processes results
5. Raspberry Pi decides actions
6. Raspberry Pi executes actions

### New Workflow (I/O Device)

1. **Jetson** requests frame from Raspberry Pi
2. **Jetson** runs detection and analysis
3. **Jetson** decides what actions to take
4. **Jetson** sends detection + action to Raspberry Pi
5. **Raspberry Pi** executes requested actions
6. **Raspberry Pi** caches detection for web UI

---

## Benefits

### 1. Clear Separation of Concerns
- Raspberry Pi: I/O operations (what it's good at)
- Jetson Orin: AI processing (what it's good at)

### 2. Easier Development
- Jetson project can be developed independently
- No need to coordinate code changes between devices
- Clear API contract

### 3. Better Performance
- Raspberry Pi remains responsive (no heavy processing)
- Jetson can optimize detection loop independently
- No blocking operations on Raspberry Pi

### 4. Scalability
- Easy to upgrade either component independently
- Can add multiple Raspberry Pi I/O devices to one Jetson
- Can distribute processing across multiple Jetsons

### 5. Flexibility
- Jetson can implement any detection logic
- Easy to switch AI models
- Custom recognition models handled entirely on Jetson

---

## Database Architecture

### Dual Database System

**Raspberry Pi Database (`security.db`):**
- Purpose: Local cache for web UI
- Populated by: Jetson webhook calls
- Contains: Recent detections for display
- Size: Limited, can be pruned

**Jetson Orin Database (Your Implementation):**
- Purpose: Full detection history and analytics
- Populated by: Detection loop
- Contains: All detections, analytics, training data
- Size: Unlimited, full history

**Synchronization:**
- Real-time: Jetson pushes to Pi via webhook
- On-demand: Pi can query Jetson for full history
- Conflict resolution: Jetson is source of truth

---

## Testing

### Test Camera Frame Endpoint

```bash
curl http://192.168.0.26:5000/api/camera/frame | jq .
```

Expected: JSON with base64-encoded frame

### Test Webhook

```bash
curl -X POST http://192.168.0.26:5000/api/webhook/detection \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-10-12T20:15:30",
    "object_type": "car",
    "confidence": 0.87,
    "bbox": [0.3, 0.2, 0.7, 0.8],
    "car_id": "test_car",
    "action": null
  }'
```

Expected: `{"success": true, "detection_id": 1, "message": "Detection processed"}`

### Test Pan-Tilt

```bash
curl -X POST http://192.168.0.26:5000/api/pantilt/command \
  -H "Content-Type: application/json" \
  -d '{"action": "move", "pan": 10, "tilt": -5, "speed": 5}'
```

Expected: `{"success": true, "position": {"pan": 10, "tilt": -5}}`

### Test Telegram

```bash
curl -X POST http://192.168.0.26:5000/api/telegram/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Test from Jetson"}'
```

Expected: `{"success": true, "message": "Notification sent"}`

---

## Migration Notes

### What Still Works

- Music scheduler (completely unchanged)
- Web UI (same interface, data from webhook)
- Live camera feed (still from Pi camera)
- Pan-Tilt manual controls (now via command API)
- Telegram notifications (now via send API)
- Flipper Zero automation (now via trigger API)

### What Changed

- Detection loop now runs on Jetson
- Object detector removed from Raspberry Pi
- Security system initialization (I/O mode only)
- API endpoints (new webhook/command endpoints)

### What to Implement on Jetson

1. Detection loop (request frames, run AI, send results)
2. Object tracking logic (send Pan-Tilt commands)
3. Decision making (determine actions based on detections)
4. Custom car/person recognition
5. Full detection database
6. Optional: Status/history query endpoints

---

## Performance Expectations

### Bandwidth

- Frame size: ~50-100 KB (JPEG quality 85)
- At 10 FPS: ~500 KB/s to 1 MB/s
- Gigabit Ethernet recommended

### Latency

- Frame request: 20-50 ms
- Detection (Jetson): 30-100 ms
- Webhook: 10-30 ms
- **Total loop: 100-200 ms (5-10 FPS achievable)**

### Optimization Tips

1. Reduce frame resolution (640x480 vs 1920x1080)
2. Lower JPEG quality (70 vs 85)
3. Skip frames if detection is slow
4. Use HTTP keep-alive connections
5. Batch multiple detections in one webhook

---

## Next Steps

### For Raspberry Pi (Complete ✓)

- ✓ Add webhook endpoints
- ✓ Add camera frame endpoint
- ✓ Add Pan-Tilt command endpoint
- ✓ Add Telegram send endpoint
- ✓ Add Flipper trigger endpoint
- ✓ Update configuration
- ✓ Update documentation

### For Jetson Orin (To Do)

- [ ] Implement detection loop
- [ ] Add frame request logic
- [ ] Add webhook posting
- [ ] Implement object tracking
- [ ] Add custom car recognition
- [ ] Create detection database
- [ ] Optional: Add status/history endpoints

---

## Documentation

All documentation has been updated:

1. **JETSON_INTEGRATION.md** - Comprehensive integration guide
2. **API_DOCUMENTATION.md** - Complete API reference
3. **config.json** - Updated with Jetson configuration
4. **REFACTOR_SUMMARY.md** - This file

---

## Support

For questions or issues:

1. Review `JETSON_INTEGRATION.md` for detailed integration guide
2. Check `API_DOCUMENTATION.md` for API reference
3. Test endpoints with curl to verify functionality
4. Check logs: `sudo journalctl -u homepi.service -f`
5. Verify network connectivity between Pi and Jetson

---

## Version

**Refactor Version:** 2.1.0  
**Date:** October 12, 2025  
**Architecture:** I/O Device Mode  
**Status:** Complete and Ready for Jetson Integration

