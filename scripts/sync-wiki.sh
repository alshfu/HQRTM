#!/usr/bin/env bash
#
# sync-wiki.sh — зеркалирование docs/wiki/ → GitHub Wiki.
#
# Источник истины — docs/wiki/*.md в основном репо (версионируется, ревью в PR).
# GitHub Wiki — зеркало: правим в docs/wiki/, затем запускаем этот скрипт.
# НЕ редактировать Wiki напрямую в вебе — затрётся при следующей синхронизации.
#
# Перед первым запуском Wiki нужно инициализировать через UI (один раз):
#   Settings → Features → включить Wikis, затем вкладка Wiki → Create the first page.
# Пока этого нет, *.wiki.git недоступен для push.
#
# Использование:
#   ./scripts/sync-wiki.sh ["сообщение коммита"]
#
set -euo pipefail

# --- расположение ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$REPO_ROOT/docs/wiki"

COMMIT_MSG="${1:-sync wiki from docs/wiki/}"

# --- вычислить URL wiki из origin ---
if ! ORIGIN_URL="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null)"; then
  echo "ОШИБКА: не найден git remote 'origin' в $REPO_ROOT" >&2
  exit 1
fi
# https://github.com/<owner>/<repo>.git  ИЛИ  git@github.com:<owner>/<repo>.git
WIKI_URL="${ORIGIN_URL%.git}.wiki.git"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "ОШИБКА: нет каталога источника $SRC_DIR" >&2
  exit 1
fi

echo "Источник: $SRC_DIR"
echo "Wiki:     $WIKI_URL"

# --- проверить доступность wiki ---
if ! git ls-remote "$WIKI_URL" >/dev/null 2>&1; then
  cat >&2 <<EOF

ОШИБКА: Wiki-репозиторий недоступен ($WIKI_URL).
Скорее всего Wiki ещё не инициализирован. Один раз через UI:
  1) Settings → Features → включить «Wikis»
  2) вкладка Wiki → «Create the first page» → Save Page
После этого запусти скрипт снова.
EOF
  exit 1
fi

# --- клонировать во временный каталог ---
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

git clone --quiet "$WIKI_URL" "$WORK_DIR/wiki"
cd "$WORK_DIR/wiki"

# определить ветку по умолчанию (у wiki обычно master)
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo master)"

# --- синхронизировать содержимое (удаляем старое, копируем актуальное) ---
# Чистим только .md в корне wiki, служебное (.git) не трогаем.
find . -maxdepth 1 -name '*.md' -delete
cp "$SRC_DIR"/*.md .

git add -A
if git diff --cached --quiet; then
  echo "Изменений нет — Wiki уже актуальна."
  exit 0
fi

git commit --quiet -m "$COMMIT_MSG"
git push --quiet origin "$BRANCH"

echo "Готово: запушено $(ls "$SRC_DIR"/*.md | wc -l | tr -d ' ') страниц в ветку '$BRANCH'."
echo "Открыть: ${ORIGIN_URL%.git}/wiki"
