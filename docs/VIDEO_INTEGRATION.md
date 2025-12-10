# Video & Image Playback Integration

## Overview
Gestures can now include synchronized video and image playback. Media displays on screen while the robot performs physical movements.

## Setup
Install VLC support:
```bash
pip install python-vlc
```

Also requires VLC media player installed on the system.

## Pre-configured Media Gestures

### 1. Countdown Gesture
Plays countdown video with celebratory arm movements.

**File**: `static/media/video/countdown_video.mp4`

**Usage**:
```json
{"action": "gesture", "gesture": "countdown_gesture"}
```

### 2. Show Diamond
Displays diamond image for specified duration.

**File**: `static/media/image/diamond.jpeg`

**Usage**:
```json
{"action": "gesture", "gesture": "show_diamond"}
```

With custom duration:
```json
{"action": "gesture", "gesture": "show_diamond", "params": {"duration": 5.0}}
```

### 3. Show Star
Displays star image for specified duration.

**File**: `static/media/image/star.jpeg`

**Usage**:
```json
{"action": "gesture", "gesture": "show_star"}
```

With custom duration:
```json
{"action": "gesture", "gesture": "show_star", "params": {"duration": 5.0}}
```

## Media File Setup

1. Place your files in the correct directories:
   ```
   static/
   └── media/
       ├── video/
       │   └── countdown_video.mp4
       └── image/
           ├── diamond.jpeg
           └── star.jpeg
   ```

2. The gestures will automatically find and play these files.

## Command Line Usage

```bash
# Interactive mode
python robot_client.py --interactive

# Then send commands:
gesture countdown_gesture
gesture show_diamond
gesture show_star
```

## Usage

### From Client
Send a WebSocket message with video parameters:

```json
{
  "action": "gesture",
  "gesture": "gesture_with_video",
  "params": {
    "video_path": "/path/to/your/video.mp4"
  }
}
```

### From Python
```python
from robot_gestures import execute_gesture

# Execute gesture with video
result = execute_gesture("gesture_with_video", video_path="/path/to/video.mp4")
```

### Command Line Client
```bash
# Not yet supported directly - send via interactive mode:
python robot_client.py --interactive

# Then enter:
{"action": "gesture", "gesture": "gesture_with_video", "params": {"video_path": "/path/to/video.mp4"}}
```

## Creating Custom Video Gestures

Add to `robot_gestures.py`:

```python
def my_custom_video_gesture(self, video_path=None):
    """Custom gesture with video."""
    
    # Start video (non-blocking)
    video_thread = None
    if MEDIA_AVAILABLE and video_path and media_player:
        video_thread = media_player.play_video(
            video_path=video_path,
            fullscreen=True,
            muted=False,
            blocking=False
        )
    
    # Perform gesture movements
    if not MOTORS_AVAILABLE:
        print("[SIMULATION] Performing gesture")
        time.sleep(3.0)
    else:
        # Your motor commands here
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        # ... more movements
        time.sleep(0.5)
    
    # Wait for video to complete
    if video_thread:
        video_thread.join()
```

Register in `GESTURES` dict:
```python
GESTURES = {
    # ... existing gestures
    'my_custom_video_gesture': gesture_controller.my_custom_video_gesture,
}
```

## Media Player Options

From `media_player.py`:

```python
media_player.play_video(
    video_path="/path/to/video.mp4",
    fullscreen=True,   # Fullscreen mode (default: True)
    muted=True,        # Mute audio (default: True)
    blocking=True      # Wait for video to finish (default: True)
)
```

## Notes

- Videos play in a separate thread to avoid blocking gesture execution
- Set `blocking=False` to let gesture and video run in parallel
- Set `blocking=True` to wait for video before continuing
- Media player automatically stops all videos on cleanup
- In simulation mode (no VLC), logs show what would play
- Supports any video format VLC supports (mp4, avi, mov, etc.)
