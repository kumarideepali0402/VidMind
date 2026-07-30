const analyzeForm = document.getElementById("analyze-form");
const analyzeBtn = document.getElementById("analyze-btn");
const clearBtn = document.getElementById("clear-btn");
const statusBox = document.getElementById("status-box");
const statusText = document.getElementById("status-text");
const welcome = document.getElementById("welcome");
const results = document.getElementById("results");
const errorBox = document.getElementById("error-box");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

let sessionId = null;
let pollTimer = null;

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

function setLoading(isLoading, message = "Processing...") {
  analyzeBtn.disabled = isLoading;
  statusBox.classList.toggle("hidden", !isLoading);
  statusText.textContent = message;
}

function renderMarkdown(element, text) {
  element.innerHTML = marked.parse(text || "_No content._");
}

function switchTab(tabName) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });

  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${tabName}`);
  });
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => switchTab(tab.dataset.tab));
});

function showResults(data) {
  welcome.classList.add("hidden");
  results.classList.remove("hidden");
  clearBtn.classList.remove("hidden");

  document.getElementById("result-title").textContent = data.title || "Untitled";
  renderMarkdown(document.getElementById("panel-summary"), data.summary);
  renderMarkdown(document.getElementById("panel-actions"), data.action_items);
  renderMarkdown(document.getElementById("panel-decisions"), data.key_decisions);
  renderMarkdown(document.getElementById("panel-questions"), data.open_questions);
  document.getElementById("panel-transcript").textContent = data.transcript || "";

  chatMessages.innerHTML = "";
  switchTab("summary");
}

async function pollJob(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);

  if (response.status === 404) {
    throw new Error(
      "Analysis was interrupted — the server restarted while processing. Click Analyze again."
    );
  }

  if (!response.ok) {
    let detail = "Failed to check job status.";
    try {
      const payload = await response.json();
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  const job = await response.json();
  setLoading(true, job.stage || "Processing...");

  if (job.status === "done") {
    sessionId = job.session_id;
    showResults(job.result);
    setLoading(false);
    return;
  }

  if (job.status === "error") {
    const raw = job.error || "Analysis failed.";
    const friendly = raw.includes("403") || raw.includes("Forbidden")
      ? "YouTube blocked the download. Upload the video file instead, or retry after updating yt-dlp (`pip install -U yt-dlp`)."
      : raw;
    throw new Error(friendly);
  }

  pollTimer = setTimeout(() => pollJob(jobId), 2000);
}

analyzeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const source = document.getElementById("source").value.trim();
  const fileInput = document.getElementById("file");
  const language = document.getElementById("language").value;

  if (!source && !fileInput.files.length) {
    showError("Please enter a YouTube URL or upload a file.");
    return;
  }

  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }

  const formData = new FormData();
  formData.append("language", language);

  if (fileInput.files.length) {
    formData.append("file", fileInput.files[0]);
  } else {
    formData.append("source", source);
  }

  setLoading(true, "Starting analysis...");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Could not start analysis.");
    }

    await pollJob(payload.job_id);
  } catch (error) {
    setLoading(false);
    showError(error.message);
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const question = chatInput.value.trim();
  if (!question || !sessionId) {
    return;
  }

  appendMessage("user", question);
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Chat request failed.");
    }

    appendMessage("assistant", payload.answer);
  } catch (error) {
    const msg =
      error.message === "Failed to fetch"
        ? "Could not reach the server. Make sure it is running and try Analyze again."
        : error.message;
    showError(msg);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

function appendMessage(role, content) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerHTML = role === "assistant" ? marked.parse(content) : content;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

clearBtn.addEventListener("click", async () => {
  if (sessionId) {
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  }

  sessionId = null;
  analyzeForm.reset();
  results.classList.add("hidden");
  welcome.classList.remove("hidden");
  clearBtn.classList.add("hidden");
  hideError();
  setLoading(false);
});
