const lanesEl = document.getElementById("lanes");
const timeColumnEl = document.getElementById("timeColumn");
const subtitleEl = document.getElementById("subtitle");
const tabsEl = document.getElementById("sportTabs");
const plateauSelectEl = document.getElementById("plateauSelect");
const dateInputEl = document.getElementById("dateInput");
const formDateEl = document.getElementById("formDate");
const bookingFormEl = document.getElementById("bookingForm");
const flashEl = document.getElementById("flash");
const todayBtnEl = document.getElementById("todayBtn");
const utilisateurInputEl = bookingFormEl.elements.namedItem("utilisateur");
const peopleCountEl = document.getElementById("peopleCount");
const capacityMinEl = document.getElementById("capacityMin");
const capacityMaxEl = document.getElementById("capacityMax");
const plateauSelectNode = bookingFormEl.elements.namedItem("plateau_id");
const arrivalSelectEl = document.getElementById("arrivalSelect");
const departureSelectEl = document.getElementById("departureSelect");
const myReservationsListEl = document.getElementById("myReservationsList");
const submitBtnEl = bookingFormEl.querySelector("button[type='submit']");
const profileAvatarEl = document.getElementById("profileAvatar");
const profileNameEl = document.getElementById("profileName");
const settingsBtnEl = document.getElementById("settingsBtn");
const logoutBtnEl = document.getElementById("logoutBtn");
const settingsModalEl = document.getElementById("settingsModal");
const settingsFlashEl = document.getElementById("settingsFlash");
const profileFormEl = document.getElementById("profileForm");
const passwordFormEl = document.getElementById("passwordForm");
const deleteFormEl = document.getElementById("deleteForm");
const supportBtnEl = document.getElementById("supportBtn");
const compactModeToggleEl = document.getElementById("compactModeToggle");
const profileFullNameEl = document.getElementById("profileFullName");
const profileEmailEl = document.getElementById("profileEmail");
const profileTelephoneEl = document.getElementById("profileTelephone");

const START_HOUR = 8;
const END_HOUR = 22;
const SLOT_MINUTES = 30;
const SLOT_HEIGHT = 28;
const LANE_HEADER_HEIGHT = 34;
const LANE_FOOTER_HEIGHT = 34;

let plateaux = [];
let reservations = [];
let allReservations = [];
let selectedSport = "Tous";
let currentUser = "";
let editingReservationId = null;
let currentAccount = null;

function isoDateToday() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function showFlash(message, type = "success") {
  flashEl.textContent = message;
  flashEl.className = `flash ${type}`;
}

function showSettingsFlash(message, type = "success") {
  settingsFlashEl.textContent = message;
  settingsFlashEl.className = `flash settings-flash ${type}`;
}

function initialsFromUsername(fullNameOrUsername) {
  const text = String(fullNameOrUsername || "").trim();
  if (!text) return "--";
  // Prend la première lettre du prénom et du nom si possible
  const parts = text.split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  // Si un seul mot, prendre les deux premières lettres
  return text.slice(0, 2).toUpperCase();
}

function setAuthUi(account) {
  currentAccount = account;
  if (!account) {
    profileNameEl.textContent = "Invite";
    profileAvatarEl.textContent = "--";
    utilisateurInputEl.disabled = false;
    if (profileFullNameEl) profileFullNameEl.value = "";
    if (profileEmailEl) profileEmailEl.value = "";
    if (profileTelephoneEl) profileTelephoneEl.value = "";
    return;
  }

  currentUser = sanitizeUser(account.username);
  utilisateurInputEl.value = account.username;
  utilisateurInputEl.disabled = true;
  profileNameEl.textContent = account.full_name || account.username;
  profileAvatarEl.textContent = initialsFromUsername(account.full_name || account.username);
  if (profileFullNameEl) profileFullNameEl.value = account.full_name || account.username;
  if (profileEmailEl) profileEmailEl.value = account.email || "";
  if (profileTelephoneEl) profileTelephoneEl.value = account.telephone || "";
}

function normalizeApiErrorMessage(detail, status, fallback) {
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first.msg === "string") {
      return `Validation invalide: ${first.msg}`;
    }
  }

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (status === 422) {
    return "Validation invalide. Verifiez les champs du formulaire.";
  }

  if (status === 409) {
    return "Conflit detecte pour ce creneau ou cette capacite.";
  }

  return fallback;
}

