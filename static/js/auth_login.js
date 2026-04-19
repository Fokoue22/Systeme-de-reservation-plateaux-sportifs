const loginFormEl = document.getElementById("loginForm");
const loginFlashEl = document.getElementById("loginFlash");

function setFlash(message, type = "error") {
  loginFlashEl.textContent = message;
  loginFlashEl.className = `flash ${type}`;
}

function normalizeApiError(detail, status, fallback) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (status === 401) {
    return "Identifiants invalides.";
  }
  if (status === 422) {
    return "Veuillez verifier les champs saisis.";
  }
  return fallback;
}

async function login(username, password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(normalizeApiError(data.detail, response.status, "Echec de connexion."));
  }
}

loginFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(loginFormEl);
  const username = String(fd.get("username") || "").trim();
  const password = String(fd.get("password") || "");

  try {
    await login(username, password);
    setFlash("Connexion reussie. Redirection...", "success");
    window.location.href = "/calendar";
  } catch (error) {
    setFlash(error.message || "Erreur de connexion.", "error");
  }
});
