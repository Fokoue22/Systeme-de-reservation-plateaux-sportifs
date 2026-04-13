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

const START_HOUR = 8;
const END_HOUR = 22;
const SLOT_MINUTES = 30;
const SLOT_HEIGHT = 28;
const LANE_HEADER_HEIGHT = 34;

let plateaux = [];
let reservations = [];
let selectedSport = "Tous";
let currentUser = "";

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

function toMinutes(timeValue) {
  const [h, m] = timeValue.split(":").map(Number);
  return h * 60 + m;
}

function isHalfHourSlot(value) {
  const mins = toMinutes(value);
  return mins % SLOT_MINUTES === 0;
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

function sanitizeUser(value) {
  return String(value || "").trim().toLowerCase();
}

function isMine(booking) {
  return currentUser && sanitizeUser(booking.utilisateur) === currentUser;
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
  for (const p of plateaux) {
    const option = document.createElement("option");
    option.value = String(p.id);
    option.textContent = `${p.nom} (${p.type_sport}) - min 1 / max ${p.capacite}`;
    plateauSelectEl.appendChild(option);
  }
  updateCapacityInfo();
}

function renderLanes() {
  const filtered = getFilteredPlateaux();
  lanesEl.innerHTML = "";

  subtitleEl.textContent = `${filtered.length} plateau(x) - ${dateInputEl.value}`;

  for (const plateau of filtered) {
    const lane = document.createElement("div");
    lane.className = "lane";
    lane.style.height = `${((END_HOUR - START_HOUR) * 60 / SLOT_MINUTES) * SLOT_HEIGHT + LANE_HEADER_HEIGHT}px`;

    const title = document.createElement("div");
    title.className = "lane-title";
    title.textContent = plateau.nom;
    lane.appendChild(title);

    const laneReservations = reservations.filter(
      (r) => r.plateau_id === plateau.id && r.statut === "CONFIRMED",
    );
    for (const booking of laneReservations) {
      const startMin = toMinutes(booking.creneau.debut.slice(0, 5));
      const endMin = toMinutes(booking.creneau.fin.slice(0, 5));
      const top = ((startMin - START_HOUR * 60) / SLOT_MINUTES) * SLOT_HEIGHT + LANE_HEADER_HEIGHT;
      const height = ((endMin - startMin) / SLOT_MINUTES) * SLOT_HEIGHT;
      if (height <= 0) continue;

      const card = document.createElement("div");
      const mine = isMine(booking);
      card.className = `booking ${reservationClass(booking)} ${mine ? "clickable" : ""}`.trim();
      card.style.top = `${Math.max(top, LANE_HEADER_HEIGHT)}px`;
      card.style.height = `${Math.max(height, 24)}px`;
      card.innerHTML = `
        <div class="user">${booking.utilisateur}</div>
        <div>${booking.creneau.debut.slice(0, 5)} - ${booking.creneau.fin.slice(0, 5)}</div>
        <div>${mine ? "Ma reservation" : "Non disponible"}</div>
      `;

      if (mine) {
        card.title = "Cliquer pour annuler cette reservation";
        card.addEventListener("click", async () => {
          const ok = window.confirm("Annuler cette reservation ?");
          if (!ok) return;
          try {
            await cancelReservation(booking.id);
            showFlash("Reservation annulee.", "success");
            await refreshCalendar();
          } catch (error) {
            showFlash(error.message || "Erreur lors de l'annulation", "error");
          }
        });
      }

      lane.appendChild(card);
    }

    lanesEl.appendChild(lane);
  }
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

async function refreshCalendar() {
  try {
    await Promise.all([loadPlateaux(), loadReservations()]);
    renderTabs();
    renderPlateauSelect();
    renderLanes();
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
    throw new Error(data.detail || "Echec de creation de reservation.");
  }

  return response.json();
}

async function cancelReservation(reservationId) {
  const response = await fetch(`/m2/reservations/${reservationId}/cancel?policy=FLEXIBLE`, {
    method: "POST",
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Echec de l'annulation.");
  }
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

  const payload = {
    plateau_id: Number(fd.get("plateau_id")),
    utilisateur: String(fd.get("utilisateur") || "").trim(),
    date_reservation: String(fd.get("date_reservation")),
    nb_personnes: nbPersonnes,
    creneau: {
      debut: `${debut}:00`,
      fin: `${fin}:00`,
    },
  };

  try {
    currentUser = sanitizeUser(payload.utilisateur);
    localStorage.setItem("calendarCurrentUser", currentUser);
    const created = await createReservation(payload);
    if (created.statut === "WAITLISTED") {
      showFlash("Ce creneau est deja reserve. Merci de choisir un autre horaire.", "error");
    } else {
      showFlash("Reservation creee avec succes.", "success");
    }
    await refreshCalendar();
  } catch (error) {
    showFlash(error.message || "Erreur lors de la creation", "error");
  }
});

plateauSelectNode.addEventListener("change", () => {
  updateCapacityInfo();
});

utilisateurInputEl.addEventListener("change", () => {
  currentUser = sanitizeUser(utilisateurInputEl.value);
  if (currentUser) {
    localStorage.setItem("calendarCurrentUser", currentUser);
  }
  renderLanes();
});

dateInputEl.addEventListener("change", async () => {
  formDateEl.value = dateInputEl.value;
  await refreshCalendar();
});

todayBtnEl.addEventListener("click", async () => {
  const today = isoDateToday();
  dateInputEl.value = today;
  formDateEl.value = today;
  await refreshCalendar();
});

(function bootstrap() {
  const today = isoDateToday();
  const rememberedUser = localStorage.getItem("calendarCurrentUser") || "";
  currentUser = sanitizeUser(rememberedUser);
  if (rememberedUser && !utilisateurInputEl.value) {
    utilisateurInputEl.value = rememberedUser;
  }

  dateInputEl.value = today;
  formDateEl.value = today;
  dateInputEl.min = today;
  formDateEl.min = today;
  bookingFormEl.elements.namedItem("debut").step = "1800";
  bookingFormEl.elements.namedItem("fin").step = "1800";
  bookingFormEl.elements.namedItem("debut").min = "08:00";
  bookingFormEl.elements.namedItem("fin").min = "08:30";
  bookingFormEl.elements.namedItem("debut").max = "21:30";
  bookingFormEl.elements.namedItem("fin").max = "22:00";
  peopleCountEl.step = "1";
  peopleCountEl.value = "1";
  renderTimeScale();
  refreshCalendar();
})();
