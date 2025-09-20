import React, { useState, useRef } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [conversation, setConversation] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  // --- Send Text Query ---
  const handleAsk = async () => {
    if (!query.trim()) return;
    try {
      const form = new FormData();
      form.append("session_id", "demo1");
      form.append("text", query);

      setConversation((prev) => [...prev, { role: "user", text: query }]);
      setQuery("");
      setIsTyping(true);

      const res = await axios.post("http://127.0.0.1:8000/ask", form);
      const answer = res.data.text;

      setConversation((prev) => [...prev, { role: "agent", text: answer }]);
      setIsTyping(false);

      const audioRes = await axios.get(
        `http://127.0.0.1:8000/tts?text=${encodeURIComponent(answer)}`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(audioRes.data);
      const audio = new Audio(url);
      currentAudioRef.current = audio;
      setIsAgentSpeaking(true);
      audio.play();
      audio.onended = () => setIsAgentSpeaking(false);
    } catch (err) {
      console.error(err);
      setIsTyping(false);
    }
  };

  // --- Voice Query ---
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    mediaRecorderRef.current = mediaRecorder;
    chunksRef.current = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const form = new FormData();
      form.append("session_id", "demo1");
      form.append("audio", blob, "query.webm");

      try {
        setIsTyping(true);
        const res = await axios.post("http://127.0.0.1:8000/ask-voice", form);
        const { user_text, resp_text, audio_url } = res.data;

        setConversation((prev) => [
          ...prev,
          { role: "user", text: user_text },
          { role: "agent", text: resp_text }
        ]);
        setIsTyping(false);

        if (audio_url) {
          const audio = new Audio("http://127.0.0.1:8000" + audio_url);
          currentAudioRef.current = audio;
          setIsAgentSpeaking(true);
          audio.play();
          audio.onended = () => setIsAgentSpeaking(false);
        }
      } catch (err) {
        console.error("Voice ask failed", err);
        setIsTyping(false);
      }
    };

    mediaRecorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const pauseAgentSpeaking = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsAgentSpeaking(false);
    }
  };

  const stopAgentSpeaking = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      setIsAgentSpeaking(false);
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "auto", padding: 20, fontFamily: "Arial" }}>
      {/* Header */}
      <div
        style={{
          textAlign: "center",
          fontSize: 22,
          fontWeight: "bold",
          marginBottom: 10,
          color: "#007bff"
        }}
      >
        📞 AI Veenu
      </div>

      {/* Car Image Banner */}
      <img
        src="https://www.hyundai.com/content/dam/hyundai/in/en/data/find-a-car/venue/performance/venue-performance-1.jpg"
        alt="Hyundai Venue"
        style={{
          width: "100%",
          borderRadius: "8px",
          marginBottom: "5px",
          boxShadow: "0px 4px 8px rgba(0,0,0,0.2)"
        }}
      />
      <div style={{ textAlign: "center", marginBottom: 20, fontStyle: "italic", color: "#555" }}>
        Your Smart Sales Assistant for Hyundai Venue Cars
      </div>

      {/* Chat Window */}
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: "8px",
          height: "400px",
          overflowY: "auto",
          padding: "10px",
          marginBottom: "15px",
          background: "#fefefe"
        }}
      >
        {conversation.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              margin: "8px 0"
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: "15px",
                background: msg.role === "user" ? "#007bff" : "#e5e5ea",
                color: msg.role === "user" ? "white" : "black",
                maxWidth: "70%",
                wordWrap: "break-word"
              }}
            >
              {msg.text}
            </span>
          </div>
        ))}
        {isTyping && <div>💬 AI Veenu is typing...</div>}
      </div>

      {/* Input Bar */}
      <div style={{ display: "flex", marginBottom: "10px" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          style={{
            flex: 1,
            padding: 10,
            border: "1px solid #ccc",
            borderRadius: "5px 0 0 5px"
          }}
          placeholder="Type your question..."
        />
        <button
          onClick={handleAsk}
          style={{
            padding: "0 20px",
            border: "none",
            borderRadius: "0 5px 5px 0",
            background: "#007bff",
            color: "white"
          }}
        >
          Send
        </button>
      </div>

      {/* Voice Control Buttons */}
      <div style={{ display: "flex", justifyContent: "center", gap: "15px" }}>
        {!isRecording ? (
          <button
            onClick={startRecording}
            style={{
              padding: "10px 20px",
              borderRadius: "5px",
              background: "#24cfa7ff",
              color: "white",
              border: "none"
            }}
          >
            🎙 Speak
          </button>
        ) : (
          <button
            onClick={stopRecording}
            style={{
              padding: "10px 20px",
              borderRadius: "5px",
              background: "red",
              color: "white",
              border: "none"
            }}
          >
            ⏹ Stop Recording
          </button>
        )}

        {isAgentSpeaking && (
          <>
            <button
              onClick={pauseAgentSpeaking}
              style={{
                padding: "10px 20px",
                borderRadius: "5px",
                background: "#ffc107",
                color: "black",
                border: "none"
              }}
            >
              ⏸ Pause
            </button>
            <button
              onClick={stopAgentSpeaking}
              style={{
                padding: "10px 20px",
                borderRadius: "5px",
                background: "#dc3545",
                color: "white",
                border: "none"
              }}
            >
              ⏹ Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
