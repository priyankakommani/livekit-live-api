# """
# AI Interview Agent - Pure Gemini Multimodal implementation
# Main agent implementation using LiveKit and Gemini Multimodal Live API
# """

# import os
# import json
# import logging
# import asyncio
# from datetime import datetime
# from pathlib import Path
# from dotenv import load_dotenv

# # Load environment variables
# project_root = Path(__file__).parent.parent
# env_path = project_root / '.env'
# load_dotenv(env_path)

# from livekit.agents import (
#     Agent,
#     AgentSession,
#     JobContext,
#     WorkerOptions,
#     cli,
#     tokenize,
# )
# from livekit.plugins import google
# from livekit import rtc

# from prompts import get_interview_prompt
# from local_recording_manager import LocalRecordingManager
# from transcription_handler import TranscriptionHandler

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# class InterviewAgent:
#     """Main interview agent class using Gemini Multimodal Live"""
    
#     def __init__(
#         self,
#         candidate_id: str,
#         job_role: str = "software_engineer",
#         interview_duration: int = 30
#     ):
#         self.candidate_id = candidate_id
#         self.job_role = job_role
#         self.interview_duration = interview_duration
#         self.start_time = None
#         self.recorder = None
#         self.transcription = None

#     async def start_interview(self, ctx: JobContext):
#         """Start the interview session"""
#         logger.info(f"--- STARTING MULTIMODAL INTERVIEW (Candidate: {self.candidate_id}) ---")
        
#         try:
#             # 1. Initialize components
#             api_key = os.getenv("GOOGLE_API_KEY")
#             interview_instructions = get_interview_prompt(self.job_role)
            
#             # Using gemini-2.5-flash-native-audio-latest which is verified to work!
#             logger.info("Initializing RealtimeModel (Gemini 2.5 Flash Native Audio)...")
#             model = google.realtime.RealtimeModel(
#                 model="gemini-2.5-flash-native-audio-latest",
#                 api_version="v1beta",
#                 api_key=api_key,
#                 instructions=interview_instructions,
#                 voice="Puck",
#             )

#             # Create the modern Agent holding the model
#             logger.info("Initializing Agent and AgentSession...")
#             self.agent = Agent(llm=model, instructions=interview_instructions)
#             self.session = AgentSession()
            
#             # 2. Setup Recording & Transcription
#             self.recorder = LocalRecordingManager()
#             self.transcription = TranscriptionHandler(
#                 interview_id=f"{self.candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#             )

#             # 3. Add Event Handlers for Transcription (Robustness)
#             @self.session.on("user_input_transcribed")
#             def _on_user_transcript(ev):
#                 if ev.transcript:
#                     logger.info(f"--- USER: {ev.transcript} ---")

#             @self.session.on("conversation_item_added")
#             def _on_item_added(ev):
#                 # ev.item is a ChatMessage
#                 if ev.item.role == "assistant" and ev.item.text_content:
#                     logger.info(f"--- BOT: {ev.item.text_content} ---")
#                     if self.transcription:
#                         asyncio.create_task(self.transcription.on_transcript(
#                             type('Event', (), {'participant': type('P', (), {'identity': 'AI_Interviewer'})(), 'text': ev.item.text_content, 'is_final': True})
#                         ))

#             # 4. Connect and Start
#             await ctx.connect()
#             logger.info(f"Connected to room: {ctx.room.name}")

#             # Start local recording (subscribes to tracks)
#             await self.recorder.start_recording(ctx.room, self.candidate_id)

#             # Start the session (Modern API requires the agent)
#             # Setting record=False to avoid 401 errors in LiveKit Cloud
#             await self.session.start(self.agent, room=ctx.room, record=False)
            
#             self.start_time = datetime.now()
#             logger.info("AgentSession started.")

#             # Greet the candidate using the RealtimeModel's native generation
#             # Since .say() requires a TTS, we push a message to history and generate
#             self.session.history.add_message(
#                 role="assistant",
#                 content="Hi! I'm your AI interviewer. How are you doing today?"
#             )
#             self.session.generate_reply()

#             # 5. Monitor
#             await self._monitor_interview_duration(ctx)
            
#         except Exception as e:
#             logger.error(f"Error in multimodal interview: {e}")
#             raise
#         finally:
#             # CLEANUP: Ensure recordings and transcripts are saved
#             logger.info("Multimodal session cleanup starting...")
#             if self.recorder:
#                 try:
#                     info = self.recorder.stop_recording()
#                     logger.info(f"Local recording stopped: {info}")
#                 except: pass
            
#             if self.transcription:
#                 try:
#                     transcript_text = self.transcription.get_full_transcript()
#                     os.makedirs("transcripts", exist_ok=True)
#                     path = f"transcripts/{self.candidate_id}_transcript.txt"
#                     with open(path, "w") as f:
#                         f.write(transcript_text)
#                     logger.info(f"Final transcript saved to {path}")
#                 except: pass
            
#             logger.info("Cleanup complete.")

