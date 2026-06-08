/* screens-admin.jsx — (FE-AD-001/002) Ops panel: source status, metrics, users, events */

function AdminScreen({ lang }) {
  const L = STRINGS[lang];
  const lvl = {
    info:  { c: "var(--text-3)", b: null },
    warn:  { c: "var(--amber)", b: "amber" },
    error: { c: "var(--red)", b: "red" },
  };
  const planBadge = (p) => p === "Pro"
    ? <Badge kind="fcfs">Pro</Badge>
    : <Badge>Free</Badge>;

  // Riktig data från HomeQ (window.HQRTM_META) — region, antal objekt, senaste hämtning.
  const M = (typeof realMeta === "function" && realMeta()) || null;
  const metrics = [
    [L.src_latency, "0.82", "s"],
    [L.src_lastpoll, M ? M.clock : "2", M ? "" : "s"],
    [M ? "Objekt" : L.src_uptime, M ? String(M.count) : "99.94", M ? "" : "%"],
    [L.src_region, M ? M.region : "eu-north-1", ""],
  ];
  const events = M
    ? [{ t: M.clock, lvl: "info", msg: {
        sv: `Hämtade ${M.count} annonser · HomeQ (${M.region})`,
        en: `Fetched ${M.count} listings · HomeQ (${M.region})` } }, ...SAMPLE_EVENTS]
    : SAMPLE_EVENTS;

  return (
    <div className="page">
      <div className="page-head"><h2>{L.admin_title}</h2><p>{L.admin_sub}</p></div>

      {/* source status */}
      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-body row wrap" style={{ gap: 22, alignItems: "center" }}>
          <div className="row gap10">
            <span className="wsdot live" style={{ border: 0, background: "transparent", padding: 0 }}><i /></span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>{L.src_title}</div>
              <div className="badge badge-fcfs" style={{ marginTop: 4 }}><Icon name="checkcircle" />{L.src_online}</div>
            </div>
          </div>
          <div className="divider only-desktop" style={{ width: 1, height: 40, background: "var(--border)" }} />
          {metrics.map((m, i) => (
            <div key={i} style={{ whiteSpace: "nowrap", flexShrink: 0 }}>
              <div className="muted" style={{ fontSize: 11.5, fontWeight: 600 }}>{m[0]}</div>
              <div className="num" style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>{m[1]}<small style={{ fontSize: 12, color: "var(--text-3)" }}> {m[2]}</small></div>
            </div>
          ))}
          <div className="grow" />
          <Spark points={[6, 5, 7, 5, 6, 4, 5, 4, 5, 4]} w={92} h={30} />
        </div>
      </div>

      {/* metrics */}
      <div className="stats">
        <div className="stat"><div className="k"><Icon name="user" />{L.m_users}</div><div className="v num">1 284</div><div className="d up"><Icon name="trend" />+38</div></div>
        <div className="stat"><div className="k"><Icon name="dot" />{L.m_active}</div><div className="v num">312</div><div className="d up"><Icon name="checkcircle" style={{ width: 13, height: 13 }} />live</div></div>
        <div className="stat"><div className="k"><Icon name="bell" />{L.m_alerts}</div><div className="v num">2 047</div><Spark points={[5, 7, 6, 9, 8, 12, 14, 13]} /></div>
        <div className="stat"><div className="k"><Icon name="wifi" />{L.m_ws}</div><div className="v num">298</div><div className="d up"><Icon name="trend" />stabil</div></div>
      </div>

      {/* users */}
      <div className="section-title"><Icon name="user" style={{ width: 14, height: 14 }} />{L.users_title}</div>
      <div className="table-wrap" style={{ marginBottom: 22 }}>
        <table className="tbl">
          <thead><tr>
            <th>{L.u_user}</th><th>{L.u_plan}</th><th>{L.u_filters}</th><th>{L.u_tg}</th><th>{L.u_last}</th><th>{L.u_status}</th>
          </tr></thead>
          <tbody>
            {SAMPLE_USERS.map((u, i) => (
              <tr key={i}>
                <td data-l={L.users_title}>
                  <div className="row gap10">
                    <div className="avatar" style={{ width: 30, height: 30, fontSize: 12 }}>{u.name.slice(0, 1)}</div>
                    <div><div className="t-addr">{u.name}</div><div className="muted mono" style={{ fontSize: 11.5 }}>{u.email}</div></div>
                  </div>
                </td>
                <td data-l={L.u_plan}>{planBadge(u.plan)}</td>
                <td data-l={L.u_filters}><span className="num" style={{ fontWeight: 700 }}>{u.filters}</span></td>
                <td data-l={L.u_tg}>{u.tg
                  ? <span className="row gap6" style={{ color: "var(--accent-dim)", fontWeight: 600, fontSize: 12.5 }}><Icon name="checkcircle" style={{ width: 14, height: 14 }} />{L.linked_short}</span>
                  : <span className="muted" style={{ fontSize: 12.5, fontWeight: 600 }}>{L.unlinked_short}</span>}</td>
                <td data-l={L.u_last}><span className="t-time">{u.last}</span></td>
                <td data-l={L.u_status}>{u.status === "active"
                  ? <Badge kind="fcfs" icon="dot">{STRINGS[lang].active}</Badge>
                  : <Badge icon="dot">{STRINGS[lang].paused}</Badge>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* events log */}
      <div className="section-title"><Icon name="terminal" style={{ width: 14, height: 14 }} />{L.log_title}</div>
      <div className="panel">
        <div className="panel-body" style={{ padding: 6 }}>
          {events.map((e, i) => (
            <div key={i} className="row gap10" style={{ padding: "9px 12px", borderBottom: i < events.length - 1 ? "1px solid var(--line)" : 0 }}>
              <span className="mono" style={{ fontSize: 12, color: "var(--text-3)", minWidth: 64 }}>{e.t}</span>
              <span className="badge" style={{ color: lvl[e.lvl].c, borderColor: "color-mix(in oklab, " + lvl[e.lvl].c + " 30%, transparent)" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: lvl[e.lvl].c, display: "inline-block" }} />
                {e.lvl.toUpperCase()}
              </span>
              <span style={{ fontSize: 13.5 }}>{e.msg[lang]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { AdminScreen });
