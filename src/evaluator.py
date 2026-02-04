"""
Interview Evaluator
Automated evaluation and scoring of interview transcripts
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import google.generativeai as genai

logger = logging.getLogger(__name__)


class InterviewEvaluator:
    """Evaluates interview performance using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the evaluator
        
        Args:
            api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
        """
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
    async def evaluate_interview(
        self,
        transcript: str,
        job_role: str,
        candidate_id: str
    ) -> Dict:
        """
        Generate comprehensive evaluation based on interview transcript
        
        Args:
            transcript: Interview transcript text
            job_role: Job role being interviewed for
            candidate_id: Candidate identifier
            
        Returns:
            Evaluation dictionary with scores and feedback
        """
        try:
            evaluation_prompt = f"""
Analyze this interview transcript for a {job_role} position.

Transcript:
{transcript}

Provide a comprehensive evaluation in JSON format with the following structure:
{{
    "overall_score": <1-10>,
    "recommendation": "<Hire|No Hire|Maybe>",
    "strengths": [
        "strength 1",
        "strength 2",
        "strength 3"
    ],
    "areas_for_improvement": [
        "area 1",
        "area 2",
        "area 3"
    ],
    "detailed_scores": {{
        "technical_competency": <1-10>,
        "communication_skills": <1-10>,
        "problem_solving": <1-10>,
        "experience_relevance": <1-10>,
        "cultural_fit": <1-10>
    }},
    "key_observations": [
        "observation 1",
        "observation 2",
        "observation 3"
    ],
    "standout_moments": [
        "moment 1",
        "moment 2"
    ],
    "concerns": [
        "concern 1 (if any)",
        "concern 2 (if any)"
    ],
    "detailed_feedback": "A paragraph of detailed feedback about the candidate's performance",
    "next_steps_recommendation": "What should happen next in the hiring process"
}}

Guidelines:
- Be objective and fair
- Provide specific examples from the transcript
- Consider both technical and soft skills
- Be constructive in feedback
- Base scores on actual evidence from the interview

Return ONLY valid JSON, no additional text.
"""
            
            response = await self.model.generate_content_async(evaluation_prompt)
            
            # Parse JSON response
            evaluation_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if evaluation_text.startswith('```json'):
                evaluation_text = evaluation_text[7:]
            if evaluation_text.startswith('```'):
                evaluation_text = evaluation_text[3:]
            if evaluation_text.endswith('```'):
                evaluation_text = evaluation_text[:-3]
                
            evaluation = json.loads(evaluation_text.strip())
            
            # Add metadata
            evaluation['candidate_id'] = candidate_id
            evaluation['job_role'] = job_role
            evaluation['evaluated_at'] = datetime.now().isoformat()
            
            logger.info(f"Interview evaluation completed for {candidate_id}")
            return evaluation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.error(f"Response text: {response.text}")
            raise
        except Exception as e:
            logger.error(f"Error evaluating interview: {e}")
            raise
            
    async def generate_feedback_email(
        self,
        evaluation: Dict,
        candidate_name: str,
        company_name: str = "Our Company"
    ) -> str:
        """
        Generate a personalized feedback email for the candidate
        
        Args:
            evaluation: Evaluation dictionary from evaluate_interview
            candidate_name: Name of the candidate
            company_name: Name of the company
            
        Returns:
            Formatted email text
        """
        try:
            feedback_prompt = f"""
Create a professional, encouraging feedback email for {candidate_name} based on their interview evaluation.

Evaluation Summary:
- Overall Score: {evaluation.get('overall_score', 'N/A')}/10
- Recommendation: {evaluation.get('recommendation', 'N/A')}
- Strengths: {', '.join(evaluation.get('strengths', []))}
- Areas for Improvement: {', '.join(evaluation.get('areas_for_improvement', []))}
- Detailed Feedback: {evaluation.get('detailed_feedback', '')}

Requirements:
- Be professional and encouraging
- Thank them for their time
- Highlight their strengths specifically
- If areas for improvement exist, phrase constructively
- Be warm and personable
- Close with appropriate next steps
- Sign off from {company_name} Hiring Team

DO NOT include:
- Specific numerical scores
- Harsh criticism
- Anything that could be legally problematic

