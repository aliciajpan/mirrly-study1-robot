# Quick Start Guide - Robot Control Server

## TL;DR - Get Running in 2 Minutes

### On Raspberry Pi (Production)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start pigpiod (required for GPIO)
sudo pigpiod

# 3. Run the server
python3 robot_server.py
```

Server will be accessible at `ws://robot-ip:8765`

### Testing Locally
```bash
# Terminal 1: Start server
python3 robot_server.py --local

# Terminal 2: Run test client
python3 robot_client.py
```

## Command Examples

### Using robot_client.py
```
> list
Available gestures:
  - center_all
  - look_point_left
  - look_point_right
  - celebrate_arms_up
  - sad_look_down
  - talking_left_arm
  - talking_right_arm
  - eyes_left
  - eyes_right

Total: 9 gestures

> gesture celebrate_arms_up
Executing: celebrate_arms_up...
Status: success

> pause
Pause: Gesture "celebrate_arms_up" paused

> resume
Resume: Gesture "celebrate_arms_up" executed successfully

> status
Server Status:
  Current gesture: celebrate_arms_up
  Running: False
  Paused: False

> quit
```

### Direct WebSocket JSON Commands

**Execute Gesture:**
```json
{"action": "gesture", "gesture": "celebrate_arms_up"}
```

**Pause Current Gesture:**
```json
{"action": "pause"}
```

**Resume Paused Gesture:**
```json
{"action": "resume"}
```

**Restart Current Gesture:**
```json
{"action": "restart"}
```

**Get Server Status:**
```json
{"action": "status"}
```

**List Available Gestures:**
```json
{"action": "list"}
```

## Expected Server Responses

### Success
```json
{
  "status": "success",
  "message": "Gesture \"look_point_left\" executed successfully",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

### Error
```json
{
  "status": "error",
  "message": "Gesture \"invalid_gesture\" not found. Available gestures: [...]",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

### Status
```json
{
  "status": "success",
  "executor": {
    "current_gesture": "look_point_left",
    "is_running": true,
    "is_paused": false
  },
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

## Server Modes

### Listen on All Network Interfaces (Production)
```bash
python3 robot_server.py
# or explicitly
python3 robot_server.py --host 0.0.0.0 --port 8765
```

### Listen Only on Localhost (Testing)
```bash
python3 robot_server.py --local
```

### Custom Port
```bash
python3 robot_server.py --port 9000
```

## Client Options

### Interactive Mode (Default)
```bash
python3 robot_client.py
```

### Demo Sequence
```bash
python3 robot_client.py --demo
```

### Single Gesture
```bash
python3 robot_client.py --gesture look_point_right
```

### Connect to Remote Server
```bash
python3 robot_client.py --uri ws://192.168.1.100:8765
```

## Common Issues & Solutions

### ❌ "Failed to open port" / "Permission denied" (head_control.py)
**Solution:** USB Dynamixel adapter might not be connected or driver issue
```bash
# Check connection
ls -la /dev/ttyUSB*

# If not visible, install driver or check USB cable
```

### ❌ "No module named websockets"
**Solution:** Install missing dependency
```bash
pip install websockets
```

### ❌ "Cannot connect to server" (client)
**Solution:** Server not running or wrong address
```bash
# Check if server is running
ps aux | grep robot_server.py

# Test connectivity
ping robot-ip
```

### ❌ "Motor not responding" (Raspberry Pi)
**Solution:** pigpiod not running
```bash
# Start pigpiod
sudo pigpiod

# Verify it's running
ps aux | grep pigpiod
```

### ❌ "Port already in use"
**Solution:** Another process is using port 8765
```bash
# Find process using port
lsof -i :8765

# Kill it (replace PID with actual process ID)
kill -9 <PID>

# Or use different port
python3 robot_server.py --port 9000
```

## File Organization

```
mirrly-study1-robot/
├── robot_server.py          ⭐ Main server (run this)
├── robot_client.py          ⭐ Test client
├── robot_gestures.py        ⭐ Gesture library
├── control_modules/
│   ├── head_control.py      Motor control (don't modify)
│   └── torso_control.py     Motor control (don't modify)
├── SERVER_README.md         Full documentation
├── requirements.txt         Python dependencies
└── QUICKSTART.md           This file
```

## Integration Points

### For External Systems:
Connect via WebSocket to `ws://robot-ip:8765` and send JSON commands.

### Available Gestures:
1. `center_all` - Reset to neutral position
2. `look_point_left` - Look left with arm gesture
3. `look_point_right` - Look right with arm gesture
4. `celebrate_arms_up` - Celebration pose
5. `sad_look_down` - Sad expression
6. `talking_left_arm` - Talk with left arm raised
7. `talking_right_arm` - Talk with right arm raised
8. `eyes_left` - Eyes only movement left
9. `eyes_right` - Eyes only movement right

## Architecture Overview

```
External System (e.g., AI coordinator)
        ↓
    WebSocket
        ↓
  robot_server.py (handles multiple clients)
        ↓
  robot_gestures.py (gesture execution)
        ↓
  Head & Torso Motors (hardware control)
```

## Next Steps

1. **Test the demo:** `python3 robot_client.py --demo`
2. **Read full docs:** See `SERVER_README.md`
3. **Integrate:** Connect your external system via WebSocket
4. **Monitor logs:** Watch server output for debugging

## Support

- Server logs to console (timestamps + client addresses)
- Client provides feedback for each command
- All errors include descriptive messages
- Check `SERVER_README.md` for detailed troubleshooting

---

**Ready to go!** Start with `python3 robot_server.py` on the robot 🤖
