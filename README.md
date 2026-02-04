# AI Interview System

A production-ready AI-powered interview system using LiveKit and Google's Gemini Live API. Conducts one-on-one interviews with candidates, records complete sessions, and provides automated evaluation.

## Features

- 🎙️ **Real-time Voice Interviews**: Natural, human-like conversations using Gemini Live API
- 📹 **Complete Recording**: Full audio/video recording of interview sessions
- 📝 **Live Transcription**: Real-time transcription with speaker identification
- 🤖 **AI Evaluation**: Automated interview assessment and scoring
- 📊 **Multiple Roles**: Pre-configured prompts for different job positions
- 🔒 **Secure**: Enterprise-grade security with LiveKit infrastructure
- ☁️ **Cloud Storage**: Support for AWS S3 and Google Cloud Storage

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Candidate  │─────▶│  LiveKit     │◀────▶│   Gemini    │
│  (Browser)  │      │  Server      │      │  Live API   │
└─────────────┘      └──────────────┘      └─────────────┘
                           │
                           │
                     ┌─────▼──────┐
                     │   Agent    │
                     │ Application│
                     └─────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ Recording │   │Transcript │   │Evaluation │
    │  Manager  │   │  Handler  │   │  Engine   │
    └───────────┘   └───────────┘   └───────────┘
```

## Project Structure

```
ai-interview-system/
├── src/
│   ├── agent.py                 # Main interview agent
│   ├── prompts.py               # Interview prompts for different roles
│   ├── recording_manager.py    # Recording functionality
│   ├── transcription_handler.py # Transcription management
│   ├── evaluator.py            # Interview evaluation
│   └── config.py               # Configuration management
├── recordings/                  # Interview recordings
├── transcripts/                # Interview transcripts
├── evaluations/                # Evaluation reports
├── tests/                      # Test files
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Prerequisites

- Python 3.10 or higher
- Google Gemini API key
- LiveKit Cloud account (or self-hosted LiveKit server)
- Optional: AWS account (for S3 storage)

## Installation

### 1. Clone or Download the Project

```bash
cd ai-interview-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Optional (for cloud storage)
USE_CLOUD_STORAGE=false
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
```

## Getting API Keys

### Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and add to `.env` file

### LiveKit Credentials

