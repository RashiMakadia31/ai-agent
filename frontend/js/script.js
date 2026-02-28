// ===================== DOM REFERENCES ===================== //
const messagesDiv = document.getElementById('messages');
const typingIndicator = document.getElementById('typingIndicator');
const input = document.getElementById('chatInput');
const modal = document.getElementById('codeEditorModal');
const themeToggle = document.getElementById('theme-toggle');
const hamburger = document.querySelector('.hamburger');
const greeting = document.getElementById('greeting');
const API_BASE_URL = window.location.origin;
let chatHistory = {};
let inputMonaco, outputMonaco;

// ===================== AUTHENTICATION CHECK ===================== //
document.addEventListener("DOMContentLoaded", () => {
  const isLoggedIn = localStorage.getItem("isLoggedIn");
  const username = localStorage.getItem("loggedInUser");

  if (isLoggedIn !== "true") {
    window.location.href = "/login";
    return;
  }

  if (greeting && username) {
    greeting.textContent = `Welcome, ${username}`;
  }
});

// ===================== THEME TOGGLE ===================== //
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
  });
}

// ===================== SIDEBAR TOGGLE ===================== //
if (hamburger) {
  hamburger.addEventListener('click', () => {
    document.getElementById("sidebar").classList.toggle("open");
  });
}

// ===================== MODE TOGGLE ===================== //
const mysqlBtn = document.getElementById("mysql-glass-btn");
if (mysqlBtn) {
  mysqlBtn.addEventListener("click", () => {
    window.location.href = "/mysql-ui";
  });
}

// ===================== LANGUAGE HANDLING ===================== //
function getSelectedLang() {
  const selected = document.querySelector('input[name="language"]:checked');
  return selected ? selected.value : 'Python';
}

document.querySelectorAll('input[name="language"]').forEach(input => {
  input.addEventListener('change', () => {
    const lang = getSelectedLang().toLowerCase();
    if (inputMonaco) monaco.editor.setModelLanguage(inputMonaco.getModel(), lang);
    if (outputMonaco) monaco.editor.setModelLanguage(outputMonaco.getModel(), lang);
  });
});

// ===================== MODAL CONTROLS ===================== //
function toggleCodeEditor() {
  modal.classList.toggle("visible");
  modal.classList.remove("minimized", "maximized");
}

function minimizeEditor() {
  modal.classList.remove("maximized");
  modal.classList.toggle("minimized");
}

function maximizeEditor() {
  modal.classList.remove("minimized");
  modal.classList.toggle("maximized");
}

// ===================== CHAT MESSAGE HANDLING ===================== //
// Send message from input field
function sendMessage() {
  const msg = input.value.trim();
  if (!msg) return;

  if (!isCodingQuery(msg)) {
    alert("❌ This assistant responds only to code-related queries.");
    return;
  }

  // This line is crucial - it displays your message immediately.
  addMessage(msg, false);

  input.value = '';
  typingIndicator.style.display = 'flex';

  // This block fetches and displays the bot's response.
  (async () => {
    const botResponse = await getBotResponse(msg);
    typingIndicator.style.display = 'none';
    addMessage(botResponse, true);
    saveChatToHistory();
  })();
}

/// ===================== ENHANCED: SEND EDITOR CODE TO BACKEND ===================== //
async function sendEditorCode() {
  const promptInput = document.getElementById("promptBox").value.trim();
  const codeInput = inputMonaco?.getValue().trim();
  const filePath = currentFilePath || "manual_input.py";
  const useContext = document.getElementById("useProjectContext")?.checked ?? true;

  if (!promptInput || !codeInput) {
    alert("❗ Please enter both a prompt and code.");
    return;
  }

  // ✅ Payload with project context
  const payload = {
    prompt: promptInput,
    language: getSelectedLang(),
    code: codeInput,
    file: filePath,
    use_project_context: useContext,
    project_files: useContext ? uploadedFiles : {}  // full folder snapshot
  };

  console.log("📤 Sending payload:", payload);
  typingIndicator.style.display = 'flex';

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const result = await response.json();

    if (!result.response && !result.commented_code) {
      throw new Error("❌ No valid response received.");
    }

    const explanation = result.explanation || "";
    let output = result.commented_code || result.response || "No output.";

    if (typeof output !== 'string') {
      output = JSON.stringify(output, null, 2);
    }

    let combinedOutput = output;
    if (explanation && explanation.trim().toLowerCase() !== "no explanation provided.") {
      combinedOutput = `# 🧠 Explanation:\n${explanation}\n\n${output}`;
    }

    outputMonaco.setValue(combinedOutput);

    const rhs = document.getElementById("rhsEditor") || document.getElementById("outputEditor");
    if (rhs && rhs.style.display === "none") {
      rhs.style.display = "block";
    }

  } catch (err) {
    console.error("❌ Error in sendEditorCode:", err);
    outputMonaco?.setValue(`⚠️ Error: ${err.message}`);
  } finally {
    typingIndicator.style.display = 'none';
  }

  connectThinkingLogStream();
}

