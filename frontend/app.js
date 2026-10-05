let currentOptions = { flights: [], hotels: [], activities: [] };

function formatCurrentTime() {
  const d = new Date();
  let hours = d.getHours();
  const minutes = d.getMinutes();
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12;
  const minsStr = minutes < 10 ? "0" + minutes : minutes;
  return `${hours}:${minsStr} ${ampm}`;
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  appendUserMessage(message);

  const token = localStorage.getItem("planmytrip_token");
  const agentMessageDiv = appendAgentMessage("Planning your trip with multi-agent orchestration...");

  updateAgentStatus("flight", "Searching flight routes...", "60%");
  updateAgentStatus("hotel", "Scanning top properties...", "40%");
  updateAgentStatus("itinerary", "Analyzing preferences...", "30%");

  let threadIdToUse = activeThreadId;
  if (!threadIdToUse) {
    try {
      const initRes = await fetch(`${API_BASE}/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: message.substring(0, 30) + (message.length > 30 ? "..." : ""),
          destination: message.includes("Japan") ? "Japan" : (message.includes("Kerala") ? "Kerala" : (message.includes("Shimla") || message.includes("Simila") ? "Shimla" : (message.includes("Philippines") ? "Philippines" : (message.includes("Goa") ? "Goa" : "Travel Destination")))),
          departure_station: "Delhi (DEL)",
          budget_total: "2 lakhs",
          currency: "INR"
        })
      });
      if (initRes.ok) {
        const newTrip = await initRes.json();
        activeTripId = newTrip.id;
        activeThreadId = newTrip.thread_id;
        threadIdToUse = newTrip.thread_id;
        await loadTrips();
      }
    } catch (e) {
      console.error(e);
    }
  }

  if (!threadIdToUse) {
    agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Please select or create a trip first from "+ New Trip".</span>`;
    return;
  }

  const streamUrl = `${API_BASE}/chat/stream?thread_id=${encodeURIComponent(threadIdToUse)}&message=${encodeURIComponent(message)}`;

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

function updateAgentStatus(agent, subtitle, percent) {
  if (agent === "flight") {
    const card = document.querySelector(".flight-agent-bg");
    if (card) {
      const parent = card.closest(".agent-status-card");
      if (parent) {
        const sub = parent.querySelector(".agent-info-subtitle");
        const fill = parent.querySelector(".agent-progress-fill");
        if (sub) sub.innerText = subtitle;
        if (fill) fill.style.width = percent;
      }
    }
  } else if (agent === "hotel") {
    const card = document.querySelector(".hotel-agent-bg");
    if (card) {
      const parent = card.closest(".agent-status-card");
      if (parent) {
        const sub = parent.querySelector(".agent-info-subtitle");
        const fill = parent.querySelector(".agent-progress-fill");
        if (sub) sub.innerText = subtitle;
        if (fill) fill.style.width = percent;
      }
    }
  } else if (agent === "itinerary") {
    const card = document.querySelector(".itinerary-agent-bg");
    if (card) {
      const parent = card.closest(".agent-status-card");
      if (parent) {
        const sub = parent.querySelector(".agent-info-subtitle");
        const fill = parent.querySelector(".agent-progress-fill");
        if (sub) sub.innerText = subtitle;
        if (fill) fill.style.width = percent;
      }
    }
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
      updateAgentStatus("flight", "Flights discovered & ranked", "100%");
      renderOptionsGrid();
    } else if (node === "hotel_agent" && update.hotel_options) {
      currentOptions.hotels = update.hotel_options;
      updateAgentStatus("hotel", "Hotels selected within budget", "100%");
      renderOptionsGrid();
    } else if (node === "itinerary_agent" && update.activity_options) {
      currentOptions.activities = update.activity_options;
      updateAgentStatus("itinerary", "Day-wise activities scheduled", "95%");
      renderOptionsGrid();
    }
  } else if (type === "synthesis") {
    messageDiv.innerHTML = formatMarkdown(data.draft);
    updateAgentStatus("itinerary", "Itinerary completed", "100%");
  } else if (type === "interrupt") {
    showHitlPanel();
  } else if (type === "done") {
    if (activeTripId && typeof loadTripIntake === "function") {
      loadTripIntake(activeTripId);
    }
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
          <span class="option-badge" style="background: rgba(16, 185, 129, 0.1); color: #059669;">🏨 Hotel Option</span>
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
  const userWrap = document.createElement("div");
  userWrap.className = "message-user-wrap";

  const name = localStorage.getItem("planmytrip_name") || "T";
  const initial = name.charAt(0).toUpperCase();

  userWrap.innerHTML = `
    <div class="message-bubble message-user-bubble">
      ${escapeHtml(text)}
      <div class="message-time">${formatCurrentTime()}</div>
    </div>
    <div class="chat-user-avatar">${initial}</div>
  `;

  container.appendChild(userWrap);
  scrollChatToBottom();
}

function appendAgentMessage(text) {
  const container = document.getElementById("chat-messages");
  const agentWrap = document.createElement("div");
  agentWrap.className = "message-agent-wrap";

  agentWrap.innerHTML = `
    <div class="chat-agent-avatar">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" fill="#38bdf8"/>
        <circle cx="12" cy="12" r="2.5" fill="#ffffff"/>
      </svg>
    </div>
    <div class="message-bubble message-agent-bubble markdown-body">
      ${formatMarkdown(text)}
    </div>
  `;

  container.appendChild(agentWrap);
  scrollChatToBottom();
  return agentWrap.querySelector(".message-agent-bubble");
}

function scrollChatToBottom() {
  const scrollArea = document.getElementById("main-scroll-area");
  if (scrollArea) {
    scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: "smooth" });
  }
}

function formatMarkdown(text) {
  return String(text || "")
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
