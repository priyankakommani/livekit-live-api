# System Architecture

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                            │
└─────────────────────────────────────────────────────────────────┘

1. HOME PAGE (localhost:5173)
   │
   ├─ User enters name: "John Doe"
   ├─ Selects role: "Software Engineer"
   └─ Clicks "Start Interview"
      │
      ▼
2. BACKEND API (localhost:3001/api/interview/start)
   │
   ├─ Generates room: "interview_john_doe_1708088400"
   ├─ Creates LiveKit token
   ├─ Stores session in memory
   └─ Returns: { sessionId, roomName, token, url }
      │
      ▼
3. INTERVIEW ROOM (/room/:sessionId)
   │
   ├─ Frontend connects to LiveKit
   ├─ Publishes audio/video tracks
   └─ Waits for AI interviewer
      │
      ▼
4. PYTHON AGENT (auto-joins)
   │
   ├─ Detects new room
   ├─ Joins with Gemini AI
   ├─ Starts cloud recording to S3
   └─ Begins conversation
      │
      ▼
5. INTERVIEW IN PROGRESS
   │
   ├─ AI asks questions
   ├─ User responds
   ├─ Full recording to S3
   └─ Transcripts saved
      │
      ▼
6. USER ENDS CALL
   │
   ├─ Sends "USER_ENDED_CALL" signal
   ├─ Frontend disconnects
   └─ Agent receives signal → disconnects
      │
      ▼
7. POST-INTERVIEW (/success/:sessionId)
   │
   ├─ Shows Room ID
   ├─ Polls for recording
   └─ Downloads from S3

```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                    (React + Vite + LiveKit)                     │
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐           │
│  │   Home   │→ │InterviewRoom │→ │PostInterview  │           │
│  │  Page    │  │   (LiveKit)  │  │  (Download)   │           │
│  └──────────┘  └──────────────┘  └───────────────┘           │
│       │              │                    │                    │
└───────┼──────────────┼────────────────────┼────────────────────┘
        │              │                    │
        ▼              ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND API                             │
│                    (Node.js + Express)                          │
│                                                                 │
│  POST /api/interview/start  ← Create session                   │
│  POST /api/interview/end    ← Mark complete                    │
│  GET  /api/recording/:room  ← Get S3 URL                       │
│  GET  /api/recordings/list  ← List all                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│   LiveKit Cloud  │          │    AWS S3        │
│                  │          │                  │
│  - Room mgmt     │          │  - Recordings    │
│  - WebRTC        │          │  - Transcripts   │
│  - Tokens        │          │  - Signed URLs   │
└──────────────────┘          └──────────────────┘
        ▲                              ▲
        │                              │
┌─────────────────────────────────────────────────────────────────┐
│                      PYTHON AGENT                               │
│              (LiveKit Agent + Gemini AI)                        │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                │
│  │ agent.py │→ │ Gemini   │→ │  Recording   │                │
│  │          │  │ Live API │  │  Manager     │                │
│  └──────────┘  └──────────┘  └──────────────┘                │
│                                                                 │
│  - Auto-joins rooms                                            │
│  - Conducts interviews                                         │
│  - Records to S3                                               │
│  - Saves transcripts                                           │
│  - Disconnects on signal                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Enter details
     ▼
┌──────────────┐
│   Frontend   │
└────┬─────────┘
     │ 2. POST /api/interview/start
     ▼
┌──────────────┐
│   Backend    │
└────┬─────────┘
     │ 3. Create room + token
     ▼
┌──────────────┐
│  LiveKit     │
└────┬─────────┘
     │ 4. Room created
     ▼
┌──────────────┐
│ Python Agent │ ← Auto-joins
└────┬─────────┘
     │ 5. Start recording
     ▼
┌──────────────┐
│   AWS S3     │ ← Stores recording
└──────────────┘
     │
     │ 6. Interview ends
     ▼
┌──────────────┐
│   Frontend   │ ← Polls for recording
└────┬─────────┘
     │ 7. GET /api/recording/:room
     ▼
┌──────────────┐
│   Backend    │ ← Generates signed URL
└────┬─────────┘
     │ 8. Returns S3 URL
     ▼
┌──────────────┐
│     User     │ ← Downloads recording
└──────────────┘
```

## File Organization

```
ai-interview-system/
│
├── backend/                    # Node.js API Server
│   ├── server.js              # Express app with endpoints
│   ├── package.json           # Dependencies
│   └── .env                   # LiveKit + AWS credentials
│
├── frontend/                   # React UI
│   ├── src/
│   │   ├── main.jsx           # Entry point
│   │   ├── App.jsx            # Router setup
│   │   ├── Home.jsx           # Landing page
│   │   ├── InterviewRoom.jsx  # Live interview UI
│   │   ├── PostInterview.jsx  # Success + download
│   │   └── index.css          # Global styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js         # Vite config + proxy
│   └── tailwind.config.js     # Tailwind theme
│
├── src/                        # Python Agent (UNCHANGED)
│   ├── agent.py               # Main agent logic
│   ├── cloud_recording_manager.py
│   ├── transcription_handler.py
│   ├── prompts.py
│   ├── config.py
│   └── .env                   # Python env vars
│
├── README_MONOREPO.md         # Full documentation
├── START_HERE.md              # Quick start
├── IMPLEMENTATION_SUMMARY.md  # What was built
├── ARCHITECTURE.md            # This file
└── setup-monorepo.sh          # Setup script
```

## Technology Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **React Router** - Navigation
- **LiveKit Client** - WebRTC
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend
- **Node.js** - Runtime
- **Express** - Web framework
- **LiveKit Server SDK** - Token generation
- **AWS SDK** - S3 access
- **UUID** - Session IDs

### Agent (Python)
- **LiveKit Agents** - Framework
- **Google Gemini** - AI model
- **Python 3.10+** - Runtime
- **asyncio** - Async operations

## Security Model

```
┌──────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
└──────────────────────────────────────────────────────────────┘

1. Environment Variables
   ├─ All secrets in .env files
   ├─ Never committed to git
   └─ Different per environment

2. LiveKit Tokens
   ├─ Generated per session
   ├─ Room-specific access
   ├─ Time-limited
   └─ Cannot be reused

3. S3 Signed URLs
   ├─ Generated on-demand
   ├─ 1-hour expiration
   ├─ Read-only access
   └─ No permanent public URLs

4. CORS
   ├─ Backend only accepts frontend origin
   ├─ Credentials: true
   └─ Prevents unauthorized access

5. Data Isolation
   ├─ Each interview in separate room
   ├─ Recordings in candidate-specific folders
   └─ No cross-contamination
```

## Scalability

```
Current Setup (Development):
├─ Backend: Single instance
├─ Frontend: Static files
└─ Agent: Single worker

Production Setup:
├─ Backend: Multiple instances (load balanced)
├─ Frontend: CDN (Vercel/Netlify)
├─ Agent: Multiple workers (LiveKit Cloud)
└─ Database: Add for session persistence
```

---

**This architecture ensures:**
- ✅ Clean separation of concerns
- ✅ Easy to maintain and extend
- ✅ Scalable for production
- ✅ Secure by design
- ✅ No changes to working Python code
