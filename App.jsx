import React, { useState } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);

  const handleAsk = async () => {
    try {
      const form = new FormData();
      form.append("session_id", "demo1");
      form.append("text", query);

      const res = await axios.post("http://127.0.0.1:8000/ask", form);
      const answer = res.data.text;
      setResponse(answer);

      // fetch audio using /tts
      const audioRes = await axios.get(
        `http://127.0.0.1:8000/tts?text=${encodeURIComponent(answer)}`,
        { responseType: "blob" }
      );

      const url = URL.createObjectURL(audioRes.data);
      setAudioUrl(url);
    } catch (err) {
      console.error(err);
      setResponse("Error occurred.");
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>🚗 SalesBuddy AI</h2>
      <textarea
        rows={3}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ width: "100%", padding: 10 }}
        placeholder="Ask about Hyundai Venue, Nexon comparison, etc..."
      />
      <br />
      <button onClick={handleAsk} style={{ marginTop: 10, padding: "8px 16px" }}>
        Ask SalesBuddy
      </button>

      {response && (
        <div style={{ marginTop: 20 }}>
          <h4>Answer:</h4>
          <p>{response}</p>
          {audioUrl && (
            <audio controls autoPlay src={audioUrl} style={{ marginTop: 10 }} />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
