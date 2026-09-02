/* =========================
   ELEMENTS
   ========================= */

const messagesEl = document.getElementById("messages");
const input = document.getElementById("input");
const statusText = document.getElementById("status");
const statusDot = document.getElementById("statusDot");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const conversationList = document.getElementById("conversationList");
const conversationTitleEl = document.getElementById("conversationTitle");
const welcomeTemplate = document.getElementById("welcomeTemplate");

const attachBtn = document.getElementById("attachBtn");
const fileInput = document.getElementById("fileInput");
const attachChip = document.getElementById("attachChip");
const attachName = document.getElementById("attachName");
const attachRemove = document.getElementById("attachRemove");

const settingsBtn = document.getElementById("settingsBtn");
const settingsDropdown = document.getElementById("settingsDropdown");
const moreBtn = document.getElementById("moreBtn");
const moreDropdown = document.getElementById("moreDropdown");
const userMoreBtn = document.getElementById("userMoreBtn");
const userDropdown = document.getElementById("userDropdown");

/* =========================
   STATE
   ========================= */

let conversations = [];   // sidebar metadata: {id, title, preview}
let activeId = null;
let activeMessages = [];  // messages for the currently open conversation
let pendingUpload = null; // {stored_name, original_name} once a file has finished uploading

/* =========================
   INIT — hydrate from server-rendered state
   ========================= */

function init() {
  const raw = document.getElementById("initial-state").textContent;
  const state = JSON.parse(raw);

  conversations = state.conversations.map((c) => ({
    id: c.id,
    title: c.title,
    preview: c.preview,
  }));

  if (state.active) {
    activeId = state.active.id;
    activeMessages = state.active.messages;
  }

  renderSidebar();
  renderMessages();
}

/* =========================
   SIDEBAR RENDER
   ========================= */

function renderSidebar() {
  conversationList.innerHTML = "";

  conversations.forEach((convo) => {
    const btn = document.createElement("button");
    btn.className = "conversation" + (convo.id === activeId ? " active" : "");
    btn.dataset.id = convo.id;

    const title = document.createElement("span");
    title.className = "conversation-text";
    title.textContent = convo.title;

    const preview = document.createElement("span");
    preview.className = "conversation-preview";
    preview.textContent = convo.preview || "No messages yet";

    btn.appendChild(title);
    btn.appendChild(preview);

    btn.addEventListener("click", () => switchConversation(convo.id));

    conversationList.appendChild(btn);
  });
}

/* =========================
   SWITCH / CREATE CONVERSATION
   ========================= */

async function switchConversation(id) {
  if (id === activeId) return;

  try {
    const response = await fetch(`/api/conversations/${id}`);
    if (!response.ok) throw new Error("Failed to load conversation");
    const data = await response.json();

    activeId = data.id;
    activeMessages = data.messages;

    renderSidebar();
    renderMessages();
    input.focus();
  } catch (error) {
    console.error(error);
    setStatus("offline");
  }
}

async function createConversation() {
  try {
    const response = await fetch("/api/conversations", { method: "POST" });
    if (!response.ok) throw new Error("Failed to create conversation");
    const convo = await response.json();

    conversations.unshift({ id: convo.id, title: convo.title, preview: "No messages yet" });
    activeId = convo.id;
    activeMessages = [];

    renderSidebar();
    renderMessages();
    input.focus();
  } catch (error) {
    console.error(error);
    setStatus("offline");
  }
}

/* =========================
   MESSAGES RENDER
   ========================= */

function renderMessages() {
  messagesEl.innerHTML = "";
  const convo = conversations.find((c) => c.id === activeId);
  conversationTitleEl.textContent = convo ? convo.title : "Zora AI";

  if (!activeMessages || activeMessages.length === 0) {
    const node = welcomeTemplate.content.cloneNode(true);
    messagesEl.appendChild(node);
    bindSuggestionCards();
    return;
  }

  activeMessages.forEach((msg) => appendMessageRow(msg));
  scrollToBottom();
}

function appendMessageRow(msg) {
  const row = document.createElement("div");
  row.classList.add("message-row");
  if (msg.role === "user") row.classList.add("user-row");

  const bubble = document.createElement("div");
  bubble.classList.add("msg", msg.role);
  bubble.textContent = msg.content;

  if (msg.attachment) {
    const attach = document.createElement("div");
    attach.className = "msg-attachment";
    attach.textContent = "\u{1F4CE} " + msg.attachment;
    bubble.appendChild(attach);
  }

  row.appendChild(bubble);
  messagesEl.appendChild(row);
}

function bindSuggestionCards() {
  document.querySelectorAll(".suggestion-card").forEach((card) => {
    card.addEventListener("click", () => {
      input.value = card.dataset.prompt || "";
      send();
    });
  });
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/* =========================
   AUTO RESIZE TEXTAREA
   ========================= */

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    send();
  }
});

sendBtn.addEventListener("click", send);

/* =========================
   ATTACHMENTS — upload immediately on selection
   ========================= */

attachBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  attachName.textContent = `Uploading ${file.name}...`;
  attachChip.classList.remove("hidden");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) throw new Error(data.error || "Upload failed");

    pendingUpload = data; // {stored_name, original_name}
    attachName.textContent = data.original_name;
  } catch (error) {
    console.error(error);
    attachName.textContent = "Upload failed";
    pendingUpload = null;
    setTimeout(() => attachChip.classList.add("hidden"), 1500);
  } finally {
    fileInput.value = "";
  }
});

attachRemove.addEventListener("click", () => {
  pendingUpload = null;
  attachChip.classList.add("hidden");
});

/* =========================
   SEND MESSAGE
   ========================= */

