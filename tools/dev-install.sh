#!/bin/bash
# Install the working tree into the local Kodi and reload the skin.
# Usage: tools/dev-install.sh
#
# The exclude list here is the source of truth that tools/build.py mirrors,
# which in turn mirrors the export-ignore list in .gitattributes. All three have
# to agree; any one of them alone is a file that ships when it should not.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.kodi/addons/skin.contuary"
KODI_RPC="http://localhost:8080/jsonrpc"

# Whether addon.xml is about to change matters: Kodi reads the skin's <res>
# declaration only at skin load, so a resolution change needs a full restart and
# ReloadSkin() is not enough. Checked before the rsync overwrites it.
res_change=0
if [[ -f "$DEST/addon.xml" ]] && ! cmp -s "$SRC/addon.xml" "$DEST/addon.xml"; then
    res_change=1
fi

# --delete-excluded as well as --delete: plain --exclude *protects* an existing
# copy in the destination, so without it a file that was shipped before being
# added to this list would sit in the installed tree forever.
rsync -a --delete --delete-excluded \
    --exclude '.git' --exclude '.github' --exclude '.gitignore' \
    --exclude '.gitattributes' --exclude '.git-blame-ignore-revs' \
    --exclude '.venv' --exclude '.tox' \
    --exclude '__pycache__' --exclude '.mypy_cache' --exclude '.pytest_cache' \
    --exclude 'docs' --exclude 'tools' --exclude 'dist' \
    --exclude 'build.sh' --exclude 'README.md' --exclude 'Screenshot.png' \
    --exclude 'ICONS_ONLY_MENU_PLAN.md' \
    "$SRC/" "$DEST/"

if ! curl -s -m 2 -u kodi:kodi -o /dev/null "$KODI_RPC" \
        -X POST -H 'Content-Type: application/json' \
        -d '{"jsonrpc":"2.0","id":1,"method":"JSONRPC.Ping"}'; then
    echo "installed to $DEST (Kodi not reachable — skipped skin reload)"
    exit 0
fi

# ReloadSkin() re-reads the xml/ tree; it does NOT re-read addon.xml.
"$HOME/bin/kodi-builtin" 'ReloadSkin()'
echo "installed skin.contuary and reloaded the skin"

if [[ "$res_change" == 1 ]]; then
    echo
    echo "NOTE: addon.xml changed. If that was the <res> line, ReloadSkin() will"
    echo "      not pick it up — Kodi parses <res> only at skin load. Restart Kodi."
fi
# New strings.po ids are cached for the process lifetime too: if a new label
# renders blank after a reload, restart before debugging further.
