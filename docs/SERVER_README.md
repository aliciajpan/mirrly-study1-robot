# Robot Control System - Server Architecture

This document describes the modular WebSocket-based server architecture for remote robot control.

## System Architecture

```
┌─────────────────────┐
│   Remote Client     │
│  (External System)  │
└──────────┬──────────┘
           │ WebSocket
           │ (JSON Commands)
           ▼
┌─────────────────────┐
│  robot_server.py    │
│  (WebSocket Server) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│robot_gestures.py    │
│(Gesture Library)    │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  Hardware Control Modules│
│  head_control.py         │
│  torso_control.py        │
└──────────────────────────┘
```

## Components

### 1. `robot_gestures.py` - Gesture Library
Contains all robot gesture definitions and motor control logic.

**Key Classes:**
- `GestureController`: Manages all gesture execution
- `GESTURES`: Registry mapping gesture names to methods

**Available Gestures:**
- `center_all` - Reset all motors to center position
- `look_point_left` - Look and point left
- `look_point_right` - Look and point right
- `celebrate_arms_up` - Celebrate with raised arms
- `sad_look_down` - Look down sad expression
- `talking_left_arm` - Talk while gesturing left
- `talking_right_arm` - Talk while gesturing right
- `eyes_left` - Move eyes left only
- `eyes_right` - Move eyes right only

**Functions:**
```python
execute_gesture(gesture_name)        # Execute gesture by name
get_available_gestures()             # Get list of available gestures
gesture_controller.cleanup()         # Release all motors
```

### 2. `robot_server.py` - WebSocket Server
Handles remote client connections and gesture commands with play/pause/restart control.

**Key Classes:**
- `GestureExecutor`: Manages gesture execution state (play/pause/restart)
- `RobotServer`: WebSocket server handling client connections

**Command Protocol:**
```json
{
  "action": "gesture|pause|resume|restart|status|list",
  "gesture": "gesture_name"  // required for action="gesture"
}
```

**Available Actions:**
- `gesture` - Execute gesture (requires `gesture` field)
- `pause` - Pause current gesture
- `resume` - Resume paused gesture
- `restart` - Restart current gesture
- `status` - Get current server status
- `list` - List available gestures

**Response Format:**
```json
{
  "status": "success|error|warning",
  "message": "Human readable message",
  "timestamp": "ISO 8601 timestamp",
  "data": {}  // Action-specific data
}
```

### 3. `robot_client.py` - Test Client
Simple WebSocket client for testing and demonstration.

## Setup & Requirements

### Prerequisites
- Python 3.11.2 (or compatible)
- Raspberry Pi running Raspbian (production)
- `sudo pigpiod` must be running on Raspberry Pi

### Dependencies
```bash
pip install websockets
```

Motor control modules are already included:
- `control_modules/head_control.py` - Dynamixel servo control
- `control_modules/torso_control.py` - GPIO motor control

## Running the Server

### On Raspberry Pi (Production)
```bash
# Start pigpiod daemon (one time per boot)
sudo pigpiod

# Run server (accessible from any network address)
python3 robot_server.py

# Or listen only on localhost
python3 robot_server.py --local

# Custom host/port
python3 robot_server.py --host 0.0.0.0 --port 9000
```

### On Local Machine (Testing)
```bash
python3 robot_server.py --local
```

## Using the Client

### Interactive Mode
```bash
python3 robot_client.py
```

Commands:
- `list` - Show available gestures
- `status` - Show current server status
- `gesture <name>` - Execute gesture (e.g., `gesture look_point_left`)
- `pause` - Pause current gesture
- `resume` - Resume paused gesture
- `restart` - Restart current gesture
- `quit` - Exit

### Demo Mode
```bash
python3 robot_client.py --demo
```

### Execute Single Gesture
```bash
python3 robot_client.py --gesture look_point_right
```

### Connect to Remote Server
```bash
python3 robot_client.py --uri ws://robot-ip:8765
```

## Integration Examples

