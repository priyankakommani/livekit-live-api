"""
AI Interview Agent - Updated with Local Recording
Main agent implementation using LiveKit and Gemini Live API
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Ensure environment variables are set for subprocesses
os.environ['LIVEKIT_URL'] = os.getenv('LIVEKIT_URL', '')
os.environ['LIVEKIT_API_KEY'] = os.getenv('LIVEKIT_API_KEY', '')
os.environ['LIVEKIT_API_SECRET'] = os.getenv('LIVEKIT_API_SECRET', '')
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', '')

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    vad,
    tokenize,
)
from livekit.plugins import google
import livekit.plugins.silero as silero_plugin
from livekit import rtc

from prompts import get_interview_prompt
from local_recording_manager import LocalRecordingManager
from transcription_handler import TranscriptionHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InterviewAgent:
    """Main interview agent class"""
    
    def __init__(
        self,
        candidate_id: str,
        job_role: str = "software_engineer",
        interview_duration: int = 30
    ):
        self.candidate_id = candidate_id
        self.job_role = job_role
        self.interview_duration = interview_duration
        self.session: Optional[AgentSession] = None
        self.agent: Optional[Agent] = None
        self.recorder: Optional[LocalRecordingManager] = None
        self.transcription: Optional[TranscriptionHandler] = None
        self.start_time: Optional[datetime] = None
        
    async def initialize(self, ctx: JobContext):
        """Initialize the agent with LiveKit context"""
        logger.info(f"Initializing interview for candidate {self.candidate_id}")
        
        # Get interview prompt for the specific role
        interview_instructions = get_interview_prompt(self.job_role)
        
        # Initialize individual components for maximum stability
        # 1. Speech-to-Text
        stt_plugin = google.STT()
        
        # 2. Large Language Model (Gemini 1.5 Flash)
        llm_plugin = google.LLM(
            model="gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
        
        # 3. Text-to-Speech
        tts_plugin = google.TTS()
        
        # Create the agent wrapper with the stable components
        self.agent = Agent(
            instructions=interview_instructions,
            stt=stt_plugin,
            llm=llm_plugin,
            tts=tts_plugin,
            vad=silero_plugin.VAD.load(), # Use VAD for better turn detection
        )

        # Initialize the agent session (it will inherit components from the agent)
        self.session = AgentSession()
        
        # Initialize local recording manager
        self.recorder = LocalRecordingManager()
        
        # Initialize transcription handler
        self.transcription = TranscriptionHandler(
            interview_id=f"{self.candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info("Agent initialized successfully")
        
    async def start_interview(self, ctx: JobContext):
        """Start the interview session"""
        logger.info("start_interview method called")
        try:
            # Initialize agent
            logger.info("Initializing Agent components...")
            await self.initialize(ctx)
            logger.info("Agent components initialized")
            
            # Connect to the LiveKit room
            await ctx.connect()
            logger.info(f"Connected to room: {ctx.room.name}")
            
            # Start local recording marker
            recording_id = self.recorder.start_recording(
                room_name=ctx.room.name,
                candidate_id=self.candidate_id
            )
            logger.info(f"Local recording started with ID: {recording_id}")
            logger.info("Note: Actual recording happens on the client side")
            logger.info(f"Recordings will be saved to: recordings/")
            
            # Start the agent session (recording disabled to avoid 401 issues)
            logger.info("Starting AgentSession...")
            self.start_time = datetime.now()
            await self.session.start(self.agent, room=ctx.room, record=False)
            logger.info("AgentSession started successfully")
            
            # Wait a moment for audio tracks to stabilize
            await asyncio.sleep(2)
            
            # Greet the candidate immediately (Audio + Transcription)
            greeting_text = "Hi! I'm excited to learn about your experience. How are you doing today?"
            logger.info(f"Sending initial greeting: {greeting_text}")
            
            # 1. Audio greeting
            try:
                self.session.say(greeting_text)
            except Exception as e:
                logger.error(f"Error sending greeting: {e}")
                
            # Support text-base display for following turns
            @self.session.on("agent_transcribed")
            def _on_agent_transcribed(text: str):
                # When bot finishes a sentence, show it on screen
                if text:
                   # Publish as transcription for UI
                   asyncio.create_task(ctx.room.local_participant.publish_transcription(
                       rtc.Transcription(
                           participant_identity=ctx.room.local_participant.identity,
                           segments=[rtc.TranscriptionSegment(
                               id=f"agent_speech_{datetime.now().timestamp()}",
                               text=str(text),
                               start_time=0,
                               end_time=1000,
                               final=True
                           )]
                       )
                   ))
                   
            @self.session.on("user_transcribed")
            def _on_user_transcribed(text: str):
                # When user speaks, also show on screen if needed
                # (LiveKit Usually handles participant transcription automatically in the UI, 
                # but we can log it here)
                logger.info(f"User said: {text}")

            @self.session.on("agent_speaking_started")
            def _on_speaking_started(handle):
                logger.debug("Agent started speaking")

            @self.session.on("agent_speaking_finished")
            def _on_speaking_finished(handle):
                logger.debug("Agent finished speaking")

            logger.info(f"Interview started for candidate {self.candidate_id}")
            
            # Monitor interview duration
            await self._monitor_interview_duration(ctx)
            
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            raise
            
    def _setup_event_handlers(self, ctx: JobContext):
        """Set up event handlers for the session"""
        
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.TrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
            
        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant connected: {participant.identity}")
            logger.info("Reminder: Client should start recording now")
            
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant disconnected: {participant.identity}")
            
    async def _monitor_interview_duration(self, ctx: JobContext):
        """Monitor interview duration and end when time limit reached"""
        max_duration_seconds = self.interview_duration * 60
        
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                logger.info(f"Interview progress: {elapsed:.0f}s / {max_duration_seconds}s")
                
                if elapsed >= max_duration_seconds:
                    logger.info("Interview duration limit reached. Ending interview.")
                    await self.end_interview(ctx)
                    break
                    
    async def end_interview(self, ctx: JobContext):
        """End the interview and clean up"""
        try:
            logger.info("Ending interview...")
            
            # Stop recording marker
            if self.recorder:
                recording_info = self.recorder.stop_recording()
                logger.info(f"Recording session ended: {recording_info}")
                logger.info(f"Check recordings directory: {recording_info.get('recordings_directory')}")
                
                # List all recordings
                recordings = self.recorder.list_recordings()
                if recordings:
                    logger.info(f"Found {len(recordings)} recording(s):")
                    for rec in recordings:
                        logger.info(f"  - {rec['filename']} ({rec['size_mb']:.2f} MB)")
                
            # Save final transcript
            if self.transcription:
                transcript = self.transcription.get_full_transcript()
                transcript_path = f"transcripts/{self.candidate_id}_transcript.txt"
                os.makedirs("transcripts", exist_ok=True)
                with open(transcript_path, "w") as f:
                    f.write(transcript)
                logger.info(f"Transcript saved: {transcript_path}")
                
            # Disconnect from room
            await ctx.room.disconnect()
            
            logger.info("Interview ended successfully")
            logger.info("=" * 60)
            logger.info("IMPORTANT: Recordings are saved on the client side")
            logger.info("Check your Downloads folder or the recordings/ directory")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error ending interview: {e}")
            raise


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the LiveKit agent"""
    logger.info("-" * 40)
    logger.info(f"JOB RECEIVED: {ctx.job.id}")
    logger.info(f"Room name: {ctx.room.name}")
    logger.info("-" * 40)
    
    # Wait a moment for room metadata to sync if it's empty
    for _ in range(5):
        if ctx.room.metadata:
            break
        await asyncio.sleep(0.5)
        
    # Get candidate information from room metadata
    room_metadata = {}
    if ctx.room.metadata:
        try:
            room_metadata = json.loads(ctx.room.metadata)
        except Exception as e:
            logger.error(f"Error parsing room metadata: {e}")
            
    candidate_id = room_metadata.get("candidate_id", "unknown")
    job_role = room_metadata.get("job_role", "software_engineer")
    
    logger.info(f"Starting interview for candidate: {candidate_id}, role: {job_role}")
    
    # Create and start interview agent
    agent = InterviewAgent(
        candidate_id=candidate_id,
        job_role=job_role
    )
    
    await agent.start_interview(ctx)


if __name__ == "__main__":
    # Verify environment variables are set
    required_vars = ['LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        exit(1)
    
    logger.info("=" * 60)
    logger.info("AI Interview Agent - VERSION: 2.1 (VAD + Text Support)")
    logger.info("=" * 60)
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    logger.info("Recording: Client-side (saves to Downloads)")
    logger.info("=" * 60)
    
    # Run the agent with explicit credentials
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )
    )