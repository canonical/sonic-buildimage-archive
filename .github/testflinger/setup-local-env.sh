#!/bin/bash
#
# Setup local environment for sonic-mgmt testbed.
# Run this script after a clean git clone to apply local configuration.
#
# Usage:
#   ./setup-local-env.sh [<project_dir>] [-u <username>] [-a] [-c <ceos_version>] [-p <password>]
#
# Arguments:
#   <project_dir>       Optional first positional arg. Path to sonic-mgmt repo (default: current directory).
#
# Options:
#   -u <username>       Username for ansible_user and vm_host_user (default: tor-ci).
#   -a                  Disable AppArmor seclabel in all libvirt VM templates found
#                       under ansible/ (change from dynamic/apparmor to type='none').
#   -c <ceos_version>   cEOS image version (default: 4.32.5M).
#   -p <password>       Password to write to ansible/password.txt (default: tor-ci).
#   -h                  Show this help message.
#

set -euo pipefail

# First positional argument is the project directory (optional)
if [[ ${1:-} ]] && [[ ! "$1" =~ ^- ]]; then
    SCRIPT_DIR="$(cd "$1" && pwd)"
    shift
else
    SCRIPT_DIR="$(pwd)"
fi

USERNAME="tor-ci"
DISABLE_APPARMOR=false
CEOS_VERSION="4.32.5M"
PASSWORD="tor-ci"

usage() {
    sed -n '2,/^$/s/^# \?//p' "$0"
    exit 1
}

while getopts "u:ac:p:h" opt; do
    case "$opt" in
        u) USERNAME="$OPTARG" ;;
        a) DISABLE_APPARMOR=true ;;
        c) CEOS_VERSION="$OPTARG" ;;
        p) PASSWORD="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

echo "==> Configuring sonic-mgmt local environment"
echo "    Project dir:      $SCRIPT_DIR"
echo "    Username:         $USERNAME"
echo "    Disable AppArmor: $DISABLE_APPARMOR"
echo "    cEOS version:     $CEOS_VERSION"
echo "    password.txt:     (will be created)"

# --- 1. Set username in ansible/group_vars/vm_host/creds.yml ---
CREDS_FILE="$SCRIPT_DIR/ansible/group_vars/vm_host/creds.yml"
if [[ -f "$CREDS_FILE" ]]; then
    sed -i "s/^ansible_user: .*/ansible_user: ${USERNAME}/" "$CREDS_FILE"
    sed -i "s/^vm_host_user: .*/vm_host_user: ${USERNAME}/" "$CREDS_FILE"
    echo "[OK] Updated $CREDS_FILE"
else
    echo "[WARN] $CREDS_FILE not found, skipping."
fi

# --- 2. Set username in ansible/veos_vtb ---
VEOS_FILE="$SCRIPT_DIR/ansible/veos_vtb"
if [[ -f "$VEOS_FILE" ]]; then
    sed -i "s/ansible_user: use_own_value/ansible_user: ${USERNAME}/g" "$VEOS_FILE"
    sed -i "s/vm_host_user: use_own_value/vm_host_user: ${USERNAME}/g" "$VEOS_FILE"
    echo "[OK] Updated $VEOS_FILE"
else
    echo "[WARN] $VEOS_FILE not found, skipping."
fi

# --- 3. Update cEOS image version ---
CEOS_FILE="$SCRIPT_DIR/ansible/group_vars/vm_host/ceos.yml"
if [[ -f "$CEOS_FILE" ]]; then
    # Replace version in image filename, image tags, and download URLs
    sed -i -E "s/cEOS64-lab-[0-9]+\.[0-9]+\.[0-9]+[A-Z]*/cEOS64-lab-${CEOS_VERSION}/g" "$CEOS_FILE"
    sed -i -E "s/ceosimage:[0-9]+\.[0-9]+\.[0-9]+[A-Z]*/ceosimage:${CEOS_VERSION}/g" "$CEOS_FILE"
    echo "[OK] Updated cEOS version to $CEOS_VERSION in $CEOS_FILE"
else
    echo "[WARN] $CEOS_FILE not found, skipping."
fi

# --- 4. Disable AppArmor in libvirt VM templates (optional) ---
if [[ "$DISABLE_APPARMOR" == true ]]; then
    while IFS= read -r -d '' tmpl; do
        sed -i "s|<seclabel type='dynamic' model='apparmor' relabel='yes'/>|<seclabel type='none'/>|" "$tmpl"
        echo "[OK] Disabled AppArmor seclabel in $tmpl"
    done < <(find "$SCRIPT_DIR/ansible" -name '*.xml.j2' -print0)
fi

# --- 5. Create password.txt ---
echo "$PASSWORD" > "$SCRIPT_DIR/ansible/password.txt"
echo "[OK] Created ansible/password.txt"

# --- 6. Ensure cached_topologies directory exists ---
mkdir -p "$SCRIPT_DIR/ansible/.cached_topologies"
CACHED_PATH_FILE="$SCRIPT_DIR/ansible/cached_topologies_path"
if [[ ! -f "$CACHED_PATH_FILE" ]]; then
    echo "/data/sonic-mgmt/ansible/.cached_topologies" > "$CACHED_PATH_FILE"
    echo "[OK] Created $CACHED_PATH_FILE"
fi

echo ""
echo "==> Local environment setup complete."
