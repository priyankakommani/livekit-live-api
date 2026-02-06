import os
import logging
from typing import Optional
from datetime import datetime
from livekit import api

logger = logging.getLogger(__name__)

class CloudRecordingManager:
    """
    Manages LiveKit Cloud Recording using Egress API
    Records complete interview (all participants) into single MP4 file
    """
    
    def __init__(self):
        self.egress_id: Optional[str] = None
        self.candidate_id: Optional[str] = None
        
        # Initialize LiveKit API client
        self.livekit_api = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        
        logger.info("Cloud recording manager initialized")
    
    async def start_recording(self, room_name: str, candidate_id: str):
        """Start cloud recording for the entire room"""
        self.candidate_id = candidate_id
        
        logger.info("=" * 60)
        logger.info(f"STARTING CLOUD RECORDING FOR ROOM: {room_name}")
        logger.info("=" * 60)
        
        try:
            # Create room composite recording (all participants in one video)
            # Inject S3 credentials directly from ENV if available to bypass Console config
            s3_upload = None
            if os.getenv("S3_ACCESS_KEY") and os.getenv("S3_SECRET_KEY") and os.getenv("S3_BUCKET"):
                logger.info("Injecting S3 credentials from environment variables...")
                s3_upload = api.S3Upload(
                    access_key=os.getenv("S3_ACCESS_KEY"),
                    secret=os.getenv("S3_SECRET_KEY"),
                    region=os.getenv("S3_REGION", "us-east-1"),
                    bucket=os.getenv("S3_BUCKET"),
                    endpoint=os.getenv("S3_ENDPOINT") # Optional
                )
            
            file_output = api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath=f"ai_interview/{candidate_id}/{{egress_id}}.mp4",
                s3=s3_upload
            )
            
            # Start room composite egress (records entire room)
            request = api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="grid",  # Grid layout shows all participants
                audio_only=False,
                video_only=False,
                file_outputs=[file_output]
            )
            
            egress = await self.livekit_api.egress.start_room_composite_egress(request)
            self.egress_id = egress.egress_id
            
            logger.info(f"✓ Cloud recording started successfully")
            logger.info(f"  Egress ID: {self.egress_id}")
            logger.info(f"  Room: {room_name}")
            logger.info(f"  Recording will be available in LiveKit Cloud Console")
            logger.info("=" * 60)
            
            return egress
            
        except Exception as e:
            if "resource_exhausted" in str(e).lower() or "limit exceeded" in str(e).lower():
                logger.error("!!!" * 20)
                logger.error("LIVEKIT ERROR: CONCURRENT EGRESS LIMIT EXCEEDED")
                logger.error("You have too many active recordings running. Please stop old ones in LiveKit Cloud Consol.")
                logger.error("!!!" * 20)
            else:
                logger.error(f"Failed to start cloud recording: {e}", exc_info=True)
            raise
    
    async def stop_recording(self):
        """Stop the cloud recording"""
        if not self.egress_id:
            logger.warning("No active recording to stop")
            return None
        
        logger.info("=" * 60)
        logger.info("STOPPING CLOUD RECORDING")
        logger.info("=" * 60)
        
        try:
            # Stop the egress
            request = api.StopEgressRequest(egress_id=self.egress_id)
            egress = await self.livekit_api.egress.stop_egress(request)
            
            logger.info(f"✓ Cloud recording stopped successfully")
            logger.info(f"  Egress ID: {self.egress_id}")
            logger.info(f"  Status: {egress.status}")
            
            # Get download info
            if egress.file_results:
                for file_result in egress.file_results:
                    logger.info(f"  Recording file: {file_result.filename}")
                    if file_result.download_url:
                        logger.info(f"  Download URL: {file_result.download_url}")
            
            logger.info("=" * 60)
            logger.info("📥 TO DOWNLOAD YOUR RECORDING:")
            logger.info("1. Go to LiveKit Cloud Console: https://cloud.livekit.io/")
            logger.info("2. Navigate to 'Egress' or 'Recordings' section")
            logger.info(f"3. Find recording with Egress ID: {self.egress_id}")
            logger.info("4. Click 'Download' button")
            logger.info("=" * 60)
            
            return egress
            
        except Exception as e:
            logger.error(f"Error stopping cloud recording: {e}", exc_info=True)
            return None
        finally:
            await self.livekit_api.aclose()
    
    async def get_recording_info(self):
        """Get current recording status and info"""
        if not self.egress_id:
            return None
        
        try:
            egress = await self.livekit_api.egress.list_egress(egress_id=self.egress_id)
            return egress
        except Exception as e:
            logger.error(f"Error getting recording info: {e}")
            return None