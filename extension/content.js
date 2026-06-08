/* HQRTM Snabbansök — content-script på annonssidor (homeq.se / qasa.com / bostad.stockholm.se).
 *
 * Visar en liten panel med din LOKALT sparade ansökningsprofil och hjälper dig att fylla i
 * ansökningsformuläret snabbare: kopiera fält eller fyll presentationen i sidans textfält.
 * Du granskar och skickar SJÄLV — inget skickas automatiskt, inga lösenord hanteras. */

(function () {
  const FIELDS = [
    ["presentation", "Presentation"],
    ["occupation", "Sysselsättning"],
    ["income", "Inkomst (kr)"],
    ["phone", "Telefon"],
    ["household", "Hushåll"],
    ["move_in", "Inflytt"],
  ];

  // Flytande knapp
  const btn = document.createElement("button");
  btn.textContent = "HQRTM";
  Object.assign(btn.style, {
    position: "fixed", right: "16px", bottom: "16px", zIndex: 2147483647,
    background: "#15b878", color: "#04140d", border: "0", borderRadius: "999px",
    padding: "10px 14px", fontWeight: "700", fontFamily: "system-ui,sans-serif",
    cursor: "pointer", boxShadow: "0 6px 20px rgba(0,0,0,.35)",
  });
  document.documentElement.appendChild(btn);

  let panel = null;
  btn.addEventListener("click", () => (panel ? togglePanel() : openPanel()));

  function togglePanel() {
    panel.style.display = panel.style.display === "none" ? "block" : "none";
  }

  function openPanel() {
    chrome.storage.local.get(["profile"], (d) => {
      const p = d.profile || {};
      panel = document.createElement("div");
      Object.assign(panel.style, {
        position: "fixed", right: "16px", bottom: "64px", zIndex: 2147483647, width: "300px",
        background: "#141917", color: "#eef2f0", border: "1px solid #ffffff1a", borderRadius: "12px",
        padding: "12px", fontFamily: "system-ui,sans-serif", fontSize: "13px",
        boxShadow: "0 10px 30px rgba(0,0,0,.5)",
      });
      const hasData = FIELDS.some(([k]) => p[k]);
      let html = '<div style="font-weight:700;margin-bottom:8px">HQRTM Snabbansök</div>';
      if (!hasData) {
        html += '<div style="color:#9aa6a1">Öppna tillägget och fyll i din ansökningsprofil först.</div>';
      } else {
        FIELDS.forEach(([k, label]) => {
          if (!p[k]) return;
          const val = String(p[k]);
          html += `<div style="margin-bottom:7px"><div style="color:#9aa6a1;font-size:11px">${label}</div>
            <div style="display:flex;gap:6px;align-items:flex-start">
              <div style="flex:1;white-space:pre-wrap;word-break:break-word">${esc(val)}</div>
              <button data-copy="${esc(val)}" style="${btnStyle()}">Kopiera</button>
            </div></div>`;
        });
        if (p.presentation) {
          html += `<button id="hqrtm-fill" style="${btnStyle(true)};width:100%;margin-top:6px">Fyll i presentation i formuläret</button>`;
        }
      }
      html += '<div style="color:#9aa6a1;font-size:11px;margin-top:8px">Du granskar och skickar själv.</div>';
      panel.innerHTML = html;
      document.documentElement.appendChild(panel);

      panel.querySelectorAll("[data-copy]").forEach((b) =>
        b.addEventListener("click", () => navigator.clipboard.writeText(b.getAttribute("data-copy")).then(() => flash(b, "Kopierat ✓"))));
      const fill = panel.querySelector("#hqrtm-fill");
      if (fill) fill.addEventListener("click", () => fillPresentation(p.presentation, fill));
    });
  }

  function fillPresentation(text, srcBtn) {
    // Fyll det största synliga textfältet (vanligtvis "meddelande till hyresvärden").
    const areas = [...document.querySelectorAll("textarea")].filter(isVisible);
    const target = areas.sort((a, b) => b.offsetHeight - a.offsetHeight)[0];
    if (!target) { flash(srcBtn, "Hittade inget textfält"); return; }
    target.focus();
    target.value = text;
    target.dispatchEvent(new Event("input", { bubbles: true }));
    target.dispatchEvent(new Event("change", { bubbles: true }));
    flash(srcBtn, "Ifyllt ✓ — granska & skicka");
  }

  function isVisible(el) {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
  }
  function flash(b, msg) { const t = b.textContent; b.textContent = msg; setTimeout(() => (b.textContent = t), 1600); }
  function btnStyle(primary) {
    return `background:${primary ? "#15b878" : "#1f2623"};color:${primary ? "#04140d" : "#eef2f0"};border:0;border-radius:7px;padding:5px 9px;font-weight:600;cursor:pointer;font-size:12px`;
  }
  function esc(s) { const d = document.createElement("div"); d.textContent = String(s == null ? "" : s); return d.innerHTML; }
})();
