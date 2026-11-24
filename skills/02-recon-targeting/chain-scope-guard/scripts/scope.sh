#!/usr/bin/env bash
# Scope-guard wrapper. On git-bash, native python3 cannot read MSYS paths like
# /c/Users/...; cygpath converts them. In WSL there is no cygpath, and the
# /mnt/c/... path works for Linux python3 as-is.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/chain_scope_guard.py"
if command -v cygpath >/dev/null 2>&1; then
    SCRIPT="$(cygpath -w "$SCRIPT")"
fi
exec python3 "$SCRIPT" "$@"
