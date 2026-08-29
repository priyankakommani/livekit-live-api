/**
 * AI Interview Agent - Node.js Implementation
 * Uses LiveKit Agents Framework (1.0+) and Gemini Multimodal Live API
 */

import { cli, defineAgent, voice, WorkerOptions } from '@livekit/agents';
import { RoomEvent } from '@livekit/rtc-node';
import * as google from '@livekit/agents-plugin-google';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { getInterviewPrompt } from './prompts.js';
import { CloudRecordingManager } from './cloud-recording-manager.js';
import { TranscriptionHandler } from './transcription-handler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load env vars explicitly so the agent can find them no matter where it is launched from.
const rootEnv = dotenv.config({ path: path.join(__dirname, '../.env') });
const backendEnv = dotenv.config({ path: path.join(__dirname, '.env') });

const pickFirstNonEmpty = (...values) => {
    for (const value of values) {
        if (typeof value !== 'string') continue;

        const trimmed = value.trim();
        if (trimmed) return trimmed;
    }

    return undefined;
};

const resolveGoogleApiKey = () => {
    const candidates = [
        { source: 'backend/.env GOOGLE_API_KEY', value: backendEnv.parsed?.GOOGLE_API_KEY },
        { source: 'backend/.env GOOGLE_GENAI_API_KEY', value: backendEnv.parsed?.GOOGLE_GENAI_API_KEY },
        { source: 'backend/.env GEMINI_API_KEY', value: backendEnv.parsed?.GEMINI_API_KEY },
        { source: 'root .env GOOGLE_API_KEY', value: rootEnv.parsed?.GOOGLE_API_KEY },
        { source: 'root .env GOOGLE_GENAI_API_KEY', value: rootEnv.parsed?.GOOGLE_GENAI_API_KEY },
        { source: 'root .env GEMINI_API_KEY', value: rootEnv.parsed?.GEMINI_API_KEY },
        { source: 'process.env GEMINI_API_KEY', value: process.env.GEMINI_API_KEY },
        { source: 'process.env GOOGLE_API_KEY', value: process.env.GOOGLE_API_KEY },
        { source: 'process.env GOOGLE_GENAI_API_KEY', value: process.env.GOOGLE_GENAI_API_KEY },
    ];

    const picked = candidates.find(({ value }) => typeof value === 'string' && value.trim());
    const apiKey = picked?.value?.trim();

    if (!apiKey) {
        throw new Error(
            'Google API key not found. Set GOOGLE_API_KEY, GOOGLE_GENAI_API_KEY, or GEMINI_API_KEY in your .env file.',
        );
    }

    console.log(`Resolved Gemini API key from ${picked.source}`);

    // Keep the resolved key in process.env so downstream SDKs can read it too.
    process.env.GOOGLE_API_KEY = apiKey;
    process.env.GOOGLE_GENAI_API_KEY = apiKey;
    process.env.GEMINI_API_KEY = apiKey;
    return apiKey;
};

