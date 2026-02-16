# AI Interview System - Monorepo Setup

This is a complete AI-powered interview system with separate frontend and backend, maintaining all existing Python agent functionality.

## 📁 Project Structure

```
ai-interview-system/
├── backend/              # Node.js Express API
│   ├── server.js        # API endpoints for interview management
│   ├── package.json
│   └── .env
├── frontend/            # React + Vite UI
│   ├── src/
│   │   ├── Home.jsx           # Landing page
│   │   ├── InterviewRoom.jsx  # Live interview interface
│   │   └── PostInterview.jsx  # Success page with recording
│   ├── package.json
│   └── vite.config.js
├── src/                 # Python agent (UNCHANGED - working perfectly)
│   ├── agent.py         # LiveKit agent with Gemini integration
│   ├── cloud_recording_manager.py
│   └── ...
└── web/                 # Original frontend (kept for reference)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 20.9+ (for backend/frontend)
- Python 3.10+ (for agent)
- LiveKit Cloud account
- Google Gemini API key
- AWS S3 bucket (for recordings)

### Step 1: Install Backend Dependencies
```bash
cd backend
npm install
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 3: Configure Environment
The backend `.env` is already configured with your credentials. Verify it has:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `GOOGLE_API_KEY`
- `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_BUCKET`, `AWS_REGION`

### Step 4: Start the System

**Terminal 1 - Start Backend API:**
```bash
cd backend
npm start
```
Backend runs on `http://localhost:3001`

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

**Terminal 3 - Start Python Agent:**
```bash
cd src
python agent.py dev
```
Agent connects to LiveKit and waits for interview rooms.

## 🎯 How It Works

### User Flow:
1. **Home Page** (`http://localhost:5173`)
   - User enters name and selects job role
   - Clicks "Start Interview Session"

2. **Backend Creates Session**
   - Generates unique room name: `interview_{candidateId}_{timestamp}`
   - Creates LiveKit access token
   - Returns session details to frontend

3. **Interview Room**
   - Frontend connects to LiveKit with token
   - Python agent automatically joins the room
   - AI interviewer (Gemini) starts conversation
   - Full audio/video recording to S3
   - User can toggle mic/camera
   - User clicks "End Call" when done

4. **Post-Interview Page**
   - Shows unique Room ID (save this!)
   - Polls backend for recording availability
   - Downloads recording and transcript from S3

### Key Features:
✅ **Separate rooms per interview** - Each session gets unique room name  
✅ **Room ID as recording key** - Use room name to retrieve recordings  
✅ **S3 storage** - All recordings stored in `ai_interview/{candidateId}/`  
✅ **Agent auto-disconnect** - When user leaves, agent also leaves  
✅ **No manual link copying** - Everything handled through UI  

## 📡 API Endpoints

### POST `/api/interview/start`
Creates new interview session.

**Request:**
```json
{
  "candidateName": "John Doe",
  "jobRole": "software_engineer"
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "uuid-here",
  "roomName": "interview_john_doe_1234567890",
  "token": "livekit-token",
  "url": "wss://your-project.livekit.cloud"
}
```

### POST `/api/interview/end`
Marks interview as completed.

**Request:**
```json
{
  "sessionId": "uuid-here",
  "roomName": "interview_john_doe_1234567890"
}
```

### GET `/api/recording/:roomName`
Retrieves recording URL for a room.

**Response:**
```json
{
  "success": true,
  "recordingUrl": "https://s3-signed-url",
  "transcriptUrl": "https://s3-signed-url",
  "status": "available"
}
```

### GET `/api/recordings/list`
Lists all recordings in S3.

## 🔧 Troubleshooting

### Backend won't start
- Check if port 3001 is available
- Verify `.env` file exists in `backend/`
- Run `npm install` in backend folder

### Frontend won't start
- Check if port 5173 is available
- Verify Node.js version (20.9+)
- Run `npm install` in frontend folder

### Agent not joining rooms
- Ensure agent is running: `cd src && python agent.py dev`
- Check LiveKit credentials match in both `.env` files
- Verify `LIVEKIT_URL` is the same in backend and src

### Recording not found
- Wait 1-2 minutes after interview ends (processing time)
- Check S3 bucket: `ai_interview/{candidateId}/`
- Verify AWS credentials in backend `.env`

### Agent doesn't disconnect when user leaves
- The agent listens for `USER_ENDED_CALL` data packet
- Check browser console for errors
- Ensure `room.localParticipant.publishData()` is working

## 🎨 Customization

### Change Interview Duration
Edit `backend/server.js` or pass duration in metadata:
```javascript
metadata: JSON.stringify({
  candidate_id: candidateId,
  job_role: jobRole,
  interview_duration: 45 // minutes
})
```

### Add New Job Roles
Edit `src/prompts.py` to add new interview prompts.

### Customize UI Theme
Edit `frontend/tailwind.config.js` colors:
```javascript
colors: {
  primary: '#6366f1',    // Change primary color
  secondary: '#ec4899',  // Change secondary color
}
```

## 📦 Production Deployment

### Backend
```bash
cd backend
npm start
```
Deploy to: Render, Railway, Heroku, or any Node.js host

### Frontend
```bash
cd frontend
npm run build
```
Deploy `dist/` folder to: Vercel, Netlify, or any static host

### Python Agent
```bash
cd src
python agent.py start
```
Deploy to: Cloud VM, Docker container, or LiveKit Cloud

## 🔐 Security Notes

- Never commit `.env` files
- Rotate API keys regularly
- Use environment variables in production
- Enable CORS only for your frontend domain
- Set S3 bucket permissions correctly

## 📝 Notes

- **Original code untouched**: Your working Python agent in `src/` is unchanged
- **Monorepo structure**: Everything in one repository, organized in folders
- **Room-based recording**: Each interview gets a unique room, used as the key for retrieval
- **Automatic cleanup**: Agent disconnects when user leaves

## 🆘 Support

If you encounter issues:
1. Check all three services are running (backend, frontend, agent)
2. Verify environment variables are set correctly
3. Check browser console and terminal logs
4. Ensure LiveKit and AWS credentials are valid

---

**Built with ❤️ - Maintaining your perfectly working agent while adding a beautiful UI!**
