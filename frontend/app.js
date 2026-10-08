const API_BASE = window.API_BASE || ((window.location && window.location.origin && window.location.origin.startsWith("http"))
  ? `${window.location.origin}/api/v1`
  : "http://localhost:8000/api/v1");

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

  const welcomeHero = document.getElementById("chat-welcome-hero");
  if (welcomeHero) welcomeHero.style.display = "none";

  input.value = "";
  appendUserMessage(message);

  const token = localStorage.getItem("planmytrip_token");
  const agentMessageDiv = appendAgentMessage("Thinking...");

  if (!token) {
    agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Your session has ended. Please sign in to continue planning trips. <a href="login.html" style="color: var(--brand-accent); text-decoration: underline; font-weight: 600;">Go to Login</a></span>`;
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1500);
    return;
  }

  let threadIdToUse = activeThreadId;
  if (!threadIdToUse) {
    try {
      let inferredDest = "";
      const lower = message.toLowerCase();
      if (lower.includes("goa")) inferredDest = "Goa";
      else if (lower.includes("japan") || lower.includes("tokyo")) inferredDest = "Japan";
      else if (lower.includes("kerala")) inferredDest = "Kerala";
      else if (lower.includes("shimla") || lower.includes("simila") || lower.includes("manali")) inferredDest = "Shimla";
      else if (lower.includes("philippines")) inferredDest = "Philippines";
      else if (lower.includes("bali")) inferredDest = "Bali";
      else if (lower.includes("edinburgh") || lower.includes("scotland")) inferredDest = "Edinburgh";
      else if (lower.includes("france") || lower.includes("paris")) inferredDest = "France";
      else if (lower.includes("pune")) inferredDest = "Pune";
      else if (lower.includes("bangalore") || lower.includes("bengaluru") || lower.includes("benglore")) inferredDest = "Bangalore";
      else if (lower.includes("mumbai") || lower.includes("bombay")) inferredDest = "Mumbai";
      else if (lower.includes("delhi")) inferredDest = "Delhi";
      else if (lower.includes("jaipur")) inferredDest = "Jaipur";
      else if (lower.includes("hyderabad")) inferredDest = "Hyderabad";
      else if (lower.includes("kolkata") || lower.includes("calcutta")) inferredDest = "Kolkata";
      else if (lower.includes("chennai") || lower.includes("madras")) inferredDest = "Chennai";
      else {
        const destMatch = message.match(/(?:to|visit|in|explore|for|plan|planning\s+for)\s+([A-Za-z]+)/i);
        if (destMatch && destMatch[1] && !["trip", "a", "an", "the", "my", "vacation"].includes(destMatch[1].toLowerCase())) {
          inferredDest = destMatch[1].charAt(0).toUpperCase() + destMatch[1].slice(1);
        }
      }

      const tripTitle = inferredDest ? `Trip to ${inferredDest}` : "Trip Plan";

      const initRes = await fetch(`${API_BASE}/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: tripTitle,
          destination: inferredDest,
          departure_station: "",
          budget_total: "0",
          currency: "INR"
        })
      });

      if (initRes.status === 401) {
        localStorage.removeItem("planmytrip_token");
        agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Your session has expired. Redirecting to login... <a href="login.html" style="color: var(--brand-accent); text-decoration: underline; font-weight: 600;">Click here to sign in</a></span>`;
        setTimeout(() => {
          window.location.href = "login.html";
        }, 1500);
        return;
      }

      if (initRes.ok) {
        const newTrip = await initRes.json();
        activeTripId = newTrip.id;
        activeThreadId = newTrip.thread_id;
        threadIdToUse = newTrip.thread_id;
        window.history.pushState({}, "", `main.html?trip_id=${encodeURIComponent(newTrip.id)}`);
        await loadTrips();
        const activeItem = document.getElementById(`trip-item-${newTrip.id}`);
        if (activeItem) {
          document.querySelectorAll(".trip-item").forEach((el) => el.classList.remove("active"));
          activeItem.classList.add("active");
        }
      } else {
        const errJson = await initRes.json().catch(() => ({}));
        agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Unable to start new trip: ${escapeHtml(errJson.detail || initRes.statusText || "Server error")}. Please try again.</span>`;
        return;
      }
    } catch (e) {
      console.error(e);
      agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Connection error starting trip. Please check server status.</span>`;
      return;
    }
  }

  if (!threadIdToUse) {
    agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Unable to establish chat session. Please refresh or try again.</span>`;
    return;
  }

  const streamUrl = `${API_BASE}/chat/stream?thread_id=${encodeURIComponent(threadIdToUse)}&message=${encodeURIComponent(message)}`;

  try {
    const response = await fetch(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      localStorage.removeItem("planmytrip_token");
      agentMessageDiv.innerHTML = `<span style="color: var(--accent-danger);">Your session has expired. Redirecting to login...</span>`;
      setTimeout(() => {
        window.location.href = "login.html";
      }, 1500);
      return;
    }

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
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event:\s*(.+)$/m);
        const dataMatch = block.match(/^data:\s*([\s\S]+)$/m);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim();
          try {
            const eventData = JSON.parse(dataMatch[1].trim());
            handleSSEEvent(eventType, eventData, agentMessageDiv);
          } catch (parseErr) {
            console.error(parseErr);
          }
        }
      }
    }

    if (buffer.trim()) {
      const eventMatch = buffer.match(/^event:\s*(.+)$/m);
      const dataMatch = buffer.match(/^data:\s*([\s\S]+)$/m);
      if (eventMatch && dataMatch) {
        try {
          const eventData = JSON.parse(dataMatch[1].trim());
          handleSSEEvent(eventMatch[1].trim(), eventData, agentMessageDiv);
        } catch (parseErr) {
          console.error(parseErr);
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
    if (data.message && data.step !== "planning_started") {
      messageDiv.innerText = `⏳ ${data.message}`;
    }
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
    } else if (node === "hotel_agent" && update.hotel_options) {
      currentOptions.hotels = update.hotel_options;
      updateAgentStatus("hotel", "Hotels selected within budget", "100%");
    } else if (node === "itinerary_agent" && update.activity_options) {
      currentOptions.activities = update.activity_options;
      updateAgentStatus("itinerary", "Day-wise activities scheduled", "95%");
    }
  } else if (type === "intake_update") {
    if (data && data.destination && typeof loadTrips === "function") {
      loadTrips();
    }
  } else if (type === "synthesis") {
    messageDiv.innerHTML = formatMarkdown(data.draft);
    updateAgentStatus("itinerary", "Itinerary completed", "100%");
  } else if (type === "interrupt") {
    const panel = document.getElementById("hitl-panel");
    if (panel) panel.style.display = "none";
  } else if (type === "done") {
    if (activeTripId && typeof loadTripIntake === "function") {
      loadTripIntake(activeTripId);
    }
    if (typeof loadTrips === "function") {
      loadTrips();
    }
  }
}

function renderOptionsGrid() {}

function selectFlightOption(optionId) {}

function selectHotelOption(optionId) {}

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
  if (typeof setConversationMode === "function") {
    setConversationMode(true, "PlanMyTrip AI — Active Conversation");
  }
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
  if (typeof setConversationMode === "function") {
    setConversationMode(true, "PlanMyTrip AI — Active Conversation");
  }
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

function attachChatEventListeners() {
  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) {
    sendBtn.onclick = (e) => {
      if (e) e.preventDefault();
      sendChatMessage();
    };
  }
  const chatInput = document.getElementById("chat-input");
  if (chatInput) {
    chatInput.onkeydown = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    };
  }
  const hitlApprove = document.getElementById("hitl-approve-btn");
  if (hitlApprove) {
    hitlApprove.onclick = approvePlan;
  }
}

attachChatEventListeners();
document.addEventListener("DOMContentLoaded", attachChatEventListeners);
window.addEventListener("load", attachChatEventListeners);