### Python Client
```python
import asyncio
import json
import websockets

async def control_robot():
    async with websockets.connect('ws://robot-ip:8765') as ws:
        # Execute gesture
        await ws.send(json.dumps({
            'action': 'gesture',
            'gesture': 'celebrate_arms_up'
        }))
        response = json.loads(await ws.recv())
        print(response)
        
        # Pause
        await ws.send(json.dumps({'action': 'pause'}))
        response = json.loads(await ws.recv())
        print(response)

asyncio.run(control_robot())
```

### JavaScript/Node.js Client
```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://robot-ip:8765');

ws.on('open', () => {
  // Execute gesture
  ws.send(JSON.stringify({
    action: 'gesture',
    gesture: 'look_point_left'
  }));
});

ws.on('message', (message) => {
  const response = JSON.parse(message);
  console.log('Response:', response);
});

ws.on('close', () => {
  console.log('Connection closed');
});
```

### HTTP API Integration (Future)
While the current implementation uses WebSocket, it could be extended with a REST API:
```
POST /gesture/{name}       # Execute gesture
POST /control/pause        # Pause
POST /control/resume       # Resume
POST /control/restart      # Restart
GET  /status               # Get status
GET  /gestures             # List gestures
```

## Logging

The server logs all connections and commands to help with debugging:
```
2024-12-06 10:15:23,456 - INFO - Client connected: ('192.168.1.100', 54321)
2024-12-06 10:15:24,123 - INFO - [('192.168.1.100', 54321)] Executing gesture: look_point_left
2024-12-06 10:15:26,789 - INFO - Client disconnected: ('192.168.1.100', 54321)
```

## Design Decisions

### Why WebSocket?
- **Real-time**: Perfect for live robot control with immediate feedback
- **Bidirectional**: Allows command + response in same connection
- **Lower overhead**: Compared to repeated HTTP requests
- **Persistent connection**: Better for continuous monitoring

### Why Python asyncio?
- **Non-blocking**: Supports multiple concurrent clients
- **Standard library**: No additional heavy dependencies
- **Natural async/await**: Cleaner code than callbacks

### Modular Structure
- **Separation of Concerns**: Gestures separate from network logic
- **Reusability**: `robot_gestures.py` can be used without server
- **Testability**: Each module can be tested independently
- **Scalability**: Easy to add new gestures or control modes

## Error Handling

The server gracefully handles:
- Invalid JSON messages
- Unknown actions
- Missing gesture names
- Client disconnections
- Motor errors (logged and reported to client)

All errors return structured responses:
```json
{
  "status": "error",
  "message": "Descriptive error message",
  "timestamp": "ISO 8601"
}
```

## Performance Considerations

- **Gesture execution**: Blocking but non-interrupt (gesture completes fully)
- **Multiple clients**: Each client connection is independent
- **Message buffering**: Small JSON payloads (~100-500 bytes)
- **Latency**: ~50-100ms typical round-trip on local network

## Future Enhancements

1. **Gesture queuing**: Queue multiple gestures for sequential execution
2. **Custom gestures**: Dynamic gesture creation from client
3. **Motion recording**: Record and playback custom motion sequences
4. **Gesture parameters**: Modify speed/intensity per execution
5. **Status streaming**: Stream sensor data to clients in real-time
6. **REST API**: HTTP interface for broader compatibility
7. **Authentication**: Add token-based access control
8. **Persistence**: Save gesture sequences to database

## Troubleshooting

### Server won't start
```bash
# Check if port is already in use
lsof -i :8765

# Kill process on that port
fuser -k 8765/tcp
```

### Client can't connect
```bash
# Test network connectivity
ping robot-ip

# Check server is running
ps aux | grep robot_server.py

# Test with netcat
nc -zv robot-ip 8765
```

### Motor errors
```
# Ensure pigpiod is running (Raspberry Pi)
sudo pigpiod

# Check GPIO permissions
groups $USER  # Should include gpio group
```

## File Structure
```
├── robot_server.py          # WebSocket server (run this on robot)
├── robot_gestures.py        # Gesture library
├── robot_client.py          # Test client
├── control_modules/
│   ├── head_control.py      # Dynamixel servo control
│   └── torso_control.py     # GPIO motor control
└── .github/
    └── copilot-instructions.md  # AI coding guidance
```
