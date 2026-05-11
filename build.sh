#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

out_dir="${1:-$PWD}"
suffix="${2:+"-$2"}"
mkdir -p "$out_dir"

version="$(sed -n 's/.*<addon[^>]* version="\([^"]*\)".*/\1/p' addon.xml | head -1)"
if [[ -z "$version" ]]; then
    echo "could not extract version from addon.xml" >&2
    exit 1
fi

zip_path="$out_dir/skin.contuary-${version}${suffix}.zip"

git archive --format=zip --prefix=skin.contuary/ -o "$zip_path" HEAD

echo "wrote $zip_path"
