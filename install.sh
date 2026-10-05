#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1 &&    python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  exec python3 "$ROOT_DIR/system/install/installer.py" "$@"
fi

if command -v python >/dev/null 2>&1 &&    python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  exec python "$ROOT_DIR/system/install/installer.py" "$@"
fi

echo "Python 3.10 or newer is required." >&2
exit 1
