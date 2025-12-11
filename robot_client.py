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
        self.gesture_task = None  # Track active gesture task
        self.pending_requests = {}  # Map request_id to response Future
        self.request_counter = 0
        self.receiver_task = None  # Background task reading messages
    
    async def connect(self):
        """Connect to robot server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✓ Connected to {self.uri}")
            # Start background receiver task
            self.receiver_task = asyncio.create_task(self._receive_messages())
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
    
    async def _receive_messages(self):
        """Background task that continuously receives messages from server."""
        try:
            async for message in self.websocket:
                try:
                    response = json.loads(message)
                    # Print responses in a user-friendly way
                    if response.get('status') == 'success':
                        if 'gestures' in response:
                            # List response
                            print("\nAvailable gestures:")
                            for gesture in response['gestures']:
                                print(f"  - {gesture}")
                            print(f"Total: {response['count']} gestures\n")
                        elif 'executor' in response:
                            # Status response
                            executor = response['executor']
                            print("\nServer Status:")
                            print(f"  Current gesture: {executor['current_gesture'] or 'None'}")
                            print(f"  Running: {executor['is_running']}")
                            print(f"  Paused: {executor['is_paused']}\n")
                        elif 'message' in response:
                            print(f"✓ {response['message']}")
                    elif response.get('status') == 'error':
                        print(f"✗ Error: {response.get('message', 'Unknown error')}")
                    elif response.get('status') == 'warning':
                        print(f"⚠ {response.get('message', 'Warning')}")
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
        except asyncio.CancelledError:
            pass
        except websockets.exceptions.ConnectionClosed:
            print("Server connection closed")
        except Exception as e:
            print(f"Receiver error: {e}")
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.receiver_task:
            self.receiver_task.cancel()
            try:
                await self.receiver_task
            except asyncio.CancelledError:
                pass
        if self.websocket:
            await self.websocket.close()
            print("✓ Disconnected")
    
    async def send_command(self, command: dict) -> dict:
        """Send command to server (fire-and-forget)."""
        try:
            await self.websocket.send(json.dumps(command))
            return {'status': 'sent', 'message': 'Command sent to server'}
        except Exception as e:
            print(f"✗ Error sending command: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def list_gestures(self):
        """List available gestures."""
        await self.send_command({'action': 'list'})
    
    async def execute_gesture(self, gesture_name: str):
        """Execute a gesture (non-blocking - runs in background)."""
        # Cancel any existing gesture task
        if self.gesture_task and not self.gesture_task.done():
            print(f"Cancelling previous gesture...")
            self.gesture_task.cancel()
            try:
                await self.gesture_task
            except asyncio.CancelledError:
                pass
        
        print(f"\n→ Starting gesture: {gesture_name}")
        await self.send_command({
            'action': 'gesture',
            'gesture': gesture_name
        })
    
    async def pause(self):
        """Pause current gesture."""
        await self.send_command({'action': 'pause'})
    
    async def resume(self):
        """Resume paused gesture."""
        await self.send_command({'action': 'resume'})
    
    async def restart(self):
        """Restart current gesture."""
        await self.send_command({'action': 'restart'})
    
    async def status(self):
        """Get server status."""
        await self.send_command({'action': 'status'})
    
    async def interactive(self):
        """Interactive command loop (non-blocking)."""
        print("\nInteractive Mode - All commands execute instantly")
        print("Responses from server appear as they arrive")
        print("\nCommands:")
        print("  list                    - List all available gestures")
        print("  status                  - Get server status")
        print("  gesture <name>          - Execute gesture (interrupts previous)")
        print("  countdown               - Play countdown video")
        print("  diamond [duration]      - Show diamond image (default: 3s)")
        print("  star [duration]         - Show star image (default: 3s)")
        print("  pause                   - Pause current gesture")
        print("  resume                  - Resume paused gesture")
        print("  restart                 - Restart current gesture")
        print("  quit                    - Exit\n")
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Use run_in_executor to get non-blocking input
                command = await loop.run_in_executor(None, input, "> ")
                command = command.strip()
                
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
                print("\n")
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
    parser.add_argument('--interactive', action='store_true', help='Interactive shell')
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
        
        if args.interactive:
            await client.list_gestures()
            await client.interactive()
        elif args.demo:
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
