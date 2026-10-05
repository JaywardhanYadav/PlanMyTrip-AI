const API_BASE = "http://localhost:8000/api/v1";

const slideData = [
  {
    title: "Effortless Travel Planning in Indian Rupees",
    desc: "Coordinate flights, hotels, and custom daily itineraries tailored to your budget with autonomous AI agents.",
  },
  {
    title: "Coastal Getaways & Beach Resorts",
    desc: "Discover premier stays in Goa, Kerala, and the Andaman Islands with real-time room and fare rates.",
  },
  {
    title: "Cultural Journeys & Mountain Escapes",
    desc: "From the royal palaces of Rajasthan to the heights of Himachal Pradesh, planned down to the minute.",
  },
  {
    title: "Zero Overbudget Surprises",
    desc: "Automated financial reconciliation in ₹ INR keeps flights, hotels, and activities within your financial cap.",
  },
];

let currentSlide = 0;
let slideInterval = null;

function showSlide(index) {
  const totalSlides = slideData.length;
  currentSlide = (index + totalSlides) % totalSlides;

  for (let i = 0; i < totalSlides; i++) {
    const slideEl = document.getElementById(`slide-${i}`);
    if (slideEl) {
      if (i === currentSlide) {
        slideEl.classList.add("active");
      } else {
        slideEl.classList.remove("active");
      }
    }
  }

  const dots = document.querySelectorAll(".slide-dot");
  dots.forEach((dot, i) => {
    if (i === currentSlide) {
      dot.classList.add("active");
    } else {
      dot.classList.remove("active");
    }
  });

  const titleEl = document.getElementById("slide-caption-title");
  const descEl = document.getElementById("slide-caption-desc");
  if (titleEl && descEl) {
    titleEl.innerText = slideData[currentSlide].title;
    descEl.innerText = slideData[currentSlide].desc;
  }
}

function goToSlide(index) {
  showSlide(index);
  resetSlideTimer();
}

function resetSlideTimer() {
  if (slideInterval) clearInterval(slideInterval);
  slideInterval = setInterval(() => {
    showSlide(currentSlide + 1);
  }, 5000);
}

function clearBanners() {
  const errorBanner = document.getElementById("error-banner");
  const successBanner = document.getElementById("success-banner");
  if (errorBanner) {
    errorBanner.style.display = "none";
    errorBanner.innerText = "";
  }
  if (successBanner) {
    successBanner.style.display = "none";
    successBanner.innerText = "";
  }
}

function formatError(errData) {
  if (!errData) return "An error occurred";
  if (typeof errData === "string") return errData;
  if (errData.detail) {
    if (typeof errData.detail === "string") return errData.detail;
    if (Array.isArray(errData.detail)) {
      return errData.detail.map((d) => d.msg || (d.loc ? d.loc.join(" ") : "")).filter(Boolean).join(", ");
    }
  }
  return errData.message || "Request failed";
}

function showError(msg) {
  const errorBanner = document.getElementById("error-banner");
  const successBanner = document.getElementById("success-banner");
  if (successBanner) successBanner.style.display = "none";
  if (errorBanner) {
    errorBanner.innerText = typeof msg === "string" ? msg : formatError(msg);
    errorBanner.style.display = "block";
  }
}

function showSuccess(msg) {
  const errorBanner = document.getElementById("error-banner");
  const successBanner = document.getElementById("success-banner");
  if (errorBanner) errorBanner.style.display = "none";
  if (successBanner) {
    successBanner.innerText = msg;
    successBanner.style.display = "block";
  }
}

function showLogin() {
  clearBanners();
  const tabsBar = document.getElementById("auth-tabs-bar");
  if (tabsBar) tabsBar.style.display = "flex";
  const loginSec = document.getElementById("login-section");
  if (loginSec) loginSec.style.display = "block";
  const signupSec = document.getElementById("signup-section");
  if (signupSec) signupSec.style.display = "none";
  const recSec = document.getElementById("recovery-section");
  if (recSec) recSec.style.display = "none";

  const tabLogin = document.getElementById("tab-login-btn");
  if (tabLogin) tabLogin.classList.add("active");
  const tabSignup = document.getElementById("tab-signup-btn");
  if (tabSignup) tabSignup.classList.remove("active");

  const titleEl = document.getElementById("auth-main-title");
  const subEl = document.getElementById("auth-main-subtitle");
  if (titleEl) titleEl.innerText = "Welcome Back";
  if (subEl) subEl.innerText = "Plan trips across India & beyond with intelligent AI agents";
}