#     async def _monitor_interview_duration(self, ctx: JobContext):
#         max_duration_seconds = self.interview_duration * 60
#         while True:
#             await asyncio.sleep(60)
#             if self.start_time:
#                 elapsed = (datetime.now() - self.start_time).total_seconds()
#                 if elapsed >= max_duration_seconds:
#                     logger.info("Interview limit reached.")
#                     await ctx.room.disconnect()
#                     break

# async def entrypoint(ctx: JobContext):
#     logger.info(f"JOB RECEIVED: {ctx.job.id}")
    
#     # Get metadata
#     room_metadata = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
#     candidate_id = room_metadata.get("candidate_id", "unknown")
#     job_role = room_metadata.get("job_role", "software_engineer")
    
#     agent = InterviewAgent(candidate_id=candidate_id, job_role=job_role)
#     await agent.start_interview(ctx)

# if __name__ == "__main__":
#     cli.run_app(
#         WorkerOptions(
#             entrypoint_fnc=entrypoint,
#         )
#     )

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
from cloud_recording_manager import CloudRecordingManager
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
        room_id: str,
        job_role: str = "software_engineer",
        interview_duration: int = 30
    ):
        self.candidate_id = candidate_id
        self.room_id = room_id
        self.job_role = job_role
        self.interview_duration = interview_duration
        self.start_time = None
        self.recorder = None
        self.transcription = None
        self.is_cleaning_up = False

    async def handle_cleanup(self, ctx: JobContext):
        """Handle graceful shutdown, stop recording, and notify frontend"""
        if self.is_cleaning_up:
            return
        self.is_cleaning_up = True
        
        logger.info("=" * 60)
        logger.info("STARTING CLEANUP AND SAVING RECORDINGS...")
        logger.info("=" * 60)
        
        # Stop cloud recording
        download_url = None
        if self.recorder:
            try:
                logger.info("Stopping cloud recording...")
                egress = await self.recorder.stop_recording()
                if egress:
                    logger.info(f"✓ Cloud recording process final status: {egress.status}")
                    if egress.file_results and len(egress.file_results) > 0:
                        download_url = egress.file_results[0].download_url
                        if download_url:
                            logger.info(f"Download available at: {download_url}")
                    else:
                        logger.info("Recording is processing. Check LiveKit Console.")
            except Exception as e:
                logger.error(f"Error stopping cloud recording: {e}", exc_info=True)
            
            # Additional small delay to ensure LiveKit processes the stop request
            logger.info("Waiting for recording finalization...")
            await asyncio.sleep(2)

        # Send Data Packet to frontend (to trigger popup/notification)
        try:
            payload = json.dumps({
                "type": "INTERVIEW_ENDED",
                "status": "completed",
                "room_id": self.room_id,
                "recording_url": download_url,
                "message": "Interview completed. Recording is processing."
            }).encode('utf-8')

            if ctx.room.local_participant:
                await ctx.room.local_participant.publish_data(
                    payload,
                    topic="interview_status"
                )
                logger.info("✓ Sent INTERVIEW_ENDED data packet to frontend")
                # Wait a bit for packet to be delivered
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Failed to send data packet: {e}")
        
        # Save transcription
        if self.transcription:
            logger.info("Saving transcription and uploading to S3...")
            # This triggers the S3 upload logic now built into save_formatted_transcript
            egress_id = self.recorder.egress_id if self.recorder else None
            self.transcription.save_formatted_transcript(egress_id=egress_id)
        
        # Disconnect
        logger.info("Disconnecting room...")
        await ctx.room.disconnect()
        
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
            # Use Room ID for S3 folder structure
            self.recorder = CloudRecordingManager()
            self.transcription = TranscriptionHandler(
                interview_id=self.room_id 
            )
            
            # 3. Add Event Handlers for Transcription (Robustness)
            @self.session.on("user_input_transcribed")
            def _on_user_transcript(ev):
                if ev.transcript:
                    logger.info(f"--- USER: {ev.transcript} ---")
                    if self.transcription:
                        asyncio.create_task(self.transcription.on_transcript(
                            type('Event', (), {
                                'participant': type('P', (), {'identity': self.candidate_id})(),
                                'text': ev.transcript,
                                'is_final': True
                            })
                        ))
            
            @self.session.on("conversation_item_added")
            def _on_item_added(ev):
                # ev.item is a ChatMessage
                if ev.item.role == "assistant" and ev.item.text_content:
                    logger.info(f"--- BOT: {ev.item.text_content} ---")
                    if self.transcription:
                        asyncio.create_task(self.transcription.on_transcript(
                            type('Event', (), {
                                'participant': type('P', (), {'identity': 'AI_Interviewer'})(),
                                'text': ev.item.text_content,
                                'is_final': True
                            })
                        ))
            
            # 4. Connect and Start
            # Auto-subscribe is enabled by default in newer SDK versions
            logger.info("Connecting to room...")
            await ctx.connect()
            logger.info(f"Connected to room: {ctx.room.name}")
            
            # Subscribe to data packets (for user signals like "End Call")
            @ctx.room.on("data_received")
            def on_data_received(payload: bytes, participant: rtc.RemoteParticipant, kind: rtc.DataPacketKind, topic: str = ""):
                if topic == "user_actions":
                    try:
                        data = json.loads(payload.decode('utf-8'))
                        if data.get("type") == "USER_ENDED_CALL":
                            logger.info("Received USER_ENDED_CALL signal")
                            asyncio.create_task(self.handle_cleanup(ctx))
                    except Exception as e:
                        logger.error(f"Failed to process data packet: {e}")

            # Handle user disconnecting (closing tab)
            @ctx.room.on("participant_disconnected")
            def on_participant_disconnected(participant: rtc.RemoteParticipant):
                logger.info(f"Participant disconnected: {participant.identity}")
                # If the candidate leaves, we should wrap up
                if participant.identity == self.candidate_id or "candidate" in participant.identity.lower():
                    logger.info("Candidate left the interview. Cleaning up...")
                    asyncio.create_task(self.handle_cleanup(ctx))

            # Manually subscribe to all remote tracks to ensure recording works
            for participant in ctx.room.remote_participants.values():
                for publication in participant.track_publications.values():
                    if not publication.subscribed and publication.track:
                        publication.set_subscribed(True)
                        logger.info(f"Subscribed to {publication.kind} track from {participant.identity}")
            
            # Start local recording (will now receive tracks properly)
            # Start Cloud Recording (Egress)
            try:
                logger.info("Starting cloud recording...")
                await self.recorder.start_recording(ctx.room.name, self.room_id)
            except Exception as e:
                logger.error(f"FAILED TO START CLOUD RECORDING: {e}")
                
                # Notify in chat so user knows recording isn't happening
                if self.session: 
                    self.session.history.add_message(
                        role="assistant",
                        content="Warning: Session recording could not be started. Please check server configuration."
                    )
            
            # Subscribe to tracks as they're published
            @ctx.room.on("track_published")
            def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
                logger.info(f"New track published: {publication.kind} from {participant.identity}")
                publication.set_subscribed(True)
            
            # Start the session (Modern API requires the agent)
            # Setting record=False to avoid 401 errors in LiveKit Cloud
            logger.info("Starting agent session...")
            await self.session.start(self.agent, room=ctx.room, record=False)
            
            self.start_time = datetime.now()
            logger.info("AgentSession started successfully.")
            
            # Greet the candidate using the RealtimeModel's native generation
            logger.info("Sending initial greeting...")
            self.session.history.add_message(
                role="assistant",
                content="Hi! I'm your AI interviewer. How are you doing today?"
            )
            self.session.generate_reply()
            
            # 5. Monitor interview duration
            await self._monitor_interview_duration(ctx)
            
        except Exception as e:
            logger.error(f"Error in multimodal interview: {e}", exc_info=True)
            raise
        finally:
            # CLEANUP: Ensure recordings and transcripts are saved
            await self.handle_cleanup(ctx)
    
    async def _monitor_interview_duration(self, ctx: JobContext):
        """Monitor interview duration and disconnect when time limit reached"""
        max_duration_seconds = self.interview_duration * 60
        
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                remaining = max_duration_seconds - elapsed
                
                # Log remaining time every 5 minutes
                if int(elapsed) % 300 == 0:
                    logger.info(f"Interview progress: {int(elapsed/60)} minutes elapsed, {int(remaining/60)} minutes remaining")
                
                # End interview when time limit reached
                if elapsed >= max_duration_seconds:
                    logger.info("=" * 60)
                    logger.info("INTERVIEW TIME LIMIT REACHED")
                    logger.info("=" * 60)
                    
                    # Send final message to candidate
                    try:
                        self.session.history.add_message(
                            role="assistant",
                            content="Thank you for your time! The interview has concluded. Have a great day!"
                        )
                        self.session.generate_reply()
                        await asyncio.sleep(3)  # Give time for message to be sent
                    except:
                        pass
                    
                    # Disconnect
                    await ctx.room.disconnect()
                    break


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent"""
    logger.info("=" * 60)
    logger.info(f"NEW JOB RECEIVED: {ctx.job.id}")
    logger.info(f"Room: {ctx.room.name}")
    logger.info("=" * 60)
    
    # Get metadata from room
    room_metadata = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
    candidate_id = room_metadata.get("candidate_id", "unknown")
    job_role = room_metadata.get("job_role", "software_engineer")
    print(room_metadata)
    
    # FALLBACK: Ensure we never use "unknown" for folders
    if candidate_id == "unknown":
        import uuid
        # Generate a unique session ID
        candidate_id = f"session-{datetime.now().strftime('%Y%m%d_%H%M%S')}-{str(uuid.uuid4())[:6]}"
        logger.info(f"Metadata missing. Generated fallback ID: {candidate_id}")
    
    logger.info(f"Candidate ID: {candidate_id}")
    logger.info(f"Job Role: {job_role}")
    
    room_id = ctx.room.sid
    
    # Create and start interview agent
    agent = InterviewAgent(
        candidate_id=candidate_id,
        room_id=room_id,
        job_role=job_role,
        interview_duration=30  # 30 minutes default
    )
    
    await agent.start_interview(ctx)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )

    # //upto candidate audio recording 