function toMinutes(timeValue) {
  const [h, m] = timeValue.split(":").map(Number);
  return h * 60 + m;
}

function isHalfHourSlot(value) {
  const mins = toMinutes(value);
  return mins % SLOT_MINUTES === 0;
}

function normalizeText(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function capitalizeWords(value) {
  return String(value || "")
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function buildPlateauDisplayData(items) {
  const grouped = new Map();

  for (const plateau of items) {
    const key = [normalizeText(plateau.type_sport), normalizeText(plateau.emplacement)].join("|");
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(plateau);
  }

  const labelsById = new Map();
  const groups = [];

  for (const [key, groupedItems] of grouped.entries()) {
    const ordered = groupedItems.slice().sort((left, right) => left.id - right.id);
    const first = ordered[0];
    const groupLabel = `${capitalizeWords(first.type_sport)} - ${first.emplacement}`;

    ordered.forEach((plateau, index) => {
      const sequence = index + 1;
      const label = `${capitalizeWords(first.type_sport)} - ${plateau.emplacement} - M${sequence}`;
      labelsById.set(plateau.id, label);
    });

    groups.push({ groupLabel, items: ordered });
  }

  groups.sort((left, right) => left.groupLabel.localeCompare(right.groupLabel, "fr"));
  return { labelsById, groups };
}

function updateCapacityInfo() {
  const selectedPlateauId = Number(plateauSelectNode.value);
  const plateau = plateaux.find((p) => p.id === selectedPlateauId);
  const minCap = 1;
  const maxCap = plateau ? plateau.capacite : 1;
  capacityMinEl.textContent = String(minCap);
  capacityMaxEl.textContent = String(maxCap);
  peopleCountEl.min = String(minCap);
  peopleCountEl.max = String(maxCap);
  if (!peopleCountEl.value) {
    peopleCountEl.value = String(minCap);
  }
}

function formatHourMinute(totalMinutes) {
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function buildTimeOptions(selectEl, startMin, endMin) {
  selectEl.innerHTML = "";
  for (let minutes = startMin; minutes <= endMin; minutes += SLOT_MINUTES) {
    const option = document.createElement("option");
    option.value = formatHourMinute(minutes);
    option.textContent = formatHourMinute(minutes);
    selectEl.appendChild(option);
  }
}

function refreshDepartureOptions() {
  const arrival = toMinutes(arrivalSelectEl.value);
  const minDeparture = arrival + SLOT_MINUTES;
  buildTimeOptions(departureSelectEl, minDeparture, END_HOUR * 60);
}

function sanitizeUser(value) {
  return String(value || "").trim().toLowerCase();
}

function isMine(booking) {
  const activeUser = currentUser || sanitizeUser(utilisateurInputEl.value);
  if (!currentUser && activeUser) {
    currentUser = activeUser;
  }
  return activeUser && sanitizeUser(booking.utilisateur) === activeUser;
}

async function fetchCurrentAccount() {
  const response = await fetch("/auth/me", { credentials: "same-origin" });
  if (!response.ok) {
    return null;
  }
  return response.json();
}

async function updateProfile(payload) {
  const response = await fetch("/auth/me/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec de mise a jour du profil."));
  }
  return data;
}

async function changePassword(payload) {
  const response = await fetch("/auth/me/password", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec du changement de mot de passe."));
  }
  return data;
}

async function deleteAccount(currentPassword) {
  const response = await fetch("/auth/me", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ current_password: currentPassword }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok && response.status !== 204) {
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec de suppression du compte."));
  }
}

function openSettingsModal() {
  settingsModalEl.classList.remove("hidden");
  settingsModalEl.setAttribute("aria-hidden", "false");
  settingsBtnEl.setAttribute("aria-expanded", "true");
}

function closeSettingsModal() {
  settingsModalEl.classList.add("hidden");
  settingsModalEl.setAttribute("aria-hidden", "true");
  settingsBtnEl.setAttribute("aria-expanded", "false");
}

function toggleSettingsModal() {
  const isOpen = !settingsModalEl.classList.contains("hidden");
  if (isOpen) {
    closeSettingsModal();
    return;
  }
  openSettingsModal();
}

