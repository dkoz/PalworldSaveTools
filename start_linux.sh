#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = "--infologs" ]; then
    python3 "$SCRIPT_DIR/setup.py" --infologs
else
    python3 "$SCRIPT_DIR/setup.py"
fi
exit $?
