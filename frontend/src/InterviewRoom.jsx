import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Room, RoomEvent, createLocalVideoTrack, createLocalAudioTrack } from 'livekit-client';
import { Mic, MicOff, Video, VideoOff, PhoneOff, MessageSquare } from 'lucide-react';

const InterviewRoom = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [room, setRoom] = useState(null);
    const [token, setToken] = useState('');
    const [url, setUrl] = useState('');
    const [isMicOn, setIsMicOn] = useState(true);
    const [isCamOn, setIsCamOn] = useState(true);
    const [transcripts, setTranscripts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [remoteVideoTrack, setRemoteVideoTrack] = useState(null);
    const [audioEnabled, setAudioEnabled] = useState(false);

    const localVideoRef = useRef(null);
    const remoteVideoRef = useRef(null);
    const transcriptRef = useRef(null);
    const audioElementsRef = useRef([]);

    // Auto-scroll transcript to bottom
    useEffect(() => {
        if (transcriptRef.current) {
            transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
        }
    }, [transcripts]);

    useEffect(() => {
        const storedToken = localStorage.getItem(`interview_token_${sessionId}`);
        const storedUrl = localStorage.getItem(`interview_url_${sessionId}`);

        if (!storedToken || !storedUrl) {
            navigate('/');
            return;
        }

        setToken(storedToken);
        setUrl(storedUrl);
    }, [sessionId, navigate]);

    useEffect(() => {
        if (!token || !url) return;

        const newRoom = new Room({
            adaptiveStream: true,
            dynacast: true,
        });

        setRoom(newRoom);

        newRoom.on(RoomEvent.Connected, () => {
            console.log('Connected to LiveKit room');
            setIsConnected(true);
            publishTracks(newRoom);
        });

        newRoom.on(RoomEvent.Disconnected, () => {
            console.log('Disconnected');
            setIsConnected(false);
            navigate(`/success/${sessionId}`);
        });

        newRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('Track subscribed:', track.kind, 'from', participant.identity);

            if (track.kind === 'video') {
                setRemoteVideoTrack(track);
                if (remoteVideoRef.current) {
                    track.attach(remoteVideoRef.current);
                }
            } else if (track.kind === 'audio') {
                // Attach the AI agent's voice to a hidden <audio> element in the DOM.
                const audioElement = track.attach();
                audioElement.autoplay = true;
                audioElement.setAttribute('playsinline', 'true');
                audioElement.volume = 1.0;
                audioElement.style.display = 'none';
                document.body.appendChild(audioElement);
                audioElementsRef.current.push(audioElement);

                audioElement.play().catch(() => {
                    // Autoplay blocked — the AudioPlaybackStatusChanged handler
                    // and the first user gesture will unblock it.
                });

                // Reflect LiveKit's own playback gate.
                setAudioEnabled(newRoom.canPlaybackAudio);
            }
        });

        // Fires when the browser blocks / allows audio playback for the room.
        newRoom.on(RoomEvent.AudioPlaybackStatusChanged, () => {
            setAudioEnabled(newRoom.canPlaybackAudio);
        });

        // Listen for data packets (clean finish signal and transcripts)
        newRoom.on(RoomEvent.DataReceived, (payload, participant) => {
            try {
                const data = JSON.parse(new TextDecoder().decode(payload));

                if (data.type === 'INTERVIEW_ENDED') {
                    // Force disconnect and go to success
                    newRoom.disconnect();
                } else if (data.type === 'TRANSCRIPT') {
                    // Add new transcript to the state
                    setTranscripts(prev => [...prev.slice(-50), {
                        id: Date.now() + Math.random(),
                        speaker: data.speaker,
                        text: data.text,
                        timestamp: new Date().toLocaleTimeString()
                    }]);
                }
            } catch (e) {
                console.error("Failed to parse data packet", e);
            }
        });

        // Gemini native integration via LiveKit usually sends transcripts via RoomEvent.TranscriptionReceived 
        // OR standard RPC if using the new agents framework.
        // For simplicity with the python agent using `transcription_handler`, we might rely on the agent sending chat messages as transcripts.

        // However, the python agent code we saw sends `user_input_transcribed` events. 
        // Let's assume for now we just show what we can or wait for chat messages.

        const connect = async () => {
            try {
                await newRoom.connect(url, token);
                // If the browser is blocking audio, surface the "Enable Audio" button.
                setAudioEnabled(newRoom.canPlaybackAudio);
                if (!newRoom.canPlaybackAudio) {
                    newRoom.startAudio().catch(() => { /* needs a user gesture */ });
                }
            } catch (error) {
                console.error('Failed to connect:', error);
            }
        };

        connect();

        // Any first interaction on the page unblocks audio playback.
        const unlockAudio = () => {
            newRoom.startAudio().catch(() => {});
            audioElementsRef.current.forEach((el) => el.play().catch(() => {}));
        };
        document.addEventListener('pointerdown', unlockAudio);
        document.addEventListener('keydown', unlockAudio);

        return () => {
            document.removeEventListener('pointerdown', unlockAudio);
            document.removeEventListener('keydown', unlockAudio);
            newRoom.disconnect();
        };
    }, [token, url, sessionId, navigate]);

    // Attach remote video when element becomes available
    useEffect(() => {
        if (remoteVideoTrack && remoteVideoRef.current) {
            remoteVideoTrack.attach(remoteVideoRef.current);
        }
    }, [remoteVideoTrack]);

    const publishTracks = async (currentRoom) => {
        try {
            const videoTrack = await createLocalVideoTrack();
            const audioTrack = await createLocalAudioTrack();

            await currentRoom.localParticipant.publishTrack(videoTrack);
            await currentRoom.localParticipant.publishTrack(audioTrack);

            if (localVideoRef.current) {
                videoTrack.attach(localVideoRef.current);
            }

            setIsMicOn(true);
            setIsCamOn(true);
        } catch (error) {
            console.error('Error publishing tracks:', error);
        }
    };

    const toggleMic = () => {
        if (!room) return;
        const audioTrack = room.localParticipant.getTrackPublications().find(pub => pub.kind === 'audio')?.track;
        if (audioTrack) {
            if (isMicOn) {
                audioTrack.mute();
            } else {
                audioTrack.unmute();
            }
            setIsMicOn(!isMicOn);
        }
    };

    const toggleCam = () => {
        if (!room) return;
        const videoTrack = room.localParticipant.getTrackPublications().find(pub => pub.kind === 'video')?.track;
        if (videoTrack) {
            if (isCamOn) {
                videoTrack.mute();
            } else {
                videoTrack.unmute();
            }
            setIsCamOn(!isCamOn);
        }
    };

    const enableAudio = async () => {
        try {
            // LiveKit's own unlock — must run inside this click handler.
            if (room) {
                await room.startAudio();
            }
            await Promise.all(
                audioElementsRef.current.map((el) => el.play().catch(() => {}))
            );
            setAudioEnabled(room ? room.canPlaybackAudio : true);
        } catch (err) {
            console.error('Failed to enable audio:', err);
        }
    };

    const handleEndCall = async () => {
        if (confirm('Are you sure you want to end the interview?')) {
            // Signal server/agent we are done via Data Channel
            // topic must match what the agent listens for: "user_actions"
            if (room && room.localParticipant) {
                const payload = JSON.stringify({ type: "USER_ENDED_CALL" });
                const encoder = new TextEncoder();
                await room.localParticipant.publishData(encoder.encode(payload), { reliable: true, topic: "user_actions" });

                // Give it a second to send before disconnecting
                setTimeout(() => {
                    room.disconnect();
                }, 1000);
            } else {
                navigate(`/success/${sessionId}`);
            }
        }
    };

    return (
        <div className="h-screen flex flex-col bg-slate-900 overflow-hidden">
            {/* Header */}
            <header className="px-6 py-4 glass z-10 flex justify-between items-center border-b border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary"></div>
                    <span className="font-display font-bold text-lg">AI Interviewer</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`}></div>
                        <span className="text-slate-300">{isConnected ? 'Live' : 'Connecting...'}</span>
                    </div>

                    {!audioEnabled && isConnected && (
                        <button
                            onClick={enableAudio}
                            className="px-4 py-1.5 rounded-full bg-gradient-to-r from-primary to-indigo-600 text-white text-sm font-medium hover:shadow-lg hover:shadow-primary/25 transition-all animate-pulse"
                        >
                            🔊 Enable Audio
                        </button>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden">
                {/* Main Video Area */}
                <div className="lg:col-span-2 relative glass rounded-3xl overflow-hidden border border-white/10 flex items-center justify-center bg-black/40">
                    <video ref={remoteVideoRef} className="w-full h-full object-cover" autoPlay playsInline />

                    {!remoteVideoTrack && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-secondary animate-pulse-slow flex items-center justify-center text-4xl font-bold shadow-[0_0_60px_rgba(99,102,241,0.3)]">
                                AI
                            </div>
                            <p className="mt-6 text-slate-400 font-medium">Interviewer is listening...</p>
                        </div>
                    )}

                    {/* Controls Overlay */}
                    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 p-3 rounded-2xl glass border border-white/10 shadow-2xl backdrop-blur-xl">
                        <button
                            onClick={toggleMic}
                            className={`p-4 rounded-xl transition-all ${isMicOn ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}
                        >
                            {isMicOn ? <Mic size={24} /> : <MicOff size={24} />}
                        </button>
                        <button
                            onClick={toggleCam}
                            className={`p-4 rounded-xl transition-all ${isCamOn ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}
                        >
                            {isCamOn ? <Video size={24} /> : <VideoOff size={24} />}
                        </button>
                        <button
                            onClick={handleEndCall}
                            className="p-4 rounded-xl bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/20 transition-all"
                        >
                            <PhoneOff size={24} />
                        </button>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="flex flex-col gap-6">
                    {/* Local Video */}
                    <div className="glass rounded-2xl overflow-hidden aspect-video border border-white/10 relative group">
                        <video ref={localVideoRef} className="w-full h-full object-cover transform scale-x-[-1]" autoPlay playsInline muted />
                        <div className="absolute bottom-3 left-3 px-2 py-1 bg-black/60 backdrop-blur-md rounded-md text-xs font-medium text-white/90">
                            You
                        </div>
                    </div>

                    {/* Transcript / Status Placeholder */}
                    <div className="flex-1 glass rounded-2xl p-4 border border-white/10 flex flex-col">
                        <div className="flex items-center gap-2 mb-4 text-slate-400 text-sm font-medium uppercase tracking-wider">
                            <MessageSquare size={16} />
                            <span>Transcript</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-4 text-sm text-slate-300 pr-2" ref={transcriptRef}>
                            {transcripts.length === 0 ? (
                                <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                                    <span className="text-secondary font-semibold text-xs block mb-1">AI Interviewer</span>
                                    Hi! I'm your AI interviewer. How are you doing today?
                                </div>
                            ) : (
                                transcripts.map((t) => (
                                    <div key={t.id} className={`p-3 rounded-lg border ${t.speaker === 'user' ? 'bg-primary/10 border-primary/20 ml-4' : 'bg-white/5 border-white/5 mr-4'}`}>
                                        <div className="flex justify-between items-center mb-1">
                                            <span className={`font-semibold text-xs uppercase ${t.speaker === 'user' ? 'text-primary' : 'text-secondary'}`}>
                                                {t.speaker === 'user' ? 'You' : 'AI Interviewer'}
                                            </span>
                                            <span className="text-[10px] text-slate-500">{t.timestamp}</span>
                                        </div>
                                        {t.text}
                                    </div>
                                ))
                            )}

                            <div className="text-center text-slate-500 text-[10px] mt-4 italic opacity-50">
                                Transcripts are being recorded securely.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InterviewRoom;
