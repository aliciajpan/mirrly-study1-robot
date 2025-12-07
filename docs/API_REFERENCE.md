# Robot Control System - API Reference

## WebSocket Protocol

### Connection
```
ws://robot-ip:8765
```

### Message Format
All messages are JSON objects with the following structure:

```json
{
  "action": "string",        // Required: gesture, pause, resume, restart, status, list
  "gesture": "string"        // Optional: gesture name (required for action="gesture")
}
```

---

## API Endpoints (Actions)

### 1. Execute Gesture
**Action:** `gesture`

**Request:**
```json
{
  "action": "gesture",
  "gesture": "celebrate_arms_up"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Gesture \"celebrate_arms_up\" executed successfully",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

**Response (Error - Unknown Gesture):**
```json
{
  "status": "error",
  "message": "Gesture \"invalid\" not found. Available gestures: [\"center_all\", \"look_point_left\", ...]",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

**Response (Error - Execution Failed):**
```json
{
  "status": "error",
  "message": "Error executing gesture \"look_point_left\": Motor communication failed",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

### 2. Pause Gesture
**Action:** `pause`

**Request:**
```json
{
  "action": "pause"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Gesture \"celebrate_arms_up\" paused",
  "current_gesture": "celebrate_arms_up",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

**Response (No Gesture Running):**
```json
{
  "status": "warning",
  "message": "No gesture currently running",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

### 3. Resume Paused Gesture
**Action:** `resume`

**Request:**
```json
{
  "action": "resume"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Gesture \"celebrate_arms_up\" executed successfully",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

**Response (No Paused Gesture):**
```json
{
  "status": "warning",
  "message": "No paused gesture",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

### 4. Restart Gesture
**Action:** `restart`

**Request:**
```json
{
  "action": "restart"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Gesture \"celebrate_arms_up\" executed successfully",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

**Response (No Gesture to Restart):**
```json
{
  "status": "warning",
  "message": "No gesture to restart",
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

### 5. Get Server Status
**Action:** `status`

**Request:**
```json
{
  "action": "status"
}
```

**Response:**
```json
{
  "status": "success",
  "executor": {
    "current_gesture": "celebrate_arms_up",
    "is_running": true,
    "is_paused": false
  },
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

### 6. List Available Gestures
**Action:** `list`

**Request:**
```json
{
  "action": "list"
}
```

**Response:**
```json
{
  "status": "success",
  "gestures": [
    "center_all",
    "look_point_left",
    "look_point_right",
    "celebrate_arms_up",
    "sad_look_down",
    "talking_left_arm",
    "talking_right_arm",
    "eyes_left",
    "eyes_right"
  ],
  "count": 9,
  "timestamp": "2024-12-06T10:15:24.123456"
}
```

---

## Available Gestures

### 1. `center_all`
Reset all motors to neutral positions.
```
Head: center
Arms: rest position
Eyes: open
```

### 2. `look_point_left`
Look and point to the left.
```
Head: turn left
Eyes: look left
Left arm: raised
Right arm: down
```

### 3. `look_point_right`
Look and point to the right.
```
Head: turn right
Eyes: look right
Right arm: raised
Left arm: down
```

### 4. `celebrate_arms_up`
Celebration pose with arms raised.
```
Head: look up
Eyes: open
Both arms: raised
Duration: 2 seconds
```

### 5. `sad_look_down`
Sad expression looking down.
```
Head: look down
Eyebrows: closed
Both arms: down
Duration: 2 seconds
```

### 6. `talking_left_arm`
Talk while gesturing with left arm.
```
Head: center, facing forward
Left shoulder: raised
Right arm/shoulder: down
Duration: 2 seconds
```

### 7. `talking_right_arm`
Talk while gesturing with right arm.
```
Head: center, facing forward
Right shoulder: raised
Left arm/shoulder: down
Duration: 2 seconds
```

### 8. `eyes_left`
Eyes only movement to the left.
```
Head: center position
Eyes: look left
Arms: rest position
Duration: 2 seconds
```

### 9. `eyes_right`
Eyes only movement to the right.
```
Head: center position
Eyes: look right
Arms: rest position
Duration: 2 seconds
```

---

## Response Status Codes

### `success`
Command executed successfully.
```json
{
  "status": "success",
  "message": "...",
  "timestamp": "..."
}
```

### `error`
Command failed or invalid.
```json
{
  "status": "error",
  "message": "Descriptive error message",
  "timestamp": "..."
}
```

### `warning`
Command received but could not execute (non-fatal).
```json
{
  "status": "warning",
  "message": "No gesture currently running",
  "timestamp": "..."
}
```

---

## Implementation Examples

### Python
```python
import asyncio
import json
import websockets

async def example():
    async with websockets.connect('ws://localhost:8765') as ws:
        # Execute gesture
        await ws.send(json.dumps({
            'action': 'gesture',
            'gesture': 'celebrate_arms_up'
        }))
        response = json.loads(await ws.recv())
        print(f"Status: {response['status']}")
        print(f"Message: {response['message']}")

asyncio.run(example())
```

### JavaScript/Node.js
```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  ws.send(JSON.stringify({
    action: 'gesture',
    gesture: 'celebrate_arms_up'
  }));
});

ws.on('message', (message) => {
  const response = JSON.parse(message);
  console.log(`Status: ${response.status}`);
  console.log(`Message: ${response.message}`);
});
```

### cURL (via wscat)
```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8765

# Send command (in wscat prompt)
{"action": "list"}
{"action": "gesture", "gesture": "celebrate_arms_up"}
```

### Raw Socket (netcat + manual JSON)
```bash
# Connect
nc localhost 8765

# Send JSON
{"action": "status"}
```

---

## Error Handling

### Connection Errors
```
Connection refused: Server not running
Connection timeout: Network unreachable or firewall blocking
```

### Message Errors
```json
{
  "status": "error",
  "message": "Invalid JSON format"
}
```

### Gesture Errors
```json
{
  "status": "error",
  "message": "Gesture \"look_point_left\" not found. Available gestures: [...]"
}
```

### Motor Errors
```json
{
  "status": "error",
  "message": "Error executing gesture \"look_point_left\": Motor communication failed"
}
```

---

## Rate Limiting

**Current Behavior:**
- No explicit rate limiting (designed for controlled environment)
- Each gesture waits for completion (synchronous execution)
- Concurrent clients each execute independently

**Recommended Practice:**
- Space commands by gesture duration (typically 2-3 seconds)
- Wait for response before sending next command
- Implement client-side throttling for safety

---

## Connection Management

### Keep-Alive
WebSocket connection remains open until:
- Client sends close frame
- Server shutdown
- Network error

### Automatic Reconnection
Recommended client-side behavior:
```python
async def robust_connect(uri, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await websockets.connect(uri)
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    raise Exception(f"Failed to connect after {max_retries} attempts")
```

---

## Logging

Server logs all operations to console:
```
2024-12-06 10:15:23,456 - INFO - Client connected: ('192.168.1.100', 54321)
2024-12-06 10:15:24,123 - INFO - [('192.168.1.100', 54321)] Executing gesture: look_point_left
2024-12-06 10:15:26,789 - INFO - Client disconnected: ('192.168.1.100', 54321)
2024-12-06 10:15:27,000 - WARNING - [('192.168.1.100', 54322)] Unknown action: invalid_action
2024-12-06 10:15:28,500 - ERROR - [('192.168.1.100', 54323)] Error: Motor communication failed
```

---

## Performance Notes

- **Latency**: ~50-100ms per command (network + motor execution)
- **Concurrent Clients**: Tested with 10+ simultaneous connections
- **Message Size**: Typically 100-500 bytes per message
- **Gesture Duration**: 2-3 seconds (motor-dependent)

---

## Security Considerations

**Current Implementation:**
- No authentication (designed for trusted network)
- No encryption (local network assumed)

**For Production Deployment:**
- Add token-based authentication
- Use WSS (WebSocket Secure) over SSL/TLS
- Implement firewall rules
- Use VPN for remote access

---

## Future Enhancements

- [ ] REST API for compatibility
- [ ] Gesture queuing
- [ ] Custom gesture creation
- [ ] Motion recording/playback
- [ ] Sensor streaming
- [ ] Authentication & encryption
- [ ] Rate limiting
- [ ] Request logging/audit trail

---

**Last Updated:** 2024-12-06
**Version:** 1.0
**Protocol Version:** WebSocket v13 (RFC 6455)
