// Renders chat messages via textContent (never innerHTML) so message
// content can never be interpreted as HTML/script, regardless of what a
// user types — this is the client-side XSS defense to match the server's
// input-length checks.
function initChat(room) {
  const socket = io();
  const box = document.getElementById("chat-box");
  const input = document.getElementById("chat-input");
  const form = document.getElementById("chat-form");

  function appendMessage(sender, content, time) {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg";

    const senderEl = document.createElement("span");
    senderEl.className = "sender";
    senderEl.textContent = sender + ":";

    const contentEl = document.createElement("span");
    contentEl.textContent = content;

    const timeEl = document.createElement("span");
    timeEl.className = "time";
    timeEl.textContent = time ? new Date(time).toLocaleTimeString() : "";

    wrap.appendChild(senderEl);
    wrap.appendChild(contentEl);
    wrap.appendChild(timeEl);
    box.appendChild(wrap);
    box.scrollTop = box.scrollHeight;
  }

  socket.on("connect", () => {
    socket.emit("join", { room: room });
  });

  socket.on("receive_message", (data) => {
    if (data.room !== room) return;
    appendMessage(data.sender, data.content, data.created_at);
  });

  socket.on("system_notice", (data) => {
    appendMessage("system", data.message, null);
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const content = input.value.trim();
    if (!content) return;
    socket.emit("send_message", { room: room, content: content.slice(0, 500) });
    input.value = "";
  });

  box.scrollTop = box.scrollHeight;
}

document.addEventListener("DOMContentLoaded", () => {
  const app = document.getElementById("chat-app");
  if (app) {
    initChat(app.dataset.room);
  }
});
