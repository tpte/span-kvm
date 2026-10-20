#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MSI_HOST="${SPAN_KVM_MSI:-alan@172.20.10.4}"
REMOTE_DIR=".local/share/span-kvm"
SERVICE=span-kvm-msi.service

scp "$ROOT/host/msi.py" "$ROOT/host/session.py" "$ROOT/scripts/span-kvm-msi.service" "$MSI_HOST:/tmp/"
ssh "$MSI_HOST" bash <<'REMOTE'
set -euo pipefail
mkdir -p ~/.local/share/span-kvm ~/.config/systemd/user
cp /tmp/msi.py /tmp/session.py ~/.local/share/span-kvm/
cp /tmp/span-kvm-msi.service ~/.config/systemd/user/span-kvm-msi.service
systemctl --user daemon-reload
systemctl --user enable span-kvm-msi.service
systemctl --user restart span-kvm-msi.service
systemctl --user is-active span-kvm-msi.service
REMOTE
echo "msi sync ok"
