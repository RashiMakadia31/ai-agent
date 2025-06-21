async function sendQuery() {
    const input = document.getElementById("queryInput").value.trim();
    const output = document.getElementById("assistantResponse");
  
    if (!input) {
      output.innerText = "❗ Please enter a query first.";
      return;
    }
  
    output.innerText = "⏳ Thinking...";
  
    try {
      const res = await fetch("http://localhost:8000/ai-assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: input })
      });
  
      const data = await res.json();
      output.innerText = data.response || "⚠️ No response received.";
    } catch (err) {
      output.innerText = "❌ Error contacting backend:\n" + err.message;
    }
  }
  