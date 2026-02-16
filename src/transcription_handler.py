import os
import json
import logging
import boto3
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
        self.transcript_dir = "transcripts"
        self.transcript_file = os.path.join(
            self.transcript_dir,
            f"{interview_id}.jsonl"
        )
        
        # Ensure transcript directory exists
        os.makedirs(self.transcript_dir, exist_ok=True)
        
    async def on_transcript(self, event):
        """
        Handle incoming transcription events with robustness
        """
        try:
            # Safely get identity and avoid coroutines
            speaker_id = "unknown"
            if hasattr(event, 'participant') and event.participant:
                speaker_id = event.participant.identity
                # If it's still a coroutine (from ctx.room.sid), stringify it or use a default
                if not isinstance(speaker_id, str):
                    speaker_id = str(speaker_id)

            transcript_entry = {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker_id,
                "text": str(event.text) if hasattr(event, 'text') else "",
                "is_final": getattr(event, 'is_final', True),
            }
            
            self.transcript.append(transcript_entry)
            await self.save_transcript_chunk(transcript_entry)
            
            logger.debug(f"Transcript Item: [{speaker_id}] {transcript_entry['text']}")
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            
    async def save_transcript_chunk(self, entry: Dict):
        """
        Save individual transcript entry to file
        
        Args:
            entry: Transcript entry dictionary
        """
        try:
            with open(self.transcript_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Error saving transcript chunk: {e}")
            
    def get_full_transcript(self, include_non_final: bool = False) -> str:
        """
        Get the complete formatted transcript in clean Q&A style.
        Ensures fragmented entries are merged and filtered.
        """
        transcript_lines = []
        
        # 1. Clean and filter the raw transcript
        cleaned_entries = []
        for entry in self.transcript:
            # ONLY take final entries to avoid "Of", "Of co" fragments
            if not entry.get('is_final', True):
                continue
            
            text = entry.get('text', '').strip()
            if not text or len(text) < 2: # Skip tiny fragments
                continue
                
            cleaned_entries.append({
                'speaker': entry.get('speaker', 'unknown'),
                'text': text
            })

        # 2. Group consecutive turns (if the same person speaks twice in a row, merge it)
        grouped_turns = []
        if not cleaned_entries:
            return ""

        current_turn = cleaned_entries[0].copy()
        
        for i in range(1, len(cleaned_entries)):
            next_entry = cleaned_entries[i]
            # If same speaker AND the text isn't a duplicate of the start of the previous text
            if next_entry['speaker'] == current_turn['speaker']:
                # Common issue: LiveKit sends "Hello" then "Hello how are you" as two SEPARATE finals.
                # We check if the new text already contains the old text or vice versa.
                if next_entry['text'] in current_turn['text']:
                    continue # Skip duplicate
                if current_turn['text'] in next_entry['text']:
                    current_turn['text'] = next_entry['text'] # Use the longer one
                else:
                    current_turn['text'] += " " + next_entry['text']
            else:
                grouped_turns.append(current_turn)
                current_turn = next_entry.copy()
        
        grouped_turns.append(current_turn)

        # 3. Format with clean labels
        for turn in grouped_turns:
            speaker = turn['speaker']
            text = turn['text']
            
            # Map "unknown" to CANDIDATE for better readability
            if "agent" in speaker.lower() or "ai_" in speaker.lower():
                label = "INTERVIEWER"
            else:
                label = "CANDIDATE"
                
            transcript_lines.append(f"{label}: {text}")
                
        return '\n\n'.join(transcript_lines) # Double newline for clear reading
        
    def save_formatted_transcript(self, candidate_id: str, egress_id: str = None):
        """
        Save formatted transcript to a text file in the structured folder
        """
        folder_path = os.path.join("ai_interview", candidate_id)
        os.makedirs(folder_path, exist_ok=True)

        filename = f"{egress_id}_transcript.txt" if egress_id else f"{self.interview_id}_transcript.txt"
        output_path = os.path.join(folder_path, filename)
            
        try:
            formatted = self.get_full_transcript()
            with open(output_path, 'w') as f:
                f.write(f"Interview Transcript\n")
                f.write(f"Candidate ID: {candidate_id}\n")
                if egress_id:
                    f.write(f"Egress ID: {egress_id}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                f.write(formatted)
                
            logger.info(f"✓ Formatted transcript saved: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving formatted transcript: {e}")
            return None

    def save_json_transcript(self, candidate_id: str, egress_id: str = None):
        """
        Save full transcript data to a JSON file in the structured folder
        """
        folder_path = os.path.join("ai_interview", candidate_id)
        os.makedirs(folder_path, exist_ok=True)

        filename = f"{egress_id}.json" if egress_id else f"{self.interview_id}.json"
        output_path = os.path.join(folder_path, filename)

        try:
            export_data = {
                'candidate_id': candidate_id,
                'session_id': self.interview_id,
                'exported_at': datetime.now().isoformat(),
                'transcript': self.transcript,
            }
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"✓ JSON transcript saved: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving JSON transcript: {e}")
            return None

    async def publish_to_s3(self, local_path: str, candidate_id: str, s3_filename: str):
        """
        Upload the transcript file to the S3 bucket using Boto3
        """
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
                region_name=os.getenv("S3_REGION", "us-east-1")
            )
            
            bucket = os.getenv("S3_BUCKET")
            s3_key = f"ai_interview/{candidate_id}/{s3_filename}"
            
            logger.info(f"Uploading transcript to S3: s3://{bucket}/{s3_key}")
            s3_client.upload_file(local_path, bucket, s3_key)
            logger.info("✓ S3 Upload successful")
            return f"https://{bucket}.s3.amazonaws.com/{s3_key}"
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
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
