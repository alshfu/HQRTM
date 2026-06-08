/* HQRTM — klient för REST API (Vanilla JS).
 * Token i localStorage; auto-refresh av access vid 401; rutt-skydd på klienten.
 * Obs: localStorage är sårbart för XSS — flytt till httpOnly cookie är planerad (Fas 8). */

const HQRTM = (() => {
  const AK = "hqrtm_access";
  const RK = "hqrtm_refresh";

  const getAccess = () => localStorage.getItem(AK);
  const getRefresh = () => localStorage.getItem(RK);
  const setTokens = (a, r) => {
    if (a) localStorage.setItem(AK, a);
    if (r) localStorage.setItem(RK, r);
  };
  const clearTokens = () => {
    localStorage.removeItem(AK);
    localStorage.removeItem(RK);
  };
  const isAuthed = () => !!getAccess();

  async function raw(path, { method = "GET", body, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth && getAccess()) headers["Authorization"] = "Bearer " + getAccess();
    return fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  }

  async function tryRefresh() {
    const r = getRefresh();
    if (!r) return false;
    const resp = await raw("/auth/refresh", { method: "POST", body: { refresh_token: r }, auth: false });
    if (!resp.ok) return false;
    const data = await resp.json();
    setTokens(data.access_token, null);
    return true;
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
    if (ok) setTokens(data.access_token, data.refresh_token);
    return { ok, data };
  }

  async function register(email, password) {
    const { ok, data } = await api("/auth/register", { method: "POST", body: { email, password }, auth: false });
    if (ok) setTokens(data.access_token, data.refresh_token);
    return { ok, data };
  }

  function logout() {
    clearTokens();
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