export default defineAgent({
    entry: async (ctx) => {
        console.log("=".repeat(60));
        console.log("NEW JOB RECEIVED");
        console.log("=".repeat(60));

        // STEP 1: Connect to the room.
        // ctx.connect() MUST be called before any room operations.
        // Without this, ctx.waitForParticipant() throws "room is not connected".
        await ctx.connect();
        console.log("✅ Connected to room:", ctx.room.name);

        // STEP 2: Wait for the candidate to join
        const participant = await ctx.waitForParticipant();
        console.log(`✅ Participant joined: ${participant.identity}`);

        // STEP 3: Extract candidate info from participant metadata
        let candidateId = participant.identity || 'unknown';
        let jobRole = 'software_engineer';

        if (participant.metadata) {
            try {
                const meta = JSON.parse(participant.metadata);
                candidateId = meta.candidate_id || candidateId;
                jobRole = meta.job_role || jobRole;
            } catch (e) {
                console.warn("Could not parse participant metadata, using defaults");
            }
        }

        console.log(`Candidate: ${candidateId} | Role: ${jobRole} | Room: ${ctx.room.name}`);

        // STEP 4: Setup session identifiers
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const uniqueSessionId = `session_${timestamp}`;
        const interviewDuration = 30; // minutes

        const recorder = new CloudRecordingManager();
        const transcription = new TranscriptionHandler(`${candidateId}_${uniqueSessionId}`);

        // STEP 5: Build the Gemini Realtime model.
        // IMPORTANT: Must use a Gemini Live API model (bidiGenerateContent).
        // "gemini-2.0-flash-exp" was deprecated; use the preview below.
        // SDK default (non-Vertex AI): "gemini-2.5-flash-native-audio-preview-12-2025"
        const instructions = getInterviewPrompt(jobRole);
        const googleApiKey = resolveGoogleApiKey();

        const model = new google.beta.realtime.RealtimeModel({
            model: "gemini-2.5-flash-native-audio-preview-12-2025",
            apiKey: googleApiKey,
            instructions: instructions,
            voice: "Puck",
        });

        // STEP 6: Create the Agent (llm goes on Agent, agent_activity picks it up)
        const agent = new voice.Agent({
            instructions: instructions,
            llm: model,
        });

        // STEP 7: Create the AgentSession.
        // Must pass at least {} — constructor destructures opts and crashes if undefined.
        const session = new voice.AgentSession({});

        // STEP 8: Cleanup handler
        let isCleaningUp = false;
        const handleCleanup = async () => {
            if (isCleaningUp) return;
            isCleaningUp = true;

            console.log("=".repeat(60));
            console.log("CLEANUP: Stopping recording and saving transcripts...");
            console.log("=".repeat(60));

            // Stop the LiveKit egress recording
            try {
                const egress = await recorder.stopRecording();
                console.log("✅ Recording stopped. Status:", egress?.status);
            } catch (e) {
                console.error("Error stopping recording:", e.message);
            }

            // Upload transcripts to S3 (in-memory, no local files)
            try {
                const urls = await transcription.uploadTranscriptsToS3(candidateId, uniqueSessionId);
                if (urls) {
                    console.log("✅ Transcripts uploaded to S3 successfully.");
                }
            } catch (e) {
                console.error("Error uploading transcripts:", e.message);
            }

            // Notify frontend that interview is done
            try {
                if (ctx.room.localParticipant) {
                    const payload = JSON.stringify({
                        type: "INTERVIEW_ENDED",
                        status: "completed",
                        room_id: ctx.room.name,
                        egress_id: recorder.egressId || uniqueSessionId,
                        message: "Interview completed. Recording is processing."
                    });
                    await ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(payload),
                        { topic: "interview_status" }
                    );
                    console.log("✅ Sent INTERVIEW_ENDED to frontend.");
                }
            } catch (e) {
                console.error("Failed to send INTERVIEW_ENDED packet:", e.message);
            }
        };

        // STEP 9: Listen for user-triggered end-call signal
        ctx.room.on(RoomEvent.DataReceived, (payload, _participant, _kind, topic) => {
            if (topic === "user_actions") {
                try {
                    const data = JSON.parse(new TextDecoder().decode(payload));
                    if (data.type === "USER_ENDED_CALL") {
                        console.log("Received USER_ENDED_CALL — starting cleanup");
                        handleCleanup().then(() => ctx.room.disconnect()).catch(() => ctx.room.disconnect());
                    }
                } catch (e) {
                    console.error("Failed to parse data packet:", e.message);
                }
            }
        });

        // Fallback: if frontend disconnects first, run cleanup
        ctx.room.on(RoomEvent.Disconnected, () => {
            console.log("Room disconnected — running cleanup fallback");
            handleCleanup();
        });

        // STEP 10: Transcript capture — user speech
        session.on('user_input_transcribed', (ev) => {
            if (ev.transcript && ev.isFinal) {
                console.log(`USER: ${ev.transcript}`);
                transcription.onTranscript({ speaker: candidateId, text: ev.transcript, isFinal: true });

                if (ctx.room.localParticipant) {
                    ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(JSON.stringify({
                            type: 'TRANSCRIPT', speaker: 'user',
                            text: ev.transcript, timestamp: new Date().toISOString()
                        })),
                        { reliable: true, topic: "transcripts" }
                    );
                }
            }
        });

        // STEP 11: Transcript capture — bot speech
        // ChatMessage has NO .text property; use .textContent getter
        session.on('conversation_item_added', (ev) => {
            const itemText = ev.item?.textContent;
            if (ev.item?.role === 'assistant' && itemText) {
                console.log(`BOT: ${itemText}`);
                transcription.onTranscript({ speaker: 'AI_Interviewer', text: itemText, isFinal: true });

                if (ctx.room.localParticipant) {
                    ctx.room.localParticipant.publishData(
                        new TextEncoder().encode(JSON.stringify({
                            type: 'TRANSCRIPT', speaker: 'bot',
                            text: itemText, timestamp: new Date().toISOString()
                        })),
                        { reliable: true, topic: "transcripts" }
                    );
                }
            }
        });

        // Log session errors
        session.on('error', (ev) => {
            console.error("❌ Session error:", ev);
        });

        // STEP 12: Start the agent session (connects Gemini Live to the room)
        console.log("Starting agent session...");
        try {
            await session.start({ agent, room: ctx.room });
            console.log("✅ Agent session started.");
        } catch (e) {
            console.error("❌ Failed to start agent session:", e);
            return;
        }

        // STEP 13: Start LiveKit cloud recording (Egress → S3)
        // Start recording before triggering the greeting so the opening
        // words are captured.
        try {
            await recorder.startRecording(ctx.room.name, candidateId, uniqueSessionId);
            console.log("✅ Cloud recording started. Egress ID:", recorder.egressId);
        } catch (e) {
            console.error("⚠️  Could not start cloud recording:", e.message);
            // Interview continues without recording
        }

        // STEP 14: Trigger the bot's opening greeting.
        // Gemini Live does NOT speak automatically on connect — generateReply()
        // kicks off the first turn so the bot greets the candidate.
        try {
            session.generateReply();
            console.log("✅ Initial greeting triggered.");
        } catch (e) {
            console.error("⚠️  Could not trigger initial greeting:", e.message);
        }

        // STEP 15: Auto-end interview after time limit
        const startTime = Date.now();
        const interval = setInterval(async () => {
            const elapsed = (Date.now() - startTime) / 1000;
            if (elapsed >= interviewDuration * 60) {
                console.log("⏰ Interview time limit reached");
                try {
                    session.say("Thank you for your time! The interview has concluded. Have a great day!");
                } catch (e) { /* ignore */ }
                setTimeout(async () => {
                    await handleCleanup();
                    await ctx.room.disconnect();
                    clearInterval(interval);
                }, 5000);
            }
        }, 30000);

        console.log("=".repeat(60));
        console.log("✅ INTERVIEW AGENT IS LIVE AND READY");
        console.log("=".repeat(60));
    },
});

// Run the agent worker only when this file is executed directly.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    cli.runApp(new WorkerOptions({
        agent: fileURLToPath(import.meta.url),
        // Small cloud instances (Render Starter = 0.5 CPU) are slow to spin up job
        // subprocesses — each imports aws-sdk + the Google plugin + the rtc-node
        // native addon. Production defaults (3 prewarmed procs, 10s init timeout)
        // cause "runner initialization timed out" there, so relax both.
        numIdleProcesses: 1,
        initializeProcessTimeout: 60_000,
        // In production the worker's health server binds a hardcoded 8081 and
        // ignores $PORT. On hosts that route to an injected port (Render/Railway
        // web services), bind that instead so health checks pass. Falls back to
        // the framework default when PORT is unset (e.g. a background worker).
        ...(process.env.PORT ? { port: Number(process.env.PORT) } : {}),
    }));
}