function showSignup() {
  clearBanners();
  const tabsBar = document.getElementById("auth-tabs-bar");
  if (tabsBar) tabsBar.style.display = "flex";
  const loginSec = document.getElementById("login-section");
  if (loginSec) loginSec.style.display = "none";
  const signupSec = document.getElementById("signup-section");
  if (signupSec) signupSec.style.display = "block";
  const recSec = document.getElementById("recovery-section");
  if (recSec) recSec.style.display = "none";

  const tabLogin = document.getElementById("tab-login-btn");
  if (tabLogin) tabLogin.classList.remove("active");
  const tabSignup = document.getElementById("tab-signup-btn");
  if (tabSignup) tabSignup.classList.add("active");

  const titleEl = document.getElementById("auth-main-title");
  const subEl = document.getElementById("auth-main-subtitle");
  if (titleEl) titleEl.innerText = "Create Account";
  if (subEl) subEl.innerText = "Join PlanMyTrip AI for autonomous trip coordination";
}

function showRecovery() {
  clearBanners();
  const tabsBar = document.getElementById("auth-tabs-bar");
  if (tabsBar) tabsBar.style.display = "none";
  const loginSec = document.getElementById("login-section");
  if (loginSec) loginSec.style.display = "none";
  const signupSec = document.getElementById("signup-section");
  if (signupSec) signupSec.style.display = "none";
  const recSec = document.getElementById("recovery-section");
  if (recSec) recSec.style.display = "block";

  const titleEl = document.getElementById("auth-main-title");
  const subEl = document.getElementById("auth-main-subtitle");
  if (titleEl) titleEl.innerText = "Account Recovery";
  if (subEl) subEl.innerText = "Verify your registered email and birth date to log in";

  const loginEmailInput = document.getElementById("login-email");
  const recEmailInput = document.getElementById("recovery-email");
  if (loginEmailInput && recEmailInput && loginEmailInput.value.trim()) {
    recEmailInput.value = loginEmailInput.value.trim();
  }
}

async function handleLoginSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  clearBanners();

  const emailEl = document.getElementById("login-email");
  const passEl = document.getElementById("login-password");
  const loginBtn = document.getElementById("login-btn");

  const email = emailEl ? emailEl.value.trim() : "";
  const password = passEl ? passEl.value : "";

  if (!email || !password) {
    showError("Please enter both email and password");
    return;
  }

  if (loginBtn) {
    loginBtn.disabled = true;
    loginBtn.innerText = "Signing in...";
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(formatError(data) || "Authentication failed");
    }

    localStorage.setItem("planmytrip_token", data.access_token);
    localStorage.setItem("planmytrip_email", email);
    if (data.user_name) {
      localStorage.setItem("planmytrip_name", data.user_name);
    }
    window.location.href = "index.html";
  } catch (err) {
    showError(err.message);
  } finally {
    if (loginBtn) {
      loginBtn.disabled = false;
      loginBtn.innerText = "Sign In";
    }
  }
}