// ===================== CODE DETECTION HELPER ===================== //
// Check if query is code-related using keyword match
function isCodingQuery(text) {
  const keywords = ["python", "sql", "pyspark", "debug", "error", "function", "class",
    "loop", "code", "program", "compiler", "syntax", "bug", "logic",
    "algorithm", "script", "runtime", "stack", "traceback", "query"];
  return keywords.some(kw => text.toLowerCase().includes(kw));
}

// ===================== GET BOT RESPONSE ===================== //
async function getBotResponse(input) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: input, language: getSelectedLang(), code: "" })
    });
    const result = await response.json();
    return result;  // ✅ return full object including response + thinking_log
  } catch (err) {
    console.error("API error:", err);
    return { response: "⚠️ Error contacting assistant." };
  }
}


// ===================== CHAT MESSAGE RENDERER ===================== //
function addMessage(responseData, isBot) {
  const msgElem = document.createElement('div');
  msgElem.className = 'message ' + (isBot ? 'bot' : 'user');

  const textElem = document.createElement('div');
  textElem.className = 'bubble-text';

  const text = typeof responseData === 'string'
    ? responseData
    : responseData?.response || '⚠️ No response from assistant.';

  // === 🛡️ UNETHICAL DETECTION HANDLER (manual flagging support) === //
  const isViolation = typeof responseData === 'object' && responseData.violation === true;
  if (isViolation) {
    textElem.innerHTML = `
      <div class="violation-warning">
        ❌ <strong>Request blocked:</strong> ${text}
      </div>
    `;
    msgElem.appendChild(textElem);
    messagesDiv.appendChild(msgElem);
    messagesDiv.scrollTo({ top: messagesDiv.scrollHeight, behavior: 'smooth' });
    return;
  }

  // === 🧠 BOT MESSAGE HANDLING === //
  if (isBot) {
    const wrapped = document.createElement('div');
    const codeRegex = /```(\w*)\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;
    let hasValidCode = false;

    while ((match = codeRegex.exec(text)) !== null) {
      const lang = match[1] || getSelectedLang().toLowerCase();
      const codeContent = match[2];

      const beforeText = text.substring(lastIndex, match.index);
      if (beforeText.trim()) {
        const beforeDiv = document.createElement('div');
        beforeDiv.innerHTML = marked.parse(beforeText.trim());
        wrapped.appendChild(beforeDiv);
      }

      // 🛡️ If this looks like a warning or denial, skip Monaco
      if (codeContent.includes("❌") || codeContent.includes("⚠️")) {
        const denial = document.createElement('div');
        denial.innerHTML = marked.parse(codeContent);
        wrapped.appendChild(denial);
      } else {
        hasValidCode = true;
        const container = document.createElement('div');
        container.className = 'monaco-editor-container';

        const editorDiv = document.createElement('div');
        editorDiv.className = 'editor';
        container.appendChild(editorDiv);

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-monaco';
        copyBtn.textContent = 'Copy';
        copyBtn.onclick = () => {
          navigator.clipboard.writeText(codeContent);
          copyBtn.textContent = 'Copied!';
          setTimeout(() => (copyBtn.textContent = 'Copy'), 1500);
        };
        container.appendChild(copyBtn);

        if (typeof monaco !== 'undefined') {
          monaco.editor.create(editorDiv, {
            value: codeContent,
            language: lang,
            theme: 'vs-dark',
            readOnly: true,
            automaticLayout: true,
            wordWrap: 'on',
          });
        } else {
          editorDiv.textContent = codeContent;
          console.warn("⚠️ Monaco editor not loaded.");
        }

        wrapped.appendChild(container);
      }

      lastIndex = codeRegex.lastIndex;
    }

    // === Append any trailing explanation text === //
    const afterText = text.substring(lastIndex).trim();
    if (afterText) {
      const afterDiv = document.createElement('div');
      afterDiv.innerHTML = marked.parse(afterText);
      wrapped.appendChild(afterDiv);
    }

    textElem.innerHTML = "";
    textElem.appendChild(wrapped);
  } else {
    textElem.textContent = text;
  }

  msgElem.appendChild(textElem);
  messagesDiv.appendChild(msgElem);
  messagesDiv.scrollTo({ top: messagesDiv.scrollHeight, behavior: 'smooth' });

  // === Thinking Log ===
  if (isBot && typeof responseData === 'object' && responseData.thinking_log) {
    const logDiv = document.createElement('div');
    logDiv.className = 'thinking-log';
    logDiv.innerHTML = `
      <details>
        <summary>🧠 Thinking Log</summary>
        <pre>${responseData.thinking_log.join('\n')}</pre>
      </details>
    `;
    messagesDiv.appendChild(logDiv);
  }
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
      messagesDiv.scrollTo({ top: messagesDiv.scrollHeight, behavior: 'smooth' });
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

// Initialize chat tabs on load
renderChatTabs();

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
input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ===================== LOGOUT ===================== //
function logout() {
  localStorage.removeItem("isLoggedIn");
  localStorage.removeItem("loggedInUser");
  window.location.href = "/login";
}

// ===================== CONTINUE EDITING OUTPUT ===================== //
function continueEditing() {
  const outputCode = outputMonaco.getValue();
  if (!outputCode.trim()) {
    alert("⚠️ No code in the output editor to continue editing.");
    return;
  }
  inputMonaco.setValue(outputCode);
}

// ===================== GLOBAL ===================== //
let uploadedFiles = {};      // key: relative path, value: file content
let currentFilePath = '';    // currently selected file path

// ===================== FOLDER INPUT HANDLER ===================== //
document.getElementById('folderInput').addEventListener('change', async (e) => {
  const files = e.target.files;
  if (!files || files.length === 0) return;

  uploadedFiles = {};
  const tree = {};
  let baseFolder = ""; // ⬅️ For project context path

  for (const file of files) {
    const path = file.webkitRelativePath || file.name;
    const content = await file.text();
    uploadedFiles[path] = content;
    buildTree(tree, path.split('/'), content);

    if (!baseFolder) {
      const parts = path.split('/');
      baseFolder = parts.slice(0, parts.length - 1).join('/');
    }
  }

  renderInputTree(tree);

  // === Trigger LLM file analysis (optional legacy route) ===
  try {
    const res = await fetch(`${API_BASE_URL}/analyze-folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: uploadedFiles }),
    });

    const data = await res.json();
    window.agentInsights = data;
    console.log("🧠 Agent insights:", data);
    renderInputTree(tree);
  } catch (err) {
    console.error("❌ Failed agent analysis:", err);
  }

  // === New: Load full project context from folder path ===
  try {
    const contextRes = await fetch(`${API_BASE_URL}/load_project_context`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder_path: baseFolder }),
    });

    const contextData = await contextRes.json();
    console.log("✅ Project context loaded:", contextData.message);
    console.log("🧠 Thinking log:", contextData.thinking_log);

    // Show UI badge if needed
    const badge = document.getElementById("contextStatus");
    if (badge) badge.classList.remove("hidden");

  } catch (err) {
    console.error("❌ Failed to load project context:", err);
  }
});


