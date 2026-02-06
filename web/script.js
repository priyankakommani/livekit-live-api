document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    // Use the correct global for LiveKit
    const LK = window.LiveKit || window.LiveKitClient;

    const startOverlay = document.getElementById('start-overlay');
    const downloadOverlay = document.getElementById('download-overlay');
    const btnConnect = document.getElementById('btn-connect');
    const btnEnd = document.getElementById('btn-end');
    const btnMic = document.getElementById('btn-mic');
    const btnCam = document.getElementById('btn-camera');
    const tokenInput = document.getElementById('token-input');
    const localVideo = document.getElementById('local-video');
    const remoteVideo = document.getElementById('remote-video');
    const connectionStatus = document.getElementById('connection-status');
    const statusDot = connectionStatus.querySelector('.dot');
    const statusText = connectionStatus.querySelector('.text');
    const remotePlaceholder = document.querySelector('.video-placeholder');

    // Download Modal Elements
    const downloadContent = document.getElementById('download-content');
    const downloadActions = document.getElementById('download-actions');
    const downloadLink = document.getElementById('download-link');
    const btnCloseOverlay = document.getElementById('btn-close-overlay');

    let room;
    let token = new URLSearchParams(window.location.search).get('token');

    // Setup Initial State
    if (!token) {
        document.querySelector('.input-group').style.display = 'block';
    } else {
        tokenInput.value = token;
    }

    // Connect Button Handler
    btnConnect.addEventListener('click', async () => {
        const candidateName = "Candidate_" + Math.random().toString(36).substring(7);

        btnConnect.textContent = "Connecting...";
        btnConnect.disabled = true;

        try {
            // Call Node.js Backend to get Token
            const response = await fetch('http://localhost:3000/api/start-interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidateName })
            });

            if (!response.ok) throw new Error("Backend failed to start interview");

            const data = await response.json();
            token = data.token;
            window.roomId = data.roomId;
            window.geminiApiKey = data.geminiApiKey;
            window.liveKitUrl_API = data.liveKitUrl;

            console.log("Got Session from Backend:", window.roomId);

            startOverlay.classList.add('hidden');
            await connectToRoom();

        } catch (e) {
            console.error(e);
            alert("Failed to start: " + e.message);
            btnConnect.textContent = "Start Interview";
            btnConnect.disabled = false;
        }
    });

    // Control Buttons
    btnEnd.addEventListener('click', async () => {
        if (!room) return;

        // Signal the agent that we want to end
        // The agent will then stop recording, send us the link, and disconnect the room
        try {
            const payload = new TextEncoder().encode(JSON.stringify({
                type: "USER_ENDED_CALL"
            }));

            await room.localParticipant.publishData(payload, {
                reliable: true,
                topic: "user_actions"
            });
            console.log("Sent USER_ENDED_CALL signal to agent");

            // Show "Processing..." modal immediately to give feedback
            downloadOverlay.classList.remove('hidden');
            downloadContent.querySelector('.sub-text').textContent = "Wrapping up interview...";

        } catch (e) {
            console.error("Failed to signal end:", e);
            room.disconnect(); // Fallback
        }
    });

    // Basic Media Toggles (Mock state for UI, logic handled by room)
    let isMicOn = true;
    let isCamOn = true;

    btnMic.addEventListener('click', () => {
        isMicOn = !isMicOn;
        if (room) {
            room.localParticipant.setMicrophoneEnabled(isMicOn);
        }
        updateBtnState(btnMic, isMicOn);
    });

    btnCam.addEventListener('click', () => {
        isCamOn = !isCamOn;
        if (room) {
            room.localParticipant.setCameraEnabled(isCamOn);
        }
        updateBtnState(btnCam, isCamOn);
    });

    function updateBtnState(btn, isOn) {
        if (isOn) {
            btn.classList.remove('off');
            btn.style.opacity = "1";
        } else {
            btn.classList.add('off');
            btn.style.opacity = "0.7";
        }
    }

    // --- LiveKit Logic ---

    function waitForSDK() {
        return new Promise((resolve, reject) => {
            if (window.LiveKit || window.LiveKitClient) return resolve(window.LiveKit || window.LiveKitClient);

            console.log("Waiting for LiveKit SDK to load...");
            let checks = 0;
            const interval = setInterval(() => {
                const lk = window.LiveKit || window.LiveKitClient;
                if (lk) {
                    clearInterval(interval);
                    console.log("LiveKit SDK loaded.");
                    resolve(lk);
                }
                checks++;
                if (checks > 50) { // Wait up to 5 seconds
                    clearInterval(interval);
                    reject("SDK Loading timed out");
                }
            }, 100);
        });
    }

    let gemini;
    let transcript = "";
    let audioContext;

    async function connectToRoom() {
        let LK;
        try {
            LK = await waitForSDK();
        } catch (e) {
            alert("LiveKit SDK not loaded.");
            return;
        }

        room = new LK.Room({ adaptiveStream: true, dynacast: true });

        // --- Event Listeners ---
        room.on(LK.RoomEvent.Connected, async () => {
            console.log('Connected to room!');
            statusDot.style.backgroundColor = '#10b981';
            statusText.textContent = "Live Interview";

            // 1. Tell backend to start recording
            fetch('http://localhost:3000/api/start-recording', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roomId: window.roomId })
            });

            // 2. Start Gemini
            if (window.geminiApiKey) {
                gemini = new GeminiRealtime(window.geminiApiKey);
                gemini.onTranscript = (speaker, text) => {
                    transcript += `[${speaker}]: ${text}\n\n`;
                    console.log(`${speaker}: ${text}`);
                };
                gemini.onAudioData = (base64) => playGeminiAudio(base64);

                await gemini.connect();
                console.log("Gemini is ready and listening.");

                // Visually show bot joined
                if (remotePlaceholder) {
                    remotePlaceholder.style.display = 'none';
                    const botStatus = document.createElement('div');
                    botStatus.id = 'bot-indicator';
                    botStatus.innerHTML = '<span style="color: #60a5fa;">●</span> AI Interviewer Active';
                    botStatus.style.position = 'absolute';
                    botStatus.style.bottom = '20px';
                    botStatus.style.left = '50%';
                    botStatus.style.transform = 'translateX(-50%)';
                    botStatus.style.padding = '8px 16px';
                    botStatus.style.background = 'rgba(0,0,0,0.6)';
                    botStatus.style.borderRadius = '20px';
                    botStatus.style.fontSize = '0.9em';
                    remoteVideo.parentElement.appendChild(botStatus);
                }
            }
        });

        room.on(LK.RoomEvent.TrackSubscribed, (track) => {
            if (track.kind === LK.Track.Kind.Video) track.attach(remoteVideo);
        });

        try {
            let wsUrl = window.liveKitUrl_API || "wss://liveapi-2g06q8uk.livekit.cloud";
            await room.connect(wsUrl, token);
            await room.localParticipant.enableCameraAndMicrophone();

            // Attach local video
            const localVidTrack = Array.from(room.localParticipant.videoTracks.values())[0].track;
            if (localVidTrack) localVidTrack.attach(localVideo);

            // Start Audio bridge to Gemini
            startAudioStreaming();

        } catch (e) {
            console.error('Failed to connect:', e);
            alert('Failed to connect: ' + e.message);
        }
    }

    // --- Audio Bridge: Mic -> Gemini ---
    async function startAudioStreaming() {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (!gemini) return;
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = floatTo16BitPCM(inputData);
            const base64 = b64EncodeUnicode(pcmData);
            gemini.sendAudioChunk(base64);
        };
    }

    // --- Audio Playback: Gemini -> Speakers ---
    async function playGeminiAudio(base64) {
        if (!audioContext) return;
        if (audioContext.state === 'suspended') await audioContext.resume();

        const binary = atob(base64);
        const bufferLen = binary.length;
        const bytes = new Uint8Array(bufferLen);
        for (let i = 0; i < bufferLen; i++) bytes[i] = binary.charCodeAt(i);

        // Gemini returns Int16 (16-bit PCM), we need Float32 for Web Audio
        const pcm16 = new Int16Array(bytes.buffer);
        const floatData = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {
            floatData[i] = pcm16[i] / 32768;
        }

        const audioBuffer = audioContext.createBuffer(1, floatData.length, 24000);
        audioBuffer.getChannelData(0).set(floatData);

        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start();
    }

    // --- Utils ---
    function floatTo16BitPCM(input) {
        let output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            let s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output.buffer;
    }

    function b64EncodeUnicode(buffer) {
        let binary = '';
        let bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
    }

    // --- End Interview ---
    btnEnd.addEventListener('click', async () => {
        if (!confirm("Are you sure you want to end the interview?")) return;

        if (gemini) gemini.disconnect();
        if (room) room.disconnect();

        // 3. Finalize on backend (Stop recording + Save transcript)
        try {
            const res = await fetch('http://localhost:3000/api/complete-interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roomId: window.roomId, transcript: transcript })
            });
            const data = await res.json();
            showDownloadModal(null, window.roomId);
        } catch (e) {
            console.error("Failed to complete interview:", e);
        }
    });

    function showDownloadModal(url, roomId) {
        downloadOverlay.classList.remove('hidden');
        if (roomId) {
            const statusText = downloadOverlay.querySelector('p');
            if (statusText) statusText.innerHTML = `Session <strong>${roomId}</strong> completed and saved in S3.`;
        }
        downloadActions.classList.remove('hidden');
        downloadLink.textContent = "Close";
        downloadLink.href = "#";
        downloadLink.onclick = () => downloadOverlay.classList.add('hidden');
    }

    btnCloseOverlay.addEventListener('click', () => downloadOverlay.classList.add('hidden'));

});
