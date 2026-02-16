import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, User, Briefcase } from 'lucide-react';

const Home = () => {
    const navigate = useNavigate();
    const API_BASE_URL = import.meta.env.VITE_API_URL || '';

    const [formData, setFormData] = useState({
        candidateName: '',
        jobRole: 'software_engineer'
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.candidateName) return;

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/interview/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (data.success) {
                // Store token in localStorage for the room component
                localStorage.setItem(`interview_token_${data.sessionId}`, data.token);
                localStorage.setItem(`interview_url_${data.sessionId}`, data.url);
                localStorage.setItem(`interview_room_${data.sessionId}`, data.roomName);

                navigate(`/room/${data.sessionId}`);
            } else {
                alert('Failed to start interview: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to connect to server');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="max-w-md w-full glass rounded-3xl p-8 shadow-2xl">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-gradient-to-br from-primary to-secondary mb-4 shadow-lg shadow-primary/30">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-4xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400 mb-2">
                        AI Interview Pro
                    </h1>
                    <p className="text-slate-400">Ready to start your technical assessment?</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                            <User className="w-4 h-4" /> Full Name
                        </label>
                        <input
                            type="text"
                            required
                            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-slate-600"
                            placeholder="Ex. Alex Johnson"
                            value={formData.candidateName}
                            onChange={(e) => setFormData({ ...formData, candidateName: e.target.value })}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                            <Briefcase className="w-4 h-4" /> Target Role
                        </label>
                        <select
                            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                            value={formData.jobRole}
                            onChange={(e) => setFormData({ ...formData, jobRole: e.target.value })}
                        >
                            <option value="software_engineer">Software Engineer</option>
                            <option value="data_scientist">Data Scientist</option>
                            <option value="product_manager">Product Manager</option>
                            <option value="frontend_developer">Frontend Developer</option>
                            <option value="devops_engineer">DevOps Engineer</option>
                        </select>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90 text-white font-semibold py-4 rounded-xl shadow-lg shadow-indigo-500/25 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <span className="animate-pulse">Starting Session...</span>
                        ) : (
                            <>
                                Start Interview Session <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Home;
