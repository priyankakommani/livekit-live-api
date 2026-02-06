# Deployment Roadmap: Scalable AI Interview System

This document outlines the architecture for deploying this system as a scalable, distributed web application using a monorepo structure.

## 1. Architecture Overview (Microservices / Separated Concerns)

We will move from a "local Python script" to a professional **Client-Server-Worker** model.

### **Backend (Node.js/Next.js API)**
*   **Role**: Handles user management, database (recording links), authentication, and orchestrating LiveKit rooms.
*   **Hosting**: Render / Railway / Vercel.
*   **Database**: PostgreSQL or MongoDB (to store `candidate_id`, `interview_status`, `recording_s3_url`, `transcript_s3_url`).

### **Frontend (React/Next.js)**
*   **Role**: The user interface for the candidate.
*   **Hosting**: Vercel / Netlify.
*   **Tech**: LiveKit Components (React SDK), TailwindCSS.

### **AI Agent (Python Worker)**
*   **Role**: The "Brain". It connects to the LiveKit room as a participant to conduct the interview.
*   **Hosting**: **Self-hosted on EC2 / DigitalOcean** (recommended for low latency) OR **LiveKit Cloud Egress/Agents** (managed).
*   **Why separate?**: The AI Agent is a continuous process that needs to listen for jobs. It is NOT a standard HTTP API.

---

## 2. Monorepo Structure

Repo Structure:
```
/apps
  /web           (Next.js Frontend)
  /api           (Node.js/Express Backend)
  /agent         (The Python AI Agent - what you have now)
/packages
  /db            (Shared database schema/Prisma)
  /config        (Shared typescript configs)
```

---

## 3. Deployment Steps

### Phase 1: The Database & API
1.  **Set up PostgreSQL**: Use Supabase or Neon.tech.
2.  **Create Tables**: `Interviews`, `Candidates`.
    *   `Interviews` table should have: `id`, `s3_recording_url`, `s3_transcript_url`, `status`.
3.  **Create API Endpoint**: `POST /api/interview/start`
    *   Generates a LiveKit Token.
    *   Returns the Token + Room Name.

### Phase 2: The AI Worker (Agent)
1.  The Python agent code you have is the "Worker".
2.  **Dockerize It**: Create a `Dockerfile` for the python agent.
3.  **Deploy**: Run this container on a cloud VM (e.g., AWS EC2, Fly.io).
4.  **Connect**: Set `LIVEKIT_URL` and keys in the VM. The agent will automatically connect to your LiveKit Cloud project and wait for rooms to join.

### Phase 3: The Frontend
1.  Deploy your Next.js/React app to Vercel.
2.  Users visit `your-app.com/interview/[id]`.
3.  Frontend calls `API` to get a token.
4.  Frontend connects to LiveKit Room.
5.  **Magic**: The Agent (running on your VM) sees the room creation and automatically joins.

---

## 4. Retrieving Recordings

1.  **Current Flow**: The generic test script just logs the URL.
2.  **Production Flow**:
    *   In `agent.py`, inside `handle_cleanup`:
    *   Instead of just logging the `download_url` or S3 path, make an HTTP Request to your API:
        ```python
        requests.post("https://api.yourapp.com/webhooks/interview-ended", json={
            "interview_id": self.candidate_id,
            "recording_url": f"https://{bucket}.s3.amazonaws.com/{key}",
            "transcript_url": ...
        })
        ```
    *   Your API receives this webhook and updates the Database.
    *   Your Admin Dashboard reads from the Database to show the video.

---

## 5. Security & S3
*   Use **Presigned URLs** for viewing videos to keep your S3 bucket private.
*   The Agent uses the private keys to uploads, the Frontend requests a temporary View Link from the API.