// ===================== FILE TREE BUILDING ===================== //

// ✅ Checks if the file is a valid code file (ignores hidden/system files)
function isCodeFile(filename) {
  const allowedExtensions = /\.(py|js|ts|java|cpp|c|html|css|sql)$/i;
  const systemOrHidden = filename.includes('__pycache__') ||
                         filename.includes('.DS_Store') ||
                         filename.startsWith('.') ||
                         filename.endsWith('/');
  return allowedExtensions.test(filename) && !systemOrHidden;
}

// ✅ Groups uploaded files by top-level folder
function groupFilesByFolder(fileMap) {
  const grouped = {};
  for (const fullPath in fileMap) {
    if (!isCodeFile(fullPath)) continue;
    const parts = fullPath.split('/');
    const folder = parts.length > 1 ? parts[0] : 'root';
    if (!grouped[folder]) grouped[folder] = {};
    grouped[folder][fullPath] = fileMap[fullPath];
  }
  return grouped;
}

// ===================== TREE RENDERER (FLAT FOLDER VIEW) ===================== //
function renderInputTree(fileMap) {
  const container = document.getElementById("fileTree");
  container.innerHTML = "";

  const grouped = groupFilesByFolder(fileMap);

  for (const folder in grouped) {
    const wrapper = document.createElement("div");
    wrapper.className = "folder-wrapper";

    const icon = document.createElement("div");
    icon.className = "folder-icon-container";
    icon.innerHTML = `<i class="fa-solid fa-folder-open"></i>`;

    const name = document.createElement("div");
    name.className = "folder-name";
    name.textContent = folder;

    const ul = document.createElement("ul");
    ul.className = "file-list";

    for (const fullPath in grouped[folder]) {
      const fileName = fullPath.split("/").pop();

      const li = document.createElement("li");
      li.className = "file";
      li.setAttribute("data-fullpath", fullPath);
      li.innerHTML = `<span class="file-label">${fileName}</span>`;

      li.onclick = () => {
        currentFilePath = fullPath;
        inputMonaco.setValue(fileMap[fullPath]);
        highlightActiveFile(fullPath);
      };

      ul.appendChild(li);
    }

    wrapper.appendChild(icon);
    wrapper.appendChild(name);
    wrapper.appendChild(ul);
    container.appendChild(wrapper);
  }
}

