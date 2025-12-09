"""
Simple WebSocket client for testing robot server.
Demonstrates how to interact with the robot control system.
"""

import asyncio
import json
import sys
import os
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


class RobotClient:
    """WebSocket client for robot control."""
    
    def __init__(self, uri: str = None):
        if uri is None:
            host = os.getenv('CLIENT_HOST', 'localhost')
            port = os.getenv('CLIENT_PORT', '8765')
            uri = f"ws://{host}:{port}"
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to robot server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✓ Connected to {self.uri}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
            print("✓ Disconnected")
    
    async def send_command(self, command: dict) -> dict:
        """Send command and get response."""
        try:
            await self.websocket.send(json.dumps(command))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            print(f"✗ Error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def list_gestures(self):
        """List available gestures."""
        response = await self.send_command({'action': 'list'})
        if response['status'] == 'success':
            print("\nAvailable gestures:")
            for gesture in response['gestures']:
                print(f"  - {gesture}")
            print(f"\nTotal: {response['count']} gestures\n")
        else:
            print(f"Error: {response['message']}")
    
    async def execute_gesture(self, gesture_name: str):
        """Execute a gesture."""
        print(f"\nExecuting: {gesture_name}...")
        response = await self.send_command({
            'action': 'gesture',
            'gesture': gesture_name
        })
        print(f"Status: {response['status']}")
        if response['status'] != 'success':
            print(f"Message: {response['message']}")
    
    async def pause(self):
        """Pause current gesture."""
        response = await self.send_command({'action': 'pause'})
        print(f"Pause: {response['message']}")
    
    async def resume(self):
        """Resume paused gesture."""
        response = await self.send_command({'action': 'resume'})
        print(f"Resume: {response['message']}")
    
    async def restart(self):
        """Restart current gesture."""
        response = await self.send_command({'action': 'restart'})
        print(f"Restart: {response['message']}")
    
    async def status(self):
        """Get server status."""
        response = await self.send_command({'action': 'status'})
        if response['status'] == 'success':
            executor = response['executor']
            print("\nServer Status:")
            print(f"  Current gesture: {executor['current_gesture'] or 'None'}")
            print(f"  Running: {executor['is_running']}")
            print(f"  Paused: {executor['is_paused']}\n")
    
    async def interactive(self):
        """Interactive command loop."""
        print("\nInteractive Mode")
        print("Commands:")
        print("  list                    - List all available gestures")
        print("  status                  - Get server status")
        print("  gesture <name>          - Execute gesture")
        print("  countdown               - Play countdown video")
        print("  diamond [duration]      - Show diamond image (default: 3s)")
        print("  star [duration]         - Show star image (default: 3s)")
        print("  pause                   - Pause current gesture")
        print("  resume                  - Resume paused gesture")
        print("  restart                 - Restart current gesture")
        print("  quit                    - Exit\n")
        
        while True:
            try:
                command = input("> ").strip()
                
                if not command:
                    continue
                
                if command == 'quit':
                    break
                elif command == 'list':
                    await self.list_gestures()
                elif command == 'status':
                    await self.status()
                elif command == 'pause':
                    await self.pause()
                elif command == 'resume':
                    await self.resume()
                elif command == 'restart':
                    await self.restart()
                elif command == 'countdown':
                    await self.execute_gesture('countdown_gesture')
                elif command.startswith('diamond'):
                    parts = command.split()
                    duration = float(parts[1]) if len(parts) > 1 else 3.0
                    await self.send_command({
                        'action': 'gesture',
                        'gesture': 'show_diamond',
                        'params': {'duration': duration}
                    })
                elif command.startswith('star'):
                    parts = command.split()
                    duration = float(parts[1]) if len(parts) > 1 else 3.0
                    await self.send_command({
                        'action': 'gesture',
                        'gesture': 'show_star',
                        'params': {'duration': duration}
                    })
                elif command.startswith('gesture '):
                    gesture_name = command[8:].strip()
                    await self.execute_gesture(gesture_name)
                else:
                    print(f"Unknown command: {command}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


async def demo_sequence(client: RobotClient):
    """Run a demo sequence of gestures."""
    demo_gestures = [
        'center_all',
        'look_point_left',
        'center_all',
        'look_point_right',
        'center_all',
        'celebrate_arms_up',
        'center_all',
    ]
    
    print("\n=== Running Demo Sequence ===\n")
    
    for gesture in demo_gestures:
        await client.execute_gesture(gesture)
        await asyncio.sleep(0.5)  # Small delay between gestures
    
    print("\n=== Demo Complete ===\n")


async def media_demo(client: RobotClient):
    """Run a demo of media playback gestures."""
    print("\n=== Running Media Demo ===\n")
    
    print("1. Countdown video...")
    await client.execute_gesture('countdown_gesture')
    await asyncio.sleep(1)
    
    print("\n2. Show diamond (3 seconds)...")
    await client.send_command({
        'action': 'gesture',
        'gesture': 'show_diamond',
        'params': {'duration': 3.0}
    })
    await asyncio.sleep(0.5)
    
    print("\n3. Show star (3 seconds)...")
    await client.send_command({
        'action': 'gesture',
        'gesture': 'show_star',
        'params': {'duration': 3.0}
    })
    
    print("\n=== Media Demo Complete ===\n")


async def main():
    """Main entry point."""
    import argparse
    
    # Get defaults from environment
    default_host = os.getenv('CLIENT_HOST', 'localhost')
    default_port = os.getenv('CLIENT_PORT', '8765')
    default_uri = f"ws://{default_host}:{default_port}"
    
    parser = argparse.ArgumentParser(description='Robot Control Client')
    parser.add_argument('--uri', default=default_uri, help=f'Server URI (default: {default_uri} from .env)')
    parser.add_argument('--demo', action='store_true', help='Run demo sequence')
    parser.add_argument('--media-demo', action='store_true', help='Run media demo (video/images)')
    parser.add_argument('--gesture', help='Execute single gesture')
    parser.add_argument('--countdown', action='store_true', help='Play countdown video')
    parser.add_argument('--diamond', type=float, metavar='DURATION', help='Show diamond image (duration in seconds)')
    parser.add_argument('--star', type=float, metavar='DURATION', help='Show star image (duration in seconds)')
    
    args = parser.parse_args()
    
    client = RobotClient(uri=args.uri)
    
    try:
        await client.connect()
        
        if args.demo:
            await demo_sequence(client)
        elif args.media_demo:
            await media_demo(client)
        elif args.countdown:
            await client.execute_gesture('countdown_gesture')
        elif args.diamond is not None:
            await client.send_command({
                'action': 'gesture',
                'gesture': 'show_diamond',
                'params': {'duration': args.diamond}
            })
        elif args.star is not None:
            await client.send_command({
                'action': 'gesture',
                'gesture': 'show_star',
                'params': {'duration': args.star}
            })
        elif args.gesture:
            await client.execute_gesture(args.gesture)
        else:
            await client.list_gestures()
            await client.interactive()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
