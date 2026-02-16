import fs from 'fs';
import path from 'path';
import AWS from 'aws-sdk';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class TranscriptionHandler {
    /**
     * Handles interview transcription
     * @param {string} interviewId - Unique interview identifier
     */
    constructor(interviewId) {
        this.interviewId = interviewId;
        this.transcript = [];
        this.transcriptDir = path.join(__dirname, 'transcripts');
        this.transcriptFile = path.join(this.transcriptDir, `${interviewId}.jsonl`);

        // Ensure transcript directory exists
        if (!fs.existsSync(this.transcriptDir)) {
            fs.mkdirSync(this.transcriptDir, { recursive: true });
        }
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
            await this.saveTranscriptChunk(entry);
        } catch (error) {
            console.error('Error processing transcript:', error);
        }
    }

    /**
     * Save individual transcript entry to file
     * @param {object} entry - Transcript entry
     */
    async saveTranscriptChunk(entry) {
        try {
            fs.appendFileSync(this.transcriptFile, JSON.stringify(entry) + '\n');
        } catch (error) {
            console.error('Error saving transcript chunk:', error);
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

    /**
     * Save formatted transcript to a text file
     */
    saveFormattedTranscript(candidateId, egressId = null) {
        const folderPath = path.join(__dirname, 'ai_interview', candidateId);
        if (!fs.existsSync(folderPath)) {
            fs.mkdirSync(folderPath, { recursive: true });
        }

        const filename = egressId ? `${egressId}_transcript.txt` : `${this.interviewId}_transcript.txt`;
        const outputPath = path.join(folderPath, filename);

        try {
            const formatted = this.getFullTranscript();
            const content = [
                `Interview Transcript`,
                `Candidate ID: ${candidateId}`,
                egressId ? `Egress ID: ${egressId}` : '',
                `Generated: ${new Date().toISOString()}`,
                '='.repeat(80),
                '',
                formatted
            ].filter(Boolean).join('\n');

            fs.writeFileSync(outputPath, content);
            console.log(`✓ Formatted transcript saved: ${outputPath}`);
            return outputPath;
        } catch (error) {
            console.error('Error saving formatted transcript:', error);
            return null;
        }
    }

    /**
     * Save full transcript data to a JSON file
     */
    saveJsonTranscript(candidateId, egressId = null) {
        const folderPath = path.join(__dirname, 'ai_interview', candidateId);
        if (!fs.existsSync(folderPath)) {
            fs.mkdirSync(folderPath, { recursive: true });
        }

        const filename = egressId ? `${egressId}.json` : `${this.interviewId}.json`;
        const outputPath = path.join(folderPath, filename);

        try {
            const exportData = {
                candidate_id: candidateId,
                session_id: this.interviewId,
                exported_at: new Date().toISOString(),
                transcript: this.transcript,
            };
            fs.writeFileSync(outputPath, JSON.stringify(exportData, null, 2));
            console.log(`✓ JSON transcript saved: ${outputPath}`);
            return outputPath;
        } catch (error) {
            console.error('Error saving JSON transcript:', error);
            return null;
        }
    }

    /**
     * Upload the transcript file to S3
     */
    async publishToS3(localPath, candidateId, s3Filename) {
        try {
            const s3Client = new AWS.S3({
                accessKeyId: process.env.S3_ACCESS_KEY,
                secretAccessKey: process.env.S3_SECRET_KEY,
                region: process.env.S3_REGION || 'us-east-1'
            });

            const bucket = process.env.S3_BUCKET;
            const s3Key = `ai_interview/${candidateId}/${s3Filename}`;

            console.log(`Uploading transcript to S3: s3://${bucket}/${s3Key}`);

            const fileContent = fs.readFileSync(localPath);
            await s3Client.upload({
                Bucket: bucket,
                Key: s3Key,
                Body: fileContent
            }).promise();

            console.log('✓ S3 Upload successful');
            return `https://${bucket}.s3.amazonaws.com/${s3Key}`;
        } catch (error) {
            console.error('Failed to upload to S3:', error);
            return null;
        }
    }
}
