#!/usr/bin/env bash
#
# sync-wiki.sh — spegling av docs/wiki/ → GitHub Wiki.
#
# Källa — docs/wiki/*.md i huvudrepot (versionshanteras, granskas i PR).
# GitHub Wiki — spegel: vi redigerar i docs/wiki/, sedan kör vi detta skript.
# Redigera INTE Wiki direkt i webben — det skrivs över vid nästa spegling.
#
# Innan första körningen måste Wiki initieras via UI (en gång):
#   Settings → Features → aktivera Wikis, sedan fliken Wiki → Create the first page.
# Tills detta är gjort är *.wiki.git inte tillgänglig för push.
#
# Användning:
#   ./scripts/sync-wiki.sh ["commit-meddelande"]
#
set -euo pipefail

# --- plats ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$REPO_ROOT/docs/wiki"

COMMIT_MSG="${1:-sync wiki from docs/wiki/}"

# --- beräkna wiki-URL från origin ---
if ! ORIGIN_URL="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null)"; then
  echo "FEL: hittade inte git remote 'origin' i $REPO_ROOT" >&2
  exit 1
fi
# https://github.com/<owner>/<repo>.git  ELLER  git@github.com:<owner>/<repo>.git
WIKI_URL="${ORIGIN_URL%.git}.wiki.git"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "FEL: källkatalogen $SRC_DIR finns inte" >&2
  exit 1
fi

echo "Källa:    $SRC_DIR"
echo "Wiki:     $WIKI_URL"

# --- kontrollera att wiki är tillgänglig ---
if ! git ls-remote "$WIKI_URL" >/dev/null 2>&1; then
  cat >&2 <<EOF

FEL: Wiki-repot är inte tillgängligt ($WIKI_URL).
Troligen är Wiki ännu inte initierad. En gång via UI:
  1) Settings → Features → aktivera «Wikis»
  2) fliken Wiki → «Create the first page» → Save Page
Kör sedan skriptet igen.
EOF
  exit 1
fi

# --- klona till temporär katalog ---
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

git clone --quiet "$WIKI_URL" "$WORK_DIR/wiki"
cd "$WORK_DIR/wiki"

# bestäm standardgren (wiki har vanligtvis master)
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo master)"

# --- synkronisera innehållet (tar bort gammalt, kopierar aktuellt) ---
# Vi rensar bara .md i roten av wiki, systemfiler (.git) rör vi inte.
find . -maxdepth 1 -name '*.md' -delete
cp "$SRC_DIR"/*.md .

git add -A
if git diff --cached --quiet; then
  echo "Inga ändringar — Wiki är redan aktuell."
  exit 0
fi

git commit --quiet -m "$COMMIT_MSG"
git push --quiet origin "$BRANCH"

echo "Klart: pushade $(ls "$SRC_DIR"/*.md | wc -l | tr -d ' ') sidor till grenen '$BRANCH'."
echo "Öppna: ${ORIGIN_URL%.git}/wiki"
