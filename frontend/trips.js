const API_BASE = "http://localhost:8000/api/v1";

let activeTripId = null;
let activeThreadId = null;

async function loadTrips() {
  const token = localStorage.getItem("planmytrip_token");
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const email = localStorage.getItem("planmytrip_email") || "User";
  document.getElementById("user-display").innerText = email;

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

    if (trips.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem; text-align: center;">No trips planned yet. Click "+ New Trip" above.</div>`;
      return;
    }

    trips.forEach((trip) => {
      const item = document.createElement("div");
      item.className = `trip-item ${trip.id === activeTripId ? "active" : ""}`;
      item.onclick = () => selectTrip(trip);

      const formattedBudget = parseFloat(trip.budget_total).toLocaleString("en-IN");
      item.innerHTML = `
        <div class="trip-item-title">${escapeHtml(trip.title)}</div>
        <div class="trip-item-meta">${escapeHtml(trip.destination)} • ₹${formattedBudget}</div>
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

async function createNewTrip() {
  const token = localStorage.getItem("planmytrip_token");
  const destination = prompt("Enter your destination (e.g. Goa, Mumbai, Delhi, Paris):");
  if (!destination) return;

  const budgetInput = prompt("Enter your budget (e.g. 2 lakhs, 5 lakhs, 1.5L, 50000):", "2 lakhs");
  if (!budgetInput) return;

  const title = prompt("Enter a trip title (e.g. Vacation in " + destination + "):", `Trip to ${destination}`);
  if (!title) return;

  try {
    const res = await fetch(`${API_BASE}/trips`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        title,
        destination,
        budget_total: budgetInput,
        currency: "INR",
      }),
    });

    if (!res.ok) throw new Error("Failed to create trip");
    const newTrip = await res.json();
    await loadTrips();
    selectTrip(newTrip);
  } catch (err) {
    alert(err.message);
  }
}

function selectTrip(trip) {
  activeTripId = trip.id;
  activeThreadId = trip.thread_id;
  document.getElementById("active-trip-title").innerText = `${trip.title} (${trip.destination})`;
  
  const chatMessages = document.getElementById("chat-messages");
  chatMessages.innerHTML = `
    <div class="message-card message-agent">
      Welcome to your planning workspace for <strong>${escapeHtml(trip.destination)}</strong>! 
      Tell me your preferences (e.g. budget, dates, style of travel) and I will coordinate our agents to find flights, accommodations, and an itinerary.
    </div>
  `;

  document.getElementById("hitl-panel").style.display = "none";
  loadTrips();
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

document.getElementById("new-trip-btn").addEventListener("click", createNewTrip);
document.getElementById("logout-btn").addEventListener("click", logout);
document.addEventListener("DOMContentLoaded", loadTrips);
