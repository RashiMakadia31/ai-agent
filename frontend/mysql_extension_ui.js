// Use same-origin API base so this works in local and deployed environments.
const API_BASE_URL = window.location.origin;

let currentSchema = "";
const chatArea = document.getElementById("chatArea");
const userInput = document.getElementById("userInput");

function parseAndDisplayTables(schemaString) {
  const tableList = document.getElementById("tableList");
  if (!tableList) return;

  const regex = /Table: (\w+)/gi;
  const tableNames = [];
  let match;
  while ((match = regex.exec(schemaString)) !== null) {
    tableNames.push(match[1]);
  }

  tableList.innerHTML = "";
  if (!tableNames.length) {
    tableList.innerHTML = "<li>No tables found.</li>";
    return;
  }

  tableNames.forEach((name) => {
    const listItem = document.createElement("li");
    listItem.textContent = name;
    listItem.onclick = () => {
      const input = document.getElementById("userInput");
      input.value += ` ${name} `;
      input.focus();
    };
    tableList.appendChild(listItem);
  });
}

async function connectAndLoadSchema() {
  const host = document.getElementById("dbHost").value.trim();
  const user = document.getElementById("dbUser").value.trim();
  const password = document.getElementById("dbPassword").value.trim();
  const database = document.getElementById("dbDatabase").value.trim();
  const port = 3306;

  const connectionStatus = document.getElementById("connectionStatus");
  const schemaOutput = document.getElementById("schemaOutput");

  if (!host || !user || !database) {
    connectionStatus.innerText = "Please fill in Host, User, and Database fields.";
    connectionStatus.className = "status-message status-error";
    return;
  }

  connectionStatus.innerText = "Connecting and loading schema...";
  connectionStatus.className = "status-message status-info";
  schemaOutput.innerText = "Loading...";
  currentSchema = "";

  try {
    const res = await fetch(`${API_BASE_URL}/sql/connect-and-schema`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host, user, password, database, port })
    });

    const data = await res.json();
    if (!res.ok) {
      connectionStatus.innerText = `Connection Error: ${data.detail || data.message || "Unknown error"}`;
      connectionStatus.className = "status-message status-error";
      schemaOutput.innerText = "Failed to load schema.";
      addMessage(`Connection Error: ${data.detail || data.message || "Unknown error"}`, "bot");
      return;
    }

    connectionStatus.innerText = data.message || "Connected to MySQL.";
    connectionStatus.className = "status-message status-info";
    currentSchema = data.schema || "";
    schemaOutput.innerText = currentSchema || "No schema returned.";
    addMessage("Connected to MySQL successfully. Schema loaded.", "bot");
    parseAndDisplayTables(currentSchema);
  } catch (err) {
    connectionStatus.innerText = "Error contacting backend: " + err.message;
    connectionStatus.className = "status-message status-error";
    schemaOutput.innerText = "Failed to load schema.";
    addMessage(`Error contacting backend: ${err.message}`, "bot");
  }
}

function handleKeyDown(event) {
  if (event.key === "Enter") {
    sendMessage();
    event.preventDefault();
  }
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addMessage(text, "user");
  userInput.value = "";

  if (!currentSchema) {
    renderBotMessage("Please connect to MySQL and load the schema first.");
    return;
  }

  renderBotMessage("Asking assistant...");

  try {
    const res = await fetch(`${API_BASE_URL}/sql/ask-ai`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: `${text}\n\nDatabase schema:\n${currentSchema}`
      })
    });

    const data = await res.json();
    if (res.ok) {
      renderBotMessage(data.response || "No response");
    } else {
      renderBotMessage(`Error from assistant: ${data.detail || data.message || "Unknown error"}`);
    }
  } catch (err) {
    console.error(err);
    renderBotMessage("Could not connect to backend.");
  }
}

function addMessage(msg, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  div.textContent = msg;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function renderBotMessage(text) {
  const html = marked.parse(text);
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.innerHTML = html;

  wrapper.querySelectorAll("pre").forEach((pre) => {
    const code = pre.querySelector("code");
    if (code && !code.className.includes("language-")) {
      code.className = "language-sql";
    }

    const outer = document.createElement("div");
    outer.className = "code-block-wrapper";
    pre.replaceWith(outer);
    outer.appendChild(pre);

    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-button";
    copyBtn.innerText = "Copy";
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(code ? code.innerText : pre.innerText);
      copyBtn.innerText = "Copied!";
      setTimeout(() => {
        copyBtn.innerText = "Copy";
      }, 2000);
    };
    outer.appendChild(copyBtn);
  });

  chatArea.appendChild(wrapper);
  chatArea.scrollTop = chatArea.scrollHeight;
  hljs.highlightAll();
}

document.addEventListener("DOMContentLoaded", () => hljs.highlightAll());

function openMySQLModal() {
  mysqlConnectionModal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeMySQLModal() {
  mysqlConnectionModal.style.display = "none";
  document.body.style.overflow = "";
}
