"""
Robot Server Status Monitor
Shows real-time server stats and health checks.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Error: websockets module not found. Install with: pip install websockets")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv module not found. Install with: pip install python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class ServerMonitor:
    """Monitor robot server health and status."""
    
    def __init__(self, uri: str = None):
        if uri is None:
            host = os.getenv('CLIENT_HOST', 'localhost')
            port = os.getenv('CLIENT_PORT', '8765')
            uri = f"ws://{host}:{port}"
        self.uri = uri
        self.websocket = None
        self.stats = {
            'total_commands': 0,
            'successful_gestures': 0,
            'failed_gestures': 0,
            'last_gesture': None,
            'last_error': None,
        }
    
    async def connect(self) -> bool:
        """Connect to server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✓ Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
    
    async def send_command(self, command: dict) -> dict:
        """Send command and get response."""
        try:
            await self.websocket.send(json.dumps(command))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def health_check(self) -> dict:
        """Perform server health check."""
        checks = {
            'timestamp': datetime.now().isoformat(),
            'connection': 'failed',
            'server_responsive': False,
            'gestures_available': 0,
            'errors': []
        }
        
        # Check connection
        if self.websocket and not self.websocket.closed:
            checks['connection'] = 'connected'
        
        # Check server responsiveness
        response = await self.send_command({'action': 'status'})
        if response.get('status') == 'success':
            checks['server_responsive'] = True
        else:
            checks['errors'].append('Server not responding to status command')
        
        # Check available gestures
        response = await self.send_command({'action': 'list'})
        if response.get('status') == 'success':
            checks['gestures_available'] = response.get('count', 0)
        else:
            checks['errors'].append('Could not retrieve gesture list')
        
        return checks
    
    def print_status(self, status: dict):
        """Pretty print status information."""
        print("\n" + "="*50)
        print("SERVER STATUS CHECK")
        print("="*50)
        print(f"Timestamp: {status['timestamp']}")
        print(f"Connection: {status['connection']}")
        print(f"Server Responsive: {'✓' if status['server_responsive'] else '✗'}")
        print(f"Gestures Available: {status['gestures_available']}")
        
        if status['errors']:
            print("\nErrors:")
            for error in status['errors']:
                print(f"  - {error}")
        else:
            print("\n✓ All checks passed")
        print("="*50 + "\n")
    
    async def continuous_monitor(self, interval: int = 5):
        """Continuously monitor server health."""
        print(f"Monitoring server every {interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                status = await self.health_check()
                self.print_status(status)
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")


async def main():
    """Main entry point."""
    import argparse
    
    # Get defaults from environment
    default_host = os.getenv('CLIENT_HOST', 'localhost')
    default_port = os.getenv('CLIENT_PORT', '8765')
    default_uri = f"ws://{default_host}:{default_port}"
    default_interval = int(os.getenv('MONITOR_INTERVAL', '5'))
    
    parser = argparse.ArgumentParser(description='Robot Server Status Monitor')
    parser.add_argument('--uri', default=default_uri, help=f'Server URI (default: {default_uri} from .env)')
    parser.add_argument('--interval', type=int, default=default_interval, help=f'Check interval (default: {default_interval}s from .env)')
    parser.add_argument('--once', action='store_true', help='Check once and exit')
    
    args = parser.parse_args()
    
    monitor = ServerMonitor(uri=args.uri)
    
    try:
        if not await monitor.connect():
            sys.exit(1)
        
        if args.once:
            status = await monitor.health_check()
            monitor.print_status(status)
        else:
            await monitor.continuous_monitor(interval=args.interval)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await monitor.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
