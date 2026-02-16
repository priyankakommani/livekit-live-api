# 🏗️ Why 3 Servers? Architecture Explained

## The 3 Servers

### 1. **Backend (Node.js/Express)** - Port 3001
**Purpose:** API Gateway & Session Management

**What it does:**
- Creates interview sessions
- Generates LiveKit tokens
- Manages session metadata
- Retrieves recordings from S3
- Provides REST API for frontend

**Why needed:**
- Frontend can't directly access LiveKit API (security)
- Frontend can't access AWS S3 directly (credentials)
- Centralizes business logic
- Manages authentication

### 2. **Frontend (React/Vite)** - Port 5173
**Purpose:** User Interface

**What it does:**
- Beautiful UI for users
- Connects to LiveKit for video/audio
- Displays interview room
- Shows recordings

**Why needed:**
- Users need a visual interface
- Handles WebRTC connections
- Manages user interactions

### 3. **Python Agent (LiveKit Agent)** - No port (connects to LiveKit)
**Purpose:** AI Interviewer

**What it does:**
- Listens for new interview rooms
- Joins as the "AI Interviewer"
- Uses Gemini AI for conversation
- Records the interview to S3
- Generates transcripts

**Why needed:**
- Gemini Multimodal Live API integration
- Real-time AI conversation
- Server-side recording (more reliable)
- Transcript generation

## Can We Reduce to 2 Servers?

### ❌ **Can't Remove Python Agent**
The Python agent is ESSENTIAL because:
- It's the AI interviewer itself
- Handles Gemini Multimodal Live API
- Records the interview
- Without it, there's no AI to interview the candidate

### ✅ **Could Merge Backend + Frontend**
You could combine them:
- Build frontend → Serve from backend
- Single server on one port
- But loses development flexibility

### 🎯 **Recommended: Keep All 3**
This is a **microservices architecture**:
- Each service has one responsibility
- Easy to scale independently
- Easy to debug
- Industry best practice

## Data Flow

```
User Browser (Frontend)
    ↓
    ├─→ Backend API (Create session, get token)
    │   ↓
    │   LiveKit Cloud (Room created)
    │   ↓
    └─→ LiveKit Cloud (Connect with token)
        ↓
        Python Agent (Auto-joins room)
        ↓
        Gemini AI (Conducts interview)
        ↓
        AWS S3 (Stores recording)
        ↓
        Backend API (Retrieves recording URL)
        ↓
        Frontend (Downloads recording)
```

## Production Deployment

In production, you'd deploy:
1. **Backend** → Render/Railway/Heroku
2. **Frontend** → Vercel/Netlify (static hosting)
3. **Python Agent** → Cloud VM/Docker/LiveKit Cloud

All 3 run independently and communicate through LiveKit and your backend API.

## Simplification Options

### Option A: Keep Current (Recommended)
✅ Clean separation
✅ Easy to maintain
✅ Scalable
❌ 3 terminal windows

### Option B: Merge Backend + Frontend
- Build frontend, serve from backend
- 2 servers instead of 3
- Loses hot-reload during development

### Option C: Use LiveKit Cloud Agents (Future)
- Deploy Python agent to LiveKit Cloud
- Only run backend + frontend locally
- Agent runs in cloud automatically

---

**Bottom Line:** The 3-server setup is intentional and follows best practices. Each server has a specific role and can't be easily eliminated without losing functionality.
