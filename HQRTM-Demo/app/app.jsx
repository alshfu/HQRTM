/* app.jsx — root: routing, shell, live WS simulation, tweaks */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#15b878",
  "theme": "light",
  "view": "comfort",
  "density": "cozy",
  "card": "card",
  "feedFeel": "urgency",
  "lang": "sv",
  "frame": "desktop",
  "sound": false
}/*EDITMODE-END*/;

const ACCENTS = ["#15b878", "#2f74e0", "#7a5cf0", "#e8893a", "#e2566f", "#0fb5c4"];

function luminance(hex) {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.replace(/./g, (c) => c + c) : h, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
}

let _ac = null;
function playBlip(feel) {
  try {
    _ac = _ac || new (window.AudioContext || window.webkitAudioContext)();
    const t0 = _ac.currentTime;
    const o = _ac.createOscillator(), g = _ac.createGain();
    o.type = "sine";
    const f1 = feel === "terminal" ? 880 : feel === "calm" ? 523 : 740;
    o.frequency.setValueAtTime(f1, t0);
    o.frequency.exponentialRampToValueAtTime(f1 * 1.5, t0 + 0.08);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(feel === "calm" ? 0.06 : 0.12, t0 + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.22);
    o.connect(g); g.connect(_ac.destination);
    o.start(t0); o.stop(t0 + 0.24);
  } catch (e) { /* noop */ }
}

