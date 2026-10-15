#!/bin/sh
# No Python/Node prerequisite. Run with sh; only local help checks follow setup.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project=${1:-"$here/../laRkdown"}
feature=${2:-core}
cache=${XDG_CACHE_HOME:-"$HOME/.cache"}/laRkdown
case "$feature" in core|base|pptx) ;; *) echo 'Feature must be core, base or pptx.' >&2; exit 1;; esac
if [ ! -f "$project/run.py" ] || [ -f "$project/../tools/build_release.py" ]; then
    echo 'Use an extracted research directory.' >&2; exit 1
fi
awk '/"workspace_kind"[[:space:]]*:[[:space:]]*"personal-research"/ {found=1} END {exit !found}' "$project/.agents/config/project-layout.json" || { echo 'Unsupported research directory.' >&2; exit 1; }
selected=''
for candidate in python3 python python3.14 python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if selected=$("$candidate" -I -c 'import sys,ssl,xml.etree.ElementTree; assert (3,11)<=sys.version_info[:2]<(3,15); print(sys.executable)' 2>/dev/null); then break; else selected=''; fi
    fi
done
if [ -z "$selected" ]; then
    system=$(uname -s | tr '[:upper:]' '[:lower:]')
    case "$(uname -m)" in x86_64) arch=amd64;; arm64|aarch64) arch=arm64;; *) echo 'Unsupported architecture.' >&2; exit 1;; esac
    row=$(awk -F '\t' -v key="$system-$arch" '$1=="uv" && $2==key {print $3 " " $4 " " $5}' "$here/runtime-assets.tsv")
    [ -n "$row" ] || { echo 'No reviewed bootstrap asset.' >&2; exit 1; }
    version=${row%% *}; rest=${row#* }; hash=${rest%% *}; url=${rest#* }
    case "$url" in https://github.com/astral-sh/uv/releases/download/*) ;; *) exit 1;; esac
    folder="$cache/bootstrap/uv-$version-$system-$arch"
    for path in "$cache" "$cache/bootstrap" "$folder"; do [ ! -L "$path" ] || { echo 'Linked runtime caches are unsupported.' >&2; exit 1; }; done
    mkdir -p "$folder"
    hash_file() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
    archive="$folder/uv.tar.gz"
    part=$(mktemp "$folder/download.XXXXXXXX")
    stage=$(mktemp -d "$folder/stage.XXXXXXXX")
    # Cleanup only these exact temporary paths, using the same shell.
    trap 'rm -f -- "$part"; if [ -f "$stage/uv" ]; then rm -f -- "$stage/uv"; fi; rmdir -- "$stage" 2>/dev/null || true' EXIT HUP INT TERM
    if [ ! -f "$archive" ]; then
        curl --fail --location --connect-timeout 15 --max-time 120 --retry 1 --output "$part" "$url"
        [ "$(hash_file "$part")" = "$hash" ] || { echo 'Bootstrap checksum mismatch.' >&2; exit 1; }
        mv -n -- "$part" "$archive"
    fi
    [ "$(hash_file "$archive")" = "$hash" ] || { echo 'Cached bootstrap archive changed.' >&2; exit 1; }
    # Extract only the known executable to a chosen filename; never unpack archive paths.
    member=$(tar -tzf "$archive" | awk '/(^|\/)uv$/ {print}')
    [ "$(printf '%s\n' "$member" | wc -l | tr -d ' ')" = 1 ] || exit 1
    tar -xOzf "$archive" "$member" > "$stage/uv"
    uv="$folder/uv"
    if [ -f "$uv" ]; then
        [ "$(hash_file "$uv")" = "$(hash_file "$stage/uv")" ] || { echo 'Cached bootstrap executable changed.' >&2; exit 1; }
    else
        chmod 755 "$stage/uv"
        mv -n -- "$stage/uv" "$uv"
    fi
    export UV_PYTHON_INSTALL_DIR="$cache/python" UV_PYTHON_INSTALL_BIN=0 UV_PYTHON_INSTALL_REGISTRY=0 UV_NO_PROGRESS=1 UV_NO_CONFIG=1
    python_version=$(awk -F '\t' '$1=="python" {print $3}' "$here/runtime-assets.tsv")
    "$uv" python install "$python_version" --no-bin --no-registry >/dev/null
    selected=$("$uv" python find --managed-python "$python_version")
fi
"$selected" "$here/setup_larkdown.py" --project "$project" --feature "$feature" --python "$selected" --cache "$cache"