async function send() {
  const text = input.value.trim();
  if (!text) return;

  if (!activeId) {
    await createConversation();
    if (!activeId) return; // creation failed, bail out
  }

  // optimistic render of the user's message
  activeMessages.push({
    role: "user",
    content: text,
    attachment: pendingUpload ? pendingUpload.original_name : null,
  });
  renderMessages();

  input.value = "";
  input.style.height = "auto";

  const attachment = pendingUpload ? pendingUpload.original_name : null;
  const attachmentPath = pendingUpload ? pendingUpload.stored_name : null;
  pendingUpload = null;
  attachChip.classList.add("hidden");

  setStatus("thinking");
  sendBtn.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: activeId,
        text,
        attachment,
        attachment_path: attachmentPath,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      activeMessages.push({ role: "ai", content: data.error || "Something went wrong." });
      setStatus(data.kind === "not_configured" ? "offline" : "error");
    } else {
      activeMessages = data.conversation.messages;
      updateConversationMeta(data.conversation.id, data.conversation.title, data.reply);
      setStatus("online");
    }
  } catch (error) {
    console.error(error);
    activeMessages.push({
      role: "ai",
      content: "Connection error. The backend is not reachable.",
    });
    setStatus("offline");
  } finally {
    renderMessages();
    renderSidebar();
    sendBtn.disabled = false;
    input.focus();
  }
}

function updateConversationMeta(id, title, preview) {
  const convo = conversations.find((c) => c.id === id);
  if (convo) {
    convo.title = title;
    convo.preview = preview;
  }
  conversationTitleEl.textContent = title;
}

function setStatus(state) {
  statusDot.classList.remove("thinking", "offline");
  if (state === "thinking") {
    statusText.textContent = "Thinking...";
    statusDot.classList.add("thinking");
  } else if (state === "offline") {
    statusText.textContent = "Offline";
    statusDot.classList.add("offline");
  } else if (state === "error") {
    statusText.textContent = "Error";
    statusDot.classList.add("offline");
  } else {
    statusText.textContent = "Online";
  }
}

/* =========================
   NEW CHAT
   ========================= */

newChatBtn.addEventListener("click", createConversation);

/* =========================
   DROPDOWN MENUS
   ========================= */

function setupDropdown(button, dropdown) {
  button.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.contains("open");
    closeAllDropdowns();
    if (!isOpen) {
      dropdown.classList.add("open");
      button.setAttribute("aria-expanded", "true");
    }
  });
}

function closeAllDropdowns() {
  [settingsDropdown, moreDropdown, userDropdown].forEach((d) => d.classList.remove("open"));
  [settingsBtn, moreBtn, userMoreBtn].forEach((b) => b.setAttribute("aria-expanded", "false"));
}

document.addEventListener("click", closeAllDropdowns);

setupDropdown(settingsBtn, settingsDropdown);
setupDropdown(moreBtn, moreDropdown);
setupDropdown(userMoreBtn, userDropdown);

document.querySelectorAll(".dropdown").forEach((dropdown) => {
  dropdown.addEventListener("click", (e) => e.stopPropagation());
});

/* =========================
   DROPDOWN ACTIONS
   ========================= */

document.querySelectorAll("[data-action]").forEach((btn) => {
  btn.addEventListener("click", () => {
    handleAction(btn.dataset.action);
    closeAllDropdowns();
  });
});

async function handleAction(action) {
  switch (action) {
    case "toggle-theme": {
      const isLight = document.documentElement.getAttribute("data-theme") === "light";
      document.documentElement.setAttribute("data-theme", isLight ? "" : "light");
      localStorage.setItem("zora-theme", isLight ? "dark" : "light");
      document.querySelectorAll('[data-action="toggle-theme"]').forEach((b) => {
        b.textContent = isLight ? "Switch to light theme" : "Switch to dark theme";
      });
      break;
    }

    case "clear-conversation": {
      if (!activeId) break;
      await fetch(`/api/conversations/${activeId}/messages`, { method: "DELETE" });
      activeMessages = [];
      updateConversationMeta(activeId, conversationTitleEl.textContent, "No messages yet");
      renderMessages();
      renderSidebar();
      break;
    }

    case "rename": {
      if (!activeId) break;
      const convo = conversations.find((c) => c.id === activeId);
      const name = prompt("Rename conversation", convo ? convo.title : "");
      if (name && name.trim()) {
        await fetch(`/api/conversations/${activeId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: name.trim() }),
        });
        updateConversationMeta(activeId, name.trim(), convo ? convo.preview : "");
        renderSidebar();
      }
      break;
    }

    case "delete": {
      if (!activeId) break;
      await fetch(`/api/conversations/${activeId}`, { method: "DELETE" });
      conversations = conversations.filter((c) => c.id !== activeId);
      if (conversations.length === 0) {
        await createConversation();
      } else {
        await switchConversation(conversations[0].id);
      }
      break;
    }

    case "export-one": {
      if (!activeId) break;
      window.location = `/api/conversations/${activeId}/export`;
      break;
    }

    case "export-all": {
      window.location = "/api/conversations/export";
      break;
    }

    case "clear-all": {
      if (confirm("Clear all conversations? This can't be undone.")) {
        await fetch("/api/conversations", { method: "DELETE" });
        conversations = [];
        await createConversation();
      }
      break;
    }
  }
}

/* =========================
   THEME — restore saved preference
   ========================= */

if (localStorage.getItem("zora-theme") === "light") {
  document.documentElement.setAttribute("data-theme", "light");
  document.querySelectorAll('[data-action="toggle-theme"]').forEach((b) => {
    b.textContent = "Switch to dark theme";
  });
}

/* =========================
   INIT
   ========================= */

init();