Return only the email body, no subject line.
"""
            
            response = await self.model.generate_content_async(feedback_prompt)
            email_body = response.text.strip()
            
            logger.info(f"Feedback email generated for {candidate_name}")
            return email_body
            
        except Exception as e:
            logger.error(f"Error generating feedback email: {e}")
            raise
            
    async def compare_candidates(
        self,
        evaluations: list[Dict],
        job_role: str
    ) -> Dict:
        """
        Compare multiple candidates for the same role
        
        Args:
            evaluations: List of evaluation dictionaries
            job_role: Job role being compared
            
        Returns:
            Comparison analysis
        """
        try:
            # Extract key information
            candidates_summary = []
            for eval in evaluations:
                candidates_summary.append({
                    'candidate_id': eval.get('candidate_id'),
                    'overall_score': eval.get('overall_score'),
                    'recommendation': eval.get('recommendation'),
                    'strengths': eval.get('strengths', []),
                    'technical_score': eval.get('detailed_scores', {}).get('technical_competency', 0),
                })
                
            comparison_prompt = f"""
Compare these candidates for a {job_role} position:

{json.dumps(candidates_summary, indent=2)}

Provide a comparison analysis in JSON format:
{{
    "ranking": [
        {{
            "candidate_id": "id",
            "rank": 1,
            "reasoning": "why they rank here"
        }}
    ],
    "top_candidate": {{
        "candidate_id": "id",
        "why": "detailed reasoning"
    }},
    "key_differentiators": [
        "differentiator 1",
        "differentiator 2"
    ],
    "hiring_recommendation": "Overall recommendation for the hiring team"
}}

Return ONLY valid JSON.
"""
            
            response = await self.model.generate_content_async(comparison_prompt)
            
            comparison_text = response.text.strip()
            if comparison_text.startswith('```json'):
                comparison_text = comparison_text[7:]
            if comparison_text.startswith('```'):
                comparison_text = comparison_text[3:]
            if comparison_text.endswith('```'):
                comparison_text = comparison_text[:-3]
                
            comparison = json.loads(comparison_text.strip())
            comparison['compared_at'] = datetime.now().isoformat()
            comparison['job_role'] = job_role
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing candidates: {e}")
            raise
            
    def save_evaluation(self, evaluation: Dict, output_dir: str = "evaluations"):
        """
        Save evaluation to file
        
        Args:
            evaluation: Evaluation dictionary
            output_dir: Directory to save evaluations
        """
        os.makedirs(output_dir, exist_ok=True)
        
        candidate_id = evaluation.get('candidate_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{candidate_id}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(evaluation, f, indent=2)
                
            logger.info(f"Evaluation saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving evaluation: {e}")
            return None


class EvaluationReport:
    """Generate formatted evaluation reports"""
    
    @staticmethod
    def generate_markdown_report(evaluation: Dict) -> str:
        """
        Generate a markdown-formatted evaluation report
        
        Args:
            evaluation: Evaluation dictionary
            
        Returns:
            Markdown formatted report
        """
        report = f"""# Interview Evaluation Report

## Candidate Information
- **Candidate ID**: {evaluation.get('candidate_id', 'N/A')}
- **Job Role**: {evaluation.get('job_role', 'N/A')}
- **Evaluation Date**: {evaluation.get('evaluated_at', 'N/A')}

## Overall Assessment
- **Overall Score**: {evaluation.get('overall_score', 'N/A')}/10
- **Recommendation**: **{evaluation.get('recommendation', 'N/A')}**

## Detailed Scores
"""
        
        detailed_scores = evaluation.get('detailed_scores', {})
        for category, score in detailed_scores.items():
            category_name = category.replace('_', ' ').title()
            report += f"- **{category_name}**: {score}/10\n"
            
        report += "\n## Strengths\n"
        for strength in evaluation.get('strengths', []):
            report += f"- {strength}\n"
            
        report += "\n## Areas for Improvement\n"
        for area in evaluation.get('areas_for_improvement', []):
            report += f"- {area}\n"
            
        report += "\n## Key Observations\n"
        for observation in evaluation.get('key_observations', []):
            report += f"- {observation}\n"
            
        if evaluation.get('standout_moments'):
            report += "\n## Standout Moments\n"
            for moment in evaluation.get('standout_moments', []):
                report += f"- {moment}\n"
                
        if evaluation.get('concerns'):
            report += "\n## Concerns\n"
            for concern in evaluation.get('concerns', []):
                report += f"- {concern}\n"
                
        report += f"\n## Detailed Feedback\n\n{evaluation.get('detailed_feedback', 'N/A')}\n"
        report += f"\n## Next Steps\n\n{evaluation.get('next_steps_recommendation', 'N/A')}\n"
        
        return report
        
    @staticmethod
    def save_markdown_report(evaluation: Dict, output_path: str):
        """Save evaluation as markdown file"""
        report = EvaluationReport.generate_markdown_report(evaluation)
        
        try:
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"Markdown report saved: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving markdown report: {e}")
            return None
