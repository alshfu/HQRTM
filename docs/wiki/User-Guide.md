# Guide för användare

**Användare** (roll `user`) — registrerad mottagare av aviseringar med egna filter.

## 1. Registrering och inloggning
- `/register` — e-post + lösenord (≥ 8 tecken) + samtycke (GDPR). Inloggning sker automatiskt.
- `/login` — återkommande inloggning. Sessionen lagras i webbläsaren (JWT); access-token förnyas automatiskt.

## 2. Panel (`/app`)
Till vänster — navigering: **Flöde**, **Filter**, **Aviseringar**, **Konto** (inställningar).

### Flöde
- Visar annonser som **matchar dina filter** (växeln «Endast matchade»).
- Kort: titel, område, rum, yta, hyra, källplattform, märket «FÖRST TILL KVARN» för FCFS.
  Knappen **Öppna →** leder direkt till annonsen hos källan.

### Filter
- **Skapa**: namn, område/stad, maxhyra, minsta antal rum, «endast FCFS».
- **Pausa/Aktivera** — stäng av ett filter tillfälligt utan att radera.
- **Radera** — ta bort filtret.
- Du kan skapa flera filter; träffar från valfritt aktivt filter hamnar i flödet/aviseringarna.

### Aviseringar (historik)
- Lista över skickade aviseringar med paginering, leveransstatus och latens.

### Konto (inställningar)
- **Profil**: e-post, roll.
- **Ansökningsprofil**: spara presentation, sysselsättning, inkomst, telefon, hushåll och önskad
  inflytt en gång — «Kopiera presentation» låter dig klistra in dina uppgifter på sekunder när du
  ansöker (ett-tryck-ansökan via «Ansök» i flödet/Telegram leder direkt till källans annons).
- **Telegram**: knappen «Koppla Telegram» genererar en kod och deep-link. Öppna boten, tryck
  «Start» — kontot kopplas och matchande FCFS-annonser skickas till Telegram med länk till källan.
- **Radera konto (GDPR)**: knappen «Radera mitt konto» raderar oåterkalleligt kontot och all data
  (filter, aviseringar).

## 3. Så kommer aviseringar
Den centrala pollern bevakar plattformarna → hittar FCFS → jämför med dina filter →
skickar en avisering med länk (mål ≤ 1,5 s). Boten **ansöker inte** åt dig — den aviserar bara.

## 4. Integritet (GDPR)
Endast e-post, Telegram chat_id och dina filter lagras. Lösenordet — som hash (Argon2).
Radering av kontot tar bort all relaterad data. Se [Efterlevnad](Compliance).
