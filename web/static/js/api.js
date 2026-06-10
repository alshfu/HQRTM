/* HQRTM — klient för REST API (Vanilla JS).
 * Auth via httpOnly-cookies (sätts av servern; JS kan inte läsa token → skydd mot XSS).
 * Cookies skickas automatiskt (same-origin). I localStorage ligger ENDAST en icke-känslig
 * sessionsflagga för rutt-skyddet på klienten (UX); den verkliga kontrollen sker på servern. */

const HQRTM = (() => {
  const SK = "hqrtm_session"; // UX-flagga (inte en token) — styr klientens redirect till /login

  const isAuthed = () => localStorage.getItem(SK) === "1";
  const markAuthed = () => localStorage.setItem(SK, "1");
  const clearTokens = () => localStorage.removeItem(SK); // namnet behålls för bakåtkompatibilitet

  async function raw(path, { method = "GET", body } = {}) {
    const headers = { "Content-Type": "application/json" };
    // credentials: skicka httpOnly-cookies med varje begäran (same-origin).
    return fetch(path, {
      method,
      headers,
      credentials: "same-origin",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async function tryRefresh() {
    // Refresh-token ligger i httpOnly-cookie → tom body, servern läser cookien.
    const resp = await raw("/auth/refresh", { method: "POST", body: {} });
    return resp.ok;
  }

  /* Begäran med auto-refresh. Returnerar {ok, status, data}. */
  async function api(path, opts = {}) {
    let resp = await raw(path, opts);
    if (resp.status === 401 && opts.auth !== false && (await tryRefresh())) {
      resp = await raw(path, opts);
    }
    let data = null;
    try { data = await resp.json(); } catch (_) {}
    return { ok: resp.ok, status: resp.status, data };
  }

  async function login(email, password) {
    const { ok, data } = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
    if (ok) markAuthed();
    return { ok, data };
  }

  async function register(email, password) {
    const { ok, data } = await api("/auth/register", { method: "POST", body: { email, password }, auth: false });
    if (ok) markAuthed();
    return { ok, data };
  }

  async function logout() {
    clearTokens();
    try { await raw("/auth/logout", { method: "POST" }); } catch (_) {}
    location.href = "/login";
  }

  /* Rutt-skydd: om token saknas — till /login. */
  function requireAuth() {
    if (!isAuthed()) { location.href = "/login"; return false; }
    return true;
  }

  function toast(msg, kind = "info") {
    const box = document.getElementById("toasts");
    if (!box) return alert(msg);
    const el = document.createElement("div");
    const color = kind === "error" ? "#e2563f" : "#15b878";
    el.className = "card px-4 py-3 rounded-xl text-sm shadow-lg";
    el.style.borderColor = color + "55";
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* i18n: katalogen kommer från mallen (window.HQRTM_I18N). Fallback — själva nyckeln.
   * Substitution {var}: HQRTM.t("x.y", {n: 5}). Se web/i18n.py. */
  function t(key, vars) {
    const cat = window.HQRTM_I18N || {};
    let s = cat[key] != null ? cat[key] : key;
    if (vars) for (const k in vars) s = s.replaceAll("{" + k + "}", vars[k]);
    return s;
  }

  return { api, login, register, logout, requireAuth, isAuthed, toast, esc, t, clearTokens };
})();
