# Configuration Guide

## Environment Variables

All robot control system settings can be configured using environment variables in a `.env` file.

### Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` to customize your settings:**
   ```bash
   nano .env
   # or
   notepad .env
   ```

3. **Configuration is automatically loaded** when you run the server, client, or monitor.

---

## Available Settings

### Server Configuration

**`SERVER_HOST`** (default: `0.0.0.0`)
- Host address for the server to listen on
- `0.0.0.0` - Listen on all network interfaces (production)
- `localhost` - Listen only on local machine (testing)
- Specific IP - Listen on specific interface

**`SERVER_PORT`** (default: `8765`)
- Port number for the WebSocket server
- Must be available (not in use by another service)
- Range: 1024-65535 recommended

### Client Configuration

**`CLIENT_HOST`** (default: `localhost`)
- Default host for client and monitor to connect to
- Use `localhost` for local testing
- Use robot's IP address for remote connection

**`CLIENT_PORT`** (default: `8765`)
- Default port for client and monitor to connect to
- Must match the server port

### Monitoring Configuration

**`MONITOR_INTERVAL`** (default: `5`)
- Default interval in seconds for continuous monitoring
- Range: 1-3600 (1 second to 1 hour)

### Logging Configuration

**`LOG_LEVEL`** (default: `INFO`)
- Logging verbosity level
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `DEBUG` - Most verbose (useful for development)
- `INFO` - Standard logging (recommended)
- `WARNING` - Only warnings and errors
- `ERROR` - Only errors
- `CRITICAL` - Only critical errors

---

## Example Configurations

### Development Setup
```env
SERVER_HOST=localhost
SERVER_PORT=8765
CLIENT_HOST=localhost
CLIENT_PORT=8765
MONITOR_INTERVAL=2
LOG_LEVEL=DEBUG
```

### Production Setup (Raspberry Pi)
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8765
CLIENT_HOST=192.168.1.100
CLIENT_PORT=8765
MONITOR_INTERVAL=10
LOG_LEVEL=INFO
```

### Testing with Custom Port
```env
SERVER_HOST=localhost
SERVER_PORT=9000
CLIENT_HOST=localhost
CLIENT_PORT=9000
MONITOR_INTERVAL=5
LOG_LEVEL=INFO
```

---

## Command Line Override

Environment variables serve as **defaults**, but you can override them using command-line arguments:

### Server
```bash
# Use .env defaults
python3 robot_server.py

# Override host (still uses .env port)
python3 robot_server.py --host 192.168.1.100

# Override port (still uses .env host)
python3 robot_server.py --port 9000

# Override both
python3 robot_server.py --host 0.0.0.0 --port 9000

# Use localhost regardless of .env
python3 robot_server.py --local
```

### Client
```bash
# Use .env defaults
python3 robot_client.py

# Override URI
python3 robot_client.py --uri ws://192.168.1.100:9000

# Demo with .env defaults
python3 robot_client.py --demo
```

### Monitor
```bash
# Use .env defaults
python3 robot_monitor.py

# Override URI
python3 robot_monitor.py --uri ws://192.168.1.100:9000

# Override interval
python3 robot_monitor.py --interval 10

# Override both
python3 robot_monitor.py --uri ws://robot:8765 --interval 15
```

---

## How It Works

1. **Priority Order:**
   - Command-line arguments (highest priority)
   - Environment variables from `.env` file
   - Hardcoded defaults (fallback)

2. **Loading Process:**
   ```python
   # Server loads .env on startup
   from dotenv import load_dotenv
   load_dotenv()
   
   # Then reads environment variables
   host = os.getenv('SERVER_HOST', '0.0.0.0')
   port = int(os.getenv('SERVER_PORT', '8765'))
   ```

3. **Command-line overrides:**
   ```bash
   # This uses .env HOST but overrides PORT
   python3 robot_server.py --port 9000
   ```

---

## Troubleshooting

### `.env` file not found
**Problem:** Server can't find `.env` file  
**Solution:** 
```bash
# Check file exists
ls -la .env

# Create from example
cp .env.example .env
```

### Settings not applied
**Problem:** Changes to `.env` not taking effect  
**Solution:**
```bash
# 1. Restart the server/client
# 2. Check syntax (no spaces around =)
SERVER_HOST=localhost  # ✓ Correct
SERVER_HOST = localhost  # ✗ Wrong

# 3. Verify file is in same directory as Python scripts
```

### Port already in use
**Problem:** `Address already in use` error  
**Solution:**
```bash
# Change port in .env
SERVER_PORT=9000

# Or override on command line
python3 robot_server.py --port 9000
```

### Can't connect
**Problem:** Client can't connect to server  
**Solution:**
```bash
# 1. Verify server is running
ps aux | grep robot_server

# 2. Check CLIENT_HOST matches server location
CLIENT_HOST=192.168.1.100  # Use server's IP

# 3. Check CLIENT_PORT matches SERVER_PORT
CLIENT_PORT=8765

# 4. Test connection
ping 192.168.1.100
nc -zv 192.168.1.100 8765
```

---

## Best Practices

### Development
- Use `localhost` for both server and client
- Use `DEBUG` log level
- Use short monitor intervals (2-5 seconds)

### Production
- Use `0.0.0.0` for server (all interfaces)
- Use `INFO` or `WARNING` log level
- Use longer monitor intervals (10-30 seconds)
- Document your configuration in comments

### Security
- Don't commit `.env` with production credentials
- Keep `.env.example` updated with all options
- Use `.gitignore` to exclude `.env`:
  ```gitignore
  .env
  ```

### Version Control
```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Keep example file for documentation
git add .env.example
git commit -m "Add configuration example"
```

---

## Configuration File Location

The `.env` file should be in the **same directory** as the Python scripts:

```
mirrly-study1-robot/
├── .env                  ← Your custom config
├── .env.example          ← Template/documentation
├── robot_server.py
├── robot_client.py
├── robot_monitor.py
└── robot_gestures.py
```

---

## Quick Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `SERVER_HOST` | `0.0.0.0` | Server listen address |
| `SERVER_PORT` | `8765` | Server port |
| `CLIENT_HOST` | `localhost` | Client connect address |
| `CLIENT_PORT` | `8765` | Client connect port |
| `MONITOR_INTERVAL` | `5` | Monitor check interval (sec) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Advanced Usage

### Multiple Environments

Create different `.env` files for different environments:

```bash
# Development
.env.dev

# Production
.env.prod

# Testing
.env.test
```

Load specific file:
```bash
# Copy appropriate config
cp .env.prod .env

# Or set in script
python3 robot_server.py
```

### Environment-specific Settings

```env
# .env.dev
SERVER_HOST=localhost
LOG_LEVEL=DEBUG

# .env.prod
SERVER_HOST=0.0.0.0
LOG_LEVEL=WARNING
```

---

## Installation

Don't forget to install the required dependency:

```bash
pip install python-dotenv
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Summary

✅ **Easy Configuration** - Edit `.env` file instead of changing code  
✅ **Flexible** - Command-line can override `.env` settings  
✅ **Portable** - Same code works in dev/test/production  
✅ **Documented** - `.env.example` shows all options  
✅ **Secure** - Keep `.env` out of version control  

**Start with:** Copy `.env.example` to `.env` and customize as needed!
