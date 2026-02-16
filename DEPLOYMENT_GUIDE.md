# 🚀 Deployment Guide: AI Interview System

This guide explains how to deploy your 3-component architecture to the cloud.

---

## 🏗️ Deployment Overview

| Component | Host | Type |
| :--- | :--- | :--- |
| **Frontend** | Vercel / Netlify | Static Site |
| **Backend** | Render / Railway | Web Service |
| **Python Agent** | Render / Railway | Background Worker |

---

## 1️⃣ Deploy the Backend (Node.js)
**Recommended Host:** [Render.com](https://render.com)

1. Create a **New > Web Service**.
2. Connect your GitHub repository.
3. **Settings:**
   - **Root Directory:** `backend`
   - **Environment:** `Node`
   - **Build Command:** `npm install`
   - **Start Command:** `node server.js`
4. **Environment Variables:** Add all variables from your `backend/.env`.
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `AWS_ACCESS_KEY`
   - `AWS_SECRET_KEY`
   - `AWS_BUCKET`
   - `AWS_REGION`
   - `FRONTEND_URL` (Set this to your Vercel URL once deployed)

---

## 2️⃣ Deploy the Frontend (React/Vite)
**Recommended Host:** [Vercel](https://vercel.com)

1. Create a **New Project** in Vercel.
2. **Settings:**
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. **Environment Variables:**
   - `VITE_API_URL`: Set this to your **Render Backend URL** (e.g., `https://your-api.onrender.com`).

---

## 3️⃣ Deploy the Python Agent
**Recommended Host:** [Render.com](https://render.com)

1. Create a **New > Background Worker**.
2. **Settings:**
   - **Root Directory:** (Leave empty/Root)
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd src && python agent.py start` (Production mode)
3. **Environment Variables:** Add all variables from your `src/.env`.
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `GOOGLE_API_KEY`

> **Note on Virtual Env:** Cloud providers like Render and Railway automatically create and manage the virtual environment for you based on the `requirements.txt` file. You do **not** need to upload your local `venv` folder.

---

## 🔄 Updating Configuration

### CORS Configuration
Once your frontend is deployed (e.g., `https://my-interview-app.vercel.app`), go to your **Backend settings** and update the `FRONTEND_URL` environment variable to match it. This allows the two parts to talk to each other.

### The "Processing" Delay
In production, S3 and LiveKit Egress still take about 60-90 seconds to process the video. The frontend will continue to show "Processing" until it is ready.

---

## 🛠️ Performance Tips
1. **Free Tiers:** On Render's Free tier, the backend might "sleep" after 15 minutes of inactivity. The first person to visit the site might experience a 30-second delay while it wakes up.
2. **Regions:** Try to deploy all three (LiveKit, AWS S3, Render, Vercel) in similar regions (e.g., US-East or Asia-South) to reduce latency.

---

**You are now ready to go live!** 🎊
