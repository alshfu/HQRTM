# frontend-build — production-сборка Tailwind

Сейчас фронтенд использует **Tailwind Play CDN** (`<script src="cdn.tailwindcss.com">` в `base.html`) —
быстро для прототипа, но не для прода (тянет JIT в рантайме, нет purge).

## Переезд на production-сборку (Фаза 5 полировка / Фаза 8)

```bash
cd frontend-build
npm install
npm run build      # → ../web/static/css/app.css (purged, minified)
```

После сборки в `base.html` заменить CDN-скрипт на:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
```

`content` в `tailwind.config.js` сканирует `../web/templates/**/*.html` и `../web/static/js/**/*.js`,
поэтому используемые классы не будут вырезаны.
