# frontend-build — production-сборка Tailwind

Фронтенд использует **собранный Tailwind CSS** (purged + minified), а не Play CDN.
`web/templates/base.html` грузит результат сборки:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
```

Собранный файл `web/static/css/app.css` **закоммичен** в репозиторий — приложение работает
без Node-тулчейна (CI/деплою сборка не нужна). Node нужен только для пересборки CSS.

## Что где

- `input.css` — `@tailwind`-директивы + кастомные токены/компоненты HQRTM
  (`.card`, `.input`, `.btn-accent`, `.navlink.active`, фон `body`). **Источник истины** —
  раньше эти правила жили inline в `base.html`.
- `tailwind.config.js` — тема (`accent` #15b878, шрифты Schibsted Grotesk / JetBrains Mono),
  `darkMode: "class"`, `content` сканирует `../web/templates/**/*.html` и `../web/static/js/**/*.js`
  (классы из inline-`<script>` и `api.js` тоже попадают в purge).
- `package.json` — Tailwind CLI v3 + скрипты `build`/`watch`.

## Пересборка (после правки шаблонов/классов/темы)

```bash
cd frontend-build
npm install          # один раз (node_modules в .gitignore)
npm run build        # → ../web/static/css/app.css (purged, minified)
# для разработки:
npm run watch        # пересобирает при изменениях
```

После пересборки **закоммить обновлённый `web/static/css/app.css`**.

> ⚠️ Tailwind вырезает неиспользуемые классы. Если класс строится в JS конкатенацией
> (а не цельной строкой), purge его не увидит — пиши классы целиком или добавь в safelist
> в `tailwind.config.js`.