async function handleSignupSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  clearBanners();

  const nameEl = document.getElementById("signup-name");
  const emailEl = document.getElementById("signup-email");
  const birthDateEl = document.getElementById("signup-birth-date");
  const passEl = document.getElementById("signup-password");
  const signupBtn = document.getElementById("signup-btn");

  const name = nameEl ? nameEl.value.trim() : "";
  const email = emailEl ? emailEl.value.trim() : "";
  const birth_date = birthDateEl ? birthDateEl.value : "";
  const password = passEl ? passEl.value : "";

  if (!email) {
    showError("Please enter an email address");
    return;
  }

  if (!birth_date) {
    showError("Please select your date of birth");
    return;
  }

  if (!password || password.length < 8) {
    showError("Password must be at least 8 characters long");
    return;
  }

  if (signupBtn) {
    signupBtn.disabled = true;
    signupBtn.innerText = "Creating account...";
  }

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, birth_date }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(formatError(data) || "Account creation failed");
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
      if (loginData.user_name || name) {
        localStorage.setItem("planmytrip_name", loginData.user_name || name);
      }
      window.location.href = "index.html";
    } else {
      showSuccess("Account created successfully. Please sign in.");
      showLogin();
    }
  } catch (err) {
    showError(err.message);
  } finally {
    if (signupBtn) {
      signupBtn.disabled = false;
      signupBtn.innerText = "Create Account";
    }
  }
}

async function handleRecoverySubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  clearBanners();

  const emailEl = document.getElementById("recovery-email");
  const birthDateEl = document.getElementById("recovery-birth-date");
  const passEl = document.getElementById("recovery-new-password");
  const recoveryBtn = document.getElementById("recovery-btn");

  const email = emailEl ? emailEl.value.trim() : "";
  const birth_date = birthDateEl ? birthDateEl.value : "";
  const new_password = passEl && passEl.value.trim() ? passEl.value.trim() : null;

  if (!email) {
    showError("Please enter your registered email address");
    return;
  }

  if (!birth_date) {
    showError("Please enter your registered date of birth");
    return;
  }

  if (recoveryBtn) {
    recoveryBtn.disabled = true;
    recoveryBtn.innerText = "Verifying...";
  }

  try {
    const payload = { email, birth_date };
    if (new_password) {
      payload.new_password = new_password;
    }

    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(formatError(data) || "Verification failed: Email or Birth Date does not match our records");
    }

    showSuccess("Identity verified! Logging you in...");
    localStorage.setItem("planmytrip_token", data.access_token);
    localStorage.setItem("planmytrip_email", email);
    if (data.user_name) {
      localStorage.setItem("planmytrip_name", data.user_name);
    }

    setTimeout(() => {
      window.location.href = "index.html";
    }, 900);
  } catch (err) {
    showError(err.message);
  } finally {
    if (recoveryBtn) {
      recoveryBtn.disabled = false;
      recoveryBtn.innerText = "Verify & Log In";
    }
  }
}

window.showLogin = showLogin;
window.showSignup = showSignup;
window.showRecovery = showRecovery;
window.goToSlide = goToSlide;
window.handleLoginSubmit = handleLoginSubmit;
window.handleSignupSubmit = handleSignupSubmit;
window.handleRecoverySubmit = handleRecoverySubmit;

function initAuthPage() {
  showSlide(0);
  resetSlideTimer();

  const isSignupPath = window.location.pathname.endsWith("signup.html");
  const params = new URLSearchParams(window.location.search);
  if (isSignupPath || params.get("tab") === "signup") {
    showSignup();
  } else if (params.get("tab") === "recovery") {
    showRecovery();
  } else {
    showLogin();
  }

  const tabLogin = document.getElementById("tab-login-btn");
  if (tabLogin) tabLogin.addEventListener("click", showLogin);

  const tabSignup = document.getElementById("tab-signup-btn");
  if (tabSignup) tabSignup.addEventListener("click", showSignup);

  const switchSignup = document.getElementById("switch-to-signup");
  if (switchSignup) {
    switchSignup.addEventListener("click", (e) => {
      e.preventDefault();
      showSignup();
    });
  }

  const switchLogin = document.getElementById("switch-to-login");
  if (switchLogin) {
    switchLogin.addEventListener("click", (e) => {
      e.preventDefault();
      showLogin();
    });
  }

  const gotoRec = document.getElementById("goto-recovery-btn");
  if (gotoRec) gotoRec.addEventListener("click", showRecovery);

  const recBack = document.getElementById("recovery-back-btn");
  if (recBack) recBack.addEventListener("click", showLogin);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAuthPage);
} else {
  initAuthPage();
}
