/* data.jsx — mock domain data, listing generator, i18n strings, formatters */

/* ---- Swedish areas / streets (original sample data) ---- */
const AREAS = [
  { area: "Södermalm", city: "Stockholm" },
  { area: "Vasastan", city: "Stockholm" },
  { area: "Kungsholmen", city: "Stockholm" },
  { area: "Östermalm", city: "Stockholm" },
  { area: "Hägersten", city: "Stockholm" },
  { area: "Hammarby Sjöstad", city: "Stockholm" },
  { area: "Sundbyberg", city: "Stockholm" },
  { area: "Solna", city: "Stockholm" },
  { area: "Liljeholmen", city: "Stockholm" },
  { area: "Aspudden", city: "Stockholm" },
  { area: "Majorna", city: "Göteborg" },
  { area: "Linnéstaden", city: "Göteborg" },
  { area: "Haga", city: "Göteborg" },
  { area: "Möllevången", city: "Malmö" },
  { area: "Västra Hamnen", city: "Malmö" },
  { area: "Luthagen", city: "Uppsala" },
];
const STREETS = [
  "Bondegatan", "Skånegatan", "Hornsgatan", "Folkungagatan", "Götgatan",
  "Upplandsgatan", "Sankt Eriksgatan", "Fleminggatan", "Karlbergsvägen",
  "Ringvägen", "Renstiernas gata", "Timmermansgatan", "Krukmakargatan",
  "Birger Jarlsgatan", "Odengatan", "Surbrunnsgatan", "Värmdövägen",
  "Lundagatan", "Blekingegatan", "Katarina Bangata",
];
const HOSTS = ["Stockholmshem", "Familjebostäder", "Svenska Bostäder", "Einar Mattsson", "Wallenstam", "Heimstaden", "Balder", "John Mattson"];

let __seq = 1000;
function rnd(a, b) { return Math.floor(Math.random() * (b - a + 1)) + a; }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

