# Sense HAT Joystick Controls

## Overview

The Sense HAT joystick allows you to control brightness and volume directly from the device, without needing to access the web interface!

## Controls

### 🔆 Brightness Control

**UP Button** - Increase brightness
- Toggles from low-light mode to full brightness
- Shows sun icon with brightness indicator
- Overlay displays for 2 seconds

**DOWN Button** - Decrease brightness  
- Toggles from full brightness to low-light mode
- Shows sun icon with brightness indicator
- Overlay displays for 2 seconds

### 🔊 Volume Control

**RIGHT Button** - Increase volume (+10%)
- Increases by 10% steps
- Max volume: 100%
- Shows speaker icon with volume bar
- Overlay displays for 2 seconds

**LEFT Button** - Decrease volume (-10%)
- Decreases by 10% steps
- Min volume: 0% (mute)
- Shows speaker icon with volume bar
- Overlay displays for 2 seconds

### ⚪ Middle Button - Dismiss Overlay
- Press center button to immediately dismiss control overlay
- Returns to normal screen rotation

## Visual Feedback

### Brightness Overlay 🌞
When adjusting brightness, you'll see:
- **Sun icon** in the center (brightness changes with setting)
- **Bottom bar** showing brightness level (0-8 pixels)
- **Yellow/orange colors**
- Auto-dismisses after 2 seconds

### Volume Overlay 🔊
When adjusting volume, you'll see:
- **Speaker icon** on the left
- **Right column bar** showing volume level (0-100%)
- **Blue speaker, green volume bar**
- Auto-dismisses after 2 seconds

## Display Rotation

The display is **rotated 180 degrees** to match your device orientation. If the icons appear upside down, the rotation setting can be adjusted in `display_manager.py`:

```python
display.rotation = 180  # Change to 0, 90, or 270 if needed
```

## Normal Screen Rotation

When not adjusting controls, the display cycles through 4 screens every 5 seconds:

1. **Hourglass** ⏳ - Countdown to next schedule
2. **Music Note** 🎵 - Playing status (pulsing when active)
3. **Temperature/Humidity Bars** 🌡️ - Environmental sensors
4. **Heart** ❤️ - Idle/decorative (pulsing)

## Tips

### Quick Access
- No need to reach for your phone/laptop
- Control settings while looking at the device
- Visual confirmation of current settings

### Brightness Levels
- **Low-light**: Perfect for nighttime use
- **Full brightness**: Better visibility in daylight

### Volume Adjustments
- 10% steps make it easy to fine-tune
- Can mute completely (0%)
- Changes apply immediately to playback

### Overlay Priority
- Control overlays take priority over normal screens
- Normal rotation resumes after 2 seconds
- Press middle button to dismiss immediately

## Troubleshooting

### Joystick Not Responding
1. Check Sense HAT connection
2. Verify joystick is enabled in software
3. Restart service: `sudo systemctl restart homepi.service`
4. Check logs: `sudo journalctl -u homepi.service -f`

### Wrong Display Orientation
Edit `/home/mujadded/homepi/display_manager.py`:
```python
display.rotation = 180  # Try 0, 90, 180, or 270
```

### Brightness Changes Don't Apply
- Low-light mode only has 2 levels (low/high)
- Changes are immediate but subtle
- Try in a dark room to see the difference

### Volume Changes Don't Work
- Ensure audio is initialized properly
- Check mixer isn't muted in system settings
- Verify pygame mixer is working

## Implementation Details

### Joystick Event Handling
- Events are checked every second in display loop
- Only `ACTION_PRESSED` events are processed
- Non-blocking design (doesn't interfere with display updates)

### Brightness Control
- Uses Sense HAT's `low_light` property
- Two modes: low (True) and normal (False)
- Instant switching between modes

### Volume Control
- Directly calls pygame mixer's `set_volume()`
- Range: 0.0 to 1.0 (displayed as 0-100%)
- Changes persist for current session

### Overlay System
- Temporary override of normal display
- Time-based auto-dismiss (2 seconds)
- Manual dismiss with middle button
- Thread-safe implementation

## Future Enhancements

Potential additions:
1. **More brightness levels** - Fine-grained control with multiple steps
2. **Playback control** - Play/pause with middle button
3. **Skip tracks** - Use left/right when music is playing
4. **Show current time** - Display clock on specific button
5. **Toggle screens** - Manually switch between display modes
6. **Settings menu** - Navigate through options with joystick

## Examples

### Scenario 1: Movie Night
Problem: Display too bright in dark room
- Press **DOWN** button
- See sun icon dim
- Overlay shows lower brightness
- Room-friendly brightness applied!

### Scenario 2: Music Too Loud
Problem: Volume too high
- Press **LEFT** button 2-3 times
- See speaker icon with decreasing bar
- Volume reduced by 20-30%
- Perfect listening level!

### Scenario 3: Quick Adjustment
Problem: Need to change settings quickly
- Press **UP/DOWN** or **LEFT/RIGHT**
- Verify change on display
- Press **MIDDLE** to dismiss immediately
- Continue with your task

## Summary

The joystick provides:
- ✅ **Brightness control** (Up/Down)
- ✅ **Volume control** (Left/Right)
- ✅ **Visual feedback** (animated overlays)
- ✅ **180° rotation** (proper orientation)
- ✅ **Auto-dismiss** (2-second timeout)
- ✅ **Manual dismiss** (middle button)
- ✅ **Non-intrusive** (returns to normal screens)
- ✅ **Real-time updates** (instant feedback)

No web interface needed for common adjustments! 🎮

