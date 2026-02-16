const express = require('express');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');
const { AccessToken, EgressClient, EncodedFileOutput } = require('livekit-server-sdk');
const WebSocket = require('ws');

dotenv.config();

const app = express();
const server = require('http').createServer(app);
const wss = new WebSocket.Server({ server, path: '/api/gemini' });
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'web')));

// LiveKit configuration
const LIVEKIT_URL = process.env.LIVEKIT_URL || 'wss://your-project.livekit.cloud';
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;

if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
    console.error('Missing LiveKit API keys in .env');
    process.exit(1);
}

const egressClient = new EgressClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);

/**
 * Endpoint to generate a LiveKit token
 */
app.post('/api/token', async (req, res) => {
    try {
        const { candidateId, jobRole, candidateName } = req.body;
        if (!candidateId) return res.status(400).json({ error: 'candidateId is required' });

        const roomName = `interview_${candidateId}_${Date.now()}`;
        const participantIdentity = candidateName || candidateId;

        const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
            identity: participantIdentity,
            name: participantIdentity,
            metadata: JSON.stringify({
                candidate_id: candidateId,
                job_role: jobRole || 'software_engineer',
            }),
        });

        at.addGrant({
            roomJoin: true,
            room: roomName,
            canPublish: true,
            canSubscribe: true,
        });

        const token = await at.toJwt();

        res.json({
            token,
            roomName,
            url: LIVEKIT_URL
        });
    } catch (error) {
        console.error('Error generating token:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

/**
 * Endpoint to start recording
 * Triggered by frontend once the room is active
 */
app.post('/api/record/start', async (req, res) => {
    const { roomName } = req.body;

    if (process.env.USE_CLOUD_STORAGE === 'true') {
        try {
            const timestamp = Date.now();
            const fileOutput = new EncodedFileOutput({
                filepath: `recordings/${roomName}_${timestamp}.mp4`,
                s3: {
                    bucket: process.env.AWS_BUCKET,
                    accessKey: process.env.AWS_ACCESS_KEY,
                    secret: process.env.AWS_SECRET_KEY,
                    endpoint: process.env.AWS_ENDPOINT || 's3.amazonaws.com',
                },
            });

            // We use RoomCompositeEgress to capture the whole interview
            await egressClient.startRoomCompositeEgress(roomName, {
                file: fileOutput,
                layout: 'speaker-view',
            });
            console.log(`Started recording for room: ${roomName}`);
            res.json({ status: 'success', message: 'Recording started' });
        } catch (err) {
            console.error('Failed to start recording:', err);
            res.status(500).json({ error: err.message });
        }
    } else {
        res.json({ status: 'skipped', message: 'Cloud storage disabled' });
    }
});

/**
 * Gemini WebSocket Proxy
 */
wss.on('connection', (ws) => {
    console.log('Frontend connected to Gemini Proxy');

    const GEMINI_API_KEY = process.env.GOOGLE_API_KEY;
    const geminiUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenericService/MultimodalLive?key=${GEMINI_API_KEY}`;

    const geminiWs = new WebSocket(geminiUrl);

    geminiWs.on('open', () => {
        console.log('Connected to Google Gemini API');
    });

    geminiWs.on('message', (data) => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(data);
        }
    });

    ws.on('message', (data) => {
        if (geminiWs.readyState === WebSocket.OPEN) {
            geminiWs.send(data);
        }
    });

    ws.on('close', () => {
        geminiWs.close();
    });

    geminiWs.on('close', () => {
        ws.close();
    });
});

server.listen(port, () => {
    console.log(`
🚀 AI Interview Server is running!
-----------------------------------
Local:   http://localhost:${port}
Room:    LiveKit Cloud (${LIVEKIT_URL})
-----------------------------------
    `);
});