function applyCompactMode(isCompact) {
  document.body.classList.toggle("compact-calendar", isCompact);
  localStorage.setItem("calendarCompactMode", isCompact ? "1" : "0");
}

async function logoutAccount() {
  const response = await fetch("/auth/logout", {
    method: "POST",
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error("Echec de deconnexion.");
  }
}

function renderTimeScale() {
  timeColumnEl.innerHTML = "";
  const spacer = document.createElement("div");
  spacer.className = "time-header-spacer";
  timeColumnEl.appendChild(spacer);

  for (let minutes = START_HOUR * 60; minutes <= END_HOUR * 60; minutes += SLOT_MINUTES) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    const line = document.createElement("div");
    line.className = "time-label";
    line.textContent = `${String(h).padStart(2, "0")}h${String(m).padStart(2, "0")}`;
    timeColumnEl.appendChild(line);
  }
}

function getFilteredPlateaux() {
  if (selectedSport === "Tous") {
    return plateaux;
  }
  return plateaux.filter((p) => p.type_sport === selectedSport);
}

function reservationClass(booking) {
  return isMine(booking) ? "mine" : "unavailable";
}

function renderTabs() {
  const sports = ["Tous", ...new Set(plateaux.map((p) => p.type_sport))];
  tabsEl.innerHTML = "";
  for (const sport of sports) {
    const btn = document.createElement("button");
    btn.type = "button";
    const isTousBtn = sport === "Tous";
    btn.className = `sport-tab ${isTousBtn ? "all-sports" : ""} ${sport === selectedSport ? "active" : ""}`;
    btn.textContent = isTousBtn ? "Tous les calendriers" : sport;
    btn.addEventListener("click", () => {
      selectedSport = sport;
      renderTabs();
      renderLanes();
    });
    tabsEl.appendChild(btn);
  }
}

function renderPlateauSelect() {
  plateauSelectEl.innerHTML = "";

  const displayData = buildPlateauDisplayData(plateaux);
  for (const { groupLabel, items } of displayData.groups) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = groupLabel;
    for (const p of items) {
      const option = document.createElement("option");
      option.value = String(p.id);
      option.textContent = `${displayData.labelsById.get(p.id)} (max ${p.capacite})`;
      optgroup.appendChild(option);
    }
    plateauSelectEl.appendChild(optgroup);
  }
  updateCapacityInfo();
}

function renderLanes() {
  const filtered = getFilteredPlateaux();
  const displayData = buildPlateauDisplayData(filtered);
  lanesEl.innerHTML = "";

  subtitleEl.textContent = `${filtered.length} plateau(x) - ${dateInputEl.value}`;

  for (const plateau of filtered) {
    const lane = document.createElement("div");
    lane.className = "lane";
    lane.style.height = `${((END_HOUR - START_HOUR) * 60 / SLOT_MINUTES) * SLOT_HEIGHT + LANE_HEADER_HEIGHT + LANE_FOOTER_HEIGHT}px`;

    const title = document.createElement("div");
    title.className = "lane-title";
    const laneLabel =
      displayData.labelsById.get(plateau.id) ||
      `${capitalizeWords(plateau.type_sport)} - ${plateau.nom} - ${plateau.emplacement}`;
    title.textContent = laneLabel;
    lane.appendChild(title);

    const laneReservations = reservations.filter(
      (r) => r.plateau_id === plateau.id && r.statut === "CONFIRMED",
    );
      for (const booking of laneReservations) {
        const startMin = toMinutes(booking.creneau.debut.slice(0, 5));
        const endMin = toMinutes(booking.creneau.fin.slice(0, 5));
        const top = ((startMin - START_HOUR * 60) / SLOT_MINUTES) * SLOT_HEIGHT + LANE_HEADER_HEIGHT;
        // Correction: la hauteur doit couvrir jusqu'à l'heure de fin incluse
        const height = ((endMin - startMin) / SLOT_MINUTES) * SLOT_HEIGHT;
        if (height <= 0) continue;

        const card = document.createElement("div");
        const mine = isMine(booking);
        card.className = `booking ${reservationClass(booking)}`.trim();
        card.style.top = `${Math.max(top, LANE_HEADER_HEIGHT)}px`;
        // Correction: ne pas soustraire 0.5 slot, la hauteur doit aller jusqu'à la ligne de fin
        card.style.height = `${height}px`;
        let actionsHtml = "";
        if (mine) {
          actionsHtml = `
            <div class="booking-actions">
              <button class="booking-action edit" type="button" title="Modifier la reservation" aria-label="Modifier">✏</button>
              <button class="booking-action delete" type="button" title="Supprimer la reservation" aria-label="Supprimer">🗑</button>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="user">${booking.utilisateur}</div>
          <div>${booking.creneau.debut.slice(0, 5)} - ${booking.creneau.fin.slice(0, 5)}</div>
          <div>${mine ? "Ma reservation" : "Non disponible"}</div>
          ${actionsHtml}
        `;

        if (mine) {
          const editBtn = card.querySelector(".booking-action.edit");
          const deleteBtn = card.querySelector(".booking-action.delete");

          editBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            startEditReservation(booking);
          });

          deleteBtn.addEventListener("click", async (event) => {
            event.stopPropagation();
            const ok = window.confirm("Annuler cette reservation ?");
            if (!ok) return;
            try {
              await cancelReservation(booking.id);
              showFlash("Reservation annulee.", "success");
              if (editingReservationId === booking.id) {
                resetEditMode();
              }
              await refreshCalendar();
            } catch (error) {
              showFlash(error.message || "Erreur lors de l'annulation", "error");
            }
          });
        }

        lane.appendChild(card);
      }


    const footer = document.createElement("div");
    footer.className = "lane-footer";
    footer.textContent = laneLabel;
    lane.appendChild(footer);

    lanesEl.appendChild(lane);
  }
}

