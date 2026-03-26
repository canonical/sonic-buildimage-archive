#!/bin/bash
#
# setup-testbed-ci.sh — Prepare VS testbed as the CI user (tor-ci).
#
# This script runs as tor-ci and handles the PREPARE phase:
#   1. Download CI files from yanbox (if not pre-populated)
#   2. Prepare images (gunzip, copy to expected paths)
#   3. Clone sonic-mgmt and apply local env patches
#   4. Load docker-sonic-mgmt image
#
# The DEPLOY phase (management network, mgmt container, topology)
# is handled by deploy-testbed.sh (a separate script).
#
# Usage (run as tor-ci):
#   ./setup-testbed-ci.sh <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]
#
set -ex

YANBOX_IP="${1:?Usage: $0 <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]}"
SONIC_MGMT_BRANCH="${2:-ubuntu-sonic-202405}"
SONIC_MGMT_REPO="${3:-canonical/sonic-mgmt}"

CI_HOME="$HOME"
YANBOX_URL="http://$YANBOX_IP:8000"
CI_FILES_DIR="$CI_HOME/ci-files"

# ============================================================
# Step 1: Download CI files from yanbox
# ============================================================
mkdir -p "$CI_FILES_DIR"

echo "=== Downloading sonic-vs.img.gz ==="
if [ -f "$CI_FILES_DIR/sonic-vs.img.gz" ]; then
    echo "  Already exists, skipping download"
else
    curl -f -o "$CI_FILES_DIR/sonic-vs.img.gz" "$YANBOX_URL/sonic-vs.img.gz"
fi
echo "=== sonic-vs.img.gz ($(ls -lh "$CI_FILES_DIR/sonic-vs.img.gz" | awk '{print $5}')) ==="

echo "=== Downloading cEOS image ==="
if [ -f "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar" ]; then
    echo "  Already exists, skipping download"
else
    curl -f -o "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar" "$YANBOX_URL/cEOS64-lab-4.32.5M.tar" || echo "WARN: cEOS tar not found on yanbox"
fi

echo "=== Downloading docker-sonic-mgmt ==="
if [ -f "$CI_FILES_DIR/docker-sonic-mgmt.gz" ]; then
    echo "  Already exists, skipping download"
else
    curl -f -o "$CI_FILES_DIR/docker-sonic-mgmt.gz" "$YANBOX_URL/docker-sonic-mgmt.gz" || echo "WARN: docker-sonic-mgmt.gz not found on yanbox"
fi

# ============================================================
# Step 2: Prepare images
# ============================================================
echo "=== Preparing images ==="
mkdir -p "$CI_HOME/veos-vm/images" "$CI_HOME/sonic-vm/images" "$CI_HOME/sonic-vm/disks"

cp -f "$CI_FILES_DIR/sonic-vs.img.gz" "$CI_HOME/veos-vm/images/"
cd "$CI_HOME/veos-vm/images" && gunzip -kf sonic-vs.img.gz
cp -f "$CI_HOME/veos-vm/images/sonic-vs.img" "$CI_HOME/sonic-vm/images/"

if [ -f "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar" ]; then
    cp "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar" "$CI_HOME/veos-vm/images/"
elif [ -f "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar.xz" ]; then
    cp "$CI_FILES_DIR/cEOS64-lab-4.32.5M.tar.xz" "$CI_HOME/veos-vm/images/"
    cd "$CI_HOME/veos-vm/images" && xz -df cEOS64-lab-4.32.5M.tar.xz || true
else
    echo "ERROR: cEOS image not available"
    exit 1
fi

# ============================================================
# Step 3: Clone sonic-mgmt and apply local environment
# ============================================================
echo "=== Cloning sonic-mgmt ==="
if [ -d "$CI_HOME/sonic-mgmt/.git" ]; then
    echo "sonic-mgmt already cloned, pulling latest"
    cd "$CI_HOME/sonic-mgmt" && git fetch origin && git reset --hard "origin/$SONIC_MGMT_BRANCH"
else
    git clone -q -b "$SONIC_MGMT_BRANCH" "https://github.com/$SONIC_MGMT_REPO" "$CI_HOME/sonic-mgmt"
fi

echo "=== Applying local environment patches ==="
# setup-local-env.sh is placed in $CI_HOME by setup-testbed.sh (or lxc file push)
if [ -f "$CI_HOME/setup-local-env.sh" ]; then
    cp "$CI_HOME/setup-local-env.sh" "$CI_HOME/sonic-mgmt/setup-local-env.sh"
fi
if [ -f "$CI_HOME/sonic-mgmt/setup-local-env.sh" ]; then
    chmod +x "$CI_HOME/sonic-mgmt/setup-local-env.sh"
    cd "$CI_HOME/sonic-mgmt" && ./setup-local-env.sh "$CI_HOME/sonic-mgmt" -u "$(whoami)" -a -p "$(whoami)"
fi

# ============================================================
# Step 4: Load docker-sonic-mgmt image
# ============================================================
if [ -f "$CI_FILES_DIR/docker-sonic-mgmt.gz" ]; then
    if ! docker images -q docker-sonic-mgmt:latest | grep -q .; then
        echo "=== Loading docker-sonic-mgmt image ==="
        docker load -i "$CI_FILES_DIR/docker-sonic-mgmt.gz"
    else
        echo "docker-sonic-mgmt image already loaded, skipping"
    fi
else
    echo "=== docker-sonic-mgmt.gz not found, setup-container.sh will pull it ==="
fi

echo "=== Prepare complete ==="
