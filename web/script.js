/**
 * AI Interview Pro - Frontend Logic (Direct Gemini Integration)
 */
document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const welcomeScreen = document.getElementById('welcome-screen');
    const appUi = document.getElementById('app-ui');
    const startBtn = document.getElementById('start-btn');
    const endBtn = document.getElementById('end-btn');
    const micBtn = document.getElementById('mic-btn');
    const camBtn = document.getElementById('cam-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const transcriptLog = document.getElementById('transcript-log');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    const LK = window.LiveKit || window.LiveKitClient;
    if (!LK) {
        console.error('LiveKit SDK missing. Globals:', Object.keys(window).filter(k => k.toLowerCase().includes('live')));
    }

    let room;
    let geminiSocket;
    let audioContext;
    let processor;
    let isMicOn = true;
    let isCamOn = true;

    // Start Button Handler
    startBtn.addEventListener('click', async () => {
        const name = document.getElementById('candidate-name').value.trim();
        const role = document.getElementById('job-role').value;

        if (!name) {
            alert('Please enter your name');
            return;
        }

        showLoading('Connecting to interview room...');

        try {
            // 1. Get token from our Node.js server
            const response = await fetch('/api/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidateId: name.toLowerCase().replace(/\s+/g, '_'),
                    candidateName: name,
                    jobRole: role
                })
            });

            if (!response.ok) throw new Error('Failed to get token');
            const data = await response.json();

            // 2. Connect to LiveKit
            await connectToLiveKit(data.url, data.token);

            // 3. Connect to Gemini Proxy
            await connectToGemini(role);

            // UI Transition
            welcomeScreen.classList.add('hidden');
            appUi.classList.remove('hidden');
            hideLoading();

        } catch (error) {
            console.error(error);
            alert('Error starting session: ' + error.message);
            hideLoading();
        }
    });

    async function connectToLiveKit(url, token) {
        if (!LK) {
            alert('LiveKit Client SDK not loaded. Please check your internet or script tag.');
            return;
        }

        room = new LK.Room({ adaptiveStream: true });

        room.on(LK.RoomEvent.Connected, async () => {
            statusDot.classList.add('online');
            statusText.textContent = 'Live Interview';

            // Trigger recording on server now that we are in the room
            try {
                fetch('/api/record/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roomName: room.name })
                });
            } catch (e) {
                console.error('Failed to start server-side recording:', e);
            }
        });

        await room.connect(url, token);
        await room.localParticipant.enableCameraAndMicrophone();

        const localVideo = document.getElementById('local-video');
        const videoTracks = room.localParticipant.videoTracks;
        if (videoTracks.size > 0) {
            const track = Array.from(videoTracks.values())[0].track;
            if (track) track.attach(localVideo);
        }
    }

    async function connectToGemini(role) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        geminiSocket = new WebSocket(`${protocol}//${window.location.host}/api/gemini`);

        geminiSocket.onopen = () => {
            console.log('Gemini Socket Open');
            // Send setup message
            const setupMessage = {
                setup: {
                    model: "models/gemini-2.0-flash-exp",
                    generation_config: {
                        response_modalities: ["audio"],
                    }
                }
            };
            geminiSocket.send(JSON.stringify(setupMessage));
            startAudioStreaming();
        };

        geminiSocket.onmessage = async (event) => {
            const data = JSON.parse(await event.data.text());

            if (data.serverContent?.modelTurn?.parts?.[0]?.inlineData) {
                const base64Audio = data.serverContent.modelTurn.parts[0].inlineData.data;
                playAudioFromBase64(base64Audio);
            }

            if (data.serverContent?.modelTurn?.parts?.[0]?.text) {
                addTranscript('AI: ' + data.serverContent.modelTurn.parts[0].text);
            }
        };
    }

    function startAudioStreaming() {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            const source = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(2048, 1, 1);

            source.connect(processor);
            processor.connect(audioContext.destination);

            processor.onaudioprocess = (e) => {
                if (!isMicOn) return;
                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = floatTo16BitPCM(inputData);
                const base64Data = arrayBufferToBase64(pcmData);

                if (geminiSocket.readyState === WebSocket.OPEN) {
                    geminiSocket.send(JSON.stringify({
                        realtime_input: {
                            media_chunks: [{
                                data: base64Data,
                                mime_type: "audio/pcm"
                            }]
                        }
                    }));
                }
            };
        });
    }

    // Audio Helpers
    function playAudioFromBase64(base64) {
        const binary = atob(base64);
        const len = binary.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);

        audioContext.decodeAudioData(bytes.buffer, (buffer) => {
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
        });
    }

    function floatTo16BitPCM(input) {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output.buffer;
    }

    function arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
    }

    // UI Helpers
    function showLoading(text) {
        document.getElementById('loading-text').textContent = text;
        loadingOverlay.classList.add('active');
    }

    function hideLoading() {
        loadingOverlay.classList.remove('active');
    }

    function addTranscript(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${text.toLowerCase().startsWith('ai') ? 'ai' : 'user'}`;
        msgDiv.textContent = text;
        transcriptLog.appendChild(msgDiv);
        transcriptLog.scrollTop = transcriptLog.scrollHeight;
    }

    // Controls
    micBtn.addEventListener('click', () => {
        isMicOn = !isMicOn;
        micBtn.classList.toggle('muted', !isMicOn);
    });

    camBtn.addEventListener('click', () => {
        isCamOn = !isCamOn;
        camBtn.classList.toggle('muted', !isCamOn);
    });

    endBtn.addEventListener('click', () => {
        if (confirm('Finish interview?')) location.reload();
    });
});
