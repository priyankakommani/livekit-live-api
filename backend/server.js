import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { AccessToken, EgressClient, RoomServiceClient } from 'livekit-server-sdk';
import AWS from 'aws-sdk';
import { v4 as uuidv4 } from 'uuid';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true
}));
app.use(express.json());

// LiveKit Configuration
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;

if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET || !LIVEKIT_URL) {
    console.error('❌ Missing LiveKit credentials in .env');
    process.exit(1);
}

// AWS S3 Configuration
const awsRegion = process.env.AWS_REGION || 'us-east-1';
const s3 = new AWS.S3({
    accessKeyId: process.env.AWS_ACCESS_KEY,
    secretAccessKey: process.env.AWS_SECRET_KEY,
    region: awsRegion,
    endpoint: `https://s3.${awsRegion}.amazonaws.com`,
    s3ForcePathStyle: false,
});

const egressClient = new EgressClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
const roomService = new RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);

// In-memory storage for interview sessions (in production, use a database)
const interviewSessions = new Map();

/**
 * POST /api/interview/start
 * Creates a new interview session and returns room details
 */
app.post('/api/interview/start', async (req, res) => {
    try {
        const { candidateName, jobRole } = req.body;

        if (!candidateName) {
            return res.status(400).json({ error: 'Candidate name is required' });
        }

        // Generate unique identifiers
        const sessionId = uuidv4();
        const candidateId = candidateName.toLowerCase().replace(/\s+/g, '_');
        const roomName = `interview_${candidateId}_${Date.now()}`;
        const timestamp = new Date().toISOString();

        // Create LiveKit access token
        const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
            identity: candidateId,
            name: candidateName,
            metadata: JSON.stringify({
                candidate_id: candidateId,
                job_role: jobRole || 'software_engineer',
                session_id: sessionId
            })
        });

        at.addGrant({
            roomJoin: true,
            room: roomName,
            canPublish: true,
            canSubscribe: true,
            canPublishData: true
        });

        const token = await at.toJwt();

        // Store session info
        const sessionData = {
            sessionId,
            roomName,
            candidateId,
            candidateName,
            jobRole: jobRole || 'software_engineer',
            startTime: timestamp,
            status: 'active',
            recordingKey: null,
            egressId: null
        };

        interviewSessions.set(sessionId, sessionData);
        interviewSessions.set(roomName, sessionData); // Also index by room name

        console.log(`✅ Created interview session: ${sessionId}`);
        console.log(`   Room: ${roomName}`);
        console.log(`   Candidate: ${candidateName}`);

        res.json({
            success: true,
            sessionId,
            roomName,
            token,
            url: LIVEKIT_URL,
            candidateId,
            message: 'Interview session created successfully'
        });

    } catch (error) {
        console.error('Error creating interview session:', error);
        res.status(500).json({
            error: 'Failed to create interview session',
            details: error.message
        });
    }
});

/**
 * POST /api/interview/end
 * Marks an interview as ended and returns session details
 */
app.post('/api/interview/end', async (req, res) => {
    try {
        const { sessionId, roomName } = req.body;

        const session = interviewSessions.get(sessionId) || interviewSessions.get(roomName);

        if (!session) {
            return res.status(404).json({ error: 'Session not found' });
        }

        session.status = 'completed';
        session.endTime = new Date().toISOString();

        console.log(`✅ Interview ended: ${session.sessionId}`);

        res.json({
            success: true,
            sessionId: session.sessionId,
            roomName: session.roomName,
            message: 'Interview ended successfully. Recording will be available shortly.'
        });

    } catch (error) {
        console.error('Error ending interview:', error);
        res.status(500).json({
            error: 'Failed to end interview',
            details: error.message
        });
    }
});

/**
 * GET /api/interview/:sessionId
 * Get interview session details
 */
app.get('/api/interview/:sessionId', async (req, res) => {
    try {
        const { sessionId } = req.params;
        const session = interviewSessions.get(sessionId);

        if (!session) {
            return res.status(404).json({ error: 'Session not found' });
        }

        res.json({
            success: true,
            session
        });

    } catch (error) {
        console.error('Error fetching session:', error);
        res.status(500).json({
            error: 'Failed to fetch session',
            details: error.message
        });
    }
});

