/**
 * AI Interview Agent - Node.js Implementation
 * Uses LiveKit Agents Framework (1.0+) and Gemini Multimodal Live API
 */

import { cli, defineAgent, voice, WorkerOptions } from '@livekit/agents';
import { RoomEvent, DataPacketKind } from '@livekit/rtc-node';
import * as google from '@livekit/agents-plugin-google';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { getInterviewPrompt } from './prompts.js';
import { CloudRecordingManager } from './cloud-recording-manager.js';
import { TranscriptionHandler } from './transcription-handler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load env vars from parent if needed
dotenv.config({ path: path.join(__dirname, '../.env') });
dotenv.config();

export default defineAgent({
    entry: async (ctx) => {
        console.log("=".repeat(60));
        console.log(`NEW JOB RECEIVED: ${ctx.jobId}`);
        console.log(`Room: ${ctx.room.name}`);
        console.log("=".repeat(60));

        // 1. Connect to room first
        await ctx.connect();

        // 2. Initialize Metadata
        const roomMetadata = ctx.room.metadata ? JSON.parse(ctx.room.metadata) : {};
        const candidateId = roomMetadata.candidate_id || ctx.room.name;
        const jobRole = roomMetadata.job_role || 'software_engineer';
        const interviewDuration = 30; // minutes

        console.log(`Candidate ID: ${candidateId}`);
        console.log(`Job Role: ${jobRole}`);

        // 3. Setup Components
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const uniqueSessionId = `session_${timestamp}`;

        const recorder = new CloudRecordingManager();
        const transcription = new TranscriptionHandler(`${candidateId}_${uniqueSessionId}`);

        // 4. Setup Gemini Multimodal Model
        const instructions = getInterviewPrompt(jobRole);

        // Using RealtimeModel for multimodal support in Agents 1.0
        const model = new google.beta.realtime.RealtimeModel({
            model: "gemini-2.0-flash",
            apiKey: process.env.GOOGLE_API_KEY,
            instructions: instructions,
            voice: "Puck",
        });

        // Use AgentSession in 1.0+ for unified orchestration
        const session = new voice.AgentSession({
            llm: model,
        });

        // 5. Cleanup Logic
        let isCleaningUp = false;
        const handleCleanup = async () => {
            if (isCleaningUp) return;
            isCleaningUp = true;

            console.log("=".repeat(60));
            console.log("STARTING CLEANUP AND SAVING RECORDINGS...");
            console.log("=".repeat(60));

            // Stop recording
            let downloadUrl = null;
            try {
                const egress = await recorder.stopRecording();
                if (egress && egress.fileResults && egress.fileResults.length > 0) {
                    downloadUrl = egress.fileResults[0].downloadUrl;
                }
            } catch (e) {
                console.error("Error stopping recording:", e);
            }

            // Save transcripts
            try {
                const txtPath = transcription.saveFormattedTranscript(candidateId, uniqueSessionId);
                const jsonPath = transcription.saveJsonTranscript(candidateId, uniqueSessionId);

                if (txtPath) {
                    await transcription.publishToS3(txtPath, candidateId, `${uniqueSessionId}_transcript.txt`);
                }
                if (jsonPath) {
                    await transcription.publishToS3(jsonPath, candidateId, `${uniqueSessionId}.json`);
                }
            } catch (e) {
                console.error("Error saving transcripts:", e);
            }

            // Notify Frontend
            try {
                const payload = JSON.stringify({
                    type: "INTERVIEW_ENDED",
                    status: "completed",
                    room_id: ctx.room.name,
                    egress_id: recorder.egressId || uniqueSessionId,
                    recording_url: downloadUrl,
                    message: "Interview completed. Recording and transcripts are processing."
                });

                if (ctx.room.localParticipant) {
                    await ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(payload),
                        { topic: "interview_status" }
                    );
                    console.log("✓ Sent INTERVIEW_ENDED data packet");
                }
            } catch (e) {
                console.error("Failed to send data packet:", e);
            }
        };

        // 6. Event Handlers
        ctx.room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
            if (topic === "user_actions") {
                try {
                    const data = JSON.parse(new TextDecoder().decode(payload));
                    if (data.type === "USER_ENDED_CALL") {
                        console.log("Received USER_ENDED_CALL signal");
                        handleCleanup();
                    }
                } catch (e) {
                    console.error("Failed to process data packet:", e);
                }
            }
        });

        // Handle transcription events from Google plugin via and session
        session.on('user_transcript', (transcript) => {
            if (transcript.text && transcript.isFinal) {
                console.log(`--- USER: ${transcript.text} ---`);
                transcription.onTranscript({
                    speaker: candidateId,
                    text: transcript.text,
                    isFinal: true
                });

                // Send to frontend
                const transcriptData = JSON.stringify({
                    type: 'TRANSCRIPT',
                    speaker: 'user',
                    text: transcript.text,
                    timestamp: new Date().toISOString()
                });

                if (ctx.room.localParticipant) {
                    ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(transcriptData),
                        { reliable: true, topic: "transcripts" }
                    );
                }
            }
        });

        session.on('agent_transcript', (transcript) => {
            if (transcript.text && transcript.isFinal) {
                console.log(`--- BOT: ${transcript.text} ---`);
                transcription.onTranscript({
                    speaker: 'AI_Interviewer',
                    text: transcript.text,
                    isFinal: true
                });

                // Send to frontend
                const transcriptData = JSON.stringify({
                    type: 'TRANSCRIPT',
                    speaker: 'bot',
                    text: transcript.text,
                    timestamp: new Date().toISOString()
                });

                if (ctx.room.localParticipant) {
                    ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(transcriptData),
                        { reliable: true, topic: "transcripts" }
                    );
                }
            }
        });

        // 7. Start Agent Session
        await session.start(ctx.room);
        console.log("Agent session started.");

        // Initial Greeting
        setTimeout(() => {
            if (session.running) {
                session.say("Hi! I'm your AI interviewer. How are you doing today?");
            } else {
                console.warn("Agent session not running, skipping initial greeting.");
            }
        }, 1500);

        // 8. Monitor Duration
        const startTime = Date.now();
        const interval = setInterval(async () => {
            const elapsed = (Date.now() - startTime) / 1000;
            if (elapsed >= interviewDuration * 60) {
                console.log("INTERVIEW TIME LIMIT REACHED");
                session.say("Thank you for your time! The interview has concluded. Have a great day!");
                setTimeout(async () => {
                    await handleCleanup();
                    await ctx.room.disconnect();
                    clearInterval(interval);
                }, 5000);
            }
        }, 30000);

        // Handle room disconnection
        ctx.room.on(RoomEvent.Disconnected, () => {
            handleCleanup();
        });
    },
});

// Run the agent
cli.runApp(new WorkerOptions({
    agent: fileURLToPath(import.meta.url),
}));
