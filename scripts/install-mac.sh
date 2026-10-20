#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9"
MAC_PY="$ROOT/host/mac.py"
PLIST_SRC="$ROOT/scripts/com.tpte.span-kvm.mac.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.tpte.span-kvm.mac.plist"
UID_NUM="$(id -u)"
DOMAIN="gui/$UID_NUM"
LABEL="com.tpte.span-kvm.mac"

if [[ ! -x "$PYTHON" ]]; then
	echo "missing $PYTHON" >&2
	exit 1
fi
if [[ ! -f "$MAC_PY" ]]; then
	echo "missing $MAC_PY" >&2
	exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__MAC_PY__|$MAC_PY|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
pkill -f "$MAC_PY" 2>/dev/null || true
sleep 0.3
launchctl bootstrap "$DOMAIN" "$PLIST_DST"
launchctl enable "$DOMAIN/$LABEL"
launchctl kickstart -k "$DOMAIN/$LABEL"
sleep 1
if tail -5 /tmp/span-mac.log | grep -q "span-mac running"; then
	echo "span-mac ok"
	exit 0
fi
echo "span-mac failed; see /tmp/span-mac.log" >&2
tail -8 /tmp/span-mac.log >&2
exit 1
