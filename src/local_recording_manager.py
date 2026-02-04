"""
Local Recording Manager
Records audio/video locally using MediaRecorder API on the client side
"""

import os
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalRecordingManager:
    """
    Manages local recording of interview sessions
    Note: This coordinates with client-side recording, not server-side
    """
    
    def __init__(self):
        self.recording_started = False
        self.candidate_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.recordings_dir = Path("recordings")
        
        # Ensure recordings directory exists
        self.recordings_dir.mkdir(exist_ok=True)
        logger.info(f"Local recordings directory: {self.recordings_dir.absolute()}")
        
    def start_recording(self, room_name: str, candidate_id: str) -> str:
        """
        Mark recording as started (actual recording happens on client)
        
        Args:
            room_name: Name of the LiveKit room
            candidate_id: Unique identifier for the candidate
            
        Returns:
            Recording ID (timestamp-based)
        """
        self.candidate_id = candidate_id
        self.start_time = datetime.now()
        self.recording_started = True
        
        recording_id = f"{candidate_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Recording started for candidate: {candidate_id}")
        logger.info(f"Recording ID: {recording_id}")
        logger.info(f"Recordings will be saved to: {self.recordings_dir.absolute()}")
        
        return recording_id
        
    def stop_recording(self) -> dict:
        """
        Mark recording as stopped
        
        Returns:
            dict with recording information
        """
        if not self.recording_started:
            logger.warning("No active recording to stop")
            return {}
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        self.recording_started = False
        
        logger.info(f"Recording stopped for candidate: {self.candidate_id}")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        return {
            "candidate_id": self.candidate_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "recordings_directory": str(self.recordings_dir.absolute())
        }
    
    def get_recording_path(self, candidate_id: str, timestamp: str = None) -> Path:
        """Get the expected path for a recording file"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{candidate_id}_{timestamp}.webm"
        return self.recordings_dir / filename
    
    def list_recordings(self) -> list:
        """List all local recordings"""
        recordings = []
        
        for file in self.recordings_dir.glob("*.webm"):
            stat = file.stat()
            recordings.append({
                "filename": file.name,
                "path": str(file.absolute()),
                "size_mb": stat.st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return recordings


# Alternative: Server-side recording using ffmpeg (for self-hosted LiveKit only)
class ServerSideRecordingManager:
    """
    Server-side recording manager
    Only works with self-hosted LiveKit + Egress service
    """
    
    def __init__(self):
        logger.warning(
            "Server-side recording requires self-hosted LiveKit with Egress service. "
            "LiveKit Cloud free tier does not support this. "
            "Consider using client-side recording instead."
        )