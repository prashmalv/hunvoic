import React, { useState, useRef } from "react";
import axios from "axios";
import jsPDF from "jspdf";

function App() {
  const [query, setQuery] = useState("");
  const [conversation, setConversation] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // --- Text Ask ---
  const handleAsk = async () => {
    try {
      const form = new FormData();
      form.append("session_id", "demo1");
      form.append("text", query);

      const res = await axios.post("http://127.0.0.1:8000/ask", form);
      const answer = res.data.text;

      setConversation((prev) => [
        ...prev,
        { role: "user", text: query },
        { role: "agent", text: answer }
      ]);
      setQuery("");

      // fetch audio
      const audioRes = await axios.get(
        `http://127.0.0.1:8000/tts?text=${encodeURIComponent(answer)}`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(audioRes.data);
      const audio = new Audio(url);
      audio.play();
    } catch (err) {
      console.error(err);
    }
  };

  // --- Voice Ask ---
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
        const res = await axios.post("http://127.0.0.1:8000/ask-voice", form);
        const { user_text, resp_text, audio_url } = res.data;

        setConversation((prev) => [
          ...prev,
          { role: "user", text: user_text },
          { role: "agent", text: resp_text }
        ]);

        if (audio_url) {
          const audio = new Audio("http://127.0.0.1:8000" + audio_url);
          audio.play();
        }
      } catch (err) {
        console.error("Voice ask failed", err);
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

  // --- Export Conversation ---
  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(conversation, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "conversation.json";
    link.click();
  };

  const exportPDF = () => {
    const doc = new jsPDF();
    let y = 10;
    conversation.forEach((msg, idx) => {
      const text = `${msg.role === "user" ? "You" : "SalesBuddy"}: ${msg.text}`;
      doc.text(text, 10, y);
      y += 10;
      if (y > 280) {
        doc.addPage();
        y = 10;
      }
    });
    doc.save("conversation.pdf");
  };

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>🚗 SalesBuddy AI</h2>

      {/* Text Query */}
      <textarea
        rows={3}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ width: "100%", padding: 10 }}
        placeholder="Ask about Hyundai Venue, Nexon comparison, etc..."
      />
      <br />
      <button onClick={handleAsk} style={{ marginTop: 10, padding: "8px 16px" }}>
        Ask SalesBuddy (Text)
      </button>

      {/* Voice Query */}
      <div style={{ marginTop: 20 }}>
        {!isRecording ? (
          <button onClick={startRecording} style={{ padding: "8px 16px" }}>
            🎙 Start Speaking
          </button>
        ) : (
          <button onClick={stopRecording} style={{ padding: "8px 16px", background: "red", color: "white" }}>
            ⏹ Stop Recording
          </button>
        )}
      </div>

      {/* Conversation */}
      <div style={{ marginTop: 30 }}>
        <h4>Conversation:</h4>
        {conversation.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: 10 }}>
            <b>{msg.role === "user" ? "You" : "SalesBuddy"}:</b> {msg.text}
          </div>
        ))}
      </div>

      {/* Export Buttons */}
      <div style={{ marginTop: 20 }}>
        <button onClick={exportJSON} style={{ marginRight: 10, padding: "6px 12px" }}>
          ⬇ Export JSON
        </button>
        <button onClick={exportPDF} style={{ padding: "6px 12px" }}>
          📄 Export PDF
        </button>
      </div>
    </div>
  );
}

export default App;