function formatDateFr(value) {
  return value;
}

function formatTimeFr(value) {
  const [h, m] = value.slice(0, 5).split(":");
  return `${h} h ${m}`;
}

function renderMyReservations() {
  const displayData = buildPlateauDisplayData(plateaux);
  const labelsById = displayData.labelsById;
  const seen = new Set();
  const mine = allReservations
    .filter(
      (item) =>
        isMine(item) &&
        item.statut === "CONFIRMED" &&
        item.date_reservation === dateInputEl.value &&
        !seen.has(item.id) &&
        seen.add(item.id),
    )
    .sort((a, b) => {
      if (a.date_reservation !== b.date_reservation) {
        return a.date_reservation.localeCompare(b.date_reservation);
      }
      return a.creneau.debut.localeCompare(b.creneau.debut);
    });

  if (!mine.length) {
    myReservationsListEl.innerHTML = '<p class="empty-state">Aucune reservation pour le moment.</p>';
    return;
  }

  const byDate = new Map();
  for (const item of mine) {
    if (!byDate.has(item.date_reservation)) {
      byDate.set(item.date_reservation, []);
    }
    byDate.get(item.date_reservation).push(item);
  }

  myReservationsListEl.innerHTML = "";
  for (const [dateValue, items] of byDate.entries()) {
    const dayBlock = document.createElement("article");
    dayBlock.className = "my-reservation-day";

    const title = document.createElement("h4");
    title.textContent = formatDateFr(dateValue);
    dayBlock.appendChild(title);

    for (const item of items) {
      const line = document.createElement("p");
      line.className = "my-reservation-item";
      const label = labelsById.get(item.plateau_id) || `Plateau #${item.plateau_id}`;
      line.textContent = `${item.creneau.debut.slice(0, 5)} a ${item.creneau.fin.slice(0, 5)} ${label}`;
      dayBlock.appendChild(line);
    }

    myReservationsListEl.appendChild(dayBlock);
  }
}

function startEditReservation(booking) {
  editingReservationId = booking.id;
  plateauSelectNode.value = String(booking.plateau_id);
  updateCapacityInfo();
  formDateEl.value = booking.date_reservation;
  arrivalSelectEl.value = booking.creneau.debut.slice(0, 5);
  refreshDepartureOptions();
  departureSelectEl.value = booking.creneau.fin.slice(0, 5);
  peopleCountEl.value = String(booking.nb_personnes || 1);
  submitBtnEl.textContent = "Mettre a jour la reservation";
  showFlash("Mode edition active: modifiez les champs puis confirmez.", "success");
}

