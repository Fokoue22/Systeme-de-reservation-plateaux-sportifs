const registerFormEl = document.getElementById("registerForm");
const registerFlashEl = document.getElementById("registerFlash");

function setFlash(message, type = "error") {
  registerFlashEl.textContent = message;
  registerFlashEl.className = `flash ${type}`;
}

function normalizeApiError(detail, status, fallback) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (status === 409) {
    return "Ce nom utilisateur existe deja.";
  }
  if (status === 422) {
    return "Veuillez verifier les champs saisis.";
  }
  return fallback;
}

async function register(payload) {
  const response = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(normalizeApiError(data.detail, response.status, "Echec de creation du compte."));
  }
}

registerFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(registerFormEl);

  const username = String(fd.get("username") || "").trim();
  const email = String(fd.get("email") || "").trim();
  const telephone = String(fd.get("telephone") || "").trim();
  const password = String(fd.get("password") || "");
  const passwordConfirm = String(fd.get("password_confirm") || "");
  const termsAccepted = Boolean(fd.get("terms"));

  if (password !== passwordConfirm) {
    setFlash("Les mots de passe ne correspondent pas.", "error");
    return;
  }

  if (!termsAccepted) {
    setFlash("Vous devez accepter les conditions d'utilisation.", "error");
    return;
  }

  try {
    await register({
      username,
      password,
      email,
      telephone: telephone || null,
    });
    setFlash("Compte cree. Redirection vers le calendrier...", "success");
    window.location.href = "/calendar";
  } catch (error) {
    setFlash(error.message || "Erreur lors de l'inscription.", "error");
  }
});
