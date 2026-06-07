/* screens-app.jsx — Filter form, Filters screen, Dashboard / live feed */

const CITIES = ["Stockholm", "Göteborg", "Malmö", "Uppsala"];
function defaultFilter() {
  return { id: null, name: "", city: "Stockholm", areas: [], rentMin: 5000, rentMax: 14000,
    roomsMin: 1, roomsMax: 3, sqmMin: 30, sqmMax: 90, fcfsOnly: true, active: true };
}
function estimateMatches(f) {
  const areaW = (f.areas.length || 3) * 2.4;
  const rentW = Math.max(0, (f.rentMax - f.rentMin)) / 1400;
  const roomW = (f.roomsMax - f.roomsMin + 1) * 1.3;
  const fcfsW = f.fcfsOnly ? 0.55 : 1;
  return Math.max(1, Math.round((areaW + rentW + roomW) * fcfsW));
}

/* the reusable filter form body (used in modal + onboarding) */
function FilterFormBody({ lang, value, onChange, embedded }) {
  const L = STRINGS[lang];
  const f = value;
  const set = (patch) => onChange({ ...f, ...patch });
  const areaOptions = AREAS.filter((a) => a.city === f.city).map((a) => a.area);
  const toggleArea = (a) => set({ areas: f.areas.includes(a) ? f.areas.filter((x) => x !== a) : [...f.areas, a] });
  const numFix = (k, v, partner, dir) => {
    const n = Number(v) || 0;
    const patch = { [k]: n };
    if (dir === "min" && n > f[partner]) patch[partner] = n;
    if (dir === "max" && n < f[partner]) patch[partner] = n;
    set(patch);
  };
  const est = estimateMatches(f);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {!embedded && (
        <Field label={L.filter_name}>
          <input className="input" placeholder={lang === "sv" ? "t.ex. Söder · 2:a" : "e.g. Söder · 2 rooms"}
                 value={f.name} onChange={(e) => set({ name: e.target.value })} />
        </Field>
      )}
      <div className="form-grid">
        <Field label={L.f_city}>
          <select className="select" value={f.city} onChange={(e) => set({ city: e.target.value, areas: [] })}>
            {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label={L.f_rooms}>
          <div className="range-pair">
            <select className="select" value={f.roomsMin} onChange={(e) => numFix("roomsMin", e.target.value, "roomsMax", "min")}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
            <span className="sep">–</span>
            <select className="select" value={f.roomsMax} onChange={(e) => numFix("roomsMax", e.target.value, "roomsMin", "max")}>
              {[1, 2, 3, 4, 5, 6].map((n) => <option key={n} value={n}>{n}+</option>)}
            </select>
          </div>
        </Field>
      </div>

      <Field label={L.f_areas} hint={`${f.areas.length || L.all}`}>
        <div className="chips">
          {areaOptions.map((a) => (
            <button type="button" key={a} className={`chip${f.areas.includes(a) ? " on" : ""}`} onClick={() => toggleArea(a)}>
              {f.areas.includes(a) && <Icon name="check" strokeWidth="2.6" />}{a}
            </button>
          ))}
        </div>
      </Field>

      <div className="form-grid">
        <Field label={L.f_rent}>
          <div className="range-pair">
            <div className="input-group">
              <input className="input" type="number" step="500" value={f.rentMin} onChange={(e) => numFix("rentMin", e.target.value, "rentMax", "min")} />
            </div>
            <span className="sep">–</span>
            <div className="input-group">
              <input className="input" type="number" step="500" value={f.rentMax} onChange={(e) => numFix("rentMax", e.target.value, "rentMin", "max")} />
            </div>
          </div>
        </Field>
        <Field label={L.f_sqm}>
          <div className="range-pair">
            <input className="input" type="number" step="5" value={f.sqmMin} onChange={(e) => numFix("sqmMin", e.target.value, "sqmMax", "min")} />
            <span className="sep">–</span>
            <input className="input" type="number" step="5" value={f.sqmMax} onChange={(e) => numFix("sqmMax", e.target.value, "sqmMin", "max")} />
          </div>
        </Field>
      </div>

      <div className="setting-row" style={{ borderBottom: 0, padding: "4px 0" }}>
        <div className="filter-ico" style={{ width: 38, height: 38 }}><Icon name="zap" /></div>
        <div className="sr-meta">
          <b>{L.f_fcfs_only}</b>
          <span>{L.f_fcfs_hint}</span>
        </div>
        <Switch on={f.fcfsOnly} onChange={(v) => set({ fcfsOnly: v })} label={L.f_fcfs_only} />
      </div>

      <div className="row gap10" style={{ background: "var(--accent-soft)", border: "1px solid var(--accent-line)", borderRadius: "var(--r-sm)", padding: "11px 14px" }}>
        <Icon name="eye" style={{ width: 18, height: 18, color: "var(--accent-dim)" }} />
        <div style={{ fontSize: 13.5 }}>
          <b className="num" style={{ color: "var(--accent-dim)", fontSize: 16 }}>≈ {est}</b>{" "}
          <span style={{ color: "var(--text-2)" }}>{L.would_match}</span>{" · "}
          <span className="muted num">{Math.round(est * 1.6)} {L.per_week}</span>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- Filters */
function FiltersScreen({ lang, filters, onSave, onDelete, onToggle }) {
  const L = STRINGS[lang];
  const [editing, setEditing] = React.useState(null); // filter object or null
  const [draft, setDraft] = React.useState(null);
  const [confirmDel, setConfirmDel] = React.useState(null);

  const openNew = () => { const d = defaultFilter(); setDraft(d); setEditing("new"); };
  const openEdit = (f) => { setDraft({ ...f }); setEditing(f.id); };
  const save = () => {
    const d = { ...draft };
    if (!d.name.trim()) d.name = d.areas[0] || d.city;
    onSave(d);
    setEditing(null); setDraft(null);
  };

  return (
    <div className="page">
      <div className="row page-head" style={{ alignItems: "flex-end" }}>
        <div className="grow">
          <h2>{L.filters_title}</h2>
          <p>{L.filters_sub}</p>
        </div>
        <Btn variant="primary" icon="plus" onClick={openNew}>{L.new_filter}</Btn>
      </div>

      {filters.length === 0 ? (
        <div className="panel"><EmptyState icon="sliders" title={L.no_filters_t} text={L.no_filters_p}
          action={<Btn variant="primary" icon="plus" onClick={openNew}>{L.new_filter}</Btn>} /></div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filters.map((f) => (
            <div className={`filter-card${f.active ? "" : " off"}`} key={f.id}>
              <div className="filter-ico"><Icon name={f.fcfsOnly ? "zap" : "layers"} /></div>
              <div className="filter-meta">
                <h4>{f.name}
                  {f.active ? <Badge kind="fcfs" icon="dot">{L.active}</Badge> : <Badge icon="dot">{L.paused}</Badge>}
                </h4>
                <div className="filter-crit">
                  <span className="crit"><Icon name="pin" />{f.areas.length ? f.areas.join(", ") : f.city}</span>
                  <span className="crit"><Icon name="coins" />{fmtKr(f.rentMin)}–{fmtKr(f.rentMax)}</span>
                  <span className="crit"><Icon name="bed" />{f.roomsMin}–{f.roomsMax} {L.room}</span>
                  <span className="crit"><Icon name="ruler" />{f.sqmMin}–{f.sqmMax} {L.sqm}</span>
                  {f.fcfsOnly && <span className="crit" style={{ color: "var(--accent-dim)" }}><Icon name="zap" />{L.fcfs_short}</span>}
                </div>
              </div>
              <div className="filter-stat only-desktop">
                <div className="n num">{f.matches7d ?? estimateMatches(f)}</div>
                <div className="l">{lang === "sv" ? "träffar / 7 d" : "matches / 7d"}</div>
              </div>
              <div className="filter-actions">
                <Switch on={f.active} onChange={() => onToggle(f.id)} label={L.active} />
                <IconBtn name="edit" label={L.edit} onClick={() => openEdit(f)} />
                <IconBtn name="trash" label={L.delete} onClick={() => setConfirmDel(f)} />
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && draft && (
        <Modal title={editing === "new" ? L.new_filter : L.edit_filter} icon="sliders"
               onClose={() => { setEditing(null); setDraft(null); }}
               footer={<>
                 <div className="grow" />
                 <Btn variant="quiet" onClick={() => { setEditing(null); setDraft(null); }}>{L.cancel}</Btn>
                 <Btn variant="primary" icon="check" onClick={save}>{editing === "new" ? L.create : L.save}</Btn>
               </>}>
          <FilterFormBody lang={lang} value={draft} onChange={setDraft} />
        </Modal>
      )}

      {confirmDel && (
        <Modal title={L.delete_filter_q} icon="trash" max={440}
               onClose={() => setConfirmDel(null)}
               footer={<>
                 <div className="grow" />
                 <Btn variant="quiet" onClick={() => setConfirmDel(null)}>{L.cancel}</Btn>
                 <Btn variant="danger" icon="trash" onClick={() => { onDelete(confirmDel.id); setConfirmDel(null); }}>{L.delete}</Btn>
               </>}>
          <p className="muted">{L.delete_filter_p}</p>
          <div className="filter-card" style={{ boxShadow: "none" }}>
            <div className="filter-ico"><Icon name="layers" /></div>
            <div className="filter-meta"><h4>{confirmDel.name}</h4>
              <div className="filter-crit"><span className="crit"><Icon name="pin" />{confirmDel.areas.join(", ") || confirmDel.city}</span></div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

/* -------------------------------------------------------------- Dashboard */
function Dashboard({ lang, feed, now, wsState, paused, soundOn, setSoundOn,
                    filters, onOpenListing, onRetry, onCreateFilter, contentSel = ".content" }) {
  const L = STRINGS[lang];
  const [q, setQ] = React.useState("");
  const [fcfsOnly, setFcfsOnly] = React.useState(false);
  const [unseen, setUnseen] = React.useState(0);
  const prevLen = React.useRef(feed.length);

  const activeFilters = filters.filter((f) => f.active).length;

  const filtered = React.useMemo(() => feed.filter((l) => {
    if (fcfsOnly && !l.fcfs) return false;
    if (q) {
      const s = (l.street + " " + l.area + " " + l.city).toLowerCase();
      if (!s.includes(q.toLowerCase())) return false;
    }
    return true;
  }), [feed, q, fcfsOnly]);

  // track unseen when new items arrive and user has scrolled down
  React.useEffect(() => {
    const scroller = document.querySelector(contentSel);
    if (feed.length > prevLen.current) {
      const delta = feed.length - prevLen.current;
      if (scroller && scroller.scrollTop > 260) setUnseen((u) => u + delta);
    }
    prevLen.current = feed.length;
  }, [feed.length, contentSel]);

  const scrollTop = () => {
    const scroller = document.querySelector(contentSel);
    if (scroller) scroller.scrollTo({ top: 0, behavior: "smooth" });
    setUnseen(0);
  };

  const todayCount = feed.filter((l) => now - l.createdAt < 86400000).length + 18;

  return (
    <div className="page page-wide" style={{ maxWidth: 1180 }}>
      {/* stat tiles */}
      <div className="stats">
        <div className="stat">
          <div className="k"><Icon name="bolt" />{L.stat_today}</div>
          <div className="v num">{todayCount}</div>
          <div className="d up"><Icon name="trend" />+12% </div>
          <Spark />
        </div>
        <div className="stat">
          <div className="k"><Icon name="layers" />{L.stat_active_filters}</div>
          <div className="v num">{activeFilters}<small> / {filters.length}</small></div>
          <div className="d up"><Icon name="checkcircle" style={{ width: 13, height: 13 }} />{L.connected}</div>
        </div>
        <div className="stat">
          <div className="k"><Icon name="clock" />{L.stat_avg_latency}</div>
          <div className="v num">0.9<small> s</small></div>
          <div className="d up"><Icon name="arrowup" style={{ width: 13, height: 13, transform: "rotate(180deg)" }} />-0.2s</div>
          <Spark points={[9, 7, 8, 6, 5, 6, 4, 4]} />
        </div>
        <div className="stat">
          <div className="k"><Icon name="flame" />{L.stat_fastest}</div>
          <div className="v num">0.4<small> s</small></div>
          <div className="d"><span className="muted" style={{ fontWeight: 600 }}>{lang === "sv" ? "Södermalm · FCFS" : "Södermalm · FCFS"}</span></div>
        </div>
      </div>

      {/* feed header */}
      <div className="row" style={{ marginBottom: 14, alignItems: "flex-end" }}>
        <div className="grow">
          <div className="section-title" style={{ marginBottom: 4 }}><Icon name="radar" style={{ width: 14, height: 14 }} />{L.live_feed}</div>
          <p className="muted" style={{ fontSize: 13.5 }}>{L.feed_sub}</p>
        </div>
      </div>

      <div className="feed-toolbar">
        <div className="searchbar">
          <Icon name="search" />
          <input className="input" placeholder={L.search_ph} value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <button className={`chip${fcfsOnly ? " on" : ""}`} onClick={() => setFcfsOnly((v) => !v)}>
          <Icon name="zap" />{L.only_fcfs}
        </button>
        <button className={`chip${soundOn ? " on" : ""}`} onClick={() => setSoundOn(!soundOn)} title={L.sound}>
          <Icon name={soundOn ? "bell" : "bell"} />{L.sound}
        </button>
      </div>

      {unseen > 0 && (
        <div className="new-banner" onClick={scrollTop}>
          <Icon name="arrowup" style={{ width: 15, height: 15 }} />
          {unseen} {unseen === 1 ? L.new_match : L.new_matches} · {L.show}
        </div>
      )}

      {/* states */}
      {wsState === "off" ? (
        <div className="panel"><EmptyState icon="wifioff" title={L.err_conn_t} text={L.err_conn_p}
          action={<Btn variant="primary" icon="history" onClick={onRetry}>{L.retry}</Btn>} /></div>
      ) : feed.length === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <SkelCard /><SkelCard /><SkelCard />
        </div>
      ) : filtered.length === 0 ? (
        <div className="panel"><EmptyState icon="search" title={L.empty_feed_t} text={L.empty_feed_p}
          action={<Btn variant="ghost" icon="sliders" onClick={onCreateFilter}>{L.create_filter}</Btn>} /></div>
      ) : (
        <>
          {paused && (
            <div className="row gap10" style={{ justifyContent: "center", padding: "8px 0", color: "var(--text-3)", fontSize: 13, fontWeight: 600 }}>
              <span className="wsdot off" style={{ border: 0, background: "transparent", padding: 0 }}><i /></span>{L.paused_listings}
            </div>
          )}
          <div className="feed">
            {filtered.map((l) => (
              <ListingCard key={l.id} l={l} lang={lang} now={now}
                fresh={now - l.createdAt < 9000} glow onOpen={onOpenListing} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

Object.assign(window, { defaultFilter, FilterFormBody, FiltersScreen, Dashboard, estimateMatches, CITIES });
