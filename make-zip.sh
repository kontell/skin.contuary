#!/usr/bin/env bash
# Build a Kodi-installable zip of the addon from the current HEAD commit.
#
# Output: skin.contuary-<version>.zip in the directory passed as $1
# (default: current working dir). The zip layout is:
#
#     skin.contuary/
#         addon.xml
#         ...
#
# `git archive` honours .gitattributes export-ignore, so build/dev
# artefacts (CLAUDE.md, Screenshot.png, .gitattributes itself, this
# script) are excluded automatically.

set -euo pipefail

cd "$(dirname "$0")"

out_dir="${1:-$PWD}"
mkdir -p "$out_dir"

version="$(sed -n 's/.*<addon[^>]* version="\([^"]*\)".*/\1/p' addon.xml | head -1)"
if [[ -z "$version" ]]; then
    echo "could not extract version from addon.xml" >&2
    exit 1
fi

zip_path="$out_dir/skin.contuary-$version.zip"

git archive --format=zip --prefix=skin.contuary/ -o "$zip_path" HEAD

echo "wrote $zip_path"
