# HQRTM Snabbansök — webbläsartillägg (klient)

En **legitim** klient som körs i användarens **egen webbläsare** och hjälper hen att agera snabbt
på matchande bostäder — utan att lagra plattformslösenord och utan automatisk inskickning.

## Vad den gör
- **Loggar in** mot HQRTM-API:t och sparar token + ansökningsprofil **lokalt** (`chrome.storage.local`).
- **Listar matchande objekt** (`/api/listings?matched=true`) i popupen — med område, rum, yta,
  **våning/balkong/kök** (där källan anger det) och hyra; ett klick öppnar annonsen hos källan
  (där användaren själv är inloggad).
- **Badge** på ikonen visar antal matchningar (uppdateras periodiskt).
- På annonssidor (homeq.se / qasa.com / bostad.stockholm.se) visar en liten panel din profil med
  **Kopiera**-knappar, **«Fyll i formuläret»** (fältmappning, se nedan) och «Endast presentation».

## Fältmappning (autofyll)
«Fyll i formuläret» matchar dina profilfält (presentation, sysselsättning, inkomst, telefon,
hushåll, inflytt) mot sidans `input`/`textarea`/`select`. Matchningen är **heuristisk** och tål
att sidorna ändras:
- **Etikett** (`<label>`, `aria-label`, omslutande/föregående text) väger tyngst, sedan
  `name`/`id`/`placeholder`/`autocomplete`, plus en bonus när inmatningstypen stämmer (tel/number/date).
- **Platsledtrådar** per domän (`PLATFORM_HINTS` i `content.js`) ger en direkt selektorträff där den är känd.
- Värden sätts via den **native** value-settern + `input`/`change`-event, så React/Vue-formulär reagerar.
  Datum normaliseras till `yyyy-mm-dd`, belopp till siffror.

Inget skickas — du granskar och trycker själv. Lägg till fler källor genom att utöka `PLATFORM_HINTS`
och `host_permissions`/`content_scripts` i `manifest.json`.

## Ikoner
`icons/icon{16,32,48,128}.png` (HQRTM-grön rundad kvadrat + vitt hus). Genereras utan beroenden:
`python extension/icons/gen_icons.py` (ändra färg/form i `gen_icons.py` vid behov).

## Gränser (medvetet)
- **Inga plattformslösenord** lagras — varken lokalt eller på server. Användaren är själv inloggad
  hos plattformen i sin webbläsare.
- **Ingen automatisk inskickning.** Tillägget fyller i / kopierar; användaren **granskar och skickar
  själv**. (Se beslut i `CLAUDE.md` → Beslutslogg: autoclicker/autoansökan byggs inte.)

## Installera (utvecklingsläge)
1. Chrome/Edge → `chrome://extensions` → slå på **Developer mode**.
2. **Load unpacked** → välj mappen `extension/`.
3. Klicka på ikonen → logga in (t.ex. `petros` / `petrosBest`).

## Filer
- `manifest.json` — MV3-manifest (storage, alarms, host_permissions, ikoner).
- `popup.html` / `popup.js` — inloggning, matchningar, profil (lokalt + sync).
- `content.js` — hjälppanel + fältmappning/autofyll på annonssidor.
- `background.js` — badge med matchningsantal.
- `icons/` — ikoner + generatorn `gen_icons.py`.

## Att göra senare
- Refresh-token-hantering, pushnotis vid ny match, fler källor (utöka `PLATFORM_HINTS`),
  butikspublicering (Chrome Web Store / AMO).
