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

const START_HOUR = 8;
const END_HOUR = 22;
const HOUR_HEIGHT = 56;

let plateaux = [];
let reservations = [];
let selectedSport = "Tous";

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

function renderTimeScale() {
  timeColumnEl.innerHTML = "";
  for (let hour = START_HOUR; hour <= END_HOUR; hour += 1) {
    const line = document.createElement("div");
    line.className = "time-label";
    line.textContent = `${String(hour).padStart(2, "0")}h`;
    timeColumnEl.appendChild(line);
  }
}

function getFilteredPlateaux() {
  if (selectedSport === "Tous") {
    return plateaux;
  }
  return plateaux.filter((p) => p.type_sport === selectedSport);
}

function reservationClass(statut) {
  if (statut === "WAITLISTED") return "waitlisted";
  if (statut === "CANCELLED") return "cancelled";
  return "confirmed";
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
    option.textContent = `${p.nom} (${p.type_sport})`;
    plateauSelectEl.appendChild(option);
  }
}

function renderLanes() {
  const filtered = getFilteredPlateaux();
  lanesEl.innerHTML = "";

  subtitleEl.textContent = `${filtered.length} plateau(x) - ${dateInputEl.value}`;

  for (const plateau of filtered) {
    const lane = document.createElement("div");
    lane.className = "lane";
    lane.style.height = `${(END_HOUR - START_HOUR + 1) * HOUR_HEIGHT}px`;

    const title = document.createElement("div");
    title.className = "lane-title";
    title.textContent = plateau.nom;
    lane.appendChild(title);

    const laneReservations = reservations.filter((r) => r.plateau_id === plateau.id);
    for (const booking of laneReservations) {
      const startMin = toMinutes(booking.creneau.debut.slice(0, 5));
      const endMin = toMinutes(booking.creneau.fin.slice(0, 5));
      const top = ((startMin - START_HOUR * 60) / 60) * HOUR_HEIGHT + 34;
      const height = ((endMin - startMin) / 60) * HOUR_HEIGHT;
      if (height <= 0) continue;

      const card = document.createElement("div");
      card.className = `booking ${reservationClass(booking.statut)}`;
      card.style.top = `${Math.max(top, 30)}px`;
      card.style.height = `${Math.max(height, 24)}px`;
      card.innerHTML = `
        <div class="user">${booking.utilisateur}</div>
        <div>${booking.creneau.debut.slice(0, 5)} - ${booking.creneau.fin.slice(0, 5)}</div>
        <div>${booking.statut}</div>
      `;
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
}

bookingFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(bookingFormEl);

  const payload = {
    plateau_id: Number(fd.get("plateau_id")),
    utilisateur: String(fd.get("utilisateur") || "").trim(),
    date_reservation: String(fd.get("date_reservation")),
    creneau: {
      debut: `${String(fd.get("debut"))}:00`,
      fin: `${String(fd.get("fin"))}:00`,
    },
  };

  try {
    await createReservation(payload);
    showFlash("Reservation creee avec succes.", "success");
    await refreshCalendar();
  } catch (error) {
    showFlash(error.message || "Erreur lors de la creation", "error");
  }
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
  dateInputEl.value = today;
  formDateEl.value = today;
  renderTimeScale();
  refreshCalendar();
})();
