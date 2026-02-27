import AWS from 'aws-sdk';

export class TranscriptionHandler {
    /**
     * Handles interview transcription completely in memory
     * @param {string} interviewId - Unique interview identifier
     */
    constructor(interviewId) {
        this.interviewId = interviewId;
        this.transcript = [];
    }

    /**
     * Handle incoming transcription events
     * @param {object} event - Transcription event object
     */
    async onTranscript(event) {
        try {
            const speakerId = event.speaker || 'unknown';
            const text = event.text || '';
            const isFinal = event.isFinal !== undefined ? event.isFinal : true;

            const entry = {
                timestamp: new Date().toISOString(),
                speaker: speakerId,
                text: String(text),
                is_final: isFinal,
            };

            this.transcript.push(entry);
            // No longer saving chunks to local disk
        } catch (error) {
            console.error('Error processing transcript:', error);
        }
    }

    /**
     * Get the complete formatted transcript in clean Q&A style
     */
    getFullTranscript() {
        if (this.transcript.length === 0) return "";

        // 1. Clean and filter the raw transcript
        const cleanedEntries = this.transcript
            .filter(entry => entry.is_final && entry.text && entry.text.trim().length >= 2)
            .map(entry => ({
                speaker: entry.speaker,
                text: entry.text.trim()
            }));

        if (cleanedEntries.length === 0) return "";

        // 2. Group consecutive turns
        const groupedTurns = [];
        let currentTurn = { ...cleanedEntries[0] };

        for (let i = 1; i < cleanedEntries.length; i++) {
            const nextEntry = cleanedEntries[i];
            if (nextEntry.speaker === currentTurn.speaker) {
                if (nextEntry.text.includes(currentTurn.text)) {
                    currentTurn.text = nextEntry.text; // Use the longer one
                } else if (!currentTurn.text.includes(nextEntry.text)) {
                    currentTurn.text += " " + nextEntry.text;
                }
            } else {
                groupedTurns.push(currentTurn);
                currentTurn = { ...nextEntry };
            }
        }
        groupedTurns.push(currentTurn);

        // 3. Format with clean labels
        return groupedTurns.map(turn => {
            const speaker = turn.speaker.toLowerCase();
            const label = (speaker.includes('agent') || speaker.includes('ai_')) ? 'INTERVIEWER' : 'CANDIDATE';
            return `${label}: ${turn.text}`;
        }).join('\n\n');
    }

    getFormattedTranscriptContent(candidateId, egressId = null) {
        const formatted = this.getFullTranscript();
        return [
            `Interview Transcript`,
            `Candidate ID: ${candidateId}`,
            egressId ? `Egress ID: ${egressId}` : '',
            `Generated: ${new Date().toISOString()}`,
            '='.repeat(80),
            '',
            formatted
        ].filter(Boolean).join('\n');
    }

    getJsonTranscriptContent(candidateId) {
        const exportData = {
            candidate_id: candidateId,
            session_id: this.interviewId,
            exported_at: new Date().toISOString(),
            transcript: this.transcript,
        };
        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Upload the transcript directly to S3 without using local files
     */
    async uploadTranscriptsToS3(candidateId, uniqueSessionId) {
        const region = process.env.S3_REGION || 'ap-south-1';
        const bucket = process.env.S3_BUCKET;

        if (!bucket || !process.env.S3_ACCESS_KEY || !process.env.S3_SECRET_KEY) {
            console.warn('S3 credentials not configured. Skipping transcript upload.');
            return null;
        }

        try {
            const s3Client = new AWS.S3({
                accessKeyId: process.env.S3_ACCESS_KEY,
                secretAccessKey: process.env.S3_SECRET_KEY,
                region,
            });

            const txtContent = this.getFormattedTranscriptContent(candidateId, uniqueSessionId);
            const txtKey = `ai_interview/${candidateId}/${uniqueSessionId}_transcript.txt`;

            await s3Client.upload({
                Bucket: bucket,
                Key: txtKey,
                Body: txtContent,
                ContentType: 'text/plain'
            }).promise();

            console.log(`✓ Text transcript uploaded: s3://${bucket}/${txtKey}`);

            const jsonContent = this.getJsonTranscriptContent(candidateId);
            const jsonKey = `ai_interview/${candidateId}/${uniqueSessionId}.json`;

            await s3Client.upload({
                Bucket: bucket,
                Key: jsonKey,
                Body: jsonContent,
                ContentType: 'application/json'
            }).promise();

            console.log(`✓ JSON transcript uploaded: s3://${bucket}/${jsonKey}`);

            return {
                txtUrl: `https://${bucket}.s3.${region}.amazonaws.com/${txtKey}`,
                jsonUrl: `https://${bucket}.s3.${region}.amazonaws.com/${jsonKey}`,
            };

        } catch (error) {
            console.error('Failed to upload transcripts to S3:', error);
            return null;
        }
    }
}
