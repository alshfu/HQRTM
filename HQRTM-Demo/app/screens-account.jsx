/* screens-account.jsx — Notification history + Account settings */

const PAGE_SIZE = 8;

function HistoryScreen({ lang, notifications, onOpenListing }) {
  const L = STRINGS[lang];
  const [page, setPage] = React.useState(0);
  const [chan, setChan] = React.useState("all");
  const [stat, setStat] = React.useState("all");

  const rows = React.useMemo(() => notifications.filter((n) =>
    (chan === "all" || n.channel === chan) && (stat === "all" || n.status === stat)
  ), [notifications, chan, stat]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pageRows = rows.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);
  React.useEffect(() => { setPage(0); }, [chan, stat]);

  const statusBadge = (s) =>
    s === "delivered" ? <Badge kind="fcfs" icon="checkcircle">{L.delivered}</Badge>
    : s === "failed" ? <Badge kind="red" icon="x">{L.failed}</Badge>
    : <Badge kind="amber" icon="clock">{L.pending}</Badge>;
  const chanIcon = (c) => c === "telegram" ? "send2" : "mail";

  return (
    <div className="page">
      <div className="page-head"><h2>{L.history_title}</h2><p>{L.history_sub}</p></div>

      <div className="feed-toolbar" style={{ marginBottom: 14 }}>
        <select className="select" style={{ width: "auto", height: 38 }} value={chan} onChange={(e) => setChan(e.target.value)}>
          <option value="all">{L.all_channels}</option>
          <option value="telegram">Telegram</option>
          <option value="email">E-post</option>
        </select>
        <select className="select" style={{ width: "auto", height: 38 }} value={stat} onChange={(e) => setStat(e.target.value)}>
          <option value="all">{L.all_status}</option>
          <option value="delivered">{L.delivered}</option>
          <option value="failed">{L.failed}</option>
        </select>
        <div className="grow" />
        <span className="muted" style={{ fontSize: 13 }}>{L.showing} {rows.length ? page * PAGE_SIZE + 1 : 0}–{Math.min(rows.length, (page + 1) * PAGE_SIZE)} {L.of} {rows.length}</span>
      </div>

      {rows.length === 0 ? (
        <div className="panel"><EmptyState icon="bell" title={L.no_history_t} text={L.no_history_p} /></div>
      ) : (
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr>
              <th>{L.h_when}</th><th>{L.h_object}</th><th>{L.h_filter}</th>
              <th>{L.h_channel}</th><th>{L.h_status}</th><th style={{ textAlign: "right" }}>{L.h_latency}</th><th></th>
            </tr></thead>
            <tbody>
              {pageRows.map((n) => (
                <tr key={n.id}>
                  <td data-l={L.h_when}><span className="t-time">{fmtClock(n.sentAt)}</span></td>
                  <td data-l={L.h_object}>
                    <div className="t-addr">{n.listing.street} {n.listing.streetNo}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{n.listing.area} · {n.listing.rooms} {L.room} · {fmtKr(n.listing.rent)} {L.rent_mo}{n.listing.fcfs ? " · FCFS" : ""}</div>
                  </td>
                  <td data-l={L.h_filter}><span className="crit" style={{ background: "var(--surface-2)" }}>{n.filterName}</span></td>
                  <td data-l={L.h_channel}><span className="row gap6" style={{ fontWeight: 600 }}><Icon name={chanIcon(n.channel)} style={{ width: 15, height: 15, color: "var(--text-3)" }} />{n.channel === "telegram" ? "Telegram" : "E-post"}</span></td>
                  <td data-l={L.h_status}>{statusBadge(n.status)}</td>
                  <td data-l={L.h_latency} style={{ textAlign: "right" }}><span className="t-lat" style={{ color: n.latencyMs < 1200 ? "var(--accent-dim)" : "var(--text-2)" }}>{(n.latencyMs / 1000).toFixed(1)}s</span></td>
                  <td style={{ textAlign: "right" }}><IconBtn name="external" label={L.view_to} onClick={() => onOpenListing(n.listing)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pager">
            <span>{page + 1} / {pages}</span>
            <div className="pnav">
              <Btn variant="ghost" size="sm" icon="chevleft" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>{L.prev}</Btn>
              <Btn variant="ghost" size="sm" iconRight="chevright" disabled={page >= pages - 1} onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}>{L.next}</Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- Settings */
function SettingsScreen({ lang, setLang, user, tgLinked, setTgLinked, onToast, onDeleteAccount }) {
  const L = STRINGS[lang];
  const [tab, setTab] = React.useState("profile");
  const [name, setName] = React.useState(user.name);
  const [email, setEmail] = React.useState(user.email);
  const [notif, setNotif] = React.useState({ telegram: true, email: false, sound: true });
  const [copied, setCopied] = React.useState(false);
  const [confirmDel, setConfirmDel] = React.useState(false);
  const [delWord, setDelWord] = React.useState("");
  const code = React.useMemo(() => "HQ-" + Math.random().toString(36).slice(2, 6).toUpperCase(), []);

  const TABS = [
    { id: "profile", label: L.set_profile, icon: "user" },
    { id: "telegram", label: L.set_telegram, icon: "send2" },
    { id: "security", label: L.set_security, icon: "lock" },
    { id: "notif", label: L.set_notif, icon: "bell" },
    { id: "privacy", label: L.set_privacy, icon: "shield" },
  ];

  return (
    <div className="page">
      <div className="page-head"><h2>{L.settings_title}</h2></div>
      <div className="settings-grid">
        <div className="settings-nav">
          {TABS.map((t) => (
            <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
              <Icon name={t.icon} />{t.label}
            </button>
          ))}
        </div>

        <div>
          {tab === "profile" && (
            <div className="panel"><div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              <div className="row gap14">
                <div className="avatar" style={{ width: 56, height: 56, fontSize: 20 }}>{name.slice(0, 1).toUpperCase()}</div>
                <div><b style={{ fontSize: 16 }}>{name}</b><div className="muted">{email}</div></div>
              </div>
              <div className="divider" />
              <div className="form-grid">
                <Field label={L.name}><input className="input" value={name} onChange={(e) => setName(e.target.value)} /></Field>
                <Field label={L.email}><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
              </div>
              <Field label={L.lang_pref}>
                <div className="segmented" style={{ width: "fit-content" }}>
                  <button className={lang === "sv" ? "active" : ""} onClick={() => setLang("sv")}>Svenska</button>
                  <button className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>English</button>
                </div>
              </Field>
              <div className="row"><div className="grow" /><Btn variant="primary" icon="check" onClick={() => onToast(L.saved)}>{L.save_changes}</Btn></div>
            </div></div>
          )}

          {tab === "telegram" && (
            <div className="panel tg-panel">
              <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div className={`tg-status ${tgLinked ? "linked" : "unlinked"}`} style={{ alignSelf: "flex-start" }}>
                  <Icon name={tgLinked ? "checkcircle" : "send2"} style={{ width: 15, height: 15 }} />
                  {tgLinked ? L.tg_linked : L.tg_unlinked}
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 700 }}>{L.tg_how}</h3>
                <ol style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 8, color: "var(--text-2)", fontSize: 14 }}>
                  <li>{L.tg_step1}</li><li>{L.tg_step2}</li><li>{L.tg_step3}</li>
                </ol>
                <div className="code-box">{code}</div>
                <div className="row gap10 wrap">
                  <Btn variant="ghost" icon={copied ? "check" : "copy"} onClick={() => { setCopied(true); onToast(L.copied); setTimeout(() => setCopied(false), 1600); }}>{copied ? L.copied : L.tg_copy}</Btn>
                  {!tgLinked
                    ? <Btn variant="primary" icon="send2" onClick={() => { setTgLinked(true); onToast(L.tg_linked); }}>{L.tg_connect}</Btn>
                    : <>
                        <Btn variant="ghost" icon="bell" onClick={() => onToast(L.tg_test_sent)}>{L.tg_test}</Btn>
                        <Btn variant="quiet" onClick={() => setTgLinked(false)}>{L.tg_unlink}</Btn>
                      </>}
                </div>
              </div>
              <div className="tg-side">
                <div className="filter-ico" style={{ width: 44, height: 44, background: "var(--surface)" }}><Icon name="send2" /></div>
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>@HQRTM_bot</h3>
                <p className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>{lang === "sv" ? "Boten skickar dig ett tryckbart larm i samma sekund som ett objekt matchar." : "The bot sends you a tappable alert the second a listing matches."}</p>
                <div className="preview-feed" style={{ marginTop: "auto" }}>
                  <div className="pf-row"><div className="pf-ph"><Photo label="" /></div>
                    <div className="pf-meta"><b>Bondegatan 12</b><span>Södermalm · 2 {L.room} · FCFS</span></div>
                    <Icon name="send2" style={{ width: 16, height: 16, color: "var(--accent)" }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === "security" && (
            <div className="panel"><div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 420 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700 }}>{L.change_pw}</h3>
              <Field label={L.cur_pw}><input className="input" type="password" placeholder="••••••••" /></Field>
              <Field label={L.new_pw} hint={L.err_pw}><input className="input" type="password" placeholder="••••••••" /></Field>
              <Field label={L.confirm_pw}><input className="input" type="password" placeholder="••••••••" /></Field>
              <div className="row"><div className="grow" /><Btn variant="primary" icon="lock" onClick={() => onToast(L.saved)}>{L.change_pw}</Btn></div>
            </div></div>
          )}

          {tab === "notif" && (
            <div className="panel"><div className="panel-body">
              {[
                { k: "telegram", t: L.notif_telegram, d: L.notif_telegram_d, icon: "send2" },
                { k: "email", t: L.notif_email, d: L.notif_email_d, icon: "mail" },
                { k: "sound", t: L.notif_sound, d: L.notif_sound_d, icon: "bell" },
              ].map((row) => (
                <div className="setting-row" key={row.k}>
                  <div className="filter-ico" style={{ width: 38, height: 38 }}><Icon name={row.icon} /></div>
                  <div className="sr-meta"><b>{row.t}</b><span>{row.d}</span></div>
                  <Switch on={notif[row.k]} onChange={(v) => setNotif({ ...notif, [row.k]: v })} label={row.t} />
                </div>
              ))}
            </div></div>
          )}

          {tab === "privacy" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              <div className="panel"><div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div className="row gap14">
                  <div className="filter-ico" style={{ width: 44, height: 44 }}><Icon name="shield" /></div>
                  <div><b style={{ fontSize: 15.5 }}>{L.privacy_t}</b><p className="muted" style={{ fontSize: 13.5, marginTop: 3, lineHeight: 1.5 }}>{L.privacy_p}</p></div>
                </div>
                <div className="row gap10 wrap">
                  <Btn variant="ghost" icon="doc" onClick={() => onToast(lang === "sv" ? "Export påbörjad" : "Export started")}>{L.export_data}</Btn>
                  <Btn variant="quiet" iconRight="external">{L.privacy_policy}</Btn>
                  <Btn variant="quiet" iconRight="external">{L.terms}</Btn>
                </div>
              </div></div>

              <div className="danger-zone">
                <div className="setting-row" style={{ borderBottom: 0 }}>
                  <div className="filter-ico" style={{ width: 38, height: 38, background: "var(--red-soft)", color: "var(--red)" }}><Icon name="trash" /></div>
                  <div className="sr-meta"><b style={{ color: "var(--red)" }}>{L.delete_acct}</b><span>{L.delete_acct_d}</span></div>
                  <Btn variant="danger" icon="trash" onClick={() => { setConfirmDel(true); setDelWord(""); }}>{L.delete}</Btn>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {confirmDel && (
        <Modal title={L.delete_acct_q} icon="shield" max={460} onClose={() => setConfirmDel(false)}
               footer={<>
                 <div className="grow" />
                 <Btn variant="quiet" onClick={() => setConfirmDel(false)}>{L.cancel}</Btn>
                 <Btn variant="danger" icon="trash" disabled={delWord.trim().toUpperCase() !== L.delete_word}
                      onClick={onDeleteAccount}>{L.delete_acct}</Btn>
               </>}>
          <p className="muted">{L.delete_acct_p}</p>
          <Field label={L.delete_acct_confirm}>
            <input className="input" value={delWord} onChange={(e) => setDelWord(e.target.value)} placeholder={L.delete_word} autoFocus />
          </Field>
        </Modal>
      )}
    </div>
  );
}

Object.assign(window, { HistoryScreen, SettingsScreen });
