import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle2, Download, Copy, RefreshCw, Home } from 'lucide-react';

const PostInterview = () => {
    const { sessionId } = useParams();
    const API_BASE_URL = import.meta.env.VITE_API_URL || '';
    const [recordingData, setRecordingData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [pollError, setPollError] = useState(false);
    const [roomName, setRoomName] = useState('');

    useEffect(() => {
        // Retrieve room name from local storage or session details
        const storedRoom = localStorage.getItem(`interview_room_${sessionId}`);
        setRoomName(storedRoom || sessionId);

        // Tell backend to mark interview as ended
        fetch(`${API_BASE_URL}/api/interview/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sessionId, roomName: storedRoom })
        }).catch(err => console.error("Error ending session:", err));

        // Poll for recording — max 36 attempts × 5s = 3 minutes
        const MAX_POLLS = 36;
        let pollCount = 0;
        let pollTimer = null;

        const pollRecording = async () => {
            pollCount++;
            if (pollCount > MAX_POLLS) {
                setLoading(false);
                setPollError(true);
                return;
            }

            try {
                const targetRoom = storedRoom || sessionId;
                console.log(`Checking recording for: ${targetRoom} (attempt ${pollCount}/${MAX_POLLS})`);

                const res = await fetch(`${API_BASE_URL}/api/recording/${targetRoom}`);
                const data = await res.json();

                if (data.success && data.status === 'available') {
                    setRecordingData(data);
                    setLoading(false);
                } else {
                    pollTimer = setTimeout(pollRecording, 5000);
                }
            } catch (error) {
                console.error("Error polling recording:", error);
                pollTimer = setTimeout(pollRecording, 5000);
            }
        };

        // Start polling immediately
        pollRecording();

        return () => {
            if (pollTimer) clearTimeout(pollTimer);
        };

    }, [sessionId]);

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        alert('Copied to clipboard!');
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 text-slate-900 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-secondary/20 rounded-full blur-[120px]"></div>
            </div>

            <div className="max-w-2xl w-full glass rounded-3xl p-10 shadow-2xl border border-white/10 text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/20 text-green-400 mb-6 ring-4 ring-green-500/10">
                    <CheckCircle2 size={40} />
                </div>

                <h1 className="text-4xl font-display font-bold mb-3">Interview Completed!</h1>
                <p className="text-slate-400 text-lg mb-8">
                    Your session has been successfully recorded and stored securely.
                </p>

                <div className="bg-slate-900/50 rounded-2xl p-6 border border-white/5 text-left mb-8">
                    <div className="grid gap-6">
                        <div>
                            <label className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2 block">
                                Safe Room ID (Save this for reference)
                            </label>
                            <div className="flex gap-2">
                                <code className="flex-1 block bg-black/40 px-4 py-3 rounded-xl font-mono text-sm text-indigo-300 border border-indigo-500/20">
                                    {roomName || 'Loading...'}
                                </code>
                                <button
                                    onClick={() => copyToClipboard(roomName)}
                                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors"
                                    title="Copy ID"
                                >
                                    <Copy size={18} />
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2 block">
                                Recording Status
                            </label>
                            {loading && !pollError ? (
                                <div className="flex items-center gap-3 text-yellow-400 bg-yellow-400/10 px-4 py-3 rounded-xl border border-yellow-400/20">
                                    <RefreshCw className="animate-spin" size={18} />
                                    <span>Processing recording... (this may take a minute)</span>
                                </div>
                            ) : pollError ? (
                                <div className="flex flex-col gap-2 text-red-400 bg-red-400/10 px-4 py-3 rounded-xl border border-red-400/20">
                                    <span className="font-semibold">Recording not available yet.</span>
                                    <span className="text-sm text-slate-400">
                                        LiveKit Egress may still be processing. Use your Room ID above to check back later via <code className="font-mono text-xs">/api/recording/&#123;roomId&#125;</code>.
                                    </span>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3 text-green-400 bg-green-400/10 px-4 py-3 rounded-xl border border-green-400/20">
                                        <CheckCircle2 size={18} />
                                        <span>Recording Ready</span>
                                    </div>

                                    <a
                                        href={recordingData.recordingUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-primary to-indigo-600 rounded-xl font-semibold hover:shadow-lg hover:shadow-primary/25 transition-all"
                                    >
                                        <Download size={18} /> Download Recording
                                    </a>

                                    {recordingData.transcriptUrl && (
                                        <a
                                            href={recordingData.transcriptUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center justify-center gap-2 w-full py-3 bg-white/5 border border-white/10 rounded-xl font-medium hover:bg-white/10 transition-all"
                                        >
                                            <Download size={18} /> Download Transcript
                                        </a>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <Link
                    to="/"
                    className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                >
                    <Home size={18} /> Return to Home
                </Link>
            </div>
        </div>
    );
};

export default PostInterview;
