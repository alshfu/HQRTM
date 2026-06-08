/* HQRTM Snabbansök — service worker. Uppdaterar ikonens badge med antal matchande objekt
 * (periodiskt via alarms) så användaren ser nya träffar utan att öppna appen. Endast läsning. */

const API = "https://hqrtm.onrender.com";

async function refreshBadge() {
  const { token } = await chrome.storage.local.get(["token"]);
  if (!token) {
    chrome.action.setBadgeText({ text: "" });
    return;
  }
  try {
    const resp = await fetch(API + "/api/listings?matched=true&limit=1", {
      headers: { Authorization: "Bearer " + token },
    });
    if (resp.status === 401) {
      chrome.action.setBadgeText({ text: "" });
      return;
    }
    const data = await resp.json();
    const n = data.total || 0;
    chrome.action.setBadgeBackgroundColor({ color: "#15b878" });
    chrome.action.setBadgeText({ text: n ? String(Math.min(n, 999)) : "" });
  } catch (_) {
    /* nät av — behåll föregående badge */
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("refresh", { periodInMinutes: 10 });
  refreshBadge();
});
chrome.runtime.onStartup.addListener(refreshBadge);
chrome.alarms.onAlarm.addListener((a) => a.name === "refresh" && refreshBadge());
chrome.storage.onChanged.addListener((c) => c.token && refreshBadge());
