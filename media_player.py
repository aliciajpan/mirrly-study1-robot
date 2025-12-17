"""
Media playback module for synchronized video/image display during gestures.
Supports VLC-based video playback and image display with threading for non-blocking operation.
"""

import time
import threading
from pathlib import Path

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    print("Warning: python-vlc not installed. Video/image playback disabled.")
    print("Install with: pip install python-vlc")
    VLC_AVAILABLE = False


class MediaPlayer:
    """Manages video and image playback during robot gestures."""
    
    def __init__(self):
        """Initialize VLC instance if available."""
        self.vlc_instance = None
        self.active_players = []
        
        if VLC_AVAILABLE:
            # VLC options: hide cursor, disable DRM for SSH/X11 compatibility, force X11 video output
            self.vlc_instance = vlc.Instance(
                '--mouse-hide-timeout=0',
                '--no-video-deco',           # No window decorations
                '--no-embedded-video',        # Don't embed video
                '--vout=xcb_x11',            # Force X11 video output (works over SSH with DISPLAY=:0)
                '--avcodec-hw=none'          # Disable hardware decoding to avoid DRM issues
            )
    
    def play_video(self, video_path, fullscreen=True, muted=True, blocking=True):
        """
        Play a video file.
        
        Args:
            video_path (str): Path to video file
            fullscreen (bool): Play in fullscreen mode
            muted (bool): Mute audio
            blocking (bool): Wait for video to finish before returning
            
        Returns:
            threading.Thread: Video playback thread (if not blocking)
        """
        if not VLC_AVAILABLE:
            print(f"[SIMULATION] Would play video: {video_path}")
            return None
        
        if not Path(video_path).exists():
            print(f"Warning: Video file not found: {video_path}")
            return None
        
        thread = threading.Thread(
            target=self._play_video_thread,
            args=(video_path, fullscreen, muted)
        )
        thread.daemon = True
        thread.start()
        
        if blocking:
            thread.join()  # Wait for video to finish
        
        return thread
    
    def play_image(self, image_path, duration=3.0, fullscreen=True, blocking=True):
        """
        Display a static image for a specified duration.
        
        Args:
            image_path (str): Path to image file
            duration (float): How long to display the image (seconds)
            fullscreen (bool): Display in fullscreen mode
            blocking (bool): Wait for display duration before returning
            
        Returns:
            threading.Thread: Image display thread (if not blocking)
        """
        if not VLC_AVAILABLE:
            print(f"[SIMULATION] Would display image: {image_path} for {duration}s")
            if blocking:
                time.sleep(duration)
            return None
        
        if not Path(image_path).exists():
            print(f"Warning: Image file not found: {image_path}")
            return None
        
        thread = threading.Thread(
            target=self._play_image_thread,
            args=(image_path, duration, fullscreen)
        )
        thread.daemon = True
        thread.start()
        
        if blocking:
            thread.join()  # Wait for display duration
        
        return thread
    
    def _play_video_thread(self, video_path, fullscreen, muted):
        """Internal method to play video in a thread."""
        player = self.vlc_instance.media_player_new()
        media = self.vlc_instance.media_new(video_path)
        
        if muted:
            media.add_option('no-audio')
        
        player.set_media(media)
        
        if fullscreen:
            player.set_fullscreen(True)
        
        # Start playback
        player.play()
        
        # Wait for player to initialize
        time.sleep(1)
        player.play()  # Ensure it's playing
        
        # Track active player
        self.active_players.append(player)
        
        # Wait for video to finish
        while True:
            state = player.get_state()
            if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
                break
            time.sleep(0.1)
        
        # Cleanup
        player.stop()
        if player in self.active_players:
            self.active_players.remove(player)
    
    def _play_image_thread(self, image_path, duration, fullscreen):
        """Internal method to display image in a thread."""
        player = self.vlc_instance.media_player_new()
        
        # VLC can display images by treating them as media with pause
        media = self.vlc_instance.media_new(image_path)
        media.add_option('image-duration=-1')  # Display indefinitely until stopped
        
        player.set_media(media)
        
        if fullscreen:
            player.set_fullscreen(True)
        
        # Start playback
        player.play()
        
        # Wait for player to initialize
        time.sleep(0.5)
        
        # Track active player
        self.active_players.append(player)
        
        # Display for specified duration
        time.sleep(duration)
        
        # Cleanup
        player.stop()
        if player in self.active_players:
            self.active_players.remove(player)
    
    def stop_all(self):
        """Stop all active video players."""
        for player in self.active_players:
            try:
                player.stop()
            except:
                pass
        self.active_players.clear()
    
    def is_available(self):
        """Check if media playback is available."""
        return VLC_AVAILABLE


# Global instance
media_player = MediaPlayer()
