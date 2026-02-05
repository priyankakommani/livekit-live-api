# Comprehensive Testing Guide: AI Interview System

This guide covers the complete end-to-end testing process for your AI Interview System, including the newly created frontend interface.

## Prerequisites

1.  **LiveKit Cloud Account**: You must have a project set up.
2.  **Cloud Storage Configured**: **CRITICAL** for recordings to work.
    *   Go to [LiveKit Cloud Console](https://cloud.livekit.io/) -> Project -> Settings -> Egress.
    *   Add your S3/GCP/Azure bucket details.
3.  **Environment Variables**: Ensure local `.env` has:
    *   `LIVEKIT_URL`
    *   `LIVEKIT_API_KEY`
    *   `LIVEKIT_API_SECRET`
    *   `GOOGLE_API_KEY` (for Gemini)

---

## Step 1: Start the Backend Agent

The Python agent powers the AI logic and manages recordings.

1.  Open Terminal 1.
2.  Navigate to `src`.
3.  Activate virtual environment (if not active):
    ```bash
    source venv/bin/activate
    ```
4.  Run the agent:
    ```bash
    python3 agent.py dev
    ```
    *You should see "Registered worker" and "Watching..." indicating it's ready.*

---

## Step 2: Serve the Frontend

We need to serve the new HTML web client locally.

1.  Open Terminal 2.
2.  Navigate to the `web` directory:
    ```bash
    cd web
    ```
3.  Start a simple HTTP server:
    ```bash
    python3 -m http.server 8000
    ```
    *The frontend is now accessible at `http://localhost:8000`.*

---

## Step 3: Generate a Test Token

You need a secure token to join the interview room.

1.  Open Terminal 3 (or use a split pane).
2.  Navigate to `src`.
3.  Run the test script (I updated it to help you):
    ```bash
    python3 ../tests/test_interview.py
    ```
4.  **COPY the access token** printed in the output.
    *   *Look for the long string starting with `eyJ...`*

---

## Step 4: Run the Interview (End-to-End Test)

1.  Open your browser to: [http://localhost:8000](http://localhost:8000)
2.  Paste the **Access Token** you copied into the input box.
3.  Click **"Start Interview"**.
4.  **Expectations**:
    *   You should see your local camera.
    *   You should see the "AI Interviewer" waiting (or connecting).
    *   The AI should greet you ("Hi! I'm your AI interviewer...").
    *   **Speak** to the AI. It should respond via audio.

---

## Step 5: Test Recording & Popup

1.  Conduct the interview for a minute.
2.  When you are done, click the **End Interview** button (Red Phone Icon) in the frontend.
    *   *Alternatively, wait for the session time limit (30 mins).*
3.  **Observation**:
    *   The call will disconnect.
    *   **The Popup should appear**: "Interview Completed".
    *   It will say "Processing recording...".

---

## Step 6: Verify Recording (The "Missing" Link)

1.  If Cloud Storage **IS** configured:
    *   Wait a few seconds/minutes.
    *   Run the helper script in Terminal 3:
        ```bash
        python3 get_latest_recording_url.py
        ```
    *   It will print a direct **Download URL**.
    *   Or check your S3 bucket directly.

2.  If Cloud Storage is **NOT** configured:
    *   The agent terminal (Terminal 1) will show a **CRITICAL ERROR** log explaining that storage is missing.
    *   The frontend popup will still show "Processing" or a safe fallback message, but no download will be possible.

---

## Troubleshooting

*   **Popup doesn't show?**
    *   Check Browser Console (F12). Look for "Data received" logs.
    *   Ensure the agent didn't crash (check Terminal 1).
*   **No Audio/Video?**
    *   Check browser permissions.
*   **Agent crashes?**
    *   Verify `GOOGLE_API_KEY` is valid.
