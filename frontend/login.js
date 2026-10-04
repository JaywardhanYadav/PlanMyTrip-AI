const API_BASE = "http://localhost:8000/api/v1";

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const errorBanner = document.getElementById("error-banner");
  const loginBtn = document.getElementById("login-btn");

  errorBanner.style.display = "none";
  loginBtn.disabled = true;
  loginBtn.innerText = "Signing in...";

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed");
    }

    localStorage.setItem("planmytrip_token", data.access_token);
    localStorage.setItem("planmytrip_email", email);
    window.location.href = "index.html";
  } catch (err) {
    errorBanner.innerText = err.message;
    errorBanner.style.display = "block";
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerText = "Sign In";
  }
});