1. Sign up at [LiveKit Cloud](https://cloud.livekit.io)
2. Create a new project
3. Go to Settings → Keys
4. Copy the URL, API Key, and API Secret to `.env` file

## Quick Start

### 1. Validate Configuration

```bash
python -c "from src.config import config; config.validate(); print('Configuration valid!')"
```

### 2. Run the Agent

```bash
cd src
python agent.py dev
```

This starts the agent in development mode. It will:
- Connect to LiveKit
- Wait for candidates to join
- Start interviews automatically
- Record and transcribe sessions

### 3. Test with a Mock Interview

You can test the system by:

1. Going to [LiveKit Playground](https://meet.livekit.io)
2. Entering your room name
3. Joining as a candidate
4. The AI interviewer will greet you and start the interview

## Usage

### Starting an Interview

The agent automatically starts when a candidate joins a LiveKit room. You can customize the interview by setting room metadata:

```python
room_metadata = {
    "candidate_id": "candidate_123",
    "job_role": "software_engineer"
}
```

### Available Job Roles

- `software_engineer` - Software Engineering positions
- `data_scientist` - Data Science positions
- `product_manager` - Product Management positions
- `frontend_developer` - Frontend Development positions
- `devops_engineer` - DevOps Engineering positions

### Custom Prompts

To add a new job role, edit `src/prompts.py`:

```python
INTERVIEW_PROMPTS = {
    "your_role": """
    Your custom interview prompt here...
    """
}
```

## Recording Management

### Local Storage (Default)

Recordings are saved to the `recordings/` directory:

```
recordings/
├── candidate_123_20250202_143020.mp4
├── candidate_456_20250202_150135.mp4
└── metadata.json
```

### Cloud Storage (S3)

To use AWS S3:

1. Set in `.env`:
```env
USE_CLOUD_STORAGE=true
AWS_ACCESS_KEY=your_key
AWS_SECRET_KEY=your_secret
AWS_BUCKET=your-bucket-name
```

2. Ensure your S3 bucket exists and has proper permissions

## Evaluation

### Running Evaluation

After an interview, run the evaluator:

```python
from src.evaluator import InterviewEvaluator
from src.transcription_handler import TranscriptionHandler

# Load transcript
handler = TranscriptionHandler("interview_id")
transcript = handler.get_full_transcript()

# Evaluate
evaluator = InterviewEvaluator()
evaluation = await evaluator.evaluate_interview(
    transcript=transcript,
    job_role="software_engineer",
    candidate_id="candidate_123"
)

# Save results
evaluator.save_evaluation(evaluation)
```

### Evaluation Output

Evaluations include:

- Overall score (1-10)
- Recommendation (Hire/No Hire/Maybe)
- Strengths and areas for improvement
- Detailed scores (technical, communication, problem-solving, etc.)
- Key observations and standout moments
- Detailed feedback
- Next steps recommendation

## Customization

### Interview Duration

Set in `.env`:
```env
INTERVIEW_DURATION_MINUTES=30
```

### Voice Selection

Available voices: `Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`

Change in `src/config.py`:
```python
GEMINI_VOICE: str = "Charon"
```

### Temperature (Creativity)

Adjust response creativity (0.0 - 1.0):

```python
GEMINI_TEMPERATURE: float = 0.7
```

## Deployment

### Development Deployment

```bash
python src/agent.py dev
```

### Production Deployment

#### Option 1: Deploy to LiveKit Cloud

```bash
livekit-cli agent deploy
```

#### Option 2: Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/agent.py", "start"]
```

Build and run:
```bash
docker build -t ai-interview-system .
docker run --env-file .env ai-interview-system
```

#### Option 3: Self-Hosted with systemd

Create `/etc/systemd/system/interview-agent.service`:

```ini
[Unit]
Description=AI Interview Agent
After=network.target

[Service]
Type=simple
User=interview
WorkingDirectory=/opt/ai-interview-system
Environment="PATH=/opt/ai-interview-system/venv/bin"
ExecStart=/opt/ai-interview-system/venv/bin/python src/agent.py start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable interview-agent
sudo systemctl start interview-agent
```

## Monitoring

### Logs

Application logs are written to stdout. Configure log level in `.env`:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Metrics

Key metrics to monitor:

- Interview duration
- Recording success rate
- API latency (Gemini and LiveKit)
- Concurrent interviews
- Error rates

### Health Check

```python
# health_check.py
from src.config import config

try:
    config.validate()
    print("✓ Configuration valid")
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

## Troubleshooting

### Common Issues

**Issue: "GOOGLE_API_KEY not found"**
- Solution: Ensure `.env` file exists and contains `GOOGLE_API_KEY`

**Issue: Recording fails**
- Solution: Check storage credentials and disk space
- Verify LiveKit Egress is enabled in your project

**Issue: High latency**
- Solution: Use a LiveKit edge location closer to users
- Consider audio-only recording for better performance

**Issue: Transcription accuracy**
- Solution: Ensure good audio quality
- Use noise cancellation
- Consider using a dedicated STT model

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python src/agent.py dev
```

## Testing

### Run Tests

```bash
pytest tests/
```

### Mock Interview Test

```bash
python tests/test_mock_interview.py
```

## Security Best Practices

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Rotate keys regularly
3. **Encryption**: Enable encryption at rest for recordings
4. **Access Control**: Use LiveKit room tokens with expiration
5. **Data Retention**: Implement automatic deletion policies
6. **Audit Logs**: Keep logs of all interview activities

## Cost Optimization

- Use `gemini-2.5-flash` model for lower costs
- Set appropriate temperature (lower = more consistent, less expensive)
- Implement max token limits
- Use audio-only recording when video not needed
- Compress recordings for storage
- Set up budget alerts in cloud platforms

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

- Documentation: See this README and code comments
- LiveKit Docs: https://docs.livekit.io
- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- Issues: Create an issue in the repository

## Acknowledgments

- Built with [LiveKit](https://livekit.io)
- Powered by [Google Gemini](https://ai.google.dev)
- Inspired by the future of AI-assisted hiring

## Roadmap

- [ ] Multi-language support
- [ ] Video analysis (facial expressions, body language)
- [ ] Integration with ATS systems
- [ ] Candidate dashboard
- [ ] Interviewer training mode
- [ ] Custom question banks
- [ ] Real-time interviewer assistance
- [ ] Interview analytics dashboard

---

**Built with ❤️ for better hiring experiences**
