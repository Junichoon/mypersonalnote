const listEl = document.getElementById("list");
const countEl = document.getElementById("count");
const updatedEl = document.getElementById("updated");
const searchEl = document.getElementById("search");
const template = document.getElementById("memo-card");
const statusFilter = document.getElementById("filter-status");
const categoryFilter = document.getElementById("filter-category");
const resetBtn = document.getElementById("reset");
const addBtn = document.getElementById("add");
const editor = document.getElementById("editor");
const editorTitle = document.getElementById("editor-title");
const formContent = document.getElementById("form-content");
const formStatus = document.getElementById("form-status");
const formCategory = document.getElementById("form-category");
const formDate = document.getElementById("form-date");
const cancelBtn = document.getElementById("cancel");

let memos = [];
let editingId = null;

function formatTime(ts) {
  if (!ts) return "";
  try {
    const date = new Date(ts);
    return date.toLocaleString("zh-TW", { hour12: false });
  } catch {
    return ts;
  }
}

function getMeta(memo, key) {
  return memo.metadata?.[key] || "";
}

function isCompleted(memo) {
  const meta = memo.metadata || {};
  const status = (meta.status || "").toLowerCase();
  return meta.completed === true || status === "done" || status === "completed" || status === "完成";
}

function applyFilters() {
  const keyword = searchEl.value.trim().toLowerCase();
  const status = statusFilter.value;
  const category = categoryFilter.value;

  const filtered = memos.filter((memo) => {
    const matchesKeyword = !keyword || memo.content?.toLowerCase().includes(keyword);
    const matchesStatus = !status || getMeta(memo, "status") === status;
    const matchesCategory = !category || getMeta(memo, "category") === category;
    return matchesKeyword && matchesStatus && matchesCategory;
  });

  render(filtered);
}

function buildFilterOptions() {
  const statuses = new Set();
  const categories = new Set();

  memos.forEach((memo) => {
    const status = getMeta(memo, "status");
    const category = getMeta(memo, "category");
    if (status) statuses.add(status);
    if (category) categories.add(category);
  });

  statusFilter.querySelectorAll("option:not(:first-child)").forEach((opt) => opt.remove());
  categoryFilter.querySelectorAll("option:not(:first-child)").forEach((opt) => opt.remove());

  Array.from(statuses).sort().forEach((status) => {
    const opt = document.createElement("option");
    opt.value = status;
    opt.textContent = status;
    statusFilter.appendChild(opt);
  });

  Array.from(categories).sort().forEach((category) => {
    const opt = document.createElement("option");
    opt.value = category;
    opt.textContent = category;
    categoryFilter.appendChild(opt);
  });
}

function render(items) {
  listEl.innerHTML = "";
  const fragment = document.createDocumentFragment();

  items.forEach((memo) => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".card");
    const completed = isCompleted(memo);
    if (completed) card.classList.add("completed");

    node.querySelector("[data-id]").textContent = memo.id;
    node.querySelector("[data-time]").textContent = formatTime(memo.timestamp);
    node.querySelector("[data-content]").textContent = memo.content;

    const metaRow = node.querySelector("[data-meta]");
    const meta = memo.metadata || {};
    Object.entries(meta).forEach(([key, value]) => {
      const span = document.createElement("span");
      span.textContent = `${key}: ${value}`;
      metaRow.appendChild(span);
    });

    const checkbox = node.querySelector("[data-check]");
    checkbox.checked = completed;
    checkbox.addEventListener("change", () => toggleCompleted(memo, checkbox.checked));

    node.querySelector("[data-gcal]").addEventListener("click", () => openGoogleCalendar(memo));
    node.querySelector("[data-edit]").addEventListener("click", () => openEditor(memo));
    node.querySelector("[data-delete]").addEventListener("click", () => deleteMemo(memo.id));

    fragment.appendChild(node);
  });

  listEl.appendChild(fragment);
  countEl.textContent = items.length;
}

async function loadMemos() {
  const res = await fetch("/api/memos", { cache: "no-store" });
  const data = await res.json();
  memos = data.memos || [];
  updatedEl.textContent = data.generatedAt || "-";
  buildFilterOptions();
  applyFilters();
}

function openEditor(memo = null) {
  editingId = memo?.id ?? null;
  editorTitle.textContent = editingId === null ? "新增備忘錄" : `編輯備忘錄 #${memo.id}`;
  formContent.value = memo?.content || "";
  formStatus.value = getMeta(memo || {}, "status");
  formCategory.value = getMeta(memo || {}, "category");
  formDate.value = getMeta(memo || {}, "date");
  editor.showModal();
}

async function saveMemo(event) {
  event.preventDefault();
  const payload = {
    content: formContent.value.trim(),
    metadata: {
      status: formStatus.value.trim(),
      category: formCategory.value.trim(),
      date: formDate.value || "",
    },
  };

  if (!payload.content) return;

  if (editingId === null) {
    await fetch("/api/memos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } else {
    await fetch(`/api/memos/${editingId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  editor.close();
  await loadMemos();
}

async function toggleCompleted(memo, checked) {
  const meta = { ...(memo.metadata || {}) };
  meta.completed = checked;
  if (checked && (!meta.status || meta.status === "pending")) {
    meta.status = "done";
  }
  if (!checked && meta.status === "done") {
    meta.status = "pending";
  }
  await fetch(`/api/memos/${memo.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: memo.content, metadata: meta }),
  });
  await loadMemos();
}

function buildCalendarUrl(memo) {
  const title = encodeURIComponent(memo.content || "");
  const date = memo.metadata?.date;
  let dates = "";
  if (date) {
    const compact = date.replaceAll("-", "");
    dates = `&dates=${compact}/${compact}`;
  }
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}${dates}`;
}

function openGoogleCalendar(memo) {
  const url = buildCalendarUrl(memo);
  window.open(url, "_blank", "noopener");
}

async function deleteMemo(id) {
  if (!confirm("確定要刪除這則備忘錄嗎？")) return;
  await fetch(`/api/memos/${id}`, { method: "DELETE" });
  await loadMemos();
}

searchEl.addEventListener("input", applyFilters);
statusFilter.addEventListener("change", applyFilters);
categoryFilter.addEventListener("change", applyFilters);
resetBtn.addEventListener("click", () => {
  searchEl.value = "";
  statusFilter.value = "";
  categoryFilter.value = "";
  applyFilters();
});
addBtn.addEventListener("click", () => openEditor());
editor.addEventListener("submit", saveMemo);
cancelBtn.addEventListener("click", () => editor.close());

loadMemos();
