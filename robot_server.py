"""
Robot WebSocket server for remote gesture control.
Handles incoming commands and manages gesture execution with play/stop control.
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

from robot_gestures import (
    execute_gesture,
    get_available_gestures,
    gesture_controller,
    start_idle_motions,
    stop_idle_motions,
    Gesture_stop,
    motor_lock,
    MOTORS_AVAILABLE,
)

import multiprocessing

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
    """Manages gesture execution state with process-based control."""
    
    def __init__(self):
        self.current_gesture: Optional[str] = None
        self.is_running = False
        self.gesture_process: Optional[multiprocessing.Process] = None
        self.gesture_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None  # Track async cleanup
    
    async def _wait_for_gesture_completion(self, process):
        """Asynchronously wait for gesture process to complete."""
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, process.join),
                timeout=None
            )
            
            # Check final exit code
            if process.exitcode == 0:
                logger.info(f"Gesture process completed successfully")
            elif process.exitcode is None:
                logger.info(f"Gesture process was terminated")
            else:
                logger.warning(f"Gesture process exited with code {process.exitcode}")
            # After gesture completion, resume idle motions only in simulation mode
            if not MOTORS_AVAILABLE:
                start_idle_motions()
        except Exception as e:
            logger.error(f"Error waiting for gesture completion: {e}")
    
    async def execute(self, gesture_name: str, **params) -> Dict:
        """
        Execute a gesture with play/pause/stop control via multiprocessing.
        
        Args:
            gesture_name: Name of gesture to execute
            **params: Optional parameters to pass to the gesture
            
        Returns:
            Response dict with status and message
        """
        # Terminate any currently running gesture process
        if self.gesture_process and self.gesture_process.is_alive():
            logger.info(f"Terminating previous gesture process before executing {gesture_name}")
            self.gesture_process.terminate()
            self.gesture_process.join(timeout=2.0)
            if self.gesture_process.is_alive():
                logger.warning("Gesture process did not terminate gracefully, killing it")
                self.gesture_process.kill()
                self.gesture_process.join()
        
        self.current_gesture = gesture_name
        self.is_running = True
        self.is_paused = False
        
        # Pause idle motions to avoid port conflicts with child process
        try:
            stop_idle_motions()
        except Exception:
            pass

        # Run gesture in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            # Create a task that runs execute_gesture (which starts the process)
            # execute_gesture returns (process, result_dict) immediately
            self.gesture_task = loop.run_in_executor(None, lambda: execute_gesture(gesture_name, **params))
            
            # Get the process and result from execute_gesture (returns immediately)
            process, result = await self.gesture_task
            
            # Store the process so pause() can terminate it
            self.gesture_process = process
            
            # Schedule async completion tracking (don't wait for it)
            if process:
                asyncio.create_task(self._wait_for_gesture_completion(process))
            
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
    
    async def _async_process_cleanup(self, process, timeout=2.0):
        """Asynchronously wait for process to terminate, then kill if needed."""
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, process.join),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            if process.is_alive():
                logger.warning("Process did not terminate, killing it")
                process.kill()
                try:
                    await loop.run_in_executor(None, process.join)
                except Exception as e:
                    logger.error(f"Error joining killed process: {e}")
        except Exception as e:
            logger.error(f"Error during process cleanup: {e}")
    
    async def stop(self) -> Dict:
        """Stop current gesture execution (terminates the gesture process)."""
        if not self.is_running:
            return {
                'status': 'warning',
                'message': 'No gesture currently running'
            }
        
        # Immediately terminate the gesture process
        if self.gesture_process and self.gesture_process.is_alive():
            logger.info(f"Terminating gesture process for stop: {self.current_gesture}")
            self.gesture_process.terminate()
            
            # Schedule async cleanup (don't wait for it)
            if self.cleanup_task:
                self.cleanup_task.cancel()
            self.cleanup_task = asyncio.create_task(
                self._async_process_cleanup(self.gesture_process)
            )
        
        # Cancel the execution task if it's still running
        if self.gesture_task and not self.gesture_task.done():
            logger.info("Cancelling gesture execution task")
            self.gesture_task.cancel()
            try:
                await self.gesture_task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        logger.info(f"Gesture stopped: {self.current_gesture}")
        
        return {
            'status': 'success',
            'message': f'Gesture "{self.current_gesture}" stopped',
            'current_gesture': self.current_gesture
        }
    
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
            
            # Extract optional parameters (e.g., video_path)
            params = data.get('params', {})
            
            logger.info(f"[{client_addr}] Executing gesture: {gesture_name} with params: {params}")
            result = await self.executor.execute(gesture_name, **params)
            result['timestamp'] = timestamp
            return result
        
        elif action == 'stop':
            logger.info(f"[{client_addr}] Stop requested")
            result = await self.executor.stop()
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
                'message': f'Unknown action: {action}. Valid actions: gesture, stop, status, list',
                'timestamp': timestamp
            }
    
    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        # Start idle motions in background only in simulation mode to avoid hardware port conflicts
        if not MOTORS_AVAILABLE:
            start_idle_motions()
        
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
