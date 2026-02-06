"""
Transcription Handler
Manages real-time transcription and transcript storage
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class TranscriptionHandler:
    """Handles interview transcription"""
    
    def __init__(self, interview_id: str):
        """
        Initialize transcription handler
        
        Args:
            interview_id: Unique interview identifier
        """
        self.interview_id = interview_id
        self.transcript: List[Dict] = []
        self.interview_id = interview_id
        self.transcript: List[Dict] = []
        # No local directory needed, we will upload to S3 directly or keep in memory
        
    async def on_transcript(self, event):
        """
        Handle incoming transcription events
        
        Args:
            event: Transcription event from LiveKit
        """
        try:
            # Only process final transcripts to avoid noise
            if not getattr(event, 'is_final', False):
                return

            speaker = event.participant.identity if hasattr(event, 'participant') else "unknown"
            text = event.text if hasattr(event, 'text') else ""
            
            if not text.strip():
                return

            # Check if we can append to the last entry (same speaker)
            if self.transcript and self.transcript[-1]['speaker'] == speaker:
                self.transcript[-1]['text'] += " " + text
            else:
                # New entry
                transcript_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "speaker": speaker,
                    "text": text
                }
                self.transcript.append(transcript_entry)
            
            logger.debug(f"Transcript: [{speaker}] {text}")
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            
    async def save_transcript_chunk(self, entry: Dict):
        """
        No-op: In-memory buffering only. Saved to S3 at end.
        """
        pass
            
    def get_full_transcript(self, include_non_final: bool = False) -> str:
        """
        Get the complete formatted transcript
        
        Args:
            include_non_final: Include non-final (interim) transcripts
            
        Returns:
            Formatted transcript string
        """
        transcript_lines = []
        
        for entry in self.transcript:
            # Skip non-final transcripts unless requested
            if not include_non_final and not entry.get('is_final', True):
                continue
                
            timestamp = entry.get('timestamp', '')
            speaker = entry.get('speaker', 'Unknown')
            text = entry.get('text', '')
            
            # Format: [HH:MM:SS] Speaker: Text
            if timestamp:
                time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp[:8]
                transcript_lines.append(f"[{time_str}] {speaker}: {text}")
            else:
                transcript_lines.append(f"{speaker}: {text}")
                
        return '\n'.join(transcript_lines)
        
    def save_formatted_transcript(self, output_path: str = None, egress_id: str = None):
        """
        Save formatted transcript to a text file (Uploads to S3)
        
        Args:
            output_path: Optional custom output path (Ignored in S3 mode)
            egress_id: Optional LiveKit Egress ID to include in filename
        """
        try:
            # Format transcript (Q&A style)
            lines = []
            for entry in self.transcript:
                speaker_label = "Interviewer" if entry['speaker'] == "AI_Interviewer" else "Candidate"
                lines.append(f"[{speaker_label}]: {entry['text']}")
            
            formatted_content = "\n\n".join(lines)
            
            # Prepare S3 Upload
            import boto3
            if os.getenv("S3_ACCESS_KEY") and os.getenv("S3_SECRET_KEY") and os.getenv("S3_BUCKET"):
                try:
                    s3 = boto3.client(
                        's3',
                        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
                        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
                        region_name=os.getenv("S3_REGION", "us-east-1")
                    )
                    
                    filename = f"{egress_id}_transcript.txt" if egress_id else "transcript.txt"
                    key = f"ai_interview/{self.interview_id}/{filename}"
                    s3.put_object(
                        Bucket=os.getenv("S3_BUCKET"),
                        Key=key,
                        Body=formatted_content,
                        ContentType='text/plain'
                    )
                    logger.info(f"✓ Transcript uploaded to S3: s3://{os.getenv('S3_BUCKET')}/{key}")
                    return key
                except Exception as s3_err:
                    logger.error(f"Failed to upload transcript to S3: {s3_err}")
                    return None
            else:
                logger.warning("S3 credentials not found, skipping transcript upload.")
                return None

        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            return None
            
    def get_transcript_statistics(self) -> Dict:
        """
        Get statistics about the transcript
        
        Returns:
            Dictionary with transcript statistics
        """
        total_entries = len(self.transcript)
        final_entries = sum(1 for entry in self.transcript if entry.get('is_final', True))
        
        # Count by speaker
        speaker_counts = {}
        for entry in self.transcript:
            if entry.get('is_final', True):
                speaker = entry.get('speaker', 'Unknown')
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
                
        # Calculate word counts
        total_words = 0
        speaker_words = {}
        for entry in self.transcript:
            if entry.get('is_final', True):
                text = entry.get('text', '')
                words = len(text.split())
                total_words += words
                
                speaker = entry.get('speaker', 'Unknown')
                speaker_words[speaker] = speaker_words.get(speaker, 0) + words
                
        return {
            'total_entries': total_entries,
            'final_entries': final_entries,
            'speaker_counts': speaker_counts,
            'total_words': total_words,
            'speaker_words': speaker_words,
        }
        
    def export_to_json(self, output_path: str = None) -> str:
        """
        Export transcript to JSON format
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = os.path.join(
                self.transcript_dir,
                f"{self.interview_id}_export.json"
            )
            
        try:
            export_data = {
                'interview_id': self.interview_id,
                'exported_at': datetime.now().isoformat(),
                'statistics': self.get_transcript_statistics(),
                'transcript': self.transcript,
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Transcript exported to JSON: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting transcript: {e}")
            return None


class TranscriptAnalyzer:
    """Analyze interview transcripts"""
    
    def __init__(self, transcript: str):
        self.transcript = transcript
        
    def extract_questions(self) -> List[str]:
        """Extract questions asked by the interviewer"""
        questions = []
        lines = self.transcript.split('\n')
        
        for line in lines:
            # Look for lines from the interviewer (agent) with question marks
            if 'agent' in line.lower() or 'interviewer' in line.lower():
                if '?' in line:
                    # Extract the text after the speaker label
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        question = parts[1].strip()
                        questions.append(question)
                        
        return questions
        
    def extract_candidate_responses(self) -> List[str]:
        """Extract candidate responses"""
        responses = []
        lines = self.transcript.split('\n')
        
        for line in lines:
            # Look for lines from the candidate
            if 'candidate' in line.lower() or 'user' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    response = parts[1].strip()
                    if response:  # Skip empty responses
                        responses.append(response)
                        
        return responses
        
    def calculate_talk_time_ratio(self) -> Dict[str, float]:
        """
        Calculate the ratio of talk time between interviewer and candidate
        
        Returns:
            Dictionary with word counts and ratios
        """
        lines = self.transcript.split('\n')
        
        interviewer_words = 0
        candidate_words = 0
        
        for line in lines:
            word_count = len(line.split())
            
            if 'agent' in line.lower() or 'interviewer' in line.lower():
                interviewer_words += word_count
            elif 'candidate' in line.lower() or 'user' in line.lower():
                candidate_words += word_count
                
        total_words = interviewer_words + candidate_words
        
        if total_words == 0:
            return {
                'interviewer_words': 0,
                'candidate_words': 0,
                'interviewer_ratio': 0,
                'candidate_ratio': 0,
            }
            
        return {
            'interviewer_words': interviewer_words,
            'candidate_words': candidate_words,
            'interviewer_ratio': interviewer_words / total_words,
            'candidate_ratio': candidate_words / total_words,
        }