/* ---- listing detail modal ---- */
function ListingModal({ l, lang, onClose, onToast }) {
  const L = STRINGS[lang];
  return (
    <Modal title={`${l.street} ${l.streetNo}`} sub={`${l.area} · ${l.city}`} icon="pin" max={520}
           onClose={onClose}
           footer={<>
             <div className="grow" />
             <Btn variant="quiet" onClick={onClose}>{L.cancel}</Btn>
             <Btn variant="primary" iconRight="external" onClick={() => { onToast(lang === "sv" ? "Öppnar på HomeQ…" : "Opening on HomeQ…"); if (l.url) window.open(l.url, "_blank", "noopener"); onClose(); }}>{L.view_to}</Btn>
           </>}>
      <div style={{ height: 170, borderRadius: "var(--r-sm)", overflow: "hidden" }}><Photo label="FOTO · HomeQ" src={l.image} /></div>
      <div className="row gap6 wrap">
        {l.fcfs ? <Badge kind="fcfs" icon="zap">{L.fcfs}</Badge> : <Badge icon="layers">{l.queueDays} {lang === "sv" ? "dagar kö" : "days queue"}</Badge>}
        <Badge icon="pin">{l.area}</Badge>
        <Badge>{l.host}</Badge>
      </div>
      <div className="form-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
        {[[L.f_rent, `${fmtKr(l.rent)}`, L.rent_mo], [L.room, l.rooms, L.room], [L.sqm, l.sqm, "m²"],
          [L.floor, l.floor, ""], [lang === "sv" ? "Inflytt" : "Move-in", l.available, ""], ["Värd", l.host, ""]].map((c, i) => (
          <div key={i} className="stat" style={{ boxShadow: "none" }}>
            <div className="k">{c[0]}</div>
            <div className="v num" style={{ fontSize: 18 }}>{c[1]}{c[2] && <small> {c[2]}</small>}</div>
          </div>
        ))}
      </div>
    </Modal>
  );
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const lang = t.lang;

  const [route, setRoute] = React.useState("landing"); // landing | auth | onboarding | app
  const [authMode, setAuthMode] = React.useState("in");
  const [page, setPage] = React.useState("feed");      // feed | filters | history | settings

  const [filters, setFilters] = React.useState(() => SAMPLE_FILTERS.map((f) => ({ ...f })));
  const [feed, setFeed] = React.useState(() => seedListings(7));
  const [notifications, setNotifications] = React.useState(() => seedNotifications(34));
  const [now, setNow] = React.useState(Date.now());
  const [wsState, setWsState] = React.useState("live"); // live | reconnecting | off
  const [paused, setPaused] = React.useState(false);
  const [tgLinked, setTgLinked] = React.useState(false);
  const [openListing, setOpenListing] = React.useState(null);
  const [toasts, setToasts] = React.useState([]);
  const [role, setRole] = React.useState("user");
  const user = role === "admin"
    ? { name: "Adam Holm", email: "admin@hqrtm.se" }
    : { name: "Elin Bergström", email: "elin@hqrtm.se" };
  const enter = (r) => { setRole(r); setRoute("app"); setPage(r === "admin" ? "admin" : "feed");
    const sc = document.querySelector(".content"); if (sc) sc.scrollTop = 0; };

  const toast = React.useCallback((msg) => {
    const id = Math.random();
    setToasts((ts) => [...ts, { id, msg }]);
    setTimeout(() => setToasts((ts) => ts.filter((x) => x.id !== id)), 2600);
  }, []);

  /* apply tweaks to <html> */
  React.useEffect(() => {
    const r = document.documentElement;
    r.dataset.theme = t.theme;
    r.dataset.view = t.view;
    r.dataset.density = t.density;
    r.dataset.card = t.view === "terminal" ? "ticker" : t.card;
    r.dataset.feed = t.feedFeel;
    r.dataset.frame = window.__HQRTM_FRAME || t.frame;
    r.style.setProperty("--accent", t.accent);
    r.style.setProperty("--accent-ink", luminance(t.accent) > 0.62 ? "#10231a" : "#ffffff");
  }, [t.theme, t.view, t.density, t.card, t.feedFeel, t.frame, t.accent]);

  /* clock tick for "x s ago" */
  React.useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  /* WebSocket simulation — pushes new matches */
  React.useEffect(() => {
    if (route !== "app" || wsState !== "live" || paused) return;
    let timer;
    const schedule = () => {
      const feel = t.feedFeel;
      const span = feel === "calm" ? [6000, 12000] : feel === "terminal" ? [1600, 4200] : [2800, 5600];
      timer = setTimeout(() => {
        const activeF = filters.filter((f) => f.active);
        const f = activeF.length ? pick(activeF) : null;
        const listing = generateListing({
          createdAt: Date.now(),
          fcfs: Math.random() < 0.6,
          filterId: f ? f.id : null,
        });
        setFeed((prev) => [listing, ...prev].slice(0, 40));
        setNotifications((prev) => [{
          id: "N" + Date.now(), listing, channel: tgLinked ? "telegram" : "email",
          status: "delivered", latencyMs: rnd(380, 1600),
          filterName: f ? f.name : (lang === "sv" ? "Alla" : "All"), sentAt: Date.now(),
        }, ...prev]);
        if (t.sound) playBlip(feel);
        schedule();
      }, rnd(span[0], span[1]));
    };
    schedule();
    return () => clearTimeout(timer);
  }, [route, wsState, paused, t.feedFeel, t.sound, filters, tgLinked, lang]);

  /* occasional reconnect blip to show resilience */
  React.useEffect(() => {
    if (route !== "app") return;
    const id = setInterval(() => {
      if (Math.random() < 0.12 && wsState === "live") {
        setWsState("reconnecting");
        setTimeout(() => setWsState("live"), 2200);
      }
    }, 16000);
    return () => clearInterval(id);
  }, [route, wsState]);

  const go = (r, opts = {}) => {
    if (opts.mode) setAuthMode(opts.mode === "up" ? "up" : "in");
    setRoute(r);
    const sc = document.querySelector(".content"); if (sc) sc.scrollTop = 0;
  };
  const navPage = (p) => {
    setPage(p);
    const sc = document.querySelector(".content"); if (sc) sc.scrollTo({ top: 0 });
  };

  /* filters CRUD */
  const saveFilter = (d) => setFilters((prev) => {
    if (d.id) return prev.map((f) => (f.id === d.id ? { ...d } : f));
    return [{ ...d, id: "F" + Date.now(), matches7d: estimateMatches(d) }, ...prev];
  });
  const deleteFilter = (id) => setFilters((prev) => prev.filter((f) => f.id !== id));
  const toggleFilter = (id) => setFilters((prev) => prev.map((f) => (f.id === id ? { ...f, active: !f.active } : f)));

  const L = STRINGS[lang];
  const setLang = (v) => setTweak("lang", v);
  const setTheme = (v) => setTweak("theme", v);

  /* ---------- public routes ---------- */
  if (route === "landing")
    return (<><Landing lang={lang} theme={t.theme} setLang={setLang} setTheme={setTheme} go={go} /><TweaksUI t={t} setTweak={setTweak} /></>);
  if (route === "auth")
    return (<><Auth lang={lang} theme={t.theme} setLang={setLang} setTheme={setTheme} go={go} initialMode={authMode}
      onAuth={(mode, email) => { const r = /^admin/i.test(email || "") ? "admin" : "user";
        if (mode === "up") { setRole("user"); setRoute("onboarding"); } else enter(r); }}
      onDemo={enter} /><TweaksUI t={t} setTweak={setTweak} /></>);
  if (route === "onboarding")
    return (<><Onboarding lang={lang} onFinish={() => { setRoute("app"); setPage("feed"); }}
      onCreateFilter={() => {}} /><TweaksUI t={t} setTweak={setTweak} /></>);

  /* ---------- app shell ---------- */
  const navMain = [
    { id: "feed", label: L.nav_feed, icon: "radar" },
    { id: "filters", label: L.nav_filters, icon: "sliders", count: filters.filter((f) => f.active).length },
  ];
  const navOps = role === "admin" ? [{ id: "admin", label: L.nav_admin, icon: "shield" }] : [];
  const navAcct = [
    { id: "history", label: L.nav_history, icon: "history" },
    { id: "settings", label: L.nav_settings, icon: "gear" },
  ];
  const NAV = [...navMain, ...navOps, ...navAcct];
  const titles = {
    feed: [L.dash_title, L.dash_sub], filters: [L.filters_title, L.filters_sub],
    admin: [L.admin_title, L.admin_sub],
    history: [L.history_title, L.history_sub], settings: [L.settings_title, ""],
  };

  return (
    <div className="app">
      {/* sidebar */}
      <aside className="side">
        <div className="side-brand">
          <div className="brand-mark"><BrandGlyph /><span className="pulse-dot" /></div>
          <div className="brand-name">HQRTM<small>Real-Time Monitor</small></div>
        </div>
        <div className="nav-label">{L.nav_main}</div>
        <nav className="nav">
          {navMain.map((n) => (
            <a key={n.id} className={`nav-item${page === n.id ? " active" : ""}`} onClick={() => navPage(n.id)}>
              <Icon name={n.icon} />{n.label}{n.count != null && <span className="count num">{n.count}</span>}
            </a>
          ))}
        </nav>
        {navOps.length > 0 && (<>
          <div className="nav-label">{L.nav_ops}</div>
          <nav className="nav">
            {navOps.map((n) => (
              <a key={n.id} className={`nav-item${page === n.id ? " active" : ""}`} onClick={() => navPage(n.id)}>
                <Icon name={n.icon} />{n.label}<span className="count num" style={{ background: "var(--amber-soft)", color: "color-mix(in oklab, var(--amber) 75%, var(--text))" }}>admin</span>
              </a>
            ))}
          </nav>
        </>)}
        <div className="nav-label">{L.nav_acct}</div>
        <nav className="nav">
          {navAcct.map((n) => (
            <a key={n.id} className={`nav-item${page === n.id ? " active" : ""}`} onClick={() => navPage(n.id)}>
              <Icon name={n.icon} />{n.label}
            </a>
          ))}
        </nav>
        <div className="side-spacer" />
        <div className="side-foot">
          <div className="userchip" onClick={() => navPage("settings")}>
            <div className="avatar">{user.name.slice(0, 1)}</div>
            <div className="userchip-meta grow"><b>{user.name}</b><span>{role === "admin" ? (lang === "sv" ? "Administratör" : "Administrator") : (tgLinked ? L.tg_linked : L.tg_unlinked)}</span></div>
            <IconBtn name="logout" label="Logga ut" onClick={(e) => { e.stopPropagation(); go("landing"); }} />
          </div>
        </div>
      </aside>

      {/* main column */}
      <div className="main">
        <header className="topbar">
          <div className="only-desktop">
            <h1>{titles[page][0]}</h1>
            {titles[page][1] && <div className="topbar-sub">{titles[page][1]}</div>}
          </div>
          <div className="only-mobile side-brand" style={{ padding: 0 }}>
            <div className="brand-mark" style={{ width: 28, height: 28 }}><BrandGlyph size={15} /></div>
            <div className="brand-name" style={{ fontSize: 14 }}>HQRTM</div>
          </div>
          <div className="topbar-spacer" />

          <span className={`wsdot ${wsState} only-desktop`}>
            <i />{wsState === "live" ? L.connected : wsState === "reconnecting" ? L.reconnecting : L.offline}
          </span>

          <div className="segmented only-desktop">
            <button className={t.view === "comfort" ? "active" : ""} onClick={() => setTweak("view", "comfort")}><Icon name="grid" />{L.comfort}</button>
            <button className={t.view === "terminal" ? "active" : ""} onClick={() => setTweak("view", "terminal")}><Icon name="terminal" />{L.terminal}</button>
          </div>

          <button className="wsdot only-desktop" style={{ cursor: "pointer" }} onClick={() => setLang(lang === "sv" ? "en" : "sv")} title="Language">
            <Icon name="globe" style={{ width: 15, height: 15 }} />{lang === "sv" ? "SV" : "EN"}
          </button>
          <IconBtn name={t.theme === "dark" ? "sun" : "moon"} label="Theme" onClick={() => setTheme(t.theme === "dark" ? "light" : "dark")} />
          <IconBtn name={t.frame === "phone" ? "monitor" : "phone"} label="Preview device" className="only-desktop"
                   onClick={() => setTweak("frame", t.frame === "phone" ? "desktop" : "phone")} />
        </header>

        <div className="content">
          {page === "feed" && (
            <Dashboard lang={lang} feed={feed} now={now} wsState={wsState} paused={paused}
              soundOn={t.sound} setSoundOn={(v) => setTweak("sound", v)}
              filters={filters} onOpenListing={setOpenListing}
              onRetry={() => setWsState("live")} onCreateFilter={() => navPage("filters")} />
          )}
          {page === "filters" && (
            <FiltersScreen lang={lang} filters={filters} onSave={saveFilter} onDelete={deleteFilter} onToggle={toggleFilter} />
          )}
          {page === "history" && (
            <HistoryScreen lang={lang} notifications={notifications} onOpenListing={setOpenListing} />
          )}
          {page === "settings" && (
            <SettingsScreen lang={lang} setLang={setLang} user={user} tgLinked={tgLinked} setTgLinked={setTgLinked}
              onToast={toast} onDeleteAccount={() => { toast(lang === "sv" ? "Konto raderat" : "Account deleted"); go("landing"); }} />
          )}
          {page === "admin" && <AdminScreen lang={lang} />}
        </div>

        {/* mobile tab bar */}
        <nav className="tabbar">
          {NAV.map((n) => (
            <button key={n.id} className={`tab${page === n.id ? " active" : ""}`} onClick={() => navPage(n.id)}>
              <Icon name={n.icon} />{n.label}
              {n.id === "filters" && n.count > 0 && <span className="tab-count num">{n.count}</span>}
            </button>
          ))}
        </nav>
      </div>

      {openListing && <ListingModal l={openListing} lang={lang} onClose={() => setOpenListing(null)} onToast={toast} />}

      {/* toasts */}
      {toasts.length > 0 && (
        <div className="toast-wrap">
          {toasts.map((t2) => (
            <div className="toast" key={t2.id}><span className="ti"><Icon name="check" strokeWidth="3" /></span>{t2.msg}</div>
          ))}
        </div>
      )}

      <TweaksUI t={t} setTweak={setTweak} />
    </div>
  );
}

