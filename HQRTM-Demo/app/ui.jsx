/* ui.jsx — shared presentational components */

function Btn({ variant = "ghost", size, icon, iconRight, children, className = "", ...rest }) {
  const cls = `btn btn-${variant}${size ? " btn-" + size : ""}${className ? " " + className : ""}`;
  return (
    <button className={cls} {...rest}>
      {icon && <Icon name={icon} />}
      {children}
      {iconRight && <Icon name={iconRight} />}
    </button>
  );
}

function IconBtn({ name, on, label, ...rest }) {
  return (
    <button className={`iconbtn${on ? " on" : ""}`} aria-label={label} title={label} {...rest}>
      <Icon name={name} />
    </button>
  );
}

function Field({ label, hint, error, children }) {
  return (
    <div className="field">
      {label && <label>{label}{hint && <span className="hint">{hint}</span>}</label>}
      {children}
      {error && <div className="field-err"><Icon name="x" style={{ width: 13, height: 13 }} />{error}</div>}
    </div>
  );
}

function Switch({ on, onChange, label }) {
  return (
    <button className="switch" data-on={on ? "1" : "0"} role="switch" aria-checked={!!on}
            aria-label={label} onClick={() => onChange(!on)}><i /></button>
  );
}

function Checkbox({ checked, onChange, children }) {
  return (
    <label className="checkbox">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="box"><Icon name="check" strokeWidth="3" /></span>
      <span>{children}</span>
    </label>
  );
}

function Badge({ kind, icon, children }) {
  return <span className={`badge${kind ? " badge-" + kind : ""}`}>{icon && <Icon name={icon} />}{children}</span>;
}

function Photo({ label = "FOTO", className = "", src = null }) {
  if (src) {
    return (
      <div className={`ph ${className}`} style={{ padding: 0, overflow: "hidden" }}>
        <img src={src} alt="" loading="lazy"
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
      </div>
    );
  }
  return <div className={`ph ${className}`}><span>{label}</span></div>;
}

/* tiny sparkline */
function Spark({ points = [4, 6, 5, 8, 7, 11, 9, 13], w = 60, h = 22, color = "var(--accent)" }) {
  const max = Math.max(...points), min = Math.min(...points);
  const dx = w / (points.length - 1);
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"}${(i * dx).toFixed(1)} ${(h - ((p - min) / (max - min || 1)) * h).toFixed(1)}`).join(" ");
  return (
    <svg className="spark" width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none">
      <path d={d} stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* Modal */
function Modal({ title, sub, icon, onClose, children, footer, max }) {
  React.useEffect(() => {
    const h = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="scrim" onMouseDown={onClose}>
      <div className="modal" style={max ? { maxWidth: max } : null} onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head">
          {icon && <div className="filter-ico" style={{ width: 38, height: 38 }}><Icon name={icon} /></div>}
          <div className="grow">
            <h2>{title}</h2>
            {sub && <div className="sub">{sub}</div>}
          </div>
          <IconBtn name="x" label="Close" onClick={onClose} />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

/* The hero of the product — a matched listing */
function ListingCard({ l, lang, now, fresh, glow, onOpen }) {
  const L = STRINGS[lang];
  const age = timeAgo(l.createdAt, lang);
  const closingSoon = fresh && l.fcfs;
  return (
    <div className={`lc${fresh ? " fresh" : ""}${glow ? " glow" : ""}`} role="article">
      <div className="lc-photo only-desktop"><Photo label="FOTO" src={l.image} /></div>
      <div className="lc-main">
        <div className="lc-top">
          <span className="lc-title">{l.street} {l.streetNo}</span>
          {l.fcfs
            ? <Badge kind="fcfs" icon="zap">{L.fcfs_short}</Badge>
            : <Badge>{l.queueDays}{lang === "sv" ? " d kö" : "d queue"}</Badge>}
          <span className="lc-area"><Icon name="pin" />{l.area} · {l.city}</span>
        </div>
        <div className="lc-specs">
          <div className="lc-spec"><span className="sl">{L.room}</span><span className="sv num">{l.rooms}<small> {L.room}</small></span></div>
          <div className="lc-spec"><span className="sl">{L.sqm}</span><span className="sv num">{l.sqm}<small> {L.sqm}</small></span></div>
          {l.floor != null && <div className="lc-spec"><span className="sl">{L.floor}</span><span className="sv num">{l.floor}<small> {L.floor}</small></span></div>}
        </div>
      </div>
      <div className="lc-side">
        <div className="lc-rent num">{fmtKr(l.rent)}<small> {L.rent_mo}</small></div>
        <div className="lc-age">
          {fresh && <span className="livedot" />}{age}
        </div>
        <div className="lc-cta">
          <Btn variant="primary" size="sm" iconRight="external" onClick={() => onOpen && onOpen(l)}>
            <span className="only-desktop">{L.view_to}</span>
            <span className="only-mobile">HomeQ</span>
          </Btn>
        </div>
      </div>
    </div>
  );
}

function SkelCard() {
  return (
    <div className="skel-card">
      <div className="skel" style={{ width: 116, height: 92 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 10, justifyContent: "center" }}>
        <div className="skel" style={{ width: "55%", height: 16 }} />
        <div className="skel" style={{ width: "35%", height: 12 }} />
        <div className="skel" style={{ width: "70%", height: 12 }} />
      </div>
      <div className="skel" style={{ width: 80, height: 20, alignSelf: "center" }} />
    </div>
  );
}

function EmptyState({ icon, title, text, action }) {
  return (
    <div className="state">
      <div className="ico"><Icon name={icon} /></div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

Object.assign(window, {
  Btn, IconBtn, Field, Switch, Checkbox, Badge, Photo, Spark,
  Modal, ListingCard, SkelCard, EmptyState,
});
