# 🚀 Pre-Launch Checklist

Use this checklist before running the system for the first time.

## ✅ Installation Checklist

### Backend
- [ ] Navigate to `backend/` folder
- [ ] Run `npm install`
- [ ] Verify `node_modules/` folder exists
- [ ] Check `.env` file has all credentials:
  - [ ] `LIVEKIT_URL`
  - [ ] `LIVEKIT_API_KEY`
  - [ ] `LIVEKIT_API_SECRET`
  - [ ] `GOOGLE_API_KEY`
  - [ ] `AWS_ACCESS_KEY`
  - [ ] `AWS_SECRET_KEY`
  - [ ] `AWS_REGION`
  - [ ] `AWS_BUCKET`

### Frontend
- [ ] Navigate to `frontend/` folder
- [ ] Run `npm install`
- [ ] Verify `node_modules/` folder exists
- [ ] Check `vite.config.js` proxy points to `http://localhost:3001`

### Python Agent
- [ ] Navigate to `src/` folder
- [ ] Python virtual environment exists: `venv/`
- [ ] Activate venv: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
- [ ] Install requirements: `pip install -r ../requirements.txt`
- [ ] Check `src/.env` file has:
  - [ ] `LIVEKIT_URL` (same as backend)
  - [ ] `LIVEKIT_API_KEY` (same as backend)
  - [ ] `LIVEKIT_API_SECRET` (same as backend)
  - [ ] `GOOGLE_API_KEY`

## ✅ Verification Checklist

### Test Backend
- [ ] Open terminal
- [ ] Run: `cd backend && npm start`
- [ ] See: "AI Interview System - Backend API Running on port 3001"
- [ ] Open browser: `http://localhost:3001/health`
- [ ] See: `{"status":"healthy",...}`

### Test Frontend
- [ ] Open new terminal
- [ ] Run: `cd frontend && npm run dev`
- [ ] See: "Local: http://localhost:5173"
- [ ] Open browser: `http://localhost:5173`
- [ ] See: Beautiful landing page with "AI Interview Pro"

### Test Python Agent
- [ ] Open new terminal
- [ ] Run: `cd src && python agent.py dev`
- [ ] See: "Agent connected to LiveKit" or similar
- [ ] No errors about missing credentials

## ✅ Credentials Verification

### LiveKit
- [ ] Account created at https://cloud.livekit.io
- [ ] Project created
- [ ] API Key and Secret copied
- [ ] URL format: `wss://your-project.livekit.cloud`
- [ ] Same credentials in both `backend/.env` and `src/.env`

### Google Gemini
- [ ] API key from https://aistudio.google.com/app/apikey
- [ ] Key starts with `AIza...`
- [ ] Same key in both `backend/.env` and `src/.env`

### AWS S3
- [ ] S3 bucket created
- [ ] Bucket name noted
- [ ] IAM user created with S3 access
- [ ] Access key and secret key copied
- [ ] Region correct (e.g., `ap-south-1`)

## ✅ Network Checklist

- [ ] Ports available:
  - [ ] 3001 (backend)
  - [ ] 5173 (frontend)
- [ ] Internet connection active
- [ ] No firewall blocking:
  - [ ] LiveKit WebSocket connections
  - [ ] AWS S3 access
  - [ ] Google API access

## ✅ File Structure Checklist

```
ai-interview-system/
├── backend/
│   ├── node_modules/     ← Should exist after npm install
│   ├── server.js
│   ├── package.json
│   └── .env              ← Must exist with credentials
├── frontend/
│   ├── node_modules/     ← Should exist after npm install
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── src/
    ├── venv/             ← Should exist (Python virtual env)
    ├── agent.py
    └── .env              ← Must exist with credentials
```

## ✅ First Run Checklist

### Step 1: Start Backend
- [ ] Terminal 1: `cd backend && npm start`
- [ ] Wait for: "Backend API Running"
- [ ] Test: `curl http://localhost:3001/health`

### Step 2: Start Frontend
- [ ] Terminal 2: `cd frontend && npm run dev`
- [ ] Wait for: "Local: http://localhost:5173"
- [ ] Open browser: `http://localhost:5173`

### Step 3: Start Agent
- [ ] Terminal 3: `cd src && python agent.py dev`
- [ ] Wait for: "Agent connected"
- [ ] No error messages

### Step 4: Test Interview
- [ ] On frontend, enter name: "Test User"
- [ ] Select role: "Software Engineer"
- [ ] Click: "Start Interview Session"
- [ ] Should redirect to interview room
- [ ] Should see: "Connecting..." then "Live"
- [ ] Should hear/see: AI interviewer greeting
- [ ] Test mic/camera controls
- [ ] Click: "End Call"
- [ ] Should see: Success page with Room ID
- [ ] Wait 1-2 minutes
- [ ] Should see: "Recording Ready"
- [ ] Click: "Download Recording"
- [ ] File should download

## ✅ Troubleshooting Quick Checks

### Backend Issues
- [ ] Check `.env` file exists
- [ ] Check port 3001 not in use: `lsof -i:3001`
- [ ] Check npm packages installed: `ls node_modules/`
- [ ] Check logs for errors

### Frontend Issues
- [ ] Check port 5173 not in use: `lsof -i:5173`
- [ ] Check npm packages installed: `ls node_modules/`
- [ ] Check browser console for errors (F12)
- [ ] Clear browser cache

### Agent Issues
- [ ] Check Python version: `python --version` (should be 3.10+)
- [ ] Check venv activated: `which python` (should show venv path)
- [ ] Check requirements installed: `pip list`
- [ ] Check `.env` credentials match backend

### Recording Issues
- [ ] Check S3 bucket exists
- [ ] Check AWS credentials valid
- [ ] Check bucket permissions allow uploads
- [ ] Wait 1-2 minutes after interview ends
- [ ] Check S3 console: `ai_interview/{candidateId}/`

## ✅ Success Indicators

You know everything is working when:
- ✅ All 3 terminals show no errors
- ✅ Frontend loads at http://localhost:5173
- ✅ Can start an interview session
- ✅ AI interviewer joins and speaks
- ✅ Can end the interview
- ✅ Recording becomes available for download
- ✅ Can download both recording and transcript

## 🎉 Ready to Launch!

If all checkboxes are ticked, you're ready to use the system!

**Next Steps:**
1. Keep all 3 terminals running
2. Open http://localhost:5173
3. Start your first interview
4. Enjoy your AI-powered interview system!

---

**Need Help?**
- Check `README_MONOREPO.md` for detailed documentation
- Check `ARCHITECTURE.md` for system design
- Check terminal logs for error messages
- Verify all credentials are correct
