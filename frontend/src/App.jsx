import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Home';
import InterviewRoom from './InterviewRoom';
import PostInterview from './PostInterview';

function App() {
    return (
        <Router>
            <div className="min-h-screen text-white">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/room/:sessionId" element={<InterviewRoom />} />
                    <Route path="/success/:sessionId" element={<PostInterview />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
