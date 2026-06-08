# HQRTM Snabbansök — webbläsartillägg (klient)

En **legitim** klient som körs i användarens **egen webbläsare** och hjälper hen att agera snabbt
på matchande bostäder — utan att lagra plattformslösenord och utan automatisk inskickning.

## Vad den gör
- **Loggar in** mot HQRTM-API:t och sparar token + ansökningsprofil **lokalt** (`chrome.storage.local`).
- **Listar matchande objekt** (`/api/listings?matched=true`) i popupen; ett klick öppnar annonsen
  hos källan (där användaren själv är inloggad).
- **Badge** på ikonen visar antal matchningar (uppdateras periodiskt).
- På annonssidor (homeq.se / qasa.com / bostad.stockholm.se) visar en liten panel din profil med
  **Kopiera**-knappar och «Fyll i presentation» som fyller sidans textfält.

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
- `manifest.json` — MV3-manifest (storage, alarms, host_permissions).
- `popup.html` / `popup.js` — inloggning, matchningar, profil (lokalt + sync).
- `content.js` — hjälppanel + autofyll på annonssidor.
- `background.js` — badge med matchningsantal.

## Att göra senare
- Ikoner (16/48/128 px), fältmappning per plattform för smartare autofyll, refresh-token-hantering,
  pushnotis vid ny match.
