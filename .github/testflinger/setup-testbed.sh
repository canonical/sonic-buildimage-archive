#!/bin/bash
#
# setup-testbed.sh — Set up a VS testbed on a testflinger-reserved machine.
#
# This script runs ON the testflinger machine (via SSH as ubuntu). It:
#   1. Installs packages (docker, python) and creates the tor-ci user
#   2. Copies setup-local-env.sh into the right place
#   3. Delegates to setup-testbed-ci.sh (running as tor-ci) for the rest
#
# Usage:
#   scp setup-testbed.sh setup-testbed-ci.sh setup-local-env.sh ubuntu@<DEVICE_IP>:~/
#   ssh ubuntu@<DEVICE_IP> ./setup-testbed.sh <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]
#
set -ex

YANBOX_IP="${1:?Usage: $0 <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]}"
SONIC_MGMT_BRANCH="${2:-ubuntu-sonic-202405}"
SONIC_MGMT_REPO="${3:-canonical/sonic-mgmt}"

CI_USER=tor-ci
CI_HOME="/home/$CI_USER"

# ============================================================
# Step 1: Install packages and create tor-ci user
# ============================================================
echo "=== Installing packages ==="
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update 
sudo apt-get remove -y containerd 2>&1 || true
sudo apt-get install -y docker-ce python3 python3-pip python-is-python3
sudo pip3 install j2cli
sudo systemctl restart docker

echo "=== Creating $CI_USER user ==="
if ! id "$CI_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash "$CI_USER"
fi
sudo usermod -aG docker "$CI_USER"
echo "$CI_USER ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/$CI_USER
# Copy SSH authorized_keys so we can SSH as tor-ci too
sudo mkdir -p "$CI_HOME/.ssh"
sudo cp ~/.ssh/authorized_keys "$CI_HOME/.ssh/authorized_keys"
sudo chown -R "$CI_USER:$CI_USER" "$CI_HOME/.ssh"
sudo chmod 700 "$CI_HOME/.ssh"
sudo chmod 600 "$CI_HOME/.ssh/authorized_keys"

# ============================================================
# Step 2: Copy helper scripts to CI user's home
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

for f in setup-testbed-ci.sh setup-local-env.sh; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        sudo cp "$SCRIPT_DIR/$f" "$CI_HOME/$f"
        sudo chown "$CI_USER:$CI_USER" "$CI_HOME/$f"
        sudo chmod +x "$CI_HOME/$f"
    fi
done

# ============================================================
# Step 3: Run setup-testbed-ci.sh as tor-ci
# ============================================================
echo "=== Delegating to setup-testbed-ci.sh as $CI_USER ==="
sudo -u "$CI_USER" -H \
    "$CI_HOME/setup-testbed-ci.sh" "$YANBOX_IP" "$SONIC_MGMT_BRANCH" "$SONIC_MGMT_REPO"
