const listEl = document.getElementById("list");
const countEl = document.getElementById("count");
const updatedEl = document.getElementById("updated");
const searchEl = document.getElementById("search");
const tagFilter = document.getElementById("filter-tag");
const resetBtn = document.getElementById("reset");
const saveAllBtn = document.getElementById("save-all");
const template = document.getElementById("memo-card");
const addContent = document.getElementById("add-content");
const addDate = document.getElementById("add-date");
const addTags = document.getElementById("add-tags");
const addMemoBtn = document.getElementById("add-memo");
const syncStatus = document.getElementById("sync-status");

let memos = [];

function formatTime(ts) {
  if (!ts) return "";
  try {
    const date = new Date(ts);
    return date.toLocaleString("zh-TW", { hour12: false });
  } catch {
    return ts;
  }
}

function normalizeTags(raw) {
  if (!raw) return [];
  return raw
    .split(/[,，]/)
    .map((tag) => tag.trim())
    .filter(Boolean)
    .map((tag) => (tag.startsWith("#") ? tag.slice(1) : tag))
    .filter(Boolean);
}

function getTags(memo) {
  const tags = memo.metadata?.tags || [];
  if (Array.isArray(tags)) return tags;
  if (typeof tags === "string") return normalizeTags(tags);
  return [];
}

function buildTagOptions() {
  const tags = new Set();
  memos.forEach((memo) => {
    getTags(memo).forEach((tag) => tags.add(tag));
  });

  tagFilter.querySelectorAll("option:not(:first-child)").forEach((opt) => opt.remove());
  Array.from(tags)
    .sort()
    .forEach((tag) => {
      const opt = document.createElement("option");
      opt.value = tag;
      opt.textContent = `#${tag}`;
      tagFilter.appendChild(opt);
    });
}

function applyFilters() {
  const keyword = searchEl.value.trim().toLowerCase();
  const tag = tagFilter.value;

  const filtered = memos.filter((memo) => {
    const matchesKeyword = !keyword || memo.content?.toLowerCase().includes(keyword);
    const tags = getTags(memo);
    const matchesTag = !tag || tags.includes(tag);
    return matchesKeyword && matchesTag;
  });

  render(filtered);
}

function render(items) {
  listEl.innerHTML = "";
  const fragment = document.createDocumentFragment();

  items.forEach((memo) => {
    const node = template.content.cloneNode(true);
    node.querySelector("[data-id]").textContent = memo.id;
    node.querySelector("[data-time]").textContent = formatTime(memo.timestamp);
    node.querySelector("[data-content]").textContent = memo.content;

    const metaRow = node.querySelector("[data-meta]");
    const meta = memo.metadata || {};
    Object.entries(meta).forEach(([key, value]) => {
      if (key === "tags") return;
      const span = document.createElement("span");
      span.textContent = `${key}: ${value}`;
      metaRow.appendChild(span);
    });

    const dateInput = node.querySelector("[data-date-input]");
    const tagsInput = node.querySelector("[data-tags-input]");
    dateInput.value = memo.metadata?.date || "";
    tagsInput.value = getTags(memo).join(", ");

    node.querySelector("[data-gcal]").addEventListener("click", () => openGoogleCalendar(memo));

    node.querySelector("[data-save]").addEventListener("click", async () => {
      await saveMemoMeta(memo, dateInput.value, tagsInput.value);
    });

    node.querySelector("[data-delete]").addEventListener("click", async () => {
      if (!confirm("確定要刪除這則備忘錄嗎？")) return;
      await fetch(`/api/memos/${memo.id}`, { method: "DELETE" });
      await loadMemos(true);
    });

    fragment.appendChild(node);
  });

  listEl.appendChild(fragment);
  countEl.textContent = items.length;
}

async function loadMemos(showStatus = false) {
  const res = await fetch("/api/memos", { cache: "no-store" });
  const data = await res.json();
  memos = data.memos || [];
  updatedEl.textContent = data.generatedAt || "-";
  buildTagOptions();
  applyFilters();
  if (showStatus) showSyncStatus("更新完成");
}

function showSyncStatus(message) {
  if (!syncStatus) return;
  syncStatus.textContent = message;
  syncStatus.classList.add("show");
  setTimeout(() => syncStatus.classList.remove("show"), 1800);
}

async function saveMemoMeta(memo, rawDate, rawTags) {
  const tags = normalizeTags(rawTags);
  const metadata = { ...(memo.metadata || {}), tags, date: rawDate || "" };
  await fetch(`/api/memos/${memo.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: memo.content, metadata }),
  });
  await loadMemos(true);
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

async function saveAll() {
  const cards = listEl.querySelectorAll(".card");
  const updates = [];

  cards.forEach((card) => {
    const id = Number(card.querySelector("[data-id]").textContent);
    const memo = memos.find((m) => m.id === id);
    const rawTags = card.querySelector("[data-tags-input]").value;
    const rawDate = card.querySelector("[data-date-input]").value;
    if (memo) {
      const metadata = { ...(memo.metadata || {}), tags: normalizeTags(rawTags), date: rawDate || "" };
      updates.push({ memo, metadata });
    }
  });

  for (const update of updates) {
    await fetch(`/api/memos/${update.memo.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: update.memo.content, metadata: update.metadata }),
    });
  }

  await loadMemos();
}

searchEl.addEventListener("input", applyFilters);
tagFilter.addEventListener("change", applyFilters);
resetBtn.addEventListener("click", () => {
  searchEl.value = "";
  tagFilter.value = "";
  applyFilters();
});
async function addMemo() {
  const content = addContent.value.trim();
  if (!content) return;
  const tags = normalizeTags(addTags.value);
  const date = addDate?.value || "";

  await fetch("/api/memos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content,
      metadata: { tags, date },
    }),
  });

  addContent.value = "";
  addTags.value = "";
  if (addDate) addDate.value = "";
  await loadMemos(true);
}

addMemoBtn.addEventListener("click", addMemo);
addContent.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addMemo();
  }
});

saveAllBtn.addEventListener("click", saveAll);

loadMemos();
