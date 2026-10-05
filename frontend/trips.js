const API_BASE = "http://localhost:8000/api/v1";

let activeTripId = null;
let activeThreadId = null;
let currentIntakeData = null;

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = String(text);
  return div.innerHTML;
}

function renderMarkdownText(text) {
  if (!text) return "";
  return String(text)
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*)\*/gim, "<em>$1</em>")
    .replace(/\n/gim, "<br>");
}

function getDestinationThumbnail(destination) {
  const d = (destination || "").toLowerCase();
  if (d.includes("japan")) return "assets/Japan.jpg?v=20261004";
  if (d.includes("kerala")) return "assets/kerala.jpg?v=20261004";
  if (d.includes("shimla") || d.includes("simila")) return "assets/Simila.jpg?v=20261004";
  if (d.includes("philippines")) return "assets/Philippines.jpg?v=20261004";
  if (d.includes("goa")) return "assets/Goa.jpg?v=20261004";
  return "assets/Goa.jpg?v=20261004";
}

function getSampleDateRange(dest) {
  const d = (dest || "").toLowerCase();
  if (d.includes("japan")) return "10–17 Apr 2026";
  if (d.includes("kerala")) return "20–25 Nov 2025";
  if (d.includes("shimla") || d.includes("simila")) return "5–9 Dec 2025";
  if (d.includes("philippines")) return "12–18 Jan 2026";
  if (d.includes("goa")) return "12–16 Dec 2025";
  return "Flexible Dates";
}

function quickFillPrompt(destination) {
  const input = document.getElementById("chat-input");
  if (!input) return;

  const d = (destination || "").toLowerCase();
  if (d.includes("japan")) {
    input.value = "Plan a 7 day cultural trip to Japan exploring Tokyo, Kyoto and Mt Fuji.";
  } else if (d.includes("kerala")) {
    input.value = "Plan a 5 day heritage trip to Kerala with temples, backwaters and local cuisine.";
  } else if (d.includes("shimla") || d.includes("simila")) {
    input.value = "Plan a 4 day scenic mountain getaway to Shimla with heritage sites and nature walks.";
  } else if (d.includes("philippines")) {
    input.value = "Plan a 6 day tropical beach vacation to Philippines with island hopping and sunset cruise.";
  } else if (d.includes("goa")) {
    input.value = "Plan a 5 day trip to Goa for 2 people in December. I want beach, good hotels and sightseeing.";
  } else if (d.includes("edinburgh")) {
    input.value = "Plan a 5 day trip to Edinburgh exploring the castle, Royal Mile and Scottish Highlands.";
  } else if (d.includes("bali")) {
    input.value = "Plan a 6 day cultural and adventure trip to Bali with temples, rice terraces and beaches.";
  } else if (d.includes("france")) {
    input.value = "Plan a 7 day trip to France covering Paris, the Eiffel Tower, Louvre and French Riviera.";
  } else {
    input.value = `Plan an exciting trip to ${destination} with top sights, hotels and flights.`;
  }

  const scrollArea = document.getElementById("main-scroll-area");
  if (scrollArea) {
    scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: "smooth" });
  }
  input.focus();
}

function applyQuickPrompt(promptText) {
  const input = document.getElementById("chat-input");
  if (!input) return;
  input.value = promptText;
  const scrollArea = document.getElementById("main-scroll-area");
  if (scrollArea) {
    scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: "smooth" });
  }
  input.focus();
}

