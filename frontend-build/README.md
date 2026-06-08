# frontend-build — production-bygge av Tailwind

Frontend använder **byggd Tailwind CSS** (purged + minified), inte Play CDN.
`web/templates/base.html` laddar byggresultatet:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
```

Den byggda filen `web/static/css/app.css` är **incheckad** i repot — appen fungerar utan
Node-toolchain (CI/driftsättning behöver inte bygga). Node behövs bara för att bygga om CSS.

## Vad finns var

- `input.css` — `@tailwind`-direktiv + HQRTM:s egna tokens/komponenter
  (`.card`, `.input`, `.btn-accent`, `.navlink.active`, bakgrund `body`). **Källa** —
  tidigare låg dessa regler inline i `base.html`.
- `tailwind.config.js` — tema (`accent` #15b878, typsnitt Schibsted Grotesk / JetBrains Mono),
  `darkMode: "class"`, `content` skannar `../web/templates/**/*.html` och `../web/static/js/**/*.js`
  (klasser från inline-`<script>` och `api.js` kommer också med i purge).
- `package.json` — Tailwind CLI v3 + skripten `build`/`watch`.

## Bygga om (efter ändring av mallar/klasser/tema)

```bash
cd frontend-build
npm install          # en gång (node_modules i .gitignore)
npm run build        # → ../web/static/css/app.css (purged, minified)
# för utveckling:
npm run watch        # bygger om vid ändringar
```

Efter ombyggnad **checka in den uppdaterade `web/static/css/app.css`**.

> ⚠️ Tailwind tar bort oanvända klasser. Om en klass byggs i JS via konkatenering (inte som en
> hel sträng) ser purge den inte — skriv klasser i sin helhet eller lägg dem i safelist i
> `tailwind.config.js`.
