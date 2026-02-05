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
        token = tokenInput.value.trim();
        if (!token) return alert('Please enter an access token');

        startOverlay.classList.add('hidden');
        await connectToRoom();
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

    async function connectToRoom() {
        // Handle global namespace differences (UMD might export as LiveKit or LiveKitClient)
        const LK = window.LiveKit || window.LiveKitClient;
        if (!LK) {
            alert("LiveKit SDK not loaded. Please refresh.");
            return;
        }

        // Initialize Room
        room = new LK.Room({
            adaptiveStream: true,
            dynacast: true,
        });

        // Set up event listeners
        room
            .on(LK.RoomEvent.Connected, () => {
                console.log('Connected to room!');
                statusDot.style.backgroundColor = '#10b981'; // Green
                statusText.textContent = "Live Interview";
                connectionStatus.classList.add('connected');
            })
            .on(LK.RoomEvent.Disconnected, () => {
                console.log('Disconnected from room');
                statusDot.style.backgroundColor = '#ef4444'; // Red
                statusText.textContent = "Disconnected";
                connectionStatus.classList.remove('connected');

                // Show completion modal just in case we didn't get the data packet
                // But normally we wait for the data packet.
                // If the user clicked "End", we show modal.
                showDownloadModal();
            })
            .on(LK.RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(LK.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(LK.RoomEvent.DataReceived, handleDataReceived); // CRITICAL: Listen for popup trigger

        try {
            // Connect to LiveKit
            // 1. Try to get URL from query param (standard LiveKit pattern)
            let wsUrl = new URLSearchParams(window.location.search).get('liveKitUrl');

            // 2. Fallback to hardcoded URL (Useful for local testing if query param missing)
            if (!wsUrl) {
                wsUrl = "wss://liveapi-2g06q8uk.livekit.cloud";
                console.log("Using fallback WebSocket URL");
            }

            await room.connect(wsUrl, token);

            // Publish Local Media
            await room.localParticipant.enableCameraAndMicrophone();

            // Attach local video
            const localVidTrack = Array.from(room.localParticipant.videoTracks.values())[0].track;
            if (localVidTrack) {
                localVidTrack.attach(localVideo);
            }

        } catch (e) {
            console.error('Failed to connect:', e);
            alert('Failed to connect: ' + e.message);
            startOverlay.classList.remove('hidden');
        }
    }

    function handleTrackSubscribed(track, publication, participant) {
        if (track.kind === LK.Track.Kind.Video) {
            // Attach remote video
            track.attach(remoteVideo);
            remotePlaceholder.style.display = 'none';
        } else if (track.kind === LK.Track.Kind.Audio) {
            // Attach remote audio
            track.attach(remoteVideo); // Can attach to any element, LiveKit handles audio context
        }
    }

    function handleTrackUnsubscribed(track, publication, participant) {
        if (track.kind === LK.Track.Kind.Video) {
            track.detach();
            remotePlaceholder.style.display = 'flex';
        }
    }

    // --- DATA PACKET HANDLER (THE POPUP LOGIC) ---
    function handleDataReceived(payload, participant, kind, topic) {
        const strData = new TextDecoder().decode(payload);
        console.log(`Data received on topic ${topic}: ${strData}`);

        if (topic === "interview_status") {
            try {
                const data = JSON.parse(strData);
                if (data.type === "INTERVIEW_ENDED") {
                    console.log("Interview Ended event received!");

                    // Disconnect if not already
                    if (room.state === LK.RoomState.Connected) {
                        room.disconnect();
                    }

                    // Show Popup with recording link if available
                    showDownloadModal(data.recording_url);
                }
            } catch (e) {
                console.error("Failed to parse data packet", e);
            }
        }
    }

    function showDownloadModal(url) {
        downloadOverlay.classList.remove('hidden');

        if (url) {
            // If URL is ready immediately
            downloadContent.querySelector('.sub-text').textContent = "Recording is ready!";
            downloadContent.querySelector('.loader').style.display = 'none';
            downloadActions.classList.remove('hidden');
            downloadLink.href = url;
            downloadLink.onclick = (e) => {
                // Prevent default validation if href is #
                if (url === '#') e.preventDefault();
            }
        } else {
            // Recording processing
            // In a real app, you might poll an API here.
            // For now, we show the message from the backend.
            setTimeout(() => {
                downloadContent.querySelector('.sub-text').textContent = "Recording is safe in Cloud Storage. Check console.";
                downloadContent.querySelector('.loader').style.display = 'none';
                // We can't give a link if we don't have it, but we confirm success.
                downloadActions.classList.remove('hidden');
                downloadLink.textContent = "Close";
                downloadLink.href = "#";
                downloadLink.onclick = () => downloadOverlay.classList.add('hidden');
            }, 2000);
        }
    }

    btnCloseOverlay.addEventListener('click', () => {
        downloadOverlay.classList.add('hidden');
    });

});