/**
 * GET /api/recording/:roomName
 * Get recording URL for a specific room
 */
app.get('/api/recording/:roomName', async (req, res) => {
    try {
        const { roomName } = req.params;
        const session = interviewSessions.get(roomName);

        if (!session) {
            return res.status(404).json({ error: 'Session not found' });
        }

        // Try to find the recording in S3
        const candidateId = session.candidateId;
        const prefix = `ai_interview/${candidateId}/`;

        const s3Params = {
            Bucket: process.env.AWS_BUCKET,
            Prefix: prefix
        };

        const s3Data = await s3.listObjectsV2(s3Params).promise();

        if (!s3Data.Contents || s3Data.Contents.length === 0) {
            return res.json({
                success: false,
                message: 'Recording not yet available. Please wait a few moments.',
                status: 'processing'
            });
        }

        // Get the most recent recording
        const sortedFiles = s3Data.Contents
            .filter(file => file.Key.endsWith('.mp4'))
            .sort((a, b) => b.LastModified - a.LastModified);

        if (sortedFiles.length === 0) {
            return res.json({
                success: false,
                message: 'Recording not yet available. Please wait a few moments.',
                status: 'processing'
            });
        }

        const recordingKey = sortedFiles[0].Key;

        // Generate a signed URL (valid for 1 hour)
        const signedUrl = s3.getSignedUrl('getObject', {
            Bucket: process.env.AWS_BUCKET,
            Key: recordingKey,
            Expires: 3600 // 1 hour
        });

        // Also get transcript if available
        const transcriptKey = recordingKey.replace('.mp4', '_transcript.txt');
        let transcriptUrl = null;

        try {
            await s3.headObject({
                Bucket: process.env.AWS_BUCKET,
                Key: transcriptKey
            }).promise();

            transcriptUrl = s3.getSignedUrl('getObject', {
                Bucket: process.env.AWS_BUCKET,
                Key: transcriptKey,
                Expires: 3600
            });
        } catch (err) {
            // Transcript not available yet
            console.log('Transcript not yet available for', roomName);
        }

        res.json({
            success: true,
            recordingUrl: signedUrl,
            transcriptUrl,
            recordingKey,
            status: 'available',
            message: 'Recording is ready'
        });

    } catch (error) {
        console.error('Error fetching recording:', error);
        res.status(500).json({
            error: 'Failed to fetch recording',
            details: error.message
        });
    }
});

/**
 * GET /api/recordings/list
 * List all recordings
 */
app.get('/api/recordings/list', async (req, res) => {
    try {
        const s3Params = {
            Bucket: process.env.AWS_BUCKET,
            Prefix: 'ai_interview/'
        };

        const s3Data = await s3.listObjectsV2(s3Params).promise();

        const recordings = s3Data.Contents
            .filter(file => file.Key.endsWith('.mp4'))
            .map(file => ({
                key: file.Key,
                size: file.Size,
                lastModified: file.LastModified,
                candidateId: file.Key.split('/')[1]
            }))
            .sort((a, b) => b.lastModified - a.lastModified);

        res.json({
            success: true,
            recordings,
            count: recordings.length
        });

    } catch (error) {
        console.error('Error listing recordings:', error);
        res.status(500).json({
            error: 'Failed to list recordings',
            details: error.message
        });
    }
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        livekit: !!LIVEKIT_API_KEY,
        s3: !!process.env.AWS_ACCESS_KEY
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚀 AI Interview System - Backend API                   ║
║                                                           ║
║   Status: Running                                         ║
║   Port: ${PORT}                                          ║
║   LiveKit: Connected                                      ║
║   S3 Storage: ${process.env.AWS_BUCKET ? 'Configured' : 'Not configured'}                                  ║
║                                                           ║
║   Endpoints:                                              ║
║   POST   /api/interview/start                            ║
║   POST   /api/interview/end                              ║
║   GET    /api/interview/:sessionId                       ║
║   GET    /api/recording/:roomName                        ║
║   GET    /api/recordings/list                            ║
║   GET    /health                                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    `);
});

export default app;