/* ---- Tweaks panel UI ---- */
function TweaksUI({ t, setTweak }) {
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="Tema & känsla" />
      <TweakRadio label="Personlighet" value={t.view} options={[{ value: "comfort", label: "Comfort" }, { value: "terminal", label: "Terminal" }]} onChange={(v) => setTweak("view", v)} />
      <TweakRadio label="Läge" value={t.theme} options={[{ value: "light", label: "Ljust" }, { value: "dark", label: "Mörkt" }]} onChange={(v) => setTweak("theme", v)} />
      <TweakColor label="Accentfärg" value={t.accent} options={ACCENTS} onChange={(v) => setTweak("accent", v)} />

      <TweakSection label="Flödet" />
      <TweakRadio label="Täthet" value={t.density} options={[{ value: "compact", label: "Tät" }, { value: "cozy", label: "Lagom" }, { value: "spacious", label: "Luftig" }]} onChange={(v) => setTweak("density", v)} />
      <TweakSelect label="Kortstil" value={t.card} options={[{ value: "card", label: "Kort (med foto)" }, { value: "row", label: "Rad (kompakt)" }, { value: "ticker", label: "Ticker (terminal)" }]} onChange={(v) => setTweak("card", v)} />
      <TweakSelect label="Känsla" value={t.feedFeel} options={[{ value: "urgency", label: "Brådska (puls)" }, { value: "calm", label: "Lugnt flöde" }, { value: "terminal", label: "Ticker-tempo" }]} onChange={(v) => setTweak("feedFeel", v)} />
      <TweakToggle label="Ljudsignal" value={t.sound} onChange={(v) => setTweak("sound", v)} />

      <TweakSection label="Övrigt" />
      <TweakRadio label="Språk" value={t.lang} options={[{ value: "sv", label: "Svenska" }, { value: "en", label: "English" }]} onChange={(v) => setTweak("lang", v)} />
      <TweakRadio label="Förhandsvy" value={t.frame} options={[{ value: "desktop", label: "Desktop" }, { value: "phone", label: "Mobil" }]} onChange={(v) => setTweak("frame", v)} />
    </TweaksPanel>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
