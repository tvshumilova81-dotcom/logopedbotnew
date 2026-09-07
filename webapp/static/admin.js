/* global Telegram */
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.setHeaderColor) { try { tg.setHeaderColor("#f2718f"); } catch (e) {} }
  if (tg.setBackgroundColor) { try { tg.setBackgroundColor("#fdf1ef"); } catch (e) {} }
}

const API_BASE = "/api/miniapp";

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
  return res.json();
}

const State = {
  cal: { year: new Date().getFullYear(), month: new Date().getMonth() + 1 },
  selectedDate: null,
};

const AdminNav = {
  go(screen) {
    document.querySelectorAll("#admin-content .screen").forEach((s) => s.classList.remove("active"));
    document.getElementById("screen-" + screen).classList.add("active");
    document.querySelectorAll("#admin-nav .nav-btn").forEach((b) => b.classList.remove("active"));
    const navBtn = document.querySelector('#admin-nav .nav-btn[data-tab="' + screen + '"]');
    if (navBtn) navBtn.classList.add("active");
    else {
      const fallback = document.querySelector('#admin-nav .nav-btn[data-tab="clients"]');
      if (fallback) fallback.classList.add("active");
    }
    if (screen === "income") Income.load();
    if (screen === "clients") Clients.load();
  },
};

const MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function formatDateHuman(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

const AdminCal = {
  async render() {
    const { year, month } = State.cal;
    document.getElementById("a-cal-month-label").textContent = MONTHS_RU[month - 1] + " " + year;

    let data;
    try {
      data = await api("/admin/calendar?year=" + year + "&month=" + month);
    } catch (e) {
      return;
    }

    const grid = document.getElementById("a-cal-grid");
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
    for (let i = 0; i < firstWeekday; i++) grid.appendChild(document.createElement("div"));

    data.days.forEach((d) => {
      const cell = document.createElement("div");
      const dayNum = parseInt(d.date.slice(-2), 10);
      const hasAny = d.free + d.booked + d.blocked > 0;
      cell.className = "day-cell" + (d.date === State.selectedDate ? " selected" : "") + (!hasAny ? " disabled" : "");
      let marker = "";
      if (d.booked > 0) marker = '<span class="dot" style="background:' + (d.date === State.selectedDate ? '#fff' : 'var(--primary)') + '"></span>';
      cell.innerHTML = dayNum + marker;
      cell.onclick = () => AdminCal.selectDay(d.date);
      grid.appendChild(cell);
    });
  },
  prevMonth() {
    let { year, month } = State.cal;
    month -= 1; if (month < 1) { month = 12; year -= 1; }
    State.cal = { year, month };
    AdminCal.render();
  },
  nextMonth() {
    let { year, month } = State.cal;
    month += 1; if (month > 12) { month = 1; year += 1; }
    State.cal = { year, month };
    AdminCal.render();
  },
  async selectDay(dateStr) {
    State.selectedDate = dateStr;
    AdminCal.render();

    const card = document.getElementById("a-day-card");
    card.style.display = "block";
    document.getElementById("a-day-title").textContent = formatDateHuman(dateStr);
    const wrap = document.getElementById("a-day-slots");
    wrap.innerHTML = '<div class="loader">Загрузка…</div>';

    let slots;
    try {
      slots = await api("/admin/slots?date=" + dateStr);
    } catch (e) {
      wrap.innerHTML = '<div class="empty-state">Не удалось загрузить</div>';
      return;
    }

    if (!slots.length) {
      wrap.innerHTML = '<div class="empty-state">На этот день нет слотов в расписании (выходной)</div>';
      return;
    }

    wrap.innerHTML = "";
    slots.forEach((s) => {
      const row = document.createElement("div");
      row.className = "slot-admin-row " + s.status;
      let info = "Свободно";
      if (s.status === "booked" && s.booking) {
        info = (s.booking.topic || "Занятие") + (s.booking.country ? " · " + s.booking.country : "");
      } else if (s.status === "blocked") {
        info = "Закрыто вами";
      }
      row.innerHTML = '<div class="time">' + s.time + '</div><div class="info">' + info + "</div>";

      if (s.status === "booked") {
        const btn = document.createElement("button");
        btn.className = "btn btn-ghost btn-sm";
        btn.textContent = "Отменить";
        btn.onclick = (ev) => { ev.stopPropagation(); AdminCal.cancelBooking(s.booking.id, dateStr); };
        row.appendChild(btn);
      } else {
        row.style.cursor = "pointer";
        row.onclick = () => AdminCal.toggle(dateStr, s.time);

        const delBtn = document.createElement("button");
        delBtn.className = "btn btn-ghost btn-sm";
        delBtn.textContent = "✕";
        delBtn.title = "Удалить это время из расписания";
        delBtn.onclick = (ev) => { ev.stopPropagation(); AdminCal.deleteSlot(dateStr, s.time); };
        row.appendChild(delBtn);
      }
      wrap.appendChild(row);
    });
  },
  async toggle(dateStr, timeStr) {
    try {
      await api("/admin/toggle", { method: "POST", body: JSON.stringify({ date: dateStr, time: timeStr }) });
      AdminCal.selectDay(dateStr);
      AdminCal.render();
    } catch (e) {
      alert("Не удалось изменить слот");
    }
  },
  async addSlot() {
    if (!State.selectedDate) return;
    const input = document.getElementById("a-new-time");
    const timeStr = input.value;
    if (!timeStr) { alert("Укажите время"); return; }
    try {
      await api("/admin/slots/add", { method: "POST", body: JSON.stringify({ date: State.selectedDate, time: timeStr }) });
      input.value = "";
      AdminCal.selectDay(State.selectedDate);
      AdminCal.render();
    } catch (e) {
      alert(e.status === 409 ? "Такое время уже есть в расписании" : "Не удалось добавить время");
    }
  },
  async deleteSlot(dateStr, timeStr) {
    if (!confirm("Удалить это время из расписания совсем?")) return;
    try {
      await api("/admin/slots/delete", { method: "POST", body: JSON.stringify({ date: dateStr, time: timeStr }) });
      AdminCal.selectDay(dateStr);
      AdminCal.render();
    } catch (e) {
      alert("Не удалось удалить (возможно, время уже занято клиентом)");
    }
  },
  async cancelBooking(bookingId, dateStr) {
    if (!confirm("Отменить эту запись клиента?")) return;
    try {
      await api("/admin/cancel_booking", { method: "POST", body: JSON.stringify({ booking_id: bookingId }) });
      AdminCal.selectDay(dateStr);
      AdminCal.render();
    } catch (e) {
      alert("Не удалось отменить запись");
    }
  },
};

const Income = {
  async load() {
    let data;
    try {
      data = await api("/admin/income");
    } catch (e) {
      return;
    }
    document.getElementById("income-amount").textContent = data.total.toLocaleString("ru-RU") + " ₽";

    const list = document.getElementById("adjustments-list");
    if (!data.adjustments.length) {
      list.innerHTML = '<div class="empty-state">Пока нет корректировок</div>';
      return;
    }
    list.innerHTML = "";
    data.adjustments.forEach((a) => {
      const row = document.createElement("div");
      row.className = "booking-row";
      const sign = a.amount >= 0 ? "+" : "";
      row.innerHTML =
        '<div class="top"><span class="dt">' + sign + a.amount.toLocaleString("ru-RU") + " ₽</span></div>" +
        '<div class="topic">' + (a.comment || "без комментария") + "</div>";
      list.appendChild(row);
    });
  },
  async addAdjustment() {
    const amountInput = document.getElementById("adj-amount");
    const commentInput = document.getElementById("adj-comment");
    const amount = parseInt(amountInput.value, 10);
    if (!amount) { alert("Укажите сумму"); return; }
    try {
      await api("/admin/income/adjust", {
        method: "POST",
        body: JSON.stringify({ amount, comment: commentInput.value || null }),
      });
      amountInput.value = "";
      commentInput.value = "";
      Income.load();
    } catch (e) {
      alert("Не удалось добавить корректировку");
    }
  },
};

const Clients = {
  list: [],
  current: null,
  async load() {
    const list = document.getElementById("clients-list");
    list.innerHTML = '<div class="loader">Загрузка…</div>';
    try {
      Clients.list = await api("/admin/clients");
    } catch (e) {
      list.innerHTML = '<div class="empty-state">Не удалось загрузить клиентов</div>';
      return;
    }
    Clients.render(Clients.list);
  },
  render(items) {
    const list = document.getElementById("clients-list");
    if (!items.length) {
      list.innerHTML = '<div class="empty-state">Клиентов пока нет</div>';
      return;
    }
    list.innerHTML = "";
    items.forEach((c) => {
      const row = document.createElement("div");
      row.className = "action-item";
      row.innerHTML =
        '<div class="icon pink"><img class="icon-img" src="/webapp/static/images/icons/icon-avatar-woman.png" alt="" /></div>' +
        '<div class="body"><strong>' + (c.parent_name || c.display_name) + '</strong><span>' + (c.child_name ? "Ребёнок: " + c.child_name + (c.child_age ? ", " + c.child_age : "") : "Профиль не заполнен") + "</span></div>" +
        '<div class="arrow">›</div>';
      row.onclick = () => Clients.openClient(c);
      list.appendChild(row);
    });
  },
  search() {
    const q = document.getElementById("client-search").value.toLowerCase();
    Clients.render(
      Clients.list.filter((c) =>
        ((c.parent_name || "") + (c.child_name || "") + (c.username || "")).toLowerCase().includes(q)
      )
    );
  },
  openClient(client) {
    Clients.current = client;
    document.getElementById("client-detail-title").textContent = client.parent_name || client.display_name;
    document.getElementById("pn-title").value = "";
    document.getElementById("pn-before").value = "";
    document.getElementById("pn-after").value = "";
    document.getElementById("pn-note").value = "";
    document.getElementById("hw-text").value = "";
    AdminNav.go("client-detail");
    Clients.loadDetail();
  },
  async loadDetail() {
    const list = document.getElementById("client-detail-list");
    list.innerHTML = '<div class="loader">Загрузка…</div>';
    let data;
    try {
      data = await api("/admin/clients/" + Clients.current.id + "/progress");
    } catch (e) {
      list.innerHTML = '<div class="empty-state">Не удалось загрузить</div>';
      return;
    }
    list.innerHTML = "";
    if (!data.notes.length && !data.homework.length) {
      list.innerHTML = '<div class="empty-state">Пока нет записей о прогрессе и заданий</div>';
      return;
    }
    data.notes.forEach((n) => {
      const card = document.createElement("div");
      card.className = "card progress-card";
      card.innerHTML =
        '<div class="progress-title">📈 ' + n.title + "</div>" +
        (n.before_text || n.after_text
          ? '<div class="before-after"><div class="ba-col"><div class="ba-lbl">Было</div><div class="ba-val">' + (n.before_text || "—") + '</div></div><div class="ba-arrow">→</div><div class="ba-col"><div class="ba-lbl">Стало</div><div class="ba-val good">' + (n.after_text || "—") + "</div></div></div>"
          : "") +
        (n.note ? '<div class="progress-note">' + n.note + "</div>" : "");
      list.appendChild(card);
    });
    data.homework.forEach((h) => {
      const row = document.createElement("div");
      row.className = "homework-row" + (h.is_done ? " done" : "");
      row.style.cursor = "default";
      row.innerHTML = '<div class="hw-check">' + (h.is_done ? "✓" : "") + '</div><div class="hw-text">📝 ' + h.text + "</div>";
      list.appendChild(row);
    });
  },
  async addProgress() {
    if (!Clients.current) return;
    const title = document.getElementById("pn-title").value.trim();
    if (!title) { alert("Укажите название"); return; }
    try {
      await api("/admin/progress/add", {
        method: "POST",
        body: JSON.stringify({
          user_id: Clients.current.id,
          title,
          before_text: document.getElementById("pn-before").value || null,
          after_text: document.getElementById("pn-after").value || null,
          note: document.getElementById("pn-note").value || null,
        }),
      });
      document.getElementById("pn-title").value = "";
      document.getElementById("pn-before").value = "";
      document.getElementById("pn-after").value = "";
      document.getElementById("pn-note").value = "";
      Clients.loadDetail();
    } catch (e) {
      alert("Не удалось добавить запись");
    }
  },
  async addHomework() {
    if (!Clients.current) return;
    const text = document.getElementById("hw-text").value.trim();
    if (!text) { alert("Введите текст задания"); return; }
    try {
      await api("/admin/homework/add", {
        method: "POST",
        body: JSON.stringify({ user_id: Clients.current.id, text }),
      });
      document.getElementById("hw-text").value = "";
      Clients.loadDetail();
    } catch (e) {
      alert("Не удалось отправить задание");
    }
  },
};

(async function boot() {
  try {
    const check = await api("/admin/check");
    if (!check.is_admin) throw new Error("not admin");
    document.getElementById("admin-content").style.display = "block";
    document.getElementById("admin-nav").style.display = "flex";
    AdminCal.render();
  } catch (e) {
    document.getElementById("access-denied").style.display = "block";
  }
})();
