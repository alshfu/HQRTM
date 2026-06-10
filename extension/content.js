/* HQRTM Snabbansök — content-script på annonssidor (homeq.se / qasa.com / bostad.stockholm.se).
 *
 * Visar en liten panel med din LOKALT sparade ansökningsprofil och hjälper dig att fylla i
 * ansökningsformuläret snabbare: kopiera fält, fyll presentationen eller fyll HELA formuläret
 * via fältmappning (matchar sidans input/textarea mot dina profilfält).
 * Du granskar och skickar SJÄLV — inget skickas automatiskt, inga lösenord hanteras. */

(function () {
  // Profilfält: [nyckel, etikett, sökord (sv/en) för fältmatchning, inmatningstyp].
  const FIELDS = [
    ["presentation", "Presentation",
      ["presentation", "meddelande", "message", "om dig", "beskriv", "motivering", "brev",
        "hälsning", "till hyresvärd", "till värden", "personligt", "why", "about"], "textarea"],
    ["occupation", "Sysselsättning",
      ["sysselsättning", "yrke", "occupation", "anställning", "arbete", "employment",
        "jobbtitel", "titel", "profession"], "text"],
    ["income", "Inkomst (kr)",
      ["inkomst", "income", "lön", "månadsinkomst", "årsinkomst", "salary", "bruttolön"], "number"],
    ["phone", "Telefon",
      ["telefon", "phone", "mobil", "mobile", "tel", "telefonnummer"], "tel"],
    ["household", "Hushåll",
      ["hushåll", "household", "antal personer", "medsökande", "persons", "people",
        "antal boende", "personer i hushåll"], "text"],
    ["move_in", "Inflytt",
      ["inflytt", "move in", "move-in", "tillträde", "inflyttning", "från datum",
        "startdatum", "önskat inflyttningsdatum"], "date"],
  ];

  // Platsspecifika ledtrådar: CSS-selektorer per fält (komplement till heuristiken).
  // Heuristiken (etikett/namn/placeholder) är primär; selektorerna ger en snabb träff där de stämmer.
  const PLATFORM_HINTS = {
    "homeq.se": {
      presentation: ['textarea[name*="message" i]', 'textarea[id*="message" i]',
        'textarea[name*="presentation" i]'],
      phone: ['input[type="tel"]', 'input[name*="phone" i]'],
    },
    "qasa.com": {
      presentation: ['textarea[name*="message" i]', 'textarea[placeholder*="hyresvärd" i]'],
      phone: ['input[type="tel"]', 'input[name*="phone" i]'],
    },
    "bostad.stockholm.se": {
      phone: ['input[type="tel"]', 'input[name*="telefon" i]'],
    },
  };

  function host() {
    return location.hostname.replace(/^www\./, "");
  }
  function hints(field) {
    const h = PLATFORM_HINTS[host()] || {};
    return h[field] || [];
  }

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
        html += `<button id="hqrtm-fill-all" style="${btnStyle(true)};width:100%;margin-top:6px">Fyll i formuläret</button>`;
        if (p.presentation) {
          html += `<button id="hqrtm-fill" style="${btnStyle()};width:100%;margin-top:6px">Endast presentation</button>`;
        }
      }
      html += '<div style="color:#9aa6a1;font-size:11px;margin-top:8px">Du granskar och skickar själv.</div>';
      panel.innerHTML = html;
      document.documentElement.appendChild(panel);

      panel.querySelectorAll("[data-copy]").forEach((b) =>
        b.addEventListener("click", () => navigator.clipboard.writeText(b.getAttribute("data-copy")).then(() => flash(b, "Kopierat ✓"))));
      const fillAll = panel.querySelector("#hqrtm-fill-all");
      if (fillAll) fillAll.addEventListener("click", () => fillForm(p, fillAll));
      const fill = panel.querySelector("#hqrtm-fill");
      if (fill) fill.addEventListener("click", () => fillPresentation(p.presentation, fill));
    });
  }

  /* ---- fältmappning ---- */

  // Fyll alla profilfält som hittar en matchande inmatning på sidan.
  function fillForm(profile, srcBtn) {
    let filled = 0;
    FIELDS.forEach(([key, , keywords, type]) => {
      const val = profile[key];
      if (val == null || val === "") return;
      const el = findField(key, keywords, type);
      if (el && setValue(el, val, type)) filled += 1;
    });
    flash(srcBtn, filled ? `Fyllde ${filled} fält ✓ — granska & skicka` : "Hittade inga fält");
  }

  // Hitta bästa inmatningsfältet för ett profilfält: platsledtrådar → heuristik (etikett/attribut).
  function findField(key, keywords, type) {
    for (const sel of hints(key)) {
      const el = [...document.querySelectorAll(sel)].find(isVisible);
      if (el) return el;
    }
    const candidates = [...document.querySelectorAll("input, textarea, select")].filter(
      (el) => isVisible(el) && isFillable(el, type)
    );
    let best = null;
    let bestScore = 0;
    for (const el of candidates) {
      const score = scoreField(el, keywords, type);
      if (score > bestScore) {
        bestScore = score;
        best = el;
      }
    }
    return bestScore > 0 ? best : null;
  }

  // Poängsätt hur väl ett fält matchar sökorden (etikett väger tyngst).
  function scoreField(el, keywords, type) {
    const hay = [
      labelText(el), el.name, el.id, el.placeholder,
      el.getAttribute("aria-label"), el.getAttribute("autocomplete"),
    ].map((s) => (s || "").toLowerCase());
    let score = 0;
    keywords.forEach((kw) => {
      const k = kw.toLowerCase();
      if (hay[0].includes(k)) score += 3; // etikett
      if (hay.slice(1).some((h) => h.includes(k))) score += 2; // attribut
    });
    if (score && typeMatches(el, type)) score += 1; // rätt inmatningstyp
    return score;
  }

  // Etikettext för ett fält: <label for=id>, omslutande <label>, eller föregående etikett.
  function labelText(el) {
    let txt = "";
    if (el.id) {
      const lab = document.querySelector(`label[for="${cssEscape(el.id)}"]`);
      if (lab) txt += " " + lab.textContent;
    }
    const wrap = el.closest("label");
    if (wrap) txt += " " + wrap.textContent;
    const prev = el.previousElementSibling;
    if (prev && /label|span|div|p/i.test(prev.tagName)) txt += " " + prev.textContent;
    const aria = el.getAttribute("aria-labelledby");
    if (aria) {
      aria.split(/\s+/).forEach((id) => {
        const n = document.getElementById(id);
        if (n) txt += " " + n.textContent;
      });
    }
    return txt;
  }

  function isFillable(el, type) {
    if (el.disabled || el.readOnly) return false;
    const tag = el.tagName.toLowerCase();
    if (tag === "textarea" || tag === "select") return true;
    const t = (el.type || "text").toLowerCase();
    const allowed = ["text", "tel", "number", "email", "date", "search", "url"];
    // För datumfält accepterar vi även text (vissa sidor använder text + maskering).
    return allowed.includes(t);
  }

  function typeMatches(el, type) {
    const tag = el.tagName.toLowerCase();
    if (type === "textarea") return tag === "textarea";
    if (tag === "textarea") return type === "presentation";
    const t = (el.type || "text").toLowerCase();
    if (type === "number") return t === "number" || t === "text";
    if (type === "tel") return t === "tel" || t === "text";
    if (type === "date") return t === "date" || t === "text";
    return true;
  }

  // Sätt värde + utlös input/change så sidans ramverk (React m.fl.) reagerar.
  function setValue(el, value, type) {
    const tag = el.tagName.toLowerCase();
    let v = String(value);
    if (tag === "select") return setSelect(el, v);
    if ((el.type || "").toLowerCase() === "number") v = v.replace(/[^\d.]/g, "");
    if ((el.type || "").toLowerCase() === "date") v = toIsoDate(v) || v;
    setNativeValue(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  // React skuggar value-settern; använd den native settern så ramverket ser ändringen.
  function setNativeValue(el, value) {
    const proto = el.tagName.toLowerCase() === "textarea"
      ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value");
    el.focus();
    if (setter && setter.set) setter.set.call(el, value);
    else el.value = value;
  }

  function setSelect(el, value) {
    const v = value.toLowerCase();
    const opt = [...el.options].find(
      (o) => o.value.toLowerCase() === v || o.textContent.toLowerCase().includes(v)
    );
    if (!opt) return false;
    el.value = opt.value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function toIsoDate(s) {
    const m = String(s).match(/(\d{4})\D(\d{1,2})\D(\d{1,2})/) // yyyy-mm-dd
      || String(s).match(/(\d{1,2})\D(\d{1,2})\D(\d{4})/); // dd-mm-yyyy
    if (!m) return null;
    const [a, b, c] = m.slice(1);
    const yyyy = a.length === 4 ? a : c;
    const dd = a.length === 4 ? c : a;
    return `${yyyy}-${String(b).padStart(2, "0")}-${String(dd).padStart(2, "0")}`;
  }

  function fillPresentation(text, srcBtn) {
    const el = findField("presentation", FIELDS[0][2], "textarea")
      || [...document.querySelectorAll("textarea")].filter(isVisible)
        .sort((a, b) => b.offsetHeight - a.offsetHeight)[0];
    if (!el) { flash(srcBtn, "Hittade inget textfält"); return; }
    setValue(el, text, "textarea");
    flash(srcBtn, "Ifyllt ✓ — granska & skicka");
  }

  /* ---- hjälpare ---- */
  function isVisible(el) {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
  }
  function flash(b, msg) { const t = b.textContent; b.textContent = msg; setTimeout(() => (b.textContent = t), 1800); }
  function btnStyle(primary) {
    return `background:${primary ? "#15b878" : "#1f2623"};color:${primary ? "#04140d" : "#eef2f0"};border:0;border-radius:7px;padding:5px 9px;font-weight:600;cursor:pointer;font-size:12px`;
  }
  function esc(s) { const d = document.createElement("div"); d.textContent = String(s == null ? "" : s); return d.innerHTML; }
  function cssEscape(s) { return (window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/"/g, '\\"'); }
})();