/* ---- riktig data från HomeQ:s publika sökning (window.HQRTM_SAMPLE) ---- */
function thumb(u) {
  return u ? "https://images.weserv.nl/?url=" + encodeURIComponent(u.replace(/^https?:\/\//, "")) + "&w=480&h=360&fit=cover&output=jpg&q=72" : null;
}
const REAL = (window.HQRTM_SAMPLE || []).map(function (it) {
  return {
    street: it.title || "Bostad", streetNo: "",
    area: it.district || "Göteborg", city: it.district || "Göteborg",
    rooms: it.rooms, sqm: it.area_m2 != null ? Math.round(it.area_m2) : null,
    rent: it.rent, fcfs: it.listing_type === "fcfs", floor: null, host: "HomeQ",
    queueDays: 0, available: "", image: thumb(it.image_url), url: it.url,
    description: it.description || "",
  };
});
function realMeta() { return window.HQRTM_META || null; }

function generateListing(opts = {}) {
  if (REAL.length) {
    const base = REAL[__seq % REAL.length];
    return Object.assign({}, base, {
      id: "L" + (++__seq),
      createdAt: opts.createdAt ?? Date.now(),
      filterId: opts.filterId ?? null,
      fcfs: opts.fcfs ?? base.fcfs,
    });
  }
  const loc = pick(AREAS);
  const rooms = opts.rooms ?? pick([1, 1, 2, 2, 2, 3, 3, 4]);
  const sqm = opts.sqm ?? rooms * rnd(18, 26) + rnd(-4, 8);
  const rent = opts.rent ?? Math.round((4200 + sqm * rnd(95, 165)) / 50) * 50;
  const fcfs = opts.fcfs ?? Math.random() < 0.58;
  const floor = rnd(0, 7);
  return {
    id: "L" + (++__seq),
    street: pick(STREETS),
    streetNo: rnd(1, 88),
    area: loc.area,
    city: loc.city,
    rooms, sqm, rent, fcfs, floor,
    host: pick(HOSTS),
    queueDays: fcfs ? 0 : rnd(120, 1900),
    available: pick(["Omgående", "1 jul", "1 aug", "15 aug", "1 sep"]),
    createdAt: opts.createdAt ?? Date.now(),
    filterId: opts.filterId ?? null,
  };
}

function seedListings(n) {
  const out = [];
  const now = Date.now();
  for (let i = 0; i < n; i++) {
    const l = generateListing({ createdAt: now - i * rnd(40, 320) * 1000 });
    out.push(l);
  }
  return out;
}

/* ---- sample saved filters ---- */
const SAMPLE_FILTERS = [
  { id: "F1", name: "Söder · 2:a", city: "Stockholm", areas: ["Södermalm", "Hammarby Sjöstad"], rentMin: 6000, rentMax: 13500, roomsMin: 2, roomsMax: 3, sqmMin: 45, sqmMax: 90, fcfsOnly: true, active: true, matches7d: 23 },
  { id: "F2", name: "Etta nära jobbet", city: "Stockholm", areas: ["Vasastan", "Kungsholmen"], rentMin: 4500, rentMax: 9500, roomsMin: 1, roomsMax: 1, sqmMin: 25, sqmMax: 45, fcfsOnly: true, active: true, matches7d: 11 },
  { id: "F3", name: "Familjelya 3–4 rum", city: "Stockholm", areas: ["Hägersten", "Aspudden", "Liljeholmen"], rentMin: 9000, rentMax: 18000, roomsMin: 3, roomsMax: 4, sqmMin: 65, sqmMax: 120, fcfsOnly: false, active: false, matches7d: 4 },
];

/* ---- sample notification history ---- */
const CHANNELS = ["telegram", "telegram", "telegram", "email"];
const NOTIF_STATUS = ["delivered", "delivered", "delivered", "delivered", "failed"];
function seedNotifications(n) {
  const out = [];
  let t = Date.now() - 60_000;
  for (let i = 0; i < n; i++) {
    t -= rnd(180, 5400) * 1000;
    const l = generateListing({ createdAt: t });
    out.push({
      id: "N" + (2000 + i),
      listing: l,
      channel: pick(CHANNELS),
      status: pick(NOTIF_STATUS),
      latencyMs: rnd(340, 2600),
      filterName: pick(SAMPLE_FILTERS).name,
      sentAt: t,
    });
  }
  return out;
}

/* ---- formatters ---- */
function fmtKr(n) { return n.toLocaleString("sv-SE").replace(/,/g, " "); }
function timeAgo(ms, lang) {
  const s = Math.max(0, Math.floor((Date.now() - ms) / 1000));
  const L = STRINGS[lang];
  if (s < 60) return s + L.t_s;
  const m = Math.floor(s / 60);
  if (m < 60) return m + L.t_m;
  const h = Math.floor(m / 60);
  if (h < 24) return h + L.t_h;
  const d = Math.floor(h / 24);
  return d + L.t_d;
}
function fmtClock(ms) {
  const d = new Date(ms);
  return d.toLocaleString("sv-SE", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/* ---- demo credentials (shown on the login screen) ---- */
const DEMO_CREDS = {
  user:  { email: "elin@hqrtm.se",  password: "demo1234" },
  admin: { email: "admin@hqrtm.se", password: "admin1234" },
};

/* ---- admin: users, system events ---- */
const SAMPLE_USERS = [
  { name: "Elin Bergström", email: "elin@hqrtm.se", plan: "Pro", filters: 3, tg: true, last: "2 min", status: "active" },
  { name: "Johan Lind", email: "johan.lind@gmail.com", plan: "Free", filters: 1, tg: true, last: "14 min", status: "active" },
  { name: "Sara Ahmadi", email: "sara.a@outlook.com", plan: "Pro", filters: 5, tg: true, last: "1 h", status: "active" },
  { name: "Viktor Berg", email: "viktor@berg.se", plan: "Free", filters: 2, tg: false, last: "3 h", status: "active" },
  { name: "Nora Holm", email: "nora.holm@gmail.com", plan: "Pro", filters: 4, tg: true, last: "5 h", status: "active" },
  { name: "Oskar Nyström", email: "oskar.n@telia.se", plan: "Free", filters: 0, tg: false, last: "2 d", status: "paused" },
  { name: "Maja Karlsson", email: "maja.k@icloud.com", plan: "Pro", filters: 2, tg: true, last: "18 min", status: "active" },
];
const SAMPLE_EVENTS = [
  { t: "12:42:18", lvl: "info",  msg: { sv: "WS-återanslutning OK (1.1s)", en: "WS reconnect OK (1.1s)" } },
  { t: "12:39:02", lvl: "warn",  msg: { sv: "Källan svarade långsamt (2.4s)", en: "Source slow response (2.4s)" } },
  { t: "12:31:55", lvl: "info",  msg: { sv: "Larm levererat · Telegram (0.4s)", en: "Alert delivered · Telegram (0.4s)" } },
  { t: "12:24:10", lvl: "info",  msg: { sv: "Nytt konto registrerat", en: "New account registered" } },
  { t: "12:18:47", lvl: "error", msg: { sv: "Pollning timeout — försöker igen", en: "Poll timeout — retrying" } },
  { t: "12:18:49", lvl: "info",  msg: { sv: "Pollning återupptagen", en: "Polling resumed" } },
  { t: "12:05:33", lvl: "info",  msg: { sv: "Filter skapat av användare", en: "Filter created by user" } },
];

/* ===========================================================================
   i18n — Swedish (sv) primary + English (en)
   ========================================================================= */
const STRINGS = {
  sv: {
    t_s: "s", t_m: "m", t_h: "h", t_d: "d",
    // nav
    nav_monitor: "Översikt", nav_feed: "Live-flöde", nav_filters: "Filter",
    nav_history: "Historik", nav_settings: "Konto", nav_main: "Bevakning", nav_acct: "Konto",
    connected: "Ansluten", reconnecting: "Återansluter…", offline: "Offline",
    // topbar / common
    new_match: "ny träff", new_matches: "nya träffar", show: "Visa", view_to: "Öppna på HomeQ",
    comfort: "Comfort", terminal: "Terminal", search_ph: "Sök adress, område…",
    save: "Spara", cancel: "Avbryt", create: "Skapa", delete: "Ta bort", edit: "Redigera",
    active: "Aktiv", paused: "Pausad", all: "Alla",
    // dashboard
    dash_title: "Översikt", dash_sub: "Realtidsbevakning av lediga lägenheter",
    stat_today: "Träffar idag", stat_active_filters: "Aktiva filter", stat_avg_latency: "Snittlatens", stat_fastest: "Snabbaste larm",
    live_feed: "Live-flöde", feed_sub: "Nya objekt som matchar dina filter, i realtid",
    fcfs: "Först till kvarn", fcfs_short: "FCFS", room: "rum", sqm: "m²", floor: "vån", rent_mo: "kr/mån", queue: "kö",
    paused_listings: "Pausat — inga nya larm just nu",
    empty_feed_t: "Inga träffar ännu", empty_feed_p: "Så fort ett objekt matchar dina filter dyker det upp här direkt. Larmet går också till din Telegram.",
    err_conn_t: "Anslutningen bröts", err_conn_p: "Vi försöker återansluta automatiskt. Inga larm missas — de köas på servern.",
    retry: "Försök igen", create_filter: "Skapa filter",
    only_fcfs: "Endast FCFS", newest: "Senaste", sound: "Ljud",
    // filters
    filters_title: "Filter", filters_sub: "Dina bevakningar. Slå på, pausa eller ändra när som helst.",
    new_filter: "Nytt filter", edit_filter: "Redigera filter", filter_name: "Namn på filter",
    f_city: "Stad", f_areas: "Områden / stadsdelar", f_rent: "Hyra (kr/mån)", f_rooms: "Antal rum",
    f_sqm: "Yta (m²)", f_fcfs_only: "Endast FCFS-objekt", f_fcfs_hint: "Bevaka bara ”först till kvarn”",
    min: "Min", max: "Max", to: "till", would_match: "skulle matcha nu", per_week: "/ vecka",
    delete_filter_q: "Ta bort detta filter?", delete_filter_p: "Bevakningen stoppas och kan inte återställas.",
    no_filters_t: "Inga filter ännu", no_filters_p: "Skapa ditt första filter för att börja bevaka lediga lägenheter.",
    // history
    history_title: "Historik", history_sub: "Alla larm vi har skickat till dig.",
    h_when: "Tid", h_object: "Objekt", h_filter: "Filter", h_channel: "Kanal", h_status: "Status", h_latency: "Latens",
    delivered: "Levererad", failed: "Misslyckad", pending: "Skickas",
    all_channels: "Alla kanaler", all_status: "Alla status", showing: "Visar", of: "av", prev: "Föregående", next: "Nästa",
    no_history_t: "Ingen historik ännu", no_history_p: "Dina skickade larm visas här.",
    // settings
    settings_title: "Konto", set_profile: "Profil", set_telegram: "Telegram", set_security: "Säkerhet",
    set_notif: "Notiser", set_privacy: "Integritet & data",
    name: "Namn", email: "E-post", lang_pref: "Språk", change_pw: "Byt lösenord",
    cur_pw: "Nuvarande lösenord", new_pw: "Nytt lösenord", confirm_pw: "Bekräfta lösenord",
    tg_linked: "Telegram kopplad", tg_unlinked: "Ej kopplad", tg_connect: "Koppla Telegram",
    tg_unlink: "Koppla bort", tg_test: "Skicka testlarm", tg_test_sent: "Testlarm skickat — kolla din Telegram!",
    tg_how: "Så kopplar du", tg_step1: "Öppna boten @HQRTM_bot i Telegram.", tg_step2: "Skicka koden nedan till boten.", tg_step3: "Klart — du får larm direkt.",
    tg_copy: "Kopiera kod", copied: "Kopierat!", tg_code_note: "Koden gäller i 10 minuter.",
    notif_telegram: "Telegram-larm", notif_telegram_d: "Få ett meddelande direkt vid ny träff.",
    notif_email: "E-postlarm", notif_email_d: "Daglig sammanfattning via e-post.",
    notif_sound: "Ljudsignal i appen", notif_sound_d: "Spela upp en kort signal vid ny träff i flödet.",
    privacy_t: "Dina data tillhör dig", privacy_p: "Vi sparar bara det som behövs för att skicka larm. Du kan exportera eller radera allt när som helst.",
    export_data: "Exportera mina data", privacy_policy: "Integritetspolicy", terms: "Användarvillkor",
    danger: "Riskzon", delete_acct: "Radera konto & all data", delete_acct_d: "Permanent borttagning av konto, filter och historik (GDPR).",
    delete_acct_q: "Radera ditt konto?", delete_acct_p: "Detta tar bort allt: profil, filter, historik och Telegram-koppling. Åtgärden kan inte ångras.",
    delete_acct_confirm: "Skriv RADERA för att bekräfta", delete_word: "RADERA",
    save_changes: "Spara ändringar", saved: "Sparat!",
    // auth
    welcome_back: "Välkommen tillbaka", signin_sub: "Logga in för att se ditt flöde.",
    create_acct: "Skapa konto", signup_sub: "Bevaka bostäder och få larm på sekunden.",
    sign_in: "Logga in", sign_up: "Registrera dig", password: "Lösenord", forgot: "Glömt lösenord?",
    no_acct: "Har du inget konto?", have_acct: "Har du redan ett konto?",
    or: "eller", consent: "Jag godkänner",
    consent_terms: "användarvillkoren", consent_and: "och", consent_privacy: "integritetspolicyn",
    consent_req: "Du måste godkänna villkoren för att fortsätta.",
    err_email: "Ange en giltig e-postadress.", err_pw: "Minst 8 tecken.",
    // onboarding
    ob_title: "Kom igång", ob_step_tg: "Koppla Telegram", ob_step_filter: "Skapa filter",
    ob_tg_t: "Få larm där du redan är", ob_tg_p: "Koppla Telegram så landar varje ny träff direkt i din ficka — på sekunden.",
    ob_skip: "Hoppa över", ob_continue: "Fortsätt", ob_finish: "Till mitt flöde",
    ob_filter_t: "Vad letar du efter?", ob_filter_p: "Vi börjar bevaka direkt. Du kan ändra allt sen.",
    // landing
    lp_eyebrow: "Realtidsbevakning av hyresrätter",
    lp_h1a: "Den lediga lägenheten är din —", lp_h1b: "om du är först.",
    lp_sub: "HQRTM bevakar HomeQ dygnet runt och larmar dig på sekunden när ett objekt matchar dina filter. Vid ”först till kvarn” avgör sekunderna.",
    lp_get_started: "Kom igång gratis", lp_signin: "Logga in", lp_live: "Live nu",
    feat_rt_t: "Larm på sekunden", feat_rt_p: "WebSocket-flöde i realtid. Inget refreshande — nya objekt dyker upp direkt.",
    feat_tg_t: "Direkt till Telegram", feat_tg_p: "Få ett tryckbart larm i fickan i samma sekund som objektet publiceras.",
    feat_fl_t: "Precisa filter", feat_fl_p: "Stad, område, hyra, rum, yta och ”endast FCFS”. Bevaka exakt det du vill ha.",
    lp_footer: "Bevakar HomeQ · Byggd för ”först till kvarn”",
    // demo + admin
    demo_title: "Testinloggning", demo_hint: "Logga in direkt — ingen registrering behövs.",
    role_user: "Användare", role_admin: "Admin", demo_as: "Logga in som",
    nav_admin: "Drift", nav_ops: "Drift",
    admin_title: "Driftpanel", admin_sub: "Källstatus, användare och systemhälsa",
    src_title: "Källa · HomeQ", src_online: "Tillgänglig", src_latency: "Pollningslatens",
    src_lastpoll: "Senaste pollning", src_uptime: "Drifttid 24h", src_region: "Region",
    m_users: "Användare", m_active: "Aktiva nu", m_alerts: "Larm idag", m_ws: "WS-anslutningar",
    users_title: "Användare", u_plan: "Plan", u_filters: "Filter", u_tg: "Telegram", u_last: "Senast aktiv", u_status: "Status",
    log_title: "Senaste händelser", linked_short: "Kopplad", unlinked_short: "Ej kopplad",
  },
  en: {
    t_s: "s", t_m: "m", t_h: "h", t_d: "d",
    nav_monitor: "Overview", nav_feed: "Live feed", nav_filters: "Filters",
    nav_history: "History", nav_settings: "Account", nav_main: "Monitoring", nav_acct: "Account",
    connected: "Connected", reconnecting: "Reconnecting…", offline: "Offline",
    new_match: "new match", new_matches: "new matches", show: "Show", view_to: "Open on HomeQ",
    comfort: "Comfort", terminal: "Terminal", search_ph: "Search address, area…",
    save: "Save", cancel: "Cancel", create: "Create", delete: "Delete", edit: "Edit",
    active: "Active", paused: "Paused", all: "All",
    dash_title: "Overview", dash_sub: "Real-time monitoring of available apartments",
    stat_today: "Matches today", stat_active_filters: "Active filters", stat_avg_latency: "Avg. latency", stat_fastest: "Fastest alert",
    live_feed: "Live feed", feed_sub: "New listings matching your filters, in real time",
    fcfs: "First come, first served", fcfs_short: "FCFS", room: "rooms", sqm: "m²", floor: "fl", rent_mo: "kr/mo", queue: "queue",
    paused_listings: "Paused — no new alerts right now",
    empty_feed_t: "No matches yet", empty_feed_p: "The moment a listing matches your filters it shows up here instantly. The alert also hits your Telegram.",
    err_conn_t: "Connection lost", err_conn_p: "We’re reconnecting automatically. No alerts are missed — they’re queued on the server.",
    retry: "Retry", create_filter: "Create filter",
    only_fcfs: "FCFS only", newest: "Newest", sound: "Sound",
    filters_title: "Filters", filters_sub: "Your monitors. Switch on, pause, or edit anytime.",
    new_filter: "New filter", edit_filter: "Edit filter", filter_name: "Filter name",
    f_city: "City", f_areas: "Areas / districts", f_rent: "Rent (kr/mo)", f_rooms: "Rooms",
    f_sqm: "Size (m²)", f_fcfs_only: "FCFS listings only", f_fcfs_hint: "Only watch “first come, first served”",
    min: "Min", max: "Max", to: "to", would_match: "would match now", per_week: "/ week",
    delete_filter_q: "Delete this filter?", delete_filter_p: "Monitoring stops and can’t be restored.",
    no_filters_t: "No filters yet", no_filters_p: "Create your first filter to start monitoring available apartments.",
    history_title: "History", history_sub: "Every alert we’ve sent you.",
    h_when: "When", h_object: "Listing", h_filter: "Filter", h_channel: "Channel", h_status: "Status", h_latency: "Latency",
    delivered: "Delivered", failed: "Failed", pending: "Sending",
    all_channels: "All channels", all_status: "All statuses", showing: "Showing", of: "of", prev: "Prev", next: "Next",
    no_history_t: "No history yet", no_history_p: "Your sent alerts will appear here.",
    settings_title: "Account", set_profile: "Profile", set_telegram: "Telegram", set_security: "Security",
    set_notif: "Notifications", set_privacy: "Privacy & data",
    name: "Name", email: "Email", lang_pref: "Language", change_pw: "Change password",
    cur_pw: "Current password", new_pw: "New password", confirm_pw: "Confirm password",
    tg_linked: "Telegram linked", tg_unlinked: "Not linked", tg_connect: "Connect Telegram",
    tg_unlink: "Unlink", tg_test: "Send test alert", tg_test_sent: "Test alert sent — check your Telegram!",
    tg_how: "How to link", tg_step1: "Open the @HQRTM_bot in Telegram.", tg_step2: "Send the code below to the bot.", tg_step3: "Done — you’ll get alerts instantly.",
    tg_copy: "Copy code", copied: "Copied!", tg_code_note: "Code valid for 10 minutes.",
    notif_telegram: "Telegram alerts", notif_telegram_d: "Get a message instantly on every new match.",
    notif_email: "Email alerts", notif_email_d: "Daily summary by email.",
    notif_sound: "In-app sound", notif_sound_d: "Play a short chime on a new match in the feed.",
    privacy_t: "Your data belongs to you", privacy_p: "We only store what’s needed to send alerts. Export or erase everything anytime.",
    export_data: "Export my data", privacy_policy: "Privacy policy", terms: "Terms of service",
    danger: "Danger zone", delete_acct: "Delete account & all data", delete_acct_d: "Permanent removal of account, filters and history (GDPR).",
    delete_acct_q: "Delete your account?", delete_acct_p: "This removes everything: profile, filters, history and Telegram link. This can’t be undone.",
    delete_acct_confirm: "Type DELETE to confirm", delete_word: "DELETE",
    save_changes: "Save changes", saved: "Saved!",
    welcome_back: "Welcome back", signin_sub: "Sign in to see your feed.",
    create_acct: "Create account", signup_sub: "Monitor listings and get alerts in seconds.",
    sign_in: "Sign in", sign_up: "Sign up", password: "Password", forgot: "Forgot password?",
    no_acct: "No account yet?", have_acct: "Already have an account?",
    or: "or", consent: "I agree to the",
    consent_terms: "terms of service", consent_and: "and", consent_privacy: "privacy policy",
    consent_req: "You must accept the terms to continue.",
    err_email: "Enter a valid email address.", err_pw: "At least 8 characters.",
    ob_title: "Get started", ob_step_tg: "Link Telegram", ob_step_filter: "Create filter",
    ob_tg_t: "Get alerts where you already are", ob_tg_p: "Link Telegram and every new match lands straight in your pocket — within a second.",
    ob_skip: "Skip", ob_continue: "Continue", ob_finish: "Go to my feed",
    ob_filter_t: "What are you looking for?", ob_filter_p: "We’ll start monitoring right away. You can change everything later.",
    lp_eyebrow: "Real-time rental monitoring",
    lp_h1a: "The empty apartment is yours —", lp_h1b: "if you’re first.",
    lp_sub: "HQRTM watches HomeQ around the clock and alerts you within a second when a listing matches your filters. With “first come, first served”, seconds decide.",
    lp_get_started: "Get started free", lp_signin: "Sign in", lp_live: "Live now",
    feat_rt_t: "Alerts in a second", feat_rt_p: "Real-time WebSocket feed. No refreshing — new listings appear instantly.",
    feat_tg_t: "Straight to Telegram", feat_tg_p: "A tappable alert in your pocket the second a listing goes live.",
    feat_fl_t: "Precise filters", feat_fl_p: "City, area, rent, rooms, size and “FCFS only”. Monitor exactly what you want.",
    lp_footer: "Monitoring HomeQ · Built for “first come, first served”",
    demo_title: "Demo login", demo_hint: "Sign in instantly — no signup needed.",
    role_user: "User", role_admin: "Admin", demo_as: "Sign in as",
    nav_admin: "Ops", nav_ops: "Ops",
    admin_title: "Ops panel", admin_sub: "Source status, users and system health",
    src_title: "Source · HomeQ", src_online: "Online", src_latency: "Poll latency",
    src_lastpoll: "Last poll", src_uptime: "Uptime 24h", src_region: "Region",
    m_users: "Users", m_active: "Active now", m_alerts: "Alerts today", m_ws: "WS connections",
    users_title: "Users", u_plan: "Plan", u_filters: "Filters", u_tg: "Telegram", u_last: "Last active", u_status: "Status",
    log_title: "Recent events", linked_short: "Linked", unlinked_short: "Not linked",
  },
};

Object.assign(window, {
  AREAS, STREETS, generateListing, seedListings, SAMPLE_FILTERS,
  seedNotifications, fmtKr, timeAgo, fmtClock, STRINGS, pick, rnd,
  DEMO_CREDS, SAMPLE_USERS, SAMPLE_EVENTS, realMeta,
});