function resetEditMode() {
  editingReservationId = null;
  submitBtnEl.textContent = "Creer la reservation";
}

async function loadPlateaux() {
  const response = await fetch("/m1/plateaux");
  if (!response.ok) throw new Error("Impossible de charger les plateaux.");
  plateaux = await response.json();
}

async function loadReservations() {
  const selectedDate = dateInputEl.value;
  const response = await fetch(`/m2/reservations?date_reservation=${selectedDate}`);
  if (!response.ok) throw new Error("Impossible de charger les reservations.");
  reservations = await response.json();
}

async function loadAllReservations() {
  const response = await fetch("/m2/reservations");
  if (!response.ok) throw new Error("Impossible de charger la liste des reservations utilisateur.");
  allReservations = await response.json();
}

async function refreshCalendar() {
  try {
    await Promise.all([loadPlateaux(), loadReservations(), loadAllReservations()]);
    renderTabs();
    renderPlateauSelect();
    renderLanes();
    renderMyReservations();
  } catch (error) {
    showFlash(error.message || "Erreur de chargement", "error");
  }
}

async function createReservation(payload) {
  const response = await fetch("/m2/reservations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec de creation de reservation."));
  }

  return response.json();
}

async function cancelReservation(reservationId) {
  const response = await fetch(`/m2/reservations/${reservationId}/cancel?policy=FLEXIBLE`, {
    method: "POST",
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec de l'annulation."));
  }
}

async function updateReservation(reservationId, payload) {
  const response = await fetch(`/m2/reservations/${reservationId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(normalizeApiErrorMessage(data.detail, response.status, "Echec de la mise a jour de reservation."));
  }
  return response.json();
}

bookingFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(bookingFormEl);
  const debut = String(fd.get("debut") || "");
  const fin = String(fd.get("fin") || "");
  const nbPersonnes = Number(fd.get("nb_personnes") || 0);
  const selectedPlateau = plateaux.find((p) => p.id === Number(fd.get("plateau_id")));
  const minCap = 1;
  const maxCap = selectedPlateau ? selectedPlateau.capacite : 1;

  if (!isHalfHourSlot(debut) || !isHalfHourSlot(fin)) {
    showFlash("Utilisez des horaires au format 08:00, 08:30, 09:00, etc.", "error");
    return;
  }

  if (toMinutes(debut) < toMinutes("08:00") || toMinutes(fin) > toMinutes("22:00")) {
    showFlash("Les reservations doivent etre entre 08:00 et 22:00.", "error");
    return;
  }

  if (nbPersonnes < minCap || nbPersonnes > maxCap) {
    showFlash(`Le nombre de personnes doit etre entre ${minCap} et ${maxCap}.`, "error");
    return;
  }

  const resolvedUser = currentAccount ? currentAccount.username : String(fd.get("utilisateur") || "").trim();
  const payload = {
    plateau_id: Number(fd.get("plateau_id")),
    utilisateur: resolvedUser,
    date_reservation: String(fd.get("date_reservation")),
    nb_personnes: nbPersonnes,
    creneau: {
      debut: `${debut}:00`,
      fin: `${fin}:00`,
    },
  };

  try {
    currentUser = sanitizeUser(payload.utilisateur);
    const result = editingReservationId
      ? await updateReservation(editingReservationId, payload)
      : await createReservation(payload);

    if (result.statut === "WAITLISTED") {
      showFlash("Reservation en attente: ce creneau est deja occupe.", "error");
    } else {
      showFlash(editingReservationId ? "Reservation mise a jour avec succes." : "Reservation creee avec succes.", "success");
    }
    resetEditMode();
    await refreshCalendar();
  } catch (error) {
    showFlash(error.message || "Erreur lors de la creation", "error");
  }
});

plateauSelectNode.addEventListener("change", () => {
  updateCapacityInfo();
});

arrivalSelectEl.addEventListener("change", () => {
  refreshDepartureOptions();
});

utilisateurInputEl.addEventListener("change", () => {
  if (currentAccount) {
    utilisateurInputEl.value = currentAccount.username;
    return;
  }
  currentUser = sanitizeUser(utilisateurInputEl.value);
  renderLanes();
  renderMyReservations();
});

utilisateurInputEl.addEventListener("input", () => {
  if (currentAccount) {
    utilisateurInputEl.value = currentAccount.username;
    return;
  }
  currentUser = sanitizeUser(utilisateurInputEl.value);
  renderMyReservations();
});

logoutBtnEl.addEventListener("click", async () => {
  try {
    await logoutAccount();
    window.location.href = "/login";
  } catch (error) {
    showFlash(error.message || "Erreur de deconnexion", "error");
  }
});

settingsBtnEl.addEventListener("click", toggleSettingsModal);

settingsModalEl.querySelectorAll("[data-close-settings]").forEach((button) => {
  button.addEventListener("click", closeSettingsModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSettingsModal();
  }
});

settingsModalEl.addEventListener("click", (event) => {
  if (event.target === settingsModalEl) {
    closeSettingsModal();
  }
});

supportBtnEl.addEventListener("click", () => {
  showSettingsFlash("L'aide et le support seront disponible prochainement.", "success");
});

compactModeToggleEl.addEventListener("change", () => {
  applyCompactMode(compactModeToggleEl.checked);
});

profileFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(profileFormEl);
  try {
    const updated = await updateProfile({
      full_name: String(fd.get("full_name") || "").trim(),
      email: String(fd.get("email") || "").trim() || null,
      telephone: String(fd.get("telephone") || "").trim() || null,
    });
    setAuthUi(updated);
    showSettingsFlash("Profil mis a jour.", "success");
    await refreshCalendar();
  } catch (error) {
    showSettingsFlash(error.message || "Erreur lors de la mise a jour du profil.", "error");
  }
});

passwordFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(passwordFormEl);
  const currentPassword = String(fd.get("current_password") || "");
  const newPassword = String(fd.get("new_password") || "");
  const confirmNewPassword = String(fd.get("confirm_new_password") || "");

  if (newPassword !== confirmNewPassword) {
    showSettingsFlash("Les nouveaux mots de passe ne correspondent pas.", "error");
    return;
  }

  try {
    await changePassword({ current_password: currentPassword, new_password: newPassword });
    passwordFormEl.reset();
    showSettingsFlash("Mot de passe mis a jour.", "success");
  } catch (error) {
    showSettingsFlash(error.message || "Erreur lors du changement de mot de passe.", "error");
  }
});

deleteFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(deleteFormEl);
  const currentPassword = String(fd.get("current_password") || "");

  const confirmed = window.confirm("Supprimer definitivement votre compte ?");
  if (!confirmed) {
    return;
  }

  try {
    await deleteAccount(currentPassword);
    window.location.href = "/login";
  } catch (error) {
    showSettingsFlash(error.message || "Erreur lors de la suppression du compte.", "error");
  }
});

dateInputEl.addEventListener("change", async () => {
  formDateEl.value = dateInputEl.value;
  resetEditMode();
  await refreshCalendar();
});

todayBtnEl.addEventListener("click", async () => {
  const today = isoDateToday();
  dateInputEl.value = today;
  formDateEl.value = today;
  resetEditMode();
  await refreshCalendar();
});

(async function bootstrap() {
  const today = isoDateToday();

  dateInputEl.value = today;
  formDateEl.value = today;
  dateInputEl.min = today;
  formDateEl.min = today;
  buildTimeOptions(arrivalSelectEl, START_HOUR * 60, END_HOUR * 60 - SLOT_MINUTES);
  arrivalSelectEl.value = "08:00";
  refreshDepartureOptions();
  departureSelectEl.value = "08:30";
  peopleCountEl.step = "1";
  peopleCountEl.value = "1";

  try {
    const account = await fetchCurrentAccount();
    if (!account) {
      window.location.href = "/login";
      return;
    }
    setAuthUi(account);
  } catch {
    window.location.href = "/login";
    return;
  }

  const compactModeEnabled = localStorage.getItem("calendarCompactMode") === "1";
  compactModeToggleEl.checked = compactModeEnabled;
  applyCompactMode(compactModeEnabled);

  if (!currentAccount && utilisateurInputEl.value) {
    currentUser = sanitizeUser(utilisateurInputEl.value);
  }

  renderTimeScale();
  await refreshCalendar();
})();
