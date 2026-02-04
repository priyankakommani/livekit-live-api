"""
Recording Manager
Handles interview recording using LiveKit Egress API
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime
from livekit import api

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages interview recording using LiveKit Egress"""
    
    def __init__(self, livekit_url: str, api_key: str, api_secret: str):
        """
        Initialize recording manager
        
        Args:
            livekit_url: LiveKit server URL
            api_key: LiveKit API key
            api_secret: LiveKit API secret
        """
        self.livekit_url = livekit_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.egress_service = api.EgressService(
            livekit_url,
            api_key,
            api_secret
        )
        self.egress_id: Optional[str] = None
        self.recording_start_time: Optional[datetime] = None
        
    async def start_recording(
        self,
        room_name: str,
        candidate_id: str,
        audio_only: bool = False
    ) -> str:
        """
        Start recording the interview session
        
        Args:
            room_name: Name of the LiveKit room
            candidate_id: Candidate identifier
            audio_only: If True, record audio only
            
        Returns:
            Egress ID for the recording
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{candidate_id}_{timestamp}"
            
            # Configure recording output
            # For production, use S3 or other cloud storage
            # For development, use local file storage
            
            if os.getenv("USE_CLOUD_STORAGE") == "true":
                # Cloud storage (S3)
                output = api.EncodedFileOutput(
                    file_type=api.EncodedFileType.MP4,
                    filepath=f"recordings/{filename}.mp4",
                    output=api.S3Upload(
                        access_key=os.getenv("AWS_ACCESS_KEY"),
                        secret=os.getenv("AWS_SECRET_KEY"),
                        region=os.getenv("AWS_REGION", "us-east-1"),
                        bucket=os.getenv("AWS_BUCKET", "interview-recordings")
                    )
                )
            else:
                # Local file storage (for development)
                output = api.EncodedFileOutput(
                    file_type=api.EncodedFileType.MP4,
                    filepath=f"recordings/{filename}.mp4"
                )
            
            # Create recording request
            request = api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="speaker-dark",  # Layout options: speaker-dark, speaker-light, grid-dark, grid-light
                audio_only=audio_only,
                video_only=False,
                file_outputs=[output]
            )
            
            # Start recording
            response = await self.egress_service.start_room_composite_egress(request)
            self.egress_id = response.egress_id
            self.recording_start_time = datetime.now()
            
            logger.info(f"Recording started: {self.egress_id}")
            logger.info(f"Output file: recordings/{filename}.mp4")
            
            return self.egress_id
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
            
    async def stop_recording(self) -> Dict:
        """
        Stop the current recording
        
        Returns:
            Recording information including file path and duration
        """
        if not self.egress_id:
            logger.warning("No active recording to stop")
            return {}
            
        try:
            # Stop the recording
            await self.egress_service.stop_egress(self.egress_id)
            
            # Get recording info
            recording_info = await self.get_recording_status(self.egress_id)
            
            # Calculate duration
            if self.recording_start_time:
                duration = (datetime.now() - self.recording_start_time).total_seconds()
                recording_info['duration_seconds'] = duration
                
            logger.info(f"Recording stopped: {self.egress_id}")
            logger.info(f"Duration: {recording_info.get('duration_seconds', 0):.2f} seconds")
            
            return recording_info
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            raise
            
    async def get_recording_status(self, egress_id: str) -> Dict:
        """
        Get the status of a recording
        
        Args:
            egress_id: The egress ID to check
            
        Returns:
            Recording status information
        """
        try:
            egress_info = await self.egress_service.get_egress(egress_id)
            
            status_info = {
                'egress_id': egress_info.egress_id,
                'status': egress_info.status,
                'room_name': egress_info.room_name,
                'started_at': egress_info.started_at,
                'ended_at': egress_info.ended_at,
            }
            
            # Add file information if available
            if hasattr(egress_info, 'file_results'):
                status_info['files'] = [
                    {
                        'filename': file.filename,
                        'size': file.size,
                        'location': file.location,
                    }
                    for file in egress_info.file_results
                ]
                
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get recording status: {e}")
            return {}
            
    async def list_recordings(self, room_name: Optional[str] = None) -> list:
        """
        List all recordings, optionally filtered by room name
        
        Args:
            room_name: Optional room name to filter by
            
        Returns:
            List of recording information
        """
        try:
            egress_list = await self.egress_service.list_egress(room_name=room_name)
            
            recordings = []
            for egress in egress_list:
                recordings.append({
                    'egress_id': egress.egress_id,
                    'room_name': egress.room_name,
                    'status': egress.status,
                    'started_at': egress.started_at,
                    'ended_at': egress.ended_at,
                })
                
            return recordings
            
        except Exception as e:
            logger.error(f"Failed to list recordings: {e}")
            return []


class RecordingMetadata:
    """Store metadata about recordings"""
    
    def __init__(self, recordings_dir: str = "recordings"):
        self.recordings_dir = recordings_dir
        self.metadata_file = os.path.join(recordings_dir, "metadata.json")
        
    def save_metadata(
        self,
        candidate_id: str,
        room_name: str,
        egress_id: str,
        job_role: str,
        duration: float,
        file_path: str
    ):
        """Save recording metadata"""
        import json
        
        metadata = {
            'candidate_id': candidate_id,
            'room_name': room_name,
            'egress_id': egress_id,
            'job_role': job_role,
            'duration_seconds': duration,
            'file_path': file_path,
            'recorded_at': datetime.now().isoformat(),
        }
        
        # Load existing metadata
        all_metadata = []
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                all_metadata = json.load(f)
                
        # Append new metadata
        all_metadata.append(metadata)
        
        # Save back
        with open(self.metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
            
        logger.info(f"Metadata saved for candidate {candidate_id}")
        
    def get_candidate_recordings(self, candidate_id: str) -> list:
        """Get all recordings for a specific candidate"""
        import json
        
        if not os.path.exists(self.metadata_file):
            return []
            
        with open(self.metadata_file, 'r') as f:
            all_metadata = json.load(f)
            
        return [
            rec for rec in all_metadata
            if rec['candidate_id'] == candidate_id
        ]
