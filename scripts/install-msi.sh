#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.local/share/span-kvm"
UNIT_DST="$HOME/.config/systemd/user/span-kvm-msi.service"

mkdir -p "$DEST"
cp "$ROOT/host/msi.py" "$ROOT/host/session.py" "$DEST/"
mkdir -p "$(dirname "$UNIT_DST")"
cp "$ROOT/scripts/span-kvm-msi.service" "$UNIT_DST"

systemctl --user daemon-reload
systemctl --user enable span-kvm-msi.service
systemctl --user restart span-kvm-msi.service
sleep 1
systemctl --user --no-pager status span-kvm-msi.service | head -12
