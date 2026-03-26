#!/bin/bash
#
# deploy-testbed.sh — Deploy VS testbed topology (runs as tor-ci).
#
# This script handles the DEPLOY phase after setup-testbed-ci.sh (prepare)
# has already downloaded images, cloned sonic-mgmt, and loaded docker images.
#
# Steps:
#   1. Setup management network
#   2. Setup mgmt container (docker-sonic-mgmt)
#   3. Inject container SSH key into host authorized_keys
#   4. Deploy testbed topology (add-topo)
#   5. Deploy minigraph (deploy-mg)
#
# Usage (run as tor-ci):
#   ./deploy-testbed.sh
#
set -ex

CI_HOME="$HOME"
MGMT_CONTAINER=mgmt
DATA_DIR=/data
TESTBED=vms-kvm-t0
TESTBED_FILE=vtestbed.yaml
INVENTORY=veos_vtb

# ============================================================
# Step 1: Setup management network
# ============================================================
echo "=== Setting up management network ==="
cd "$CI_HOME/sonic-mgmt" && sudo bash -c "export HOME=$CI_HOME && ./ansible/setup-management-network.sh"

# ============================================================
# Step 2: Setup mgmt container
# ============================================================
echo "=== Setting up mgmt container ==="
if docker ps -a --format '{{.Names}}' | grep -qx "$MGMT_CONTAINER"; then
    echo "Container $MGMT_CONTAINER already exists, skipping setup-container.sh"
    docker start "$MGMT_CONTAINER" 2>/dev/null || true
else
    cd "$CI_HOME/sonic-mgmt" && bash -x ./setup-container.sh -n "$MGMT_CONTAINER" -d "$DATA_DIR"
fi

# ============================================================
# Step 3: Inject container SSH key
# ============================================================
CONTAINER_PUBKEY=$(docker exec "$MGMT_CONTAINER" cat "$CI_HOME/.ssh/id_rsa.pub" 2>/dev/null) || true
if [ -n "$CONTAINER_PUBKEY" ]; then
    if ! grep -qF "$CONTAINER_PUBKEY" "$CI_HOME/.ssh/authorized_keys" 2>/dev/null; then
        echo "$CONTAINER_PUBKEY" >> "$CI_HOME/.ssh/authorized_keys"
        chmod 600 "$CI_HOME/.ssh/authorized_keys"
        echo "Injected container SSH pubkey into host authorized_keys"
    fi
fi

# ============================================================
# Step 4: Deploy testbed topology
# ============================================================
echo "=== Deploying testbed topology ==="
docker exec "$MGMT_CONTAINER" bash -c \
    "cd $DATA_DIR/sonic-mgmt/ansible && bash -x ./testbed-cli.sh -t $TESTBED_FILE -m $INVENTORY -k ceos add-topo $TESTBED password.txt"

# ============================================================
# Step 5: Deploy minigraph
# ============================================================
echo "=== Deploying minigraph ==="
docker exec "$MGMT_CONTAINER" bash -c \
    "cd $DATA_DIR/sonic-mgmt/ansible && bash -x ./testbed-cli.sh -t $TESTBED_FILE -m $INVENTORY deploy-mg $TESTBED $INVENTORY password.txt"

echo "=== Deploy complete ==="
