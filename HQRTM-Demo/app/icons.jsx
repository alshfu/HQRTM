/* icons.jsx — line icon set (24px grid, currentColor stroke).
   Usage: <Icon name="bolt" />  */
const ICON_PATHS = {
  bolt:      <path d="M13 2 4.5 13.5H11l-1 8.5 8.5-11.5H12l1-8.5Z" />,
  radar:     <><path d="M19.07 4.93a10 10 0 1 0 1.4 12.6" /><path d="M12 12 7 7" /><circle cx="12" cy="12" r="3.2" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3" /></>,
  feed:      <><path d="M4 6h16M4 12h16M4 18h10" /></>,
  layers:    <><path d="m12 2 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5" /><path d="m3 17 9 5 9-5" /></>,
  bell:      <><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></>,
  history:   <><path d="M3 3v5h5" /><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8" /><path d="M12 7v5l3 2" /></>,
  gear:      <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" /></>,
  pin:       <><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></>,
  bed:       <><path d="M2 9v11M2 13h20v7M22 13v-2a3 3 0 0 0-3-3H9v5" /><path d="M6 8v0" /></>,
  ruler:     <><path d="M21.3 8.7 8.7 21.3a1 1 0 0 1-1.4 0l-4.6-4.6a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4Z" /><path d="m7.5 10.5 2 2M11 7l2 2M14.5 3.5l2 2M4 14l2 2" /></>,
  coins:     <><ellipse cx="9" cy="6" rx="6" ry="3" /><path d="M3 6v6c0 1.66 2.69 3 6 3s6-1.34 6-3" /><path d="M15 9.5c2.5.3 6 1.4 6 3.5v6c0 1.66-2.69 3-6 3s-6-1.34-6-3v-1" /></>,
  arrowup:   <path d="M12 19V5M5 12l7-7 7 7" />,
  arrowright:<path d="M5 12h14M12 5l7 7-7 7" />,
  external:  <><path d="M15 3h6v6" /><path d="M10 14 21 3" /><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" /></>,
  search:    <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>,
  plus:      <path d="M12 5v14M5 12h14" />,
  check:     <path d="M20 6 9 17l-5-5" />,
  checkcircle:<><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.5 2.5 4.5-5" /></>,
  x:         <path d="M18 6 6 18M6 6l12 12" />,
  sun:       <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  moon:      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />,
  globe:     <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z" /></>,
  sliders:   <><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" /></>,
  edit:      <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></>,
  trash:     <><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" /><path d="M10 11v6M14 11v6" /></>,
  copy:      <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></>,
  send:      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" />,
  send2:     <><path d="M14.5 9.5 9 12l-4-1.5L21 4l-4 16-5.5-4-2.5 3v-4.5" /></>,
  shield:    <><path d="M12 2 4 5v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></>,
  lock:      <><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></>,
  user:      <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  mail:      <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></>,
  wifi:      <><path d="M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0" /><circle cx="12" cy="19.5" r="1" fill="currentColor" stroke="none" /></>,
  wifioff:   <><path d="M2 2l20 20M8.5 16a5 5 0 0 1 6-0.8M5 12.5a10 10 0 0 1 4-2.4M19 12.5a10 10 0 0 0-4.5-2.7" /><circle cx="12" cy="19.5" r="1" fill="currentColor" stroke="none" /></>,
  clock:     <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  filter:    <path d="M3 4h18l-7 8v6l-4 2v-8L3 4Z" />,
  grid:      <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
  list:      <><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></>,
  terminal:  <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="m7 9 3 3-3 3M13 15h4" /></>,
  sparkles:  <><path d="M12 3v4M12 17v4M3 12h4M17 12h4" /><path d="m6.3 6.3 2 2M15.7 15.7l2 2M17.7 6.3l-2 2M8.3 15.7l-2 2" /></>,
  flame:     <path d="M12 2c1 4-2 5-2 8a2 2 0 0 0 4 0c0-1 .5-1.5 1-2 1 2 2 3 2 5a5 5 0 0 1-10 0c0-4 4-6 5-11Z" />,
  phone:     <><rect x="6" y="2" width="12" height="20" rx="3" /><path d="M11 18h2" /></>,
  monitor:   <><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" /></>,
  chevdown:  <path d="m6 9 6 6 6-6" />,
  chevleft:  <path d="m15 18-6-6 6-6" />,
  chevright: <path d="m9 18 6-6-6-6" />,
  menu:      <path d="M3 6h18M3 12h18M3 18h18" />,
  logout:    <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></>,
  zap:       <path d="M11 2 4 14h6l-1 8 8-12h-6l1-8Z" />,
  eye:       <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></>,
  dot:       <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" />,
  doc:       <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M9 13h6M9 17h6" /></>,
  trend:     <><path d="M3 17l6-6 4 4 8-8" /><path d="M17 7h4v4" /></>,
};

function Icon({ name, className, style, strokeWidth = 1.7 }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round"
         strokeLinejoin="round" aria-hidden="true">
      {ICON_PATHS[name] || null}
    </svg>
  );
}

/* Brand mark glyph (signal/radar pulse — original) */
function BrandGlyph({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 13.5 10.5 6l4 4L21 3.5" />
      <circle cx="10.5" cy="13" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

Object.assign(window, { Icon, BrandGlyph, ICON_PATHS });
