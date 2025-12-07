"""
Robot WebSocket server for remote gesture control.
Handles incoming commands and manages gesture execution with play/pause/restart control.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

try:
    import websockets
    # Try new API first, fall back to old API
    try:
        from websockets.asyncio.server import serve
    except ImportError:
        from websockets.server import serve
except ImportError:
    print("Error: websockets module not found. Install with: pip install websockets")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv module not found. Install with: pip install python-dotenv")
    sys.exit(1)

from robot_gestures import execute_gesture, get_available_gestures, gesture_controller

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GestureExecutor:
    """Manages gesture execution state (play, pause, restart)."""
    
    def __init__(self):
        self.current_gesture: Optional[str] = None
        self.is_running = False
        self.is_paused = False
        self.gesture_task: Optional[asyncio.Task] = None
    
    async def execute(self, gesture_name: str) -> Dict:
        """
        Execute a gesture with play/pause/restart control.
        
        Args:
            gesture_name: Name of gesture to execute
            
        Returns:
            Response dict with status and message
        """
        # Cancel existing gesture if running
        if self.gesture_task and not self.gesture_task.done():
            self.gesture_task.cancel()
            await asyncio.sleep(0.1)  # Allow cancellation to complete
        
        self.current_gesture = gesture_name
        self.is_running = True
        self.is_paused = False
        
        # Run gesture in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, execute_gesture, gesture_name)
            self.is_running = False
            
            # Ensure result is a proper dict
            if isinstance(result, dict):
                return result
            else:
                return {
                    'status': 'error',
                    'message': f'Invalid response from gesture executor: {result}'
                }
        except asyncio.CancelledError:
            self.is_running = False
            return {
                'status': 'warning',
                'message': 'Gesture execution cancelled'
            }
        except Exception as e:
            self.is_running = False
            logger.error(f"Exception during gesture execution: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to execute gesture: {str(e)}'
            }
    
    async def pause(self) -> Dict:
        """Pause current gesture execution."""
        if not self.is_running:
            return {
                'status': 'warning',
                'message': 'No gesture currently running'
            }
        
        self.is_paused = True
        if self.gesture_task:
            self.gesture_task.cancel()
        
        return {
            'status': 'success',
            'message': f'Gesture "{self.current_gesture}" paused',
            'current_gesture': self.current_gesture
        }
    
    async def resume(self) -> Dict:
        """Resume paused gesture."""
        if not self.current_gesture:
            return {
                'status': 'warning',
                'message': 'No gesture to resume'
            }
        
        if not self.is_paused:
            return {
                'status': 'warning',
                'message': 'No paused gesture'
            }
        
        self.is_paused = False
        return await self.execute(self.current_gesture)
    
    async def restart(self) -> Dict:
        """Restart current gesture from beginning."""
        if not self.current_gesture:
            return {
                'status': 'warning',
                'message': 'No gesture to restart'
            }
        
        self.is_paused = False
        return await self.execute(self.current_gesture)
    
    def get_status(self) -> Dict:
        """Get current executor status."""
        return {
            'current_gesture': self.current_gesture,
            'is_running': self.is_running,
            'is_paused': self.is_paused
        }


class RobotServer:
    """WebSocket server for robot control."""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv('SERVER_HOST', '0.0.0.0')
        self.port = int(port or os.getenv('SERVER_PORT', '8765'))
        self.executor = GestureExecutor()
        self.clients = set()
        logger.info(f"Robot server initialized on {self.host}:{self.port}")
    
    async def handler(self, websocket, path=None):
        """Handle incoming WebSocket connections."""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")
        
        try:
            async for message in websocket:
                try:
                    response = await self._process_message(message, client_addr)
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    logger.error(f"Error processing message from {client_addr}: {str(e)}", exc_info=True)
                    error_response = {
                        'status': 'error',
                        'message': f'Server error: {str(e)}'
                    }
                    try:
                        await websocket.send(json.dumps(error_response))
                    except:
                        pass  # Client may have disconnected
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {str(e)}", exc_info=True)
        finally:
            self.clients.discard(websocket)
    
    async def _process_message(self, message: str, client_addr) -> Dict:
        """
        Process incoming message and route to appropriate handler.
        
        Expected message format:
        {
            "action": "gesture" | "pause" | "resume" | "restart" | "status" | "list",
            "gesture": "gesture_name"  # required for "gesture" action
        }
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {client_addr}")
            return {
                'status': 'error',
                'message': 'Invalid JSON format'
            }
        
        action = data.get('action')
        timestamp = datetime.now().isoformat()
        
        # Route based on action
        if action == 'gesture':
            gesture_name = data.get('gesture')
            if not gesture_name:
                return {
                    'status': 'error',
                    'message': 'Missing "gesture" field',
                    'timestamp': timestamp
                }
            logger.info(f"[{client_addr}] Executing gesture: {gesture_name}")
            result = await self.executor.execute(gesture_name)
            result['timestamp'] = timestamp
            return result
        
        elif action == 'pause':
            logger.info(f"[{client_addr}] Pause requested")
            result = await self.executor.pause()
            result['timestamp'] = timestamp
            return result
        
        elif action == 'resume':
            logger.info(f"[{client_addr}] Resume requested")
            result = await self.executor.resume()
            result['timestamp'] = timestamp
            return result
        
        elif action == 'restart':
            logger.info(f"[{client_addr}] Restart requested")
            result = await self.executor.restart()
            result['timestamp'] = timestamp
            return result
        
        elif action == 'status':
            logger.info(f"[{client_addr}] Status requested")
            return {
                'status': 'success',
                'executor': self.executor.get_status(),
                'timestamp': timestamp
            }
        
        elif action == 'list':
            logger.info(f"[{client_addr}] List gestures requested")
            return {
                'status': 'success',
                'gestures': get_available_gestures(),
                'count': len(get_available_gestures()),
                'timestamp': timestamp
            }
        
        else:
            logger.warning(f"[{client_addr}] Unknown action: {action}")
            return {
                'status': 'error',
                'message': f'Unknown action: {action}. Valid actions: gesture, pause, resume, restart, status, list',
                'timestamp': timestamp
            }
    
    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            logger.info("Server is running. Press Ctrl+C to stop.")
            try:
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown server."""
        logger.info("Shutting down server...")
        
        # Close all client connections
        for client in list(self.clients):
            await client.close()
        
        # Cleanup robot motors
        gesture_controller.cleanup()
        logger.info("Server shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    # Get defaults from environment
    default_host = os.getenv('SERVER_HOST', '0.0.0.0')
    default_port = int(os.getenv('SERVER_PORT', '8765'))
    
    parser = argparse.ArgumentParser(description='Robot WebSocket Server')
    parser.add_argument('--host', default=default_host, help=f'Server host (default: {default_host} from .env)')
    parser.add_argument('--port', type=int, default=default_port, help=f'Server port (default: {default_port} from .env)')
    parser.add_argument('--local', action='store_true', help='Listen on localhost only')
    
    args = parser.parse_args()
    
    host = 'localhost' if args.local else args.host
    port = args.port
    
    server = RobotServer(host=host, port=port)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