// ===================== UTILITY ===================== //

// ✅ Highlight the selected file in the file tree
function highlightActiveFile(path) {
  document.querySelectorAll('#fileTree li.file').forEach(el => el.classList.remove('active-file'));
  const match = [...document.querySelectorAll('#fileTree li.file')]
    .find(li => li.getAttribute('data-fullpath') === path);
  if (match) match.classList.add('active-file');
}

// ✅ Get full relative path from <li>
function getFullPathFromLI(li) {
  return li.getAttribute('data-fullpath');
}

// ===================== FOLDER UPLOAD HANDLER ===================== //
document.getElementById('folderInput').addEventListener('change', (e) => {
  const files = Array.from(e.target.files);
  const fileMap = {};
  files.forEach(file => {
    const fullPath = file.webkitRelativePath;
    const reader = new FileReader();
    reader.onload = (evt) => {
      fileMap[fullPath] = evt.target.result;
      uploadedFiles[fullPath] = evt.target.result;
      if (Object.keys(fileMap).length === files.length) {
        renderInputTree(fileMap);
      }
    };
    reader.readAsText(file);
  });
});

// ===================== GLOBAL DRAG & DROP ===================== //
document.addEventListener('dragover', (e) => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  document.body.classList.add('drag-over');
});

document.addEventListener('dragleave', (e) => {
  if (e.relatedTarget === null) {
    document.body.classList.remove('drag-over');
  }
});

document.addEventListener('drop', async (e) => {
  e.preventDefault();
  document.body.classList.remove('drag-over');
  const items = Array.from(e.dataTransfer.items).filter(item => item.kind === 'file');
  if (!items.length) return;
  await traverseDroppedItems(items);
});

// Traverse dropped folder structure
async function traverseDroppedItems(items) {
  uploadedFiles = {};
  const fileTree = {};
  const promises = [];

  for (const item of items) {
    const entry = item.webkitGetAsEntry?.();
    if (entry) promises.push(readEntryRecursive(entry, '', fileTree));
  }

  await Promise.all(promises);
  renderInputTree(fileTree);
}

// Recursively read folder entries
async function readEntryRecursive(entry, path = '', tree = {}) {
  return new Promise((resolve) => {
    if (entry.isFile) {
      entry.file(async (file) => {
        const fullPath = path + file.name;
        const content = await file.text();
        uploadedFiles[fullPath] = content;
        tree[fullPath] = content;
        resolve();
      });
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      reader.readEntries(async (entries) => {
        const innerPromises = entries.map((e) => readEntryRecursive(e, `${path}${entry.name}/`, tree));
        await Promise.all(innerPromises);
        resolve();
      });
    }
  });
}

// Dummy placeholder (safe fallback)
function renderOutputTree(fileTree) {
  // Left intentionally blank (customize if needed)
}



// ===================== THINKING LOG MODAL ===================== //

// Toggle thinking log modal visibility
function toggleThinkingLog() {
  const modal = document.getElementById("thinkingLogModal");
  const isOpening = modal.classList.toggle("hidden");

  if (isOpening) {
    startThinkingLogStream();
  } else {
    stopThinkingLogStream();
  }
}

