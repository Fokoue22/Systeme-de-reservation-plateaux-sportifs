const registerFormEl = document.getElementById("registerForm");
const registerFlashEl = document.getElementById("registerFlash");
const passwordToggleButtons = document.querySelectorAll(".password-toggle");

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

function togglePasswordVisibility(button) {
  const targetId = button.getAttribute("data-target");
  if (!targetId) return;

  const input = document.getElementById(targetId);
  if (!input) return;

  const visible = input.type === "text";
  input.type = visible ? "password" : "text";
  button.setAttribute(
    "aria-label",
    visible ? "Afficher le mot de passe" : "Masquer le mot de passe",
  );
  button.setAttribute(
    "title",
    visible ? "Afficher le mot de passe" : "Masquer le mot de passe",
  );
}

for (const button of passwordToggleButtons) {
  button.addEventListener("click", () => togglePasswordVisibility(button));
}

registerFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(registerFormEl);

  const fullName = String(fd.get("full_name") || "").trim();
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
      full_name: fullName,
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
