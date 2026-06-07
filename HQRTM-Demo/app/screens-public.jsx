/* screens-public.jsx — Landing, Auth, Onboarding */

function LangThemeControls({ lang, theme, setLang, setTheme }) {
  return (
    <div className="row gap6">
      <button className="wsdot" style={{ cursor: "pointer" }} onClick={() => setLang(lang === "sv" ? "en" : "sv")}
              title="Language">
        <Icon name="globe" style={{ width: 15, height: 15 }} />
        {lang === "sv" ? "SV" : "EN"}
      </button>
      <IconBtn name={theme === "dark" ? "sun" : "moon"} label="Theme"
               onClick={() => setTheme(theme === "dark" ? "light" : "dark")} />
    </div>
  );
}

/* a small animated live-feed used on landing + auth aside */
function PreviewFeed({ lang, n = 4 }) {
  const L = STRINGS[lang];
  const [rows, setRows] = React.useState(() => seedListings(n));
  React.useEffect(() => {
    const id = setInterval(() => {
      setRows((prev) => [generateListing({ createdAt: Date.now() }), ...prev.slice(0, n - 1)]);
    }, 2600);
    return () => clearInterval(id);
  }, [n]);
  return (
    <div className="preview-feed">
      {rows.map((l, i) => (
        <div className="pf-row" key={l.id} style={i === 0 ? { animation: "flyin .45s var(--ease) both" } : null}>
          <div className="pf-ph"><Photo label="" /></div>
          <div className="pf-meta">
            <b>{l.street} {l.streetNo}</b>
            <span>{l.area} · {l.rooms} {L.room} · {l.sqm} {L.sqm}{l.fcfs ? " · FCFS" : ""}</span>
          </div>
          <div className="pf-rent num">{fmtKr(l.rent)}</div>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- Landing */
function Landing({ lang, theme, setLang, setTheme, go }) {
  const L = STRINGS[lang];
  return (
    <div className="lp">
      <div className="lp-nav">
        <div className="side-brand" style={{ padding: 0 }}>
          <div className="brand-mark"><BrandGlyph /><span className="pulse-dot" /></div>
          <div className="brand-name">HQRTM<small>Real-Time Monitor</small></div>
        </div>
        <div className="grow" />
        <LangThemeControls lang={lang} theme={theme} setLang={setLang} setTheme={setTheme} />
        <Btn variant="quiet" onClick={() => go("auth", { mode: "in" })}>{L.lp_signin}</Btn>
        <Btn variant="primary" onClick={() => go("auth", { mode: "up" })}>{L.lp_get_started}</Btn>
      </div>

      <div className="lp-hero">
        <div className="lp-eyebrow">
          <span className="wsdot live" style={{ border: 0, background: "transparent", padding: 0 }}><i /></span>
          {L.lp_eyebrow}
        </div>
        <h1 className="lp-h1">{L.lp_h1a} <em>{L.lp_h1b}</em></h1>
        <p className="lp-sub">{L.lp_sub}</p>
        <div className="lp-cta">
          <Btn variant="primary" size="lg" icon="zap" onClick={() => go("auth", { mode: "up" })}>{L.lp_get_started}</Btn>
          <Btn variant="ghost" size="lg" iconRight="arrowright" onClick={() => go("auth", { mode: "in" })}>{L.lp_signin}</Btn>
        </div>

        <div className="lp-demo">
          <div className="panel" style={{ overflow: "hidden" }}>
            <div className="panel-head">
              <div className="filter-ico" style={{ width: 30, height: 30 }}><Icon name="radar" /></div>
              <h3>{L.live_feed}</h3>
              <div className="grow" />
              <span className="wsdot live"><i />{L.lp_live}</span>
            </div>
            <div className="panel-body"><PreviewFeed lang={lang} n={4} /></div>
          </div>
        </div>
      </div>

      <div className="lp-features">
        {[
          { i: "zap", t: L.feat_rt_t, p: L.feat_rt_p },
          { i: "send2", t: L.feat_tg_t, p: L.feat_tg_p },
          { i: "sliders", t: L.feat_fl_t, p: L.feat_fl_p },
        ].map((f) => (
          <div className="lp-feat" key={f.t}>
            <div className="fi"><Icon name={f.i} /></div>
            <h3>{f.t}</h3>
            <p>{f.p}</p>
          </div>
        ))}
      </div>

      <div className="center muted" style={{ paddingBottom: 50, fontSize: 13 }}>{L.lp_footer}</div>
    </div>
  );
}

/* ------------------------------------------------------------------- Auth */
function Auth({ lang, theme, setLang, setTheme, go, initialMode, onAuth, onDemo }) {
  const L = STRINGS[lang];
  const [mode, setMode] = React.useState(initialMode || "in");
  const [email, setEmail] = React.useState("");
  const [pw, setPw] = React.useState("");
  const [consent, setConsent] = React.useState(false);
  const [err, setErr] = React.useState({});

  const submit = (e) => {
    e.preventDefault();
    const next = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) next.email = L.err_email;
    if (pw.length < 8) next.pw = L.err_pw;
    if (mode === "up" && !consent) next.consent = L.consent_req;
    setErr(next);
    if (Object.keys(next).length === 0) onAuth(mode, email);
  };

  return (
    <div className="auth">
      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit} noValidate>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="side-brand" style={{ padding: 0, cursor: "pointer" }} onClick={() => go("landing")}>
              <div className="brand-mark"><BrandGlyph /><span className="pulse-dot" /></div>
              <div className="brand-name">HQRTM</div>
            </div>
            <LangThemeControls lang={lang} theme={theme} setLang={setLang} setTheme={setTheme} />
          </div>

          <div style={{ marginTop: 12 }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.025em" }}>
              {mode === "in" ? L.welcome_back : L.create_acct}
            </h1>
            <p className="muted" style={{ marginTop: 6 }}>{mode === "in" ? L.signin_sub : L.signup_sub}</p>
          </div>

          <Field label={L.email} error={err.email}>
            <div className="input-group">
              <span className="prefix"><Icon name="mail" style={{ width: 16, height: 16 }} /></span>
              <input className={`input${err.email ? " err" : ""}`} type="email" placeholder="namn@exempel.se"
                     value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
          </Field>

          <Field label={L.password} hint={mode === "in" ? L.forgot : null} error={err.pw}>
            <div className="input-group">
              <span className="prefix"><Icon name="lock" style={{ width: 16, height: 16 }} /></span>
              <input className={`input${err.pw ? " err" : ""}`} type="password" placeholder="••••••••"
                     value={pw} onChange={(e) => setPw(e.target.value)} />
            </div>
          </Field>

          {mode === "up" && (
            <Field error={err.consent}>
              <Checkbox checked={consent} onChange={setConsent}>
                {L.consent} <a onClick={(e) => e.preventDefault()} href="#">{L.consent_terms}</a> {L.consent_and} <a onClick={(e) => e.preventDefault()} href="#">{L.consent_privacy}</a>
              </Checkbox>
            </Field>
          )}

          <Btn variant="primary" size="lg" className="btn-block" type="submit">
            {mode === "in" ? L.sign_in : L.sign_up}
          </Btn>

          <div className="center muted" style={{ fontSize: 13.5 }}>
            {mode === "in" ? L.no_acct : L.have_acct}{" "}
            <span className="link" onClick={() => { setMode(mode === "in" ? "up" : "in"); setErr({}); }}>
              {mode === "in" ? L.sign_up : L.sign_in}
            </span>
          </div>

          <div className="auth-divider">{L.demo_title}</div>
          <div className="demo-creds">
            <button type="button" className="demo-card" onClick={() => onDemo("user")}>
              <span className="role"><Icon name="user" />{L.role_user}</span>
              <span className="cred">{DEMO_CREDS.user.email}</span>
              <span className="cred">{DEMO_CREDS.user.password}</span>
              <span className="go">{L.demo_as} {L.role_user.toLowerCase()}<Icon name="arrowright" /></span>
            </button>
            <button type="button" className="demo-card admin" onClick={() => onDemo("admin")}>
              <span className="role"><Icon name="shield" />{L.role_admin}</span>
              <span className="cred">{DEMO_CREDS.admin.email}</span>
              <span className="cred">{DEMO_CREDS.admin.password}</span>
              <span className="go">{L.demo_as} {L.role_admin.toLowerCase()}<Icon name="arrowright" /></span>
            </button>
          </div>
        </form>
      </div>

      <div className="auth-aside">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="wsdot live"><i />{L.lp_live}</span>
          <span className="badge badge-fcfs"><Icon name="zap" />{L.fcfs_short}</span>
        </div>
        <div style={{ margin: "auto 0", display: "flex", flexDirection: "column", gap: 18 }}>
          <h2 style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.15 }}>{L.lp_h1a} <span style={{ color: "var(--accent)" }}>{L.lp_h1b}</span></h2>
          <PreviewFeed lang={lang} n={5} />
        </div>
        <div className="muted" style={{ fontSize: 12.5 }}>{L.lp_footer}</div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- Onboarding */
function Onboarding({ lang, onFinish, onCreateFilter }) {
  const L = STRINGS[lang];
  const [step, setStep] = React.useState(0);
  const [linked, setLinked] = React.useState(false);
  const code = React.useMemo(() => "HQ-" + Math.random().toString(36).slice(2, 6).toUpperCase(), []);
  const [copied, setCopied] = React.useState(false);

  return (
    <div className="ob">
      <div className="ob-card">
        <div className="steps">
          <div className={`step-dot ${step > 0 ? "done" : "active"}`}>
            <i>{step > 0 ? <Icon name="check" strokeWidth="3" style={{ width: 13, height: 13 }} /> : 1}</i>
            <span>{L.ob_step_tg}</span>
          </div>
          <div className={`step-line ${step > 0 ? "done" : ""}`} />
          <div className={`step-dot ${step === 1 ? "active" : ""}`}>
            <i>2</i><span>{L.ob_step_filter}</span>
          </div>
        </div>

        {step === 0 && (
          <div className="panel">
            <div className="panel-body" style={{ padding: 24 }}>
              <div className="filter-ico" style={{ width: 48, height: 48, marginBottom: 16 }}><Icon name="send2" /></div>
              <h2 style={{ fontSize: 21, fontWeight: 800, letterSpacing: "-0.02em" }}>{L.ob_tg_t}</h2>
              <p className="muted" style={{ marginTop: 8, lineHeight: 1.55 }}>{L.ob_tg_p}</p>

              <div className="mt24" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div className="code-box">{code}</div>
                <div className="row gap10">
                  <Btn variant="ghost" icon={copied ? "check" : "copy"} onClick={() => { setCopied(true); setTimeout(() => setCopied(false), 1600); }}>
                    {copied ? L.copied : L.tg_copy}
                  </Btn>
                  <Btn variant="primary" icon="send2" onClick={() => setLinked(true)}>@HQRTM_bot</Btn>
                </div>
                <p className="muted center" style={{ fontSize: 12 }}>{L.tg_code_note}</p>
                {linked && (
                  <div className="tg-status linked" style={{ alignSelf: "center" }}>
                    <Icon name="checkcircle" style={{ width: 15, height: 15 }} />{L.tg_linked}
                  </div>
                )}
              </div>
            </div>
            <div className="modal-foot">
              <Btn variant="quiet" onClick={() => setStep(1)}>{L.ob_skip}</Btn>
              <div className="grow" />
              <Btn variant="primary" iconRight="arrowright" onClick={() => setStep(1)} disabled={false}>{L.ob_continue}</Btn>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="panel">
            <div className="panel-body" style={{ padding: 24 }}>
              <div className="filter-ico" style={{ width: 48, height: 48, marginBottom: 16 }}><Icon name="sliders" /></div>
              <h2 style={{ fontSize: 21, fontWeight: 800, letterSpacing: "-0.02em" }}>{L.ob_filter_t}</h2>
              <p className="muted" style={{ marginTop: 8 }}>{L.ob_filter_p}</p>
              <div className="mt24"><FilterFormBody lang={lang} value={defaultFilter()} onChange={() => {}} embedded /></div>
            </div>
            <div className="modal-foot">
              <Btn variant="quiet" onClick={() => setStep(0)} icon="chevleft">{L.prev}</Btn>
              <div className="grow" />
              <Btn variant="primary" icon="zap" onClick={() => { onCreateFilter(); onFinish(); }}>{L.ob_finish}</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { Landing, Auth, Onboarding, PreviewFeed, LangThemeControls });