// Close modal manually (× button)
function closeThinkingLog() {
  document.getElementById("thinkingLogModal").classList.add("hidden");
  stopThinkingLogStream();
}

// Append streamed log line to modal content
function streamThinkingLog(line) {
  const logElement = document.getElementById("thinkingLogContent");
  const div = document.createElement("div");
  div.className = "thinking-line";
  div.textContent = line;
  logElement.appendChild(div);
  logElement.scrollTop = logElement.scrollHeight;
}

// Start the SSE stream from backend
function startThinkingLogStream() {
  const logEl = document.getElementById("thinkingLogContent");
  logEl.textContent = "🧠 Agent is thinking...\n";

  eventSource = new EventSource(`${API_BASE_URL}/thinking-log`);

  eventSource.onmessage = function (event) {
    streamThinkingLog(event.data);
  };

  eventSource.onerror = function () {
    streamThinkingLog("⚠️ Lost connection to thinking stream.");
    console.error("❌ Thinking log stream error");
    eventSource.close();
  };
}

/// ===================== THINKING STREAM CONTROL ===================== //

// Stop the SSE stream
function stopThinkingLogStream() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

// Trigger thinking log from non-modal events
function connectThinkingLogStream() {
  const logEl = document.getElementById("thinkingLogContent");
  logEl.textContent = "🧠 Agent is thinking...\n";

  eventSource = new EventSource(`${API_BASE_URL}/thinking-log`);

  eventSource.onmessage = (event) => {
    streamThinkingLog(event.data);
  };

  eventSource.onerror = () => {
    streamThinkingLog("Thinking Complete");
    eventSource.close();
  };
}

// ===================== MONACO SNIPPET RENDERER ===================== //
function createMonacoSnippetBlock(lang, codeContent) {
  const container = document.createElement('div');
  container.className = 'monaco-snippet-container';
  container.style.height = "300px";
  container.style.marginTop = "12px";

  const editorDiv = document.createElement('div');
  editorDiv.className = 'monaco-snippet-editor';
  editorDiv.style.width = "100%";
  editorDiv.style.height = "100%";

  container.appendChild(editorDiv);

  // Wait until it's added to the DOM before initializing
  setTimeout(() => {
    require(['vs/editor/editor.main'], function () {
      monaco.editor.create(editorDiv, {
        value: codeContent,
        language: lang.toLowerCase(),
        theme: 'vs-dark',
        readOnly: true,
        automaticLayout: true,
        wordWrap: 'on'
      });
    });
  }, 0);

  return container;
}



// ===================== INSIGHT TOOLTIP HELPERS ===================== //
function showInsight(filename, event) {
  const data = window.agentInsights?.[filename];
  if (!data) return;

  const tooltip = document.getElementById("insightTooltip");
  tooltip.innerHTML = `
    <strong>🧠 Agent:</strong> ${data.agent}<br/>
    <strong>📄 Purpose:</strong> ${data.purpose}<br/>
    <strong>🔍 Review:</strong> ${data.review}
  `;
  tooltip.style.display = "block";
  tooltip.style.top = `${event.clientY + 10}px`;
  tooltip.style.left = `${event.clientX + 15}px`;
}

function hideInsight() {
  const tooltip = document.getElementById("insightTooltip");
  tooltip.style.display = "none";
}

function showTooltip(insight, x, y) {
  const tooltip = document.getElementById("insightTooltip");
  if (!tooltip) return;

  tooltip.style.left = `${x + 15}px`;
  tooltip.style.top = `${y}px`;
  tooltip.innerHTML = insight
    ? `
      📄 <b>Purpose:</b> ${insight.purpose}<br>
      🤖 <b>Agent:</b> ${insight.agent}<br>
      🔍 <b>Review:</b> ${insight.review}
    `
    : `🧠 Thinking...`;

  tooltip.style.display = 'block';
}

function hideTooltip() {
  const tooltip = document.getElementById("insightTooltip");
  if (tooltip) tooltip.style.display = 'none';
}

// ===================== TOOLTIP BINDING TEMPLATE ===================== //
// This is a template: use inside file tree rendering per file
// Example usage:
// const icon = document.createElement('span');
// icon.className = 'info-icon';
// icon.addEventListener('mouseenter', (e) => showTooltip(agentInsights[fileName], e.pageX, e.pageY));
// icon.addEventListener('mouseleave', hideTooltip);
