# 🚀 Quick Start Guide

## Run the Complete System in 3 Steps

### Step 1: Start Backend API
Open a terminal and run:
```bash
cd backend
npm start
```
✅ You should see: "AI Interview System - Backend API Running on port 3001"

### Step 2: Start Frontend
Open a **new terminal** and run:
```bash
cd frontend
npm run dev
```
✅ You should see: "Local: http://localhost:5173"

### Step 3: Start Python Agent
Open a **new terminal** and run:
```bash
cd src
python agent.py dev
```
✅ You should see: "Agent connected to LiveKit"

## 🎉 You're Ready!

Open your browser and go to: **http://localhost:5173**

### What to do:
1. Enter your name
2. Select a job role
3. Click "Start Interview Session"
4. Interview with the AI
5. Click "End Call" when done
6. Download your recording!

## 📋 Checklist

Before starting, make sure:
- [ ] Backend dependencies installed: `cd backend && npm install`
- [ ] Frontend dependencies installed: `cd frontend && npm install`
- [ ] Python dependencies installed: `cd src && pip install -r ../requirements.txt`
- [ ] All `.env` files are configured with your API keys

## ⚠️ Common Issues

**"Port 3001 already in use"**
- Kill the process: `lsof -ti:3001 | xargs kill -9`

**"Port 5173 already in use"**
- Kill the process: `lsof -ti:5173 | xargs kill -9`

**"Agent not connecting"**
- Check your LiveKit credentials in `src/.env`
- Make sure the URL matches the one in `backend/.env`

## 📖 Full Documentation

See `README_MONOREPO.md` for complete documentation.

---

**Need help?** Check the logs in each terminal for error messages.