async function loadTrips() {
  const token = localStorage.getItem("planmytrip_token");
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const name = localStorage.getItem("planmytrip_name");
  const email = localStorage.getItem("planmytrip_email") || "Traveler";
  const displayName = name ? name : (email.includes("@") ? email.split("@")[0] : email);

  const userDisplay = document.getElementById("user-display");
  if (userDisplay) {
    userDisplay.innerText = displayName;
  }

  const initial = displayName.charAt(0).toUpperCase() || "T";
  const avatarCircle = document.getElementById("user-avatar-circle");
  if (avatarCircle) {
    avatarCircle.innerText = initial;
  }
  const chatInitial = document.getElementById("chat-user-initial");
  if (chatInitial) {
    chatInitial.innerText = initial;
  }

  try {
    const res = await fetch(`${API_BASE}/trips`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const trips = await res.json();
    const container = document.getElementById("trips-list");
    container.innerHTML = "";

    if (!Array.isArray(trips) || trips.length === 0) {
      container.innerHTML = "";
      return;
    }

    trips.forEach((trip) => {
      const item = document.createElement("div");
      item.className = `trip-item ${trip.id === activeTripId ? "active" : ""}`;
      item.id = `trip-item-${trip.id}`;
      item.onclick = () => selectTrip(trip);

      const thumbUrl = getDestinationThumbnail(trip.destination);
      let dateMeta = "";
      if (trip.start_date && trip.end_date) {
        dateMeta = `${trip.start_date} – ${trip.end_date}`;
      } else {
        dateMeta = getSampleDateRange(trip.destination);
      }

      item.innerHTML = `
        <img src="${thumbUrl}" alt="${escapeHtml(trip.destination)}" class="trip-thumb-img">
        <div class="trip-details-block">
          <div class="trip-item-title">${escapeHtml(trip.title)}</div>
          <div class="trip-item-meta">${dateMeta}</div>
        </div>
      `;
      container.appendChild(item);
    });

    if (!activeTripId && trips.length > 0) {
      selectTrip(trips[0]);
    }
  } catch (err) {
    console.error("Failed to load trips", err);
  }
}

async function selectTrip(trip) {
  activeTripId = trip.id;
  activeThreadId = trip.thread_id;

  document.querySelectorAll(".trip-item").forEach((el) => {
    el.classList.remove("active");
  });
  const activeEl = document.getElementById(`trip-item-${trip.id}`);
  if (activeEl) {
    activeEl.classList.add("active");
  }

  const hitlPanel = document.getElementById("hitl-panel");
  if (hitlPanel) hitlPanel.style.display = "none";

  await loadTripIntake(trip.id);
  await loadTripMessages(trip.id, trip.destination);
}

async function loadTripIntake(tripId) {
  const token = localStorage.getItem("planmytrip_token");
  try {
    const res = await fetch(`${API_BASE}/trips/${tripId}/intake`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;

    const intake = await res.json();
    currentIntakeData = intake;
  } catch (err) {
    console.error("Failed to load intake", err);
  }
}

async function loadTripMessages(tripId, destination) {
  const token = localStorage.getItem("planmytrip_token");
  const chatMessages = document.getElementById("chat-messages");

  try {
    const res = await fetch(`${API_BASE}/trips/${tripId}/messages`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.ok) {
      const messages = await res.json();
      if (Array.isArray(messages) && messages.length > 0) {
        chatMessages.innerHTML = "";
        const name = localStorage.getItem("planmytrip_name") || "T";
        const initial = name.charAt(0).toUpperCase();

        messages.forEach((msg) => {
          if (msg.role === "user") {
            const userWrap = document.createElement("div");
            userWrap.className = "message-user-wrap";
            userWrap.innerHTML = `
              <div class="message-bubble message-user-bubble">
                ${escapeHtml(msg.content)}
                <div class="message-time">Just now</div>
              </div>
              <div class="chat-user-avatar">${initial}</div>
            `;
            chatMessages.appendChild(userWrap);
          } else {
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
                ${renderMarkdownText(msg.content)}
              </div>
            `;
            chatMessages.appendChild(agentWrap);
          }
        });
        scrollChatToBottom();
      }
    }
  } catch (err) {
    console.error("Failed to load messages", err);
  }
}

function openNewTripModal() {
  const modal = document.getElementById("new-trip-modal");
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(today.getDate() + 7);
  const endDate = new Date(startDate);
  endDate.setDate(startDate.getDate() + 4);

  document.getElementById("new-trip-start-date").value = startDate.toISOString().split("T")[0];
  document.getElementById("new-trip-end-date").value = endDate.toISOString().split("T")[0];
  document.getElementById("new-trip-title").value = "";
  document.getElementById("new-trip-destination").value = "";
  document.getElementById("new-trip-departure").value = "Delhi (DEL)";
  document.getElementById("new-trip-budget").value = "2 lakhs";

  modal.style.display = "flex";
}

function closeNewTripModal() {
  document.getElementById("new-trip-modal").style.display = "none";
}

async function handleNewTripSubmit(e) {
  e.preventDefault();
  const token = localStorage.getItem("planmytrip_token");

  const title = document.getElementById("new-trip-title").value.trim();
  const departure_station = document.getElementById("new-trip-departure").value.trim();
  const destination = document.getElementById("new-trip-destination").value.trim();
  const start_date = document.getElementById("new-trip-start-date").value || null;
  const end_date = document.getElementById("new-trip-end-date").value || null;
  const budget_total = document.getElementById("new-trip-budget").value.trim();

  try {
    const res = await fetch(`${API_BASE}/trips`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        title,
        departure_station,
        destination,
        start_date,
        end_date,
        budget_total,
        currency: "INR",
      }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to create trip");
    }

    const newTrip = await res.json();
    closeNewTripModal();
    activeTripId = newTrip.id;
    await loadTrips();
    selectTrip(newTrip);
  } catch (err) {
    alert(err.message);
  }
}

function openEditIntakeModal() {
  if (!currentIntakeData) return;
  document.getElementById("edit-intake-departure").value = currentIntakeData.departure_station || "";
  document.getElementById("edit-intake-destination").value = currentIntakeData.destination || "";
  document.getElementById("edit-intake-start-date").value = currentIntakeData.start_date || "";
  document.getElementById("edit-intake-end-date").value = currentIntakeData.end_date || "";
  document.getElementById("edit-intake-budget").value = currentIntakeData.budget_amount ? `${currentIntakeData.budget_amount}` : "2 lakhs";
  document.getElementById("edit-intake-modal").style.display = "flex";
}

function closeEditIntakeModal() {
  document.getElementById("edit-intake-modal").style.display = "none";
}

async function handleEditIntakeSubmit(e) {
  e.preventDefault();
  if (!activeTripId) return;

  const token = localStorage.getItem("planmytrip_token");
  const departure_station = document.getElementById("edit-intake-departure").value.trim();
  const destination = document.getElementById("edit-intake-destination").value.trim();
  const start_date = document.getElementById("edit-intake-start-date").value || null;
  const end_date = document.getElementById("edit-intake-end-date").value || null;
  const budget_amount = document.getElementById("edit-intake-budget").value.trim();

  try {
    const res = await fetch(`${API_BASE}/trips/${activeTripId}/intake`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        departure_station,
        destination,
        start_date,
        end_date,
        budget_amount,
        currency: "INR",
      }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to update parameters");
    }

    closeEditIntakeModal();
    await loadTripIntake(activeTripId);
    await loadTrips();
  } catch (err) {
    alert(err.message);
  }
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

document.getElementById("new-trip-btn").addEventListener("click", openNewTripModal);
document.getElementById("close-new-trip-modal").addEventListener("click", closeNewTripModal);
document.getElementById("cancel-new-trip-btn").addEventListener("click", closeNewTripModal);
document.getElementById("new-trip-form").addEventListener("submit", handleNewTripSubmit);

document.getElementById("close-edit-intake-modal").addEventListener("click", closeEditIntakeModal);
document.getElementById("cancel-edit-intake-btn").addEventListener("click", closeEditIntakeModal);
document.getElementById("edit-intake-form").addEventListener("submit", handleEditIntakeSubmit);

document.getElementById("logout-btn").addEventListener("click", logout);

function setupCardsCarousel() {
  const track = document.getElementById("hero-cards-track");
  if (!track || track.dataset.cloned === "true") return;
  Array.from(track.children).forEach((card) => {
    const clone = card.cloneNode(true);
    clone.setAttribute("aria-hidden", "true");
    track.appendChild(clone);
  });
  track.dataset.cloned = "true";
}

document.addEventListener("DOMContentLoaded", setupCardsCarousel);
document.addEventListener("DOMContentLoaded", loadTrips);
