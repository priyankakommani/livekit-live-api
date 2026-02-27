import { EgressClient, S3Upload, EncodedFileOutput, EncodedFileType } from 'livekit-server-sdk';

export class CloudRecordingManager {
    constructor() {
        this.egressId = null;
        this.candidateId = null;

        this.egressClient = new EgressClient(
            process.env.LIVEKIT_URL,
            process.env.LIVEKIT_API_KEY,
            process.env.LIVEKIT_API_SECRET
        );

        console.log("Cloud recording manager initialized");
    }

    /**
     * Start cloud recording for the entire room.
     *
     * S3 upload notes:
     *  - `endpoint` must be the regional endpoint (e.g. https://s3.ap-south-1.amazonaws.com)
     *    so LiveKit Egress routes to the right AWS region.
     *  - `forcePathStyle: false` is REQUIRED for AWS S3.  When a custom endpoint is set,
     *    LiveKit Egress defaults to path-style (s3.region.amazonaws.com/bucket/key).
     *    AWS returns 301 PermanentRedirect for path-style on new buckets.
     *    Virtual-hosted style (bucket.s3.region.amazonaws.com/key) works correctly.
     */
    async startRecording(roomName, candidateId, filename) {
        this.candidateId = candidateId;

        console.log("=".repeat(60));
        console.log(`STARTING CLOUD RECORDING FOR ROOM: ${roomName}`);
        console.log("=".repeat(60));

        try {
            let s3Upload = null;
            if (process.env.S3_ACCESS_KEY && process.env.S3_SECRET_KEY && process.env.S3_BUCKET) {
                const region = process.env.S3_REGION || "us-east-1";
                s3Upload = new S3Upload({
                    accessKey: process.env.S3_ACCESS_KEY,
                    secret: process.env.S3_SECRET_KEY,
                    region,
                    endpoint: `https://s3.${region}.amazonaws.com`,
                    bucket: process.env.S3_BUCKET,
                    forcePathStyle: false,   // use virtual-hosted style: bucket.s3.region.amazonaws.com
                });
            }

            const basePath = `ai_interview/${candidateId}/${filename}.mp4`;

            const fileOutput = new EncodedFileOutput({
                fileType: EncodedFileType.MP4,
                filepath: basePath,
                ...(s3Upload && { output: { case: 's3', value: s3Upload } })
            });

            const egress = await this.egressClient.startRoomCompositeEgress(
                roomName,
                fileOutput,
                { layout: "grid" }
            );

            this.egressId = egress.egressId;

            console.log(`✓ Cloud recording started successfully`);
            console.log(`  Egress ID: ${this.egressId}`);
            console.log(`  Room: ${roomName}`);
            console.log(`  S3 path: s3://${process.env.S3_BUCKET}/${basePath}`);
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
            console.log("📥 TO VERIFY YOUR RECORDING:");
            console.log("1. Go to LiveKit Cloud Console: https://cloud.livekit.io/");
            console.log(`2. Find recording with Egress ID: ${this.egressId}`);
            console.log(`3. Or check S3 bucket: s3://${process.env.S3_BUCKET}/ai_interview/${this.candidateId}/`);
            console.log("=".repeat(60));

            return egress;

        } catch (error) {
            console.error(`Error stopping cloud recording:`, error);
            return null;
        }
    }
}
