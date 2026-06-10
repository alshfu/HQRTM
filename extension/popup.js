/* HQRTM Snabbansök — popup-logik.
 * Loggar in mot HQRTM-API:t, sparar JWT + ansökningsprofil LOKALT (chrome.storage.local),
 * listar matchande annonser och låter användaren öppna dem. Profilen används av content.js
 * för autofyll på annonssidor. Inga plattformslösenord lagras någonstans. */

const API = "https://hqrtm.onrender.com";
const PROFILE_FIELDS = ["presentation", "occupation", "income", "phone", "household", "move_in"];

const $ = (id) => document.getElementById(id);
const store = chrome.storage.local;

function getToken() {
  return new Promise((r) => store.get(["token", "email"], (d) => r(d)));
}

async function api(path, opts = {}) {
  const { token } = await getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API + path, { ...opts, headers });
  let data = null;
  try { data = await resp.json(); } catch (_) {}
  return { ok: resp.ok, status: resp.status, data };
}

/* ---- inloggning ---- */
async function login() {
  $("loginErr").classList.add("hidden");
  const email = $("email").value.trim();
  const password = $("password").value;
  const resp = await fetch(API + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok || !data.access_token) {
    $("loginErr").textContent = "Fel inloggning eller lösenord.";
    $("loginErr").classList.remove("hidden");
    return;
  }
  store.set({ token: data.access_token, email }, showApp);
}

function logout() {
  store.remove(["token", "profile"], showLogin);
}

/* ---- vyer ---- */
function showLogin() {
  $("login").classList.remove("hidden");
  $("app").classList.add("hidden");
}

async function showApp() {
  $("login").classList.add("hidden");
  $("app").classList.remove("hidden");
  const { email } = await getToken();
  $("who").textContent = email || "";
  loadMatches();
  loadProfile();
}

/* ---- matchningar ---- */
function fmtKr(n) { return n == null ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " kr/mån"; }

async function loadMatches() {
  const { ok, status, data } = await api("/api/listings?matched=true&limit=25");
  if (status === 401) return logout();
  const list = $("list");
  if (!ok || !data) { $("matchInfo").textContent = "Kunde inte ladda."; return; }
  $("matchInfo").textContent = `${data.total} matchande objekt`;
  list.innerHTML = "";
  (data.items || []).forEach((it) => {
    const meta = [it.district, it.rooms ? it.rooms + " rum" : null, it.area_m2 ? it.area_m2 + " m²" : null,
      (it.floor != null) ? "vån " + it.floor : null,
      it.has_balcony ? "🌿 balkong" : null, it.has_kitchen ? "🍳 kök" : null,
      it.rent ? fmtKr(it.rent) : null].filter(Boolean).join(" · ");
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<h3>${esc(it.title || "Bostad")}</h3><div class="meta">${esc(meta)} · ${esc(it.source || "")}</div>`;
    const btn = document.createElement("button");
    btn.textContent = "Öppna & ansök →";
    btn.onclick = () => chrome.tabs.create({ url: it.url });
    card.appendChild(btn);
    list.appendChild(card);
  });
}

/* ---- profil ---- */
async function loadProfile() {
  const { ok, data } = await api("/api/profile");
  const profile = ok && data ? data : {};
  store.set({ profile });
  PROFILE_FIELDS.forEach((k) => { const el = $("p_" + k); if (el && profile[k] != null) el.value = profile[k]; });
}

async function saveProfile() {
  const body = {};
  PROFILE_FIELDS.forEach((k) => { body[k] = $("p_" + k).value; });
  const { ok, data } = await api("/api/profile", { method: "PUT", body: JSON.stringify(body) });
  if (ok) { store.set({ profile: data || body }); $("profileMsg").textContent = "Sparad ✓"; }
  else $("profileMsg").textContent = "Kunde inte spara";
  setTimeout(() => ($("profileMsg").textContent = ""), 2500);
}

function esc(s) { const d = document.createElement("div"); d.textContent = String(s == null ? "" : s); return d.innerHTML; }

/* ---- flikar ---- */
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.remove("on"));
  t.classList.add("on");
  const tab = t.dataset.tab;
  $("tab-matches").classList.toggle("hidden", tab !== "matches");
  $("tab-profile").classList.toggle("hidden", tab !== "profile");
}));

$("loginBtn").addEventListener("click", login);
$("logoutBtn").addEventListener("click", logout);
$("saveProfile").addEventListener("click", saveProfile);
$("password").addEventListener("keydown", (e) => { if (e.key === "Enter") login(); });

/* init */
getToken().then((d) => (d.token ? showApp() : showLogin()));
