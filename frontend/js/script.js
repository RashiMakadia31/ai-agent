// ===================== DOM REFERENCES ===================== //
// Get references to key DOM elements for easier access
const messagesDiv = document.getElementById('messages');
const typingIndicator = document.getElementById('typingIndicator');
const input = document.getElementById('chatInput');
const modal = document.getElementById('codeEditorModal');
const themeToggle = document.getElementById('theme-toggle');
const hamburger = document.querySelector('.hamburger');
let chatHistory = {};  // Stores chat history in localStorage
let inputMonaco, outputMonaco;  // Monaco editor instances
// ===================== THEME TOGGLE ===================== //
// Switch between dark and light theme on button click
themeToggle.addEventListener('click', () => {
  document.body.classList.toggle('light-theme');
});
// ===================== SIDEBAR TOGGLE ===================== //
// Open/close the chat history sidebar
hamburger.addEventListener('click', () => {
  document.getElementById("sidebar").classList.toggle("open");
});
// ===================== MODE TOGGLES ===================== //
// Redirect user based on toggle selection
document.getElementById("mysql-toggle").addEventListener("change", (e) => {
  if (e.target.checked) window.location.href = "mysql_assistant.html";
});
document.getElementById("vscode-toggle").addEventListener("change", (e) => {
  if (e.target.checked) window.location.href = "http://localhost:8000/vscode-ui";
});
// ===================== LANGUAGE HANDLING ===================== //
// Get currently selected language
function getSelectedLang() {
  const selected = document.querySelector('input[name="language"]:checked');
  return selected ? selected.value : 'Python';
}
// Update Monaco editor language on selection change
document.querySelectorAll('input[name="language"]').forEach(input => {
  input.addEventListener('change', () => {
    const lang = getSelectedLang();
    if (inputMonaco) monaco.editor.setModelLanguage(inputMonaco.getModel(), lang.toLowerCase());
    if (outputMonaco) monaco.editor.setModelLanguage(outputMonaco.getModel(), lang.toLowerCase());
  });
});
// ===================== MODAL CONTROLS ===================== //
// Show/hide code editor modal
function toggleCodeEditor() {
  modal.classList.toggle("visible");
  modal.classList.remove("minimized", "maximized");
}
// Minimize editor window
function minimizeEditor() {
  modal.classList.remove("maximized");
  modal.classList.toggle("minimized");
}
// Maximize editor window
function maximizeEditor() {
  modal.classList.remove("minimized");
  modal.classList.toggle("maximized");
}
// ===================== CHAT MESSAGE HANDLING ===================== //
// Send message from input field
function sendMessage() {
  const msg = input.value.trim();
  if (!msg) return;
  // Validate query type
  if (!isCodingQuery(msg)) {
    alert("❌ This assistant only responds to code-related queries.");
    return;
  }
  addMessage(msg, false);  // Display user message
  input.value = '';
  typingIndicator.style.display = 'flex';
  // Async bot response
  (async () => {
    const response = await getBotResponse(msg);
    typingIndicator.style.display = 'none';
    addMessage(response, true);  // Display bot reply
    saveChatToHistory();
  })();
}
// Send code entered in code editor
async function sendEditorCode() {
  const codeInput = inputMonaco.getValue().trim();
  const promptInput = document.getElementById("promptBox").value.trim();

  if (!codeInput) {
    alert("❗ Please enter code to run.");
    return;
  }

  typingIndicator.style.display = 'flex';
  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptInput,
        code: codeInput,
        language: ""  // Let backend infer language
      })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    outputMonaco.setValue(result.response || "⚠️ No response");
  } catch (err) {
    console.error("Error sending editor code:", err);
    outputMonaco.setValue("⚠️ Error contacting assistant.");
  } finally {
    typingIndicator.style.display = 'none';
    saveChatToHistory();
  }
}
// Check if query is code-related using keyword match
function isCodingQuery(text) {
  const keywords = ["python", "sql", "pyspark", "debug", "error", "function", "class",
    "loop", "code", "program", "compiler", "syntax", "bug", "logic",
    "algorithm", "script", "runtime", "stack", "traceback", "query"];
  return keywords.some(kw => text.toLowerCase().includes(kw));
}
// Display message (user or bot) in chat area
function addMessage(text, isBot) {
  const msgElem = document.createElement('div');
  msgElem.className = 'message ' + (isBot ? 'bot' : 'user');

  const textElem = document.createElement('div');
  textElem.className = 'bubble-text';

  if (isBot) {
    // Parse markdown + add code block copy buttons
    const html = marked.parse(text);
    const wrapped = document.createElement('div');
    wrapped.innerHTML = html;

    wrapped.querySelectorAll('pre').forEach(pre => {
      const wrapper = document.createElement('div');
      wrapper.className = 'code-block-wrapper';

      const code = pre.querySelector('code')?.cloneNode(true) || document.createElement('code');
      if (!code.className.includes('language-')) {
        code.classList.add(`language-${getSelectedLang().toLowerCase()}`);
      }

      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-button';
      copyBtn.innerText = 'Copy';
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(code.innerText);
        copyBtn.innerText = 'Copied!';
        setTimeout(() => (copyBtn.innerText = 'Copy'), 1500);
      };

      wrapper.appendChild(copyBtn);
      const newPre = pre.cloneNode(false);
      newPre.appendChild(code);
      wrapper.appendChild(newPre);
      pre.replaceWith(wrapper);
    });

    textElem.innerHTML = "";
    textElem.appendChild(wrapped);
    hljs.highlightAll();
  } else {
    textElem.textContent = text;
  }

  msgElem.appendChild(textElem);
  messagesDiv.appendChild(msgElem);
  messagesDiv.scrollTo({ top: messagesDiv.scrollHeight, behavior: 'smooth' });
}
// Get bot response from API
async function getBotResponse(input) {
  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: input, language: getSelectedLang(), code: "" })
    });
    const result = await response.json();
    return result.response;
  } catch (err) {
    console.error("API error:", err);
    return "⚠️ Error contacting assistant.";
  }
}
// Handle file upload + preview
function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function (e) {
    const preview = e.target.result.slice(0, 300);
    addMessage(`📎 Uploaded "${file.name}"\n\n${preview}...`, false);
    saveChatToHistory();
  };
  reader.readAsText(file);
}
// ===================== CHAT HISTORY ===================== //
// Save chat to localStorage
function saveChatToHistory() {
  const id = "chat-" + Date.now();
  chatHistory[id] = messagesDiv.innerHTML;
  localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
  renderChatTabs();
}
// Render chat history tabs
function renderChatTabs() {
  const container = document.getElementById("chatTabs");
  container.innerHTML = '';
  const history = JSON.parse(localStorage.getItem("chatHistory")) || {};
  chatHistory = history;

  for (const id in history) {
    const wrapper = document.createElement("div");
    wrapper.className = "chat-tab-wrapper";

    const tab = document.createElement("div");
    tab.className = "chat-tab";
    tab.textContent = new Date(+id.split('-')[1]).toLocaleString();
    tab.onclick = () => {
      messagesDiv.innerHTML = history[id];
    };

    const del = document.createElement("button");
    del.className = "chat-delete-btn";
    del.innerHTML = "⋮";
    del.onclick = (e) => {
      e.stopPropagation();
      delete history[id];
      localStorage.setItem("chatHistory", JSON.stringify(history));
      renderChatTabs();
    };

    wrapper.appendChild(tab);
    wrapper.appendChild(del);
    container.appendChild(wrapper);
  }
}
renderChatTabs();  // Initialize on load
// ===================== DRAGGABLE MODAL ===================== //
const modalHeader = document.querySelector(".code-editor-header");
let isDragging = false, offsetX = 0, offsetY = 0;
// Start dragging
modalHeader.addEventListener("mousedown", (e) => {
  if (modal.classList.contains("maximized")) return;
  isDragging = true;
  const rect = modal.getBoundingClientRect();
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
  modal.classList.add("dragging");
});
// Stop dragging
document.addEventListener("mouseup", () => {
  isDragging = false;
  modal.classList.remove("dragging");
});
// Update modal position
document.addEventListener("mousemove", (e) => {
  if (!isDragging) return;
  modal.style.top = `${e.clientY - offsetY}px`;
  modal.style.left = `${e.clientX - offsetX}px`;
  modal.style.transform = "none";
});
// ===================== MONACO EDITOR SETUP ===================== //
require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
require(['vs/editor/editor.main'], function () {
  inputMonaco = monaco.editor.create(document.getElementById('inputEditor'), {
    value: '',
    language: 'python',
    theme: 'vs-dark',
    automaticLayout: true
  });

  outputMonaco = monaco.editor.create(document.getElementById('outputEditor'), {
    value: '',
    language: 'python',
    theme: 'vs-dark',
    readOnly: true,
    automaticLayout: true
  });
  // Sync language change with editors
  document.querySelectorAll('input[name="language"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const lang = getSelectedLang().toLowerCase();
      monaco.editor.setModelLanguage(inputMonaco.getModel(), lang);
      monaco.editor.setModelLanguage(outputMonaco.getModel(), lang);
    });
  });
});
// ===================== COPY FUNCTIONS ===================== //
function copyInputMonaco() {
  navigator.clipboard.writeText(inputMonaco.getValue());
}

function copyOutputMonaco() {
  navigator.clipboard.writeText(outputMonaco.getValue());
}
// ===================== ENTER KEY HANDLER ===================== //
// Trigger send on Enter (Shift+Enter allows new line)
input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
