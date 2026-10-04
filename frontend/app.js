let currentOptions = { flights: [], hotels: [], activities: [] };

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message || !activeThreadId) return;

  input.value = "";
  appendUserMessage(message);

  const token = localStorage.getItem("planmytrip_token");
  const agentMessageDiv = appendAgentMessage("Planning in progress...");

  const streamUrl = `${API_BASE}/chat/stream?thread_id=${encodeURIComponent(activeThreadId)}&message=${encodeURIComponent(message)}`;

  try {
    const response = await fetch(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Chat stream failed: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        const eventMatch = line.match(/^event:\s*(.+)$/m);
        const dataMatch = line.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim();
          const eventData = JSON.parse(dataMatch[1].trim());
          handleSSEEvent(eventType, eventData, agentMessageDiv);
        }
      }
    }
  } catch (err) {
    agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Error: ${escapeHtml(err.message)}</span>`;
  }
}

function handleSSEEvent(type, data, messageDiv) {
  if (type === "status") {
    messageDiv.innerText = `⏳ ${data.message}`;
  } else if (type === "guardrail") {
    if (!data.allowed) {
      messageDiv.innerHTML = `<span style="color: var(--accent-danger);">⚠️ Request Rejected: ${escapeHtml(data.reason)}</span>`;
    }
  } else if (type === "node_update") {
    const node = data.node;
    const update = data.update;

    if (node === "flight_agent" && update.flight_options) {
      currentOptions.flights = update.flight_options;
      renderOptionsGrid();
    } else if (node === "hotel_agent" && update.hotel_options) {
      currentOptions.hotels = update.hotel_options;
      renderOptionsGrid();
    } else if (node === "itinerary_agent" && update.activity_options) {
      currentOptions.activities = update.activity_options;
      renderOptionsGrid();
    }
  } else if (type === "synthesis") {
    messageDiv.innerHTML = formatMarkdown(data.draft);
  } else if (type === "interrupt") {
    showHitlPanel();
  } else if (type === "done") {
    console.log("Stream completed.");
  }
}

function renderOptionsGrid() {
  let cardsContainer = document.getElementById("active-options-container");
  if (!cardsContainer) {
    cardsContainer = document.createElement("div");
    cardsContainer.id = "active-options-container";
    cardsContainer.className = "options-grid";
    document.getElementById("chat-messages").appendChild(cardsContainer);
  }

  let html = "";

  currentOptions.flights.forEach((f) => {
    const formattedFare = parseFloat(f.fare.amount).toLocaleString("en-IN");
    html += `
      <div class="option-card">
        <div>
          <span class="option-badge">✈️ Flight Option</span>
          <div class="option-title">${escapeHtml(f.carrier)}</div>
          <div class="option-price">₹${formattedFare} ${escapeHtml(f.fare.currency)}</div>
          <div class="option-meta">
            Duration: ${f.legs[0]?.duration_minutes || 180} mins<br>
            Route: ${f.legs[0]?.origin_iata} ➔ ${f.legs[0]?.destination_iata}
          </div>
        </div>
        <button class="btn-secondary" onclick="selectFlightOption('${f.option_id}')">Select Flight</button>
      </div>
    `;
  });

  currentOptions.hotels.forEach((h) => {
    const formattedTotal = parseFloat(h.total_rate.amount).toLocaleString("en-IN");
    const formattedNightly = parseFloat(h.nightly_rate.amount).toLocaleString("en-IN");
    html += `
      <div class="option-card">
        <div>
          <span class="option-badge" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7;">🏨 Hotel Option</span>
          <div class="option-title">${escapeHtml(h.name)}</div>
          <div class="option-price">₹${formattedTotal} total</div>
          <div class="option-meta">
            ${escapeHtml(h.location)}<br>
            Nightly: ₹${formattedNightly}
          </div>
        </div>
        <button class="btn-secondary" onclick="selectHotelOption('${h.option_id}')">Select Hotel</button>
      </div>
    `;
  });

  cardsContainer.innerHTML = html;
  scrollChatToBottom();
}

function selectFlightOption(optionId) {
  resumeWithFeedback("edit_flight", { selected_flight_id: optionId });
}

function selectHotelOption(optionId) {
  resumeWithFeedback("edit_hotel", { selected_hotel_id: optionId });
}

function approvePlan() {
  resumeWithFeedback("approve", {});
}

async function resumeWithFeedback(action, details) {
  const token = localStorage.getItem("planmytrip_token");
  const panel = document.getElementById("hitl-panel");
  panel.style.display = "none";

  appendAgentMessage(`Applying human decision: ${action}...`);

  try {
    const res = await fetch(`${API_BASE}/hitl/resume`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        thread_id: activeThreadId,
        action,
        ...details,
      }),
    });

    const data = await res.json();
    if (data.itinerary_draft) {
      appendAgentMessage(formatMarkdown(data.itinerary_draft));
    }
  } catch (err) {
    alert(`Resume failed: ${err.message}`);
  }
}

function showHitlPanel() {
  const panel = document.getElementById("hitl-panel");
  panel.style.display = "flex";
  scrollChatToBottom();
}

function appendUserMessage(text) {
  const container = document.getElementById("chat-messages");
  const msg = document.createElement("div");
  msg.className = "message-card message-user";
  msg.innerText = text;
  container.appendChild(msg);
  scrollChatToBottom();
}

function appendAgentMessage(text) {
  const container = document.getElementById("chat-messages");
  const msg = document.createElement("div");
  msg.className = "message-card message-agent markdown-body";
  msg.innerHTML = formatMarkdown(text);
  container.appendChild(msg);
  scrollChatToBottom();
  return msg;
}

function scrollChatToBottom() {
  const container = document.getElementById("chat-messages");
  container.scrollTop = container.scrollHeight;
}

function formatMarkdown(text) {
  return text
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*)\*/gim, "<em>$1</em>")
    .replace(/\n/gim, "<br>");
}

document.getElementById("chat-send-btn").addEventListener("click", sendChatMessage);
document.getElementById("chat-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChatMessage();
});
document.getElementById("hitl-approve-btn").addEventListener("click", approvePlan);
