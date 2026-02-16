import { EgressClient } from 'livekit-server-sdk';

export class CloudRecordingManager {
    /**
     * Manages LiveKit Cloud Recording using Egress API
     */
    constructor() {
        this.egressId = null;
        this.candidateId = null;

        // Initialize LiveKit Egress client
        this.egressClient = new EgressClient(
            process.env.LIVEKIT_URL,
            process.env.LIVEKIT_API_KEY,
            process.env.LIVEKIT_API_SECRET
        );

        console.log("Cloud recording manager initialized");
    }

    /**
     * Start cloud recording for the entire room
     */
    async startRecording(roomName, candidateId, filename) {
        this.candidateId = candidateId;

        console.log("=".repeat(60));
        console.log(`STARTING CLOUD RECORDING FOR ROOM: ${roomName}`);
        console.log("=".repeat(60));

        try {
            // Setup S3 upload if configured
            let s3Upload = null;
            if (process.env.S3_ACCESS_KEY && process.env.S3_SECRET_KEY && process.env.S3_BUCKET) {
                s3Upload = {
                    accessKey: process.env.S3_ACCESS_KEY,
                    secret: process.env.S3_SECRET_KEY,
                    region: process.env.S3_REGION || "us-east-1",
                    bucket: process.env.S3_BUCKET,
                    endpoint: process.env.S3_ENDPOINT || ""
                };
            }

            const basePath = `ai_interview/${candidateId}/${filename}.mp4`;

            const fileOutput = {
                fileType: 1, // MP4 (from livekit-server-sdk/egress.proto)
                filepath: basePath,
                s3: s3Upload
            };

            const egress = await this.egressClient.startRoomCompositeEgress(roomName, {
                layout: "grid",
                audioOnly: false,
                videoOnly: false,
                fileOutputs: [fileOutput]
            });

            this.egressId = egress.egressId;

            console.log(`✓ Cloud recording started successfully`);
            console.log(`  Egress ID: ${this.egressId}`);
            console.log(`  Room: ${roomName}`);
            console.log("=".repeat(60));

            return egress;

        } catch (error) {
            console.error(`Failed to start cloud recording:`, error);
            throw error;
        }
    }

    /**
     * Stop the cloud recording
     */
    async stopRecording() {
        if (!this.egressId) {
            console.warn("No active recording to stop");
            return null;
        }

        console.log("=".repeat(60));
        console.log("STOPPING CLOUD RECORDING");
        console.log("=".repeat(60));

        try {
            const egress = await this.egressClient.stopEgress(this.egressId);

            console.log(`✓ Cloud recording stopped successfully`);
            console.log(`  Egress ID: ${this.egressId}`);
            console.log(`  Status: ${egress.status}`);

            console.log("=".repeat(60));
            console.log("📥 TO DOWNLOAD YOUR RECORDING:");
            console.log("1. Go to LiveKit Cloud Console: https://cloud.livekit.io/");
            console.log(`2. Find recording with Egress ID: ${this.egressId}`);
            console.log("=".repeat(60));

            return egress;

        } catch (error) {
            console.error(`Error stopping cloud recording:`, error);
            return null;
        }
    }
}
