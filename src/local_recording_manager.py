import os
import logging
import asyncio
import subprocess
from typing import Optional
from datetime import datetime
from pathlib import Path
from livekit import rtc

logger = logging.getLogger(__name__)

class LocalRecordingManager:
    """
    Manages local recording of interview sessions (Audio and Video)
    """
    
    def __init__(self):
        self.candidate_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        # Always use the project root 'recordings' directory
        project_root = Path(__file__).parent.parent
        self.recordings_dir = project_root / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        logger.info(f"Local recording manager initialized. Saving to: {self.recordings_dir.absolute()}")
        self._video_tasks = {} # track -> task

    async def start_recording(self, room: rtc.Room, candidate_id: str):
        self.candidate_id = candidate_id
        self.start_time = datetime.now()
        
        logger.info(f"Local recording manager started for {candidate_id}")

        # 1. Handle already subscribed tracks (Remote)
        for participant in room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.track and publication.subscribed:
                    self._handle_track(publication.track, participant.identity)

        # 2. Handle future tracks (Remote)
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
            self._handle_track(track, participant.identity)

        # 3. Handle Local Participant (the Bot's own voice)
        for publication in room.local_participant.track_publications.values():
            if publication.track:
                self._handle_track(publication.track, "Bot")

        @room.local_participant.on("track_published")
        def on_local_track_published(publication: rtc.LocalTrackPublication):
            if publication.track:
                self._handle_track(publication.track, "Bot")

    def _handle_track(self, track: rtc.Track, identity: str):
        if track.sid in self._video_tasks:
            return

        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info(f"Recording video track {track.sid} from {identity}")
            task = asyncio.create_task(self._record_video_track(track, identity))
            self._video_tasks[track.sid] = task
        elif track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"Recording audio track {track.sid} from {identity}")
            task = asyncio.create_task(self._record_audio_track(track, identity))
            self._video_tasks[track.sid] = task

    async def _record_video_track(self, track: rtc.VideoTrack, participant_id: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.recordings_dir / f"{self.candidate_id}_video_{participant_id}_{timestamp}.mp4"
        
        # We'll use ffmpeg to encode the frames
        video_stream = rtc.VideoStream(track)
        process = None
        
        try:
            async for frame in video_stream:
                if process is None:
                    width, height = frame.width, frame.height
                    logger.info(f"Starting ffmpeg for video recording: {width}x{height} -> {output_path}")
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-f', 'rawvideo',
                        '-vcodec', 'rawvideo',
                        '-s', f'{width}x{height}',
                        '-pix_fmt', 'yuv420p',
                        '-r', '24',
                        '-i', '-',
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-pix_fmt', 'yuv420p',
                        str(output_path)
                    ]
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

                # Ensure we are sending I420 to ffmpeg
                i420_frame = frame.convert(rtc.VideoBufferType.I420)
                try:
                    process.stdin.write(i420_frame.data)
                except Exception as e:
                    logger.error(f"Error writing video to ffmpeg: {e}")
                    break
        finally:
            if process:
                process.stdin.close()
                process.wait()
                logger.info(f"Video recording finished: {output_path}")

    async def _record_audio_track(self, track: rtc.AudioTrack, participant_id: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.recordings_dir / f"{self.candidate_id}_audio_{participant_id}_{timestamp}.ogg"
        
        audio_stream = rtc.AudioStream(track)
        process = None
        
        try:
            async for frame in audio_stream:
                if process is None:
                    logger.info(f"Starting ffmpeg for audio recording: {frame.sample_rate}Hz -> {output_path}")
                    cmd = [
                        'ffmpeg', '-y',
                        '-f', 's16le',
                        '-ar', str(frame.sample_rate),
                        '-ac', str(frame.num_channels),
                        '-i', '-',
                        '-c:a', 'libopus',
                        str(output_path)
                    ]
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                
                try:
                    process.stdin.write(frame.data)
                except Exception as e:
                    logger.error(f"Error writing audio to ffmpeg: {e}")
                    break
        finally:
            if process:
                process.stdin.close()
                process.wait()
                logger.info(f"Audio recording finished: {output_path}")

    def stop_recording(self):
        for task in self._video_tasks.values():
            task.cancel()
        self._video_tasks.clear()
        return {"status": "stopped", "dir": str(self.recordings_dir.absolute())}