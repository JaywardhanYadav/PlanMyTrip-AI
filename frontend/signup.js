const API_BASE = (window.location && window.location.origin && window.location.origin.startsWith("http"))
  ? `${window.location.origin}/api/v1`
  : "http://localhost:8000/api/v1";
window.API_BASE = API_BASE;

document.getElementById("signup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const errorBanner = document.getElementById("error-banner");
  const signupBtn = document.getElementById("signup-btn");

  errorBanner.style.display = "none";
  signupBtn.disabled = true;
  signupBtn.innerText = "Creating account...";

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Account creation failed");
    }

    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const loginData = await loginRes.json();
    if (loginRes.ok) {
      localStorage.setItem("planmytrip_token", loginData.access_token);
      localStorage.setItem("planmytrip_email", email);
      window.location.href = "index.html";
    } else {
      window.location.href = "login.html";
    }
  } catch (err) {
    errorBanner.innerText = err.message;
    errorBanner.style.display = "block";
  } finally {
    signupBtn.disabled = false;
    signupBtn.innerText = "Create Account";
  }
});
