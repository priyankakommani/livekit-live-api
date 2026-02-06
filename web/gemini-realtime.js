/**
 * Gemini Realtime JS Client for Browser
 * Handles Multimodal Live WebSocket connection to Gemini 2.0 Flash
 */

class GeminiRealtime {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.ws = null;
        this.onAudioData = null; // Callback for audio output
        this.onTranscript = null; // Callback for text transcript
    }

    async connect() {
        return new Promise((resolve, reject) => {
            const url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.RealtimeService?key=${this.apiKey}`;
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log("Connected to Gemini Realtime API");
                this.sendSetup();
                resolve();
            };

            this.ws.onerror = (err) => {
                console.error("Gemini WebSocket Error:", err);
                reject(err);
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };
        });
    }

    sendSetup() {
        const setup = {
            setup: {
                model: "models/gemini-2.0-flash-exp",
                generation_config: {
                    response_modalities: ["AUDIO"],
                    speech_config: {
                        voice_config: { prebuilt_voice_config: { voice_name: "Puck" } }
                    }
                }
            }
        };
        this.ws.send(JSON.stringify(setup));
    }

    sendInitialPrompt(text) {
        console.log("Sending initial prompt to Gemini...");
        const payload = {
            client_content: {
                turns: [{
                    role: "user",
                    parts: [{ text: text || "Hello. I am here for the software engineer interview. Please start." }]
                }],
                turn_complete: true
            }
        };
        this.ws.send(JSON.stringify(payload));
    }

    sendAudioChunk(base64Audio) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                realtime_input: {
                    media_chunks: [{
                        data: base64Audio,
                        mime_type: "audio/pcm;rate=16000"
                    }]
                }
            }));
        }
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);

            // 1. Success setup
            if (data.setupComplete) {
                console.log("Gemini Setup Success.");
                this.sendInitialPrompt();
                return;
            }

            // 2. Incoming model turn
            if (data.serverContent?.modelTurn?.parts) {
                for (const part of data.serverContent.modelTurn.parts) {
                    if (part.inlineData?.mimeType === "audio/pcm;rate=24000") {
                        if (this.onAudioData) this.onAudioData(part.inlineData.data);
                    }
                    if (part.text) {
                        console.log("Gemini says:", part.text);
                        if (this.onTranscript) this.onTranscript("AI_Interviewer", part.text);
                    }
                }
            }

            // 3. Interruption
            if (data.serverContent?.interrupted) {
                console.log("Gemini turn interrupted");
            }

        } catch (e) {
            console.error("Error parsing Gemini message:", e);
        }
    }

    disconnect() {
        if (this.ws) this.ws.close();
    }
}
