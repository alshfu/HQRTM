/* HQRTM — клиент REST API (Vanilla JS).
 * Токены в localStorage; авто-refresh access по 401; защита маршрутов на клиенте.
 * Прим.: localStorage уязвим к XSS — переезд на httpOnly cookie запланирован (Фаза 8). */

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

  /* Запрос с авто-refresh. Возвращает {ok, status, data}. */
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

  /* Защита маршрута: если нет токена — на /login. */
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

  return { api, login, register, logout, requireAuth, isAuthed, toast, esc, clearTokens };
})();
