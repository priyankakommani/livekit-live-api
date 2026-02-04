"""
AI Interview Agent - Pure Gemini Multimodal implementation
Main agent implementation using LiveKit and Gemini Multimodal Live API
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    tokenize,
)
from livekit.plugins import google
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
    """Main interview agent class using Gemini Multimodal Live"""
    
    def __init__(
        self,
        candidate_id: str,
        job_role: str = "software_engineer",
        interview_duration: int = 30
    ):
        self.candidate_id = candidate_id
        self.job_role = job_role
        self.interview_duration = interview_duration
        self.start_time = None
        self.recorder = None
        self.transcription = None

    async def start_interview(self, ctx: JobContext):
        """Start the interview session"""
        logger.info(f"--- STARTING MULTIMODAL INTERVIEW (Candidate: {self.candidate_id}) ---")
        
        try:
            # 1. Initialize components
            api_key = os.getenv("GOOGLE_API_KEY")
            interview_instructions = get_interview_prompt(self.job_role)
            
            # Using gemini-2.5-flash-native-audio-latest which is verified to work!
            logger.info("Initializing RealtimeModel (Gemini 2.5 Flash Native Audio)...")
            model = google.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-latest",
                api_version="v1beta",
                api_key=api_key,
                instructions=interview_instructions,
                voice="Puck",
            )

            # Create the modern Agent holding the model
            logger.info("Initializing Agent and AgentSession...")
            self.agent = Agent(llm=model, instructions=interview_instructions)
            self.session = AgentSession()
            
            # 2. Setup Recording & Transcription
            self.recorder = LocalRecordingManager()
            self.transcription = TranscriptionHandler(
                interview_id=f"{self.candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 3. Add Event Handlers for Transcription (Robustness)
            @self.session.on("user_input_transcribed")
            def _on_user_transcript(ev):
                if ev.transcript:
                    logger.info(f"--- USER: {ev.transcript} ---")

            @self.session.on("conversation_item_added")
            def _on_item_added(ev):
                # ev.item is a ChatMessage
                if ev.item.role == "assistant" and ev.item.text_content:
                    logger.info(f"--- BOT: {ev.item.text_content} ---")
                    if self.transcription:
                        asyncio.create_task(self.transcription.on_transcript(
                            type('Event', (), {'participant': type('P', (), {'identity': 'AI_Interviewer'})(), 'text': ev.item.text_content, 'is_final': True})
                        ))

            # 4. Connect and Start
            await ctx.connect()
            logger.info(f"Connected to room: {ctx.room.name}")

            # Start the session (Modern API requires the agent)
            # Setting record=False to avoid 401 errors in LiveKit Cloud
            # Local recording manager still handles candidate data
            await self.session.start(self.agent, room=ctx.room, record=False)
            self.start_time = datetime.now()
            logger.info("AgentSession started")

            # Greet the candidate using the RealtimeModel's native generation
            # Since .say() requires a TTS, we push a message to history and generate
            self.session.history.add_message(
                role="assistant",
                content="Hi! I'm your AI interviewer. How are you doing today?"
            )
            self.session.generate_reply()

            # 5. Monitor
            await self._monitor_interview_duration(ctx)
            
        except Exception as e:
            logger.error(f"Error in multimodal interview: {e}")
            raise
        finally:
            # CLEANUP: Ensure recordings and transcripts are saved
            logger.info("Multimodal session cleanup starting...")
            if self.recorder:
                try:
                    info = self.recorder.stop_recording()
                    logger.info(f"Recording stopped: {info}")
                except: pass
            
            if self.transcription:
                try:
                    transcript_text = self.transcription.get_full_transcript()
                    os.makedirs("transcripts", exist_ok=True)
                    path = f"transcripts/{self.candidate_id}_transcript.txt"
                    with open(path, "w") as f:
                        f.write(transcript_text)
                    logger.info(f"Final transcript saved to {path}")
                except: pass
            
            logger.info("Cleanup complete.")

    async def _monitor_interview_duration(self, ctx: JobContext):
        max_duration_seconds = self.interview_duration * 60
        while True:
            await asyncio.sleep(60)
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                if elapsed >= max_duration_seconds:
                    logger.info("Interview limit reached.")
                    await ctx.room.disconnect()
                    break

async def entrypoint(ctx: JobContext):
    logger.info(f"JOB RECEIVED: {ctx.job.id}")
    
    # Get metadata
    room_metadata = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
    candidate_id = room_metadata.get("candidate_id", "unknown")
    job_role = room_metadata.get("job_role", "software_engineer")
    
    agent = InterviewAgent(candidate_id=candidate_id, job_role=job_role)
    await agent.start_interview(ctx)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )