/* global Telegram */
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.setHeaderColor) { try { tg.setHeaderColor("#f2718f"); } catch (e) {} }
  if (tg.setBackgroundColor) { try { tg.setBackgroundColor("#fdf1ef"); } catch (e) {} }
}

const API_BASE = "/api/miniapp";

const State = {
  me: null,
  countries: [],
  selectedCountry: null,
  countryReturnScreen: "book-calendar",
  cal: { year: new Date().getFullYear(), month: new Date().getMonth() + 1 },
  selectedDate: null,
  selectedTime: null,
  slotsCache: {},
  materials: null,
  historyTab: "upcoming",
  materialsTab: "purchased",
};

function initData() {
  return tg && tg.initData ? tg.initData : "";
}

async function api(path, opts = {}) {
  const headers = Object.assign(
    { "Content-Type": "application/json", "X-Telegram-Init-Data": initData() },
    opts.headers || {}
  );
  const res = await fetch(API_BASE + path, Object.assign({}, opts, { headers }));
  if (!res.ok) {
    let payload = {};
    try { payload = await res.json(); } catch (e) {}
    const err = new Error(payload.error || ("HTTP " + res.status));
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

const UI = {
  toast(msg) {
    const el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 2200);
  },
  closeModal() {
    document.getElementById("article-modal").classList.remove("show");
  },
};

const Nav = {
  go(screen) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const target = document.getElementById("screen-" + screen);
    if (target) target.classList.add("active");

    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    const navMap = { "home": "home", "book-calendar": "book-calendar", "book-success": "book-calendar", "materials": "materials", "profile": "profile", "payment": "profile", "history": "home", "consultation": "home" };
    const navKey = screen === "book-country" ? (State.countryReturnScreen === "profile" ? "profile" : "book-calendar") : navMap[screen];
    if (navKey) {
      const btn = document.querySelector('.nav-btn[data-tab="' + navKey + '"]');
      if (btn) btn.classList.add("active");
    }

    if (screen === "book-country") Booking.renderCountries();
    if (screen === "book-calendar") Calendar.render();
    if (screen === "history") History.load();
    if (screen === "materials") Materials.load();
    if (screen === "profile") {
      if (State.skipProfileFill) {
        State.skipProfileFill = false;
      } else {
        Profile.fill();
      }
    }

    if (tg && tg.HapticFeedback) { try { tg.HapticFeedback.selectionChanged(); } catch (e) {} }
  },
};

/* ==================== ГЛАВНАЯ ==================== */

async function loadMe() {
  try {
    State.me = await api("/me");
  } catch (e) {
    console.error(e);
    return;
  }
  document.getElementById("stat-lessons").textContent = State.me.stats.lessons_done;
  document.getElementById("stat-materials").textContent = State.me.stats.materials;

  const nextEl = document.getElementById("home-next-lesson");
  if (State.me.next_booking) {
    const b = State.me.next_booking;
    nextEl.style.display = "flex";
    nextEl.textContent = "🗓 Ближайшее занятие: " + formatDateHuman(b.date) + ", " + b.time;
  } else {
    nextEl.style.display = "none";
  }

  if (State.me.country) {
    document.getElementById("book-country-label").textContent = State.me.country;
    document.getElementById("profile-country-label").textContent =
      State.me.country + (State.me.timezone ? " (" + State.me.timezone + ")" : "");
    State.selectedCountry = { name: State.me.country, tz_label: State.me.timezone };
  }

  if (State.me.is_admin) {
    const existing = document.getElementById("admin-panel-link");
    if (!existing) {
      const adminBtn = document.createElement("div");
      adminBtn.id = "admin-panel-link";
      adminBtn.className = "action-item";
      adminBtn.innerHTML = '<div class="icon orange">🛠</div><div class="body"><strong>Админ-панель</strong><span>Расписание и доход</span></div><div class="arrow">›</div>';
      adminBtn.onclick = () => { window.location.href = "/webapp/admin"; };
      document.querySelector("#screen-home").appendChild(adminBtn);
    }
  }
}

function formatDateHuman(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

/* ==================== ВЫБОР СТРАНЫ ==================== */

const Booking = {
  async loadCountries() {
    if (State.countries.length) return;
    State.countries = await api("/countries");
  },
  renderCountries() {
    const q = (document.getElementById("country-search").value || "").toLowerCase();
    const list = document.getElementById("country-list");
    list.innerHTML = "";
    State.countries
      .filter((c) => c.name.toLowerCase().includes(q))
      .forEach((c) => {
        const row = document.createElement("div");
        const selected = State.selectedCountry && State.selectedCountry.name === c.name;
        row.className = "country-row" + (selected ? " selected" : "");
        row.innerHTML =
          '<span class="flag">' + c.flag + '</span>' +
          '<div><div class="name">' + c.name + '</div><div class="tz">' + c.tz_label + '</div></div>' +
          '<span class="check"></span>';
        row.onclick = () => {
          State.selectedCountry = c;
          document.getElementById("book-country-label").textContent = c.name;
          document.getElementById("profile-country-label").textContent = c.name + " (" + c.tz_label + ")";
          if (State.countryReturnScreen === "profile") State.skipProfileFill = true;
          Nav.go(State.countryReturnScreen || "book-calendar");
        };
        list.appendChild(row);
      });
  },
  async confirm() {
    if (!State.selectedDate || !State.selectedTime) return;
    const btn = document.getElementById("btn-confirm-slot");
    btn.disabled = true;
    btn.textContent = "Записываем...";
    try {
      const res = await api("/book", {
        method: "POST",
        body: JSON.stringify({
          date: State.selectedDate,
          time: State.selectedTime,
          country: State.selectedCountry ? State.selectedCountry.name : null,
          timezone: State.selectedCountry ? State.selectedCountry.tz_label : null,
          topic: document.getElementById("topic-input").value || null,
        }),
      });
      const b = res.booking;
      document.getElementById("success-details").innerHTML =
        '<div style="display:flex;gap:10px;margin-bottom:10px"><div style="font-size:20px">📅</div><div><div style="font-size:12px;color:var(--muted)">Дата и время</div><div style="font-weight:700">' + formatDateHuman(b.date) + ", " + b.time + "</div></div></div>" +
        (b.country ? '<div style="display:flex;gap:10px;margin-bottom:10px"><div style="font-size:20px">🌍</div><div><div style="font-size:12px;color:var(--muted)">Страна</div><div style="font-weight:700">' + b.country + "</div></div></div>" : "") +
        (b.topic ? '<div style="display:flex;gap:10px"><div style="font-size:20px">📝</div><div><div style="font-size:12px;color:var(--muted)">Тема</div><div style="font-weight:700">' + b.topic + "</div></div></div>" : "");
      Nav.go("book-success");
      State.selectedDate = null;
      State.selectedTime = null;
      State.slotsCache = {};
      loadMe();
      if (tg && tg.HapticFeedback) { try { tg.HapticFeedback.notificationOccurred("success"); } catch (e) {} }
    } catch (e) {
      if (e.status === 409) {
        UI.toast("Это время уже заняли, выберите другое");
        State.slotsCache = {};
        Calendar.selectDay(State.selectedDate);
      } else {
        UI.toast("Не получилось записаться, попробуйте ещё раз");
      }
    } finally {
      btn.disabled = false;
      btn.textContent = "Подтвердить запись";
    }
  },
};

/* ==================== КАЛЕНДАРЬ ==================== */

const MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const Calendar = {
  async render() {
    document.getElementById("time-card").style.display = "none";
    document.getElementById("topic-field").style.display = "none";
    document.getElementById("btn-confirm-slot").style.display = "none";

    const { year, month } = State.cal;
    document.getElementById("cal-month-label").textContent = MONTHS_RU[month - 1] + " " + year;

    let data;
    try {
      data = await api("/calendar?year=" + year + "&month=" + month);
    } catch (e) {
      UI.toast("Не удалось загрузить календарь");
      return;
    }

    const grid = document.getElementById("cal-grid");
    grid.innerHTML = "";
    WEEKDAYS_RU.forEach((wd) => {
      const el = document.createElement("div");
      el.className = "wd";
      el.textContent = wd;
      grid.appendChild(el);
    });

    const firstDate = new Date(year, month - 1, 1);
    let firstWeekday = firstDate.getDay();
    firstWeekday = firstWeekday === 0 ? 6 : firstWeekday - 1;
    for (let i = 0; i < firstWeekday; i++) {
      grid.appendChild(document.createElement("div"));
    }

    const todayStr = new Date().toISOString().slice(0, 10);

    data.days.forEach((d) => {
      const cell = document.createElement("div");
      const dayNum = parseInt(d.date.slice(-2), 10);
      const past = d.date < todayStr;
      const disabled = past || !d.has_free;
      cell.className = "day-cell" + (disabled ? " disabled" : "") + (d.date === State.selectedDate ? " selected" : "");
      cell.dataset.date = d.date;
      cell.innerHTML = dayNum + (d.has_free && !past ? '<span class="dot"></span>' : "");
      if (!disabled) cell.onclick = () => Calendar.selectDay(d.date);
      grid.appendChild(cell);
    });
  },

  prevMonth() {
    let { year, month } = State.cal;
    month -= 1;
    if (month < 1) { month = 12; year -= 1; }
    State.cal = { year, month };
    Calendar.render();
  },
  nextMonth() {
    let { year, month } = State.cal;
    month += 1;
    if (month > 12) { month = 1; year += 1; }
    State.cal = { year, month };
    Calendar.render();
  },

  async selectDay(dateStr) {
    const changingDay = State.selectedDate !== dateStr;
    State.selectedDate = dateStr;
    if (changingDay) State.selectedTime = null;

    // Подсвечиваем выбранный день в сетке месяца без повторного запроса к серверу
    document.querySelectorAll("#cal-grid .day-cell").forEach((cell) => {
      cell.classList.toggle("selected", cell.dataset.date === dateStr);
    });

    const card = document.getElementById("time-card");
    card.style.display = "block";
    document.getElementById("time-card-title").textContent = "Доступное время на " + formatDateHuman(dateStr);

    let slots = State.slotsCache[dateStr];
    if (!slots) {
      const grid = document.getElementById("time-grid");
      grid.innerHTML = '<div class="loader">Загрузка…</div>';
      try {
        slots = await api("/slots?date=" + dateStr);
        State.slotsCache[dateStr] = slots;
      } catch (e) {
        grid.innerHTML = "";
        UI.toast("Не удалось загрузить время");
        return;
      }
    }

    Calendar.renderTimeGrid(dateStr, slots);

    if (State.selectedTime) {
      document.getElementById("topic-field").style.display = "block";
      document.getElementById("btn-confirm-slot").style.display = "block";
    } else {
      document.getElementById("topic-field").style.display = "none";
      document.getElementById("btn-confirm-slot").style.display = "none";
    }
  },

  renderTimeGrid(dateStr, slots) {
    slots = slots || State.slotsCache[dateStr] || [];
    const grid = document.getElementById("time-grid");
    grid.innerHTML = "";
    if (!slots.length) {
      grid.innerHTML = '<div class="empty-state">На этот день нет доступного времени</div>';
      return;
    }
    slots.forEach((s) => {
      const chip = document.createElement("div");
      chip.className = "time-chip" + (s.status !== "free" ? " " + s.status : "") + (State.selectedTime === s.time ? " selected" : "");
      chip.textContent = s.time;
      if (s.status === "free") {
        chip.onclick = () => {
          State.selectedTime = s.time;
          Calendar.renderTimeGrid(dateStr, slots);
          document.getElementById("topic-field").style.display = "block";
          document.getElementById("btn-confirm-slot").style.display = "block";
        };
      }
      grid.appendChild(chip);
    });
  },
};

/* ==================== ИСТОРИЯ ==================== */

const History = {
  data: null,
  async load() {
    const list = document.getElementById("history-list");
    list.innerHTML = '<div class="loader">Загрузка…</div>';
    try {
      History.data = await api("/history");
    } catch (e) {
      list.innerHTML = '<div class="empty-state">Не удалось загрузить историю</div>';
      return;
    }
    History.renderList();
  },
  switchTab(tab) {
    State.historyTab = tab;
    document.getElementById("tab-upcoming").classList.toggle("active", tab === "upcoming");
    document.getElementById("tab-past").classList.toggle("active", tab === "past");
    History.renderList();
  },
  renderList() {
    const list = document.getElementById("history-list");
    const items = History.data ? History.data[State.historyTab] : [];
    if (!items || !items.length) {
      list.innerHTML = '<div class="empty-state">Пока пусто</div>';
      return;
    }
    list.innerHTML = "";
    items.forEach((b) => {
      const row = document.createElement("div");
      row.className = "booking-row";
      const statusLabel = { confirmed: "Подтверждено", completed: "Завершено", cancelled: "Отменено" }[b.status] || b.status;
      row.innerHTML =
        '<div class="top"><span class="dt">' + formatDateHuman(b.date) + ", " + b.time + '</span><span class="badge ' + b.status + '">' + statusLabel + "</span></div>" +
        '<div class="topic">' + (b.topic || "Занятие с логопедом") + "</div>";
      if (State.historyTab === "upcoming" && b.status === "confirmed") {
        const cancelBtn = document.createElement("button");
        cancelBtn.className = "btn btn-ghost btn-sm";
        cancelBtn.style.marginTop = "8px";
        cancelBtn.textContent = "Отменить запись";
        cancelBtn.onclick = () => History.cancel(b.id);
        row.appendChild(cancelBtn);
      }
      list.appendChild(row);
    });
  },
  async cancel(bookingId) {
    if (!confirm("Отменить эту запись?")) return;
    try {
      await api("/cancel", { method: "POST", body: JSON.stringify({ booking_id: bookingId }) });
      UI.toast("Запись отменена");
      History.load();
      loadMe();
    } catch (e) {
      UI.toast("Не получилось отменить запись");
    }
  },
};

/* ==================== МАТЕРИАЛЫ ==================== */

const Materials = {
  data: null,
  async load() {
    const list = document.getElementById("materials-list");
    list.innerHTML = '<div class="loader">Загрузка…</div>';
    try {
      Materials.data = await api("/materials");
    } catch (e) {
      list.innerHTML = '<div class="empty-state">Не удалось загрузить материалы</div>';
      return;
    }
    Materials.renderList();
  },
  switchTab(tab) {
    State.materialsTab = tab;
    ["purchased", "free", "paid"].forEach((t) =>
      document.getElementById("tab-" + t).classList.toggle("active", t === tab)
    );
    Materials.renderList();
  },
  renderList() {
    const list = document.getElementById("materials-list");
    if (!Materials.data) return;
    list.innerHTML = "";

    if (State.materialsTab === "purchased") {
      const items = Materials.data.purchased;
      if (!items.length) { list.innerHTML = '<div class="empty-state">Пока нет купленных материалов</div>'; return; }
      items.forEach((m) => {
        const row = document.createElement("div");
        row.className = "material-row";
        row.innerHTML = '<div class="thumb">📄</div><div><strong>' + m.title + "</strong><span>Отправлен вам в чат с ботом</span></div>";
        list.appendChild(row);
      });
    } else if (State.materialsTab === "free") {
      const items = Materials.data.free;
      items.forEach((a) => {
        const row = document.createElement("div");
        row.className = "material-row";
        row.style.cursor = "pointer";
        row.innerHTML = '<div class="thumb">🆓</div><div><strong>' + a.title + "</strong><span>Бесплатный материал</span></div>";
        row.onclick = () => Materials.openArticle(a.slug, a.title);
        list.appendChild(row);
      });
    } else {
      const items = Materials.data.available_paid;
      if (!items.length) { list.innerHTML = '<div class="empty-state">Все материалы уже у вас 🎉</div>'; return; }
      items.forEach((m) => {
        const row = document.createElement("div");
        row.className = "material-row";
        row.innerHTML = '<div class="thumb">⭐️</div><div><strong>' + m.title + "</strong><span>" + m.price_stars + ' ⭐ — купить в чате с ботом</span></div>';
        list.appendChild(row);
      });
    }
  },
  async openArticle(slug, title) {
    try {
      const article = await api("/articles/" + slug);
      document.getElementById("article-modal-title").textContent = article.title || title;
      document.getElementById("article-modal-content").textContent = article.content;
      document.getElementById("article-modal").classList.add("show");
    } catch (e) {
      UI.toast("Не удалось открыть материал");
    }
  },
};

/* ==================== ПРОФИЛЬ ==================== */

const Profile = {
  fill() {
    if (!State.me) return;
    document.getElementById("p-parent-name").value = State.me.parent_name || "";
    document.getElementById("p-child-name").value = State.me.child_name || "";
    document.getElementById("p-child-age").value = State.me.child_age || "";
    document.getElementById("p-child-gender").value = State.me.child_gender || "";
  },
  async save() {
    try {
      await api("/profile", {
        method: "POST",
        body: JSON.stringify({
          parent_name: document.getElementById("p-parent-name").value,
          child_name: document.getElementById("p-child-name").value,
          child_age: document.getElementById("p-child-age").value,
          child_gender: document.getElementById("p-child-gender").value,
          country: State.selectedCountry ? State.selectedCountry.name : (State.me && State.me.country),
          timezone: State.selectedCountry ? State.selectedCountry.tz_label : (State.me && State.me.timezone),
        }),
      });
      UI.toast("Сохранено!");
      loadMe();
    } catch (e) {
      UI.toast("Не удалось сохранить");
    }
  },
};

/* ==================== КОНСУЛЬТАЦИЯ ==================== */

const Consultation = {
  async send() {
    const textEl = document.getElementById("consultation-text");
    const text = textEl.value.trim();
    if (!text) {
      UI.toast("Напишите сообщение");
      return;
    }
    try {
      await api("/consultation", { method: "POST", body: JSON.stringify({ text }) });
      UI.toast("Отправлено! Я скоро отвечу вам в Telegram");
      textEl.value = "";
      Nav.go("home");
    } catch (e) {
      UI.toast("Не удалось отправить, попробуйте ещё раз");
    }
  },
};

/* ==================== СТАРТ ==================== */

(async function boot() {
  await Booking.loadCountries();
  await loadMe();
})();
