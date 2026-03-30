#!/bin/bash
#
# run_lxd_parallel.sh — Run VS tests in parallel using LXD VMs.
#
# Each LXD VM gets a complete, isolated testbed environment:
#   - Its own dockerd, libvirtd, br1 network, mgmt container
#   - Standard setup-testbed.sh flow (unmodified)
#   - One t0 topology deployed and tested per VM
#
# The number of VMs is computed from host RAM:
#   num_workers = (total_ram - HOST_RESERVED_MB) / VM_RAM_MB
#
# Usage (run on testflinger host as ubuntu):
#   ./run_lxd_parallel.sh <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]
#
# Environment variables:
#   VM_RAM_MB        — RAM per LXD VM in MiB (default: 32768 = 32 GB)
#   VM_DISK_GB       — qcow2 disk per VM in GiB (default: 200)
#   HOST_RESERVED_MB — RAM reserved for host in MiB (default: 16384 = 16 GB)
#   VM_CPUS          — vCPUs per VM (default: 12)
#   MAX_WORKERS      — Cap on number of workers (default: unlimited)
#   VS_IMAGE_URL     — Full URL to sonic-vs.img.gz (default: $YANBOX_URL/sonic-vs.img.gz)
#
set -euo pipefail

# Close stdin for the entire script. LXD/LXC commands (init, exec, copy) may
# attempt to read stdin when it is a pipe (non-tty), which blocks forever when
# run via SSH or testflinger.  Redirecting to /dev/null prevents this.
exec < /dev/null

YANBOX_IP="${1:?Usage: $0 <yanbox_ip> [sonic_mgmt_branch] [sonic_mgmt_repo]}"
SONIC_MGMT_BRANCH="${2:-ubuntu-sonic-202405}"
SONIC_MGMT_REPO="${3:-canonical/sonic-mgmt}"

VM_RAM_MB="${VM_RAM_MB:-24576}"
VM_DISK_GB="${VM_DISK_GB:-200}"
HOST_RESERVED_MB="${HOST_RESERVED_MB:-16384}"
VM_CPUS="${VM_CPUS:-12}"
MAX_WORKERS="${MAX_WORKERS:-99}"
VS_IMAGE_URL="${VS_IMAGE_URL:-}"

YANBOX_URL="http://$YANBOX_IP:8000"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_LIST_FILE="${SCRIPT_DIR}/upstream_t0_tests.txt"
LOG_DIR="$HOME/lxd-test-results-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$LOG_DIR"

# Use sudo lxc in case group membership hasn't taken effect yet
LXC="sudo lxc"

# ============================================================
# Step 1: Compute number of workers from host RAM
# ============================================================
echo "=== Step 1: Computing worker count ==="
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
AVAILABLE_RAM_MB=$((TOTAL_RAM_MB - HOST_RESERVED_MB))
NUM_WORKERS=$((AVAILABLE_RAM_MB / VM_RAM_MB))

if [ "$NUM_WORKERS" -lt 1 ]; then
    echo "ERROR: Not enough RAM. Total: ${TOTAL_RAM_MB}MB, Reserved: ${HOST_RESERVED_MB}MB, Per VM: ${VM_RAM_MB}MB" >&2
    exit 1
fi

if [ "$NUM_WORKERS" -gt "$MAX_WORKERS" ]; then
    NUM_WORKERS="$MAX_WORKERS"
fi

# If no NVMe disk is present (SATA-only machine), cap workers to avoid
# I/O contention during parallel KVM disk image copies + VM boot
if ! ls /dev/nvme*n1 &>/dev/null; then
    MAX_SATA_WORKERS=4
    echo "  No NVMe detected — capping workers to $MAX_SATA_WORKERS (SATA I/O limit)"
    if [ "$NUM_WORKERS" -gt "$MAX_SATA_WORKERS" ]; then
        NUM_WORKERS="$MAX_SATA_WORKERS"
    fi
fi

echo "  Host RAM:      ${TOTAL_RAM_MB} MB"
echo "  Reserved:      ${HOST_RESERVED_MB} MB"
echo "  Per VM:        ${VM_RAM_MB} MB"
echo "  Workers:       ${NUM_WORKERS}"

# ============================================================
# Step 2: Validate test list
# ============================================================
echo ""
echo "=== Step 2: Validating test list ==="
if [ ! -f "$TEST_LIST_FILE" ]; then
    echo "ERROR: Test list file not found: $TEST_LIST_FILE" >&2
    exit 1
fi
TOTAL=$(wc -l < "$TEST_LIST_FILE")
echo "  Test list: $TEST_LIST_FILE ($TOTAL files)"
echo "  Worker scripts will be generated in Step 4 (after sonic-mgmt is cloned)"

# ============================================================
# Step 3: Install and initialize LXD
# ============================================================
echo ""
echo "=== Step 3: Setting up LXD ==="
if ! command -v lxd &>/dev/null; then
    sudo snap install lxd
fi

# Initialize LXD if no storage pool exists yet
if ! $LXC storage list --format csv 2>/dev/null | grep -q .; then
    echo "  No storage pool found, initializing LXD..."

    # Find an unused disk (no partitions, not mounted, >1GB) for zfs pool
    SPARE_DISK=""
    for dev in /dev/nvme*n1 /dev/sd?; do
        [ -b "$dev" ] || continue
        # Skip if it has partitions
        if lsblk -n -o TYPE "$dev" 2>/dev/null | grep -q part; then continue; fi
        # Skip if any part of it is mounted
        if lsblk -n -o MOUNTPOINT "$dev" 2>/dev/null | grep -q /; then continue; fi
        # Skip zero-size disks (empty USB readers etc.)
        SIZE=$(lsblk -n -o SIZE -b "$dev" 2>/dev/null | head -1)
        if [ -z "$SIZE" ] || [ "$SIZE" -lt 1073741824 ]; then continue; fi
        SPARE_DISK="$dev"
        break
    done

    if [ -n "$SPARE_DISK" ]; then
        echo "  Found spare disk: $SPARE_DISK — using zfs backend"
        STORAGE_DRIVER="zfs"
        STORAGE_SOURCE="$SPARE_DISK"
    else
        echo "  No spare disk found — using btrfs loop backend on root filesystem"
        STORAGE_DRIVER="btrfs"
        STORAGE_SOURCE=""
        # Default btrfs loop is only 30GB which is too small for VMs.
        # Size the loop to use 80% of root filesystem free space.
        ROOT_FREE_GB=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
        LOOP_SIZE_GB=$(( ROOT_FREE_GB * 80 / 100 ))
        # Minimum: enough for 1 VM disk + overhead
        MIN_LOOP_GB=$(( VM_DISK_GB + 50 ))
        if [ "$LOOP_SIZE_GB" -lt "$MIN_LOOP_GB" ]; then
            echo "  WARNING: Root has only ${ROOT_FREE_GB}GB free, loop=${LOOP_SIZE_GB}GB < minimum ${MIN_LOOP_GB}GB" >&2
        fi
        echo "  Loop size: ${LOOP_SIZE_GB}GB (root free: ${ROOT_FREE_GB}GB)"
    fi

    # Build preseed YAML
    PRESEED="config: {}
networks:
- name: lxdbr0
  type: bridge
  config:
    ipv4.address: auto
    ipv6.address: auto
storage_pools:
- name: default
  driver: ${STORAGE_DRIVER}"

    if [ -n "$STORAGE_SOURCE" ]; then
        PRESEED="${PRESEED}
  config:
    source: ${STORAGE_SOURCE}"
    else
        PRESEED="${PRESEED}
  config:
    size: ${LOOP_SIZE_GB}GiB"
    fi

    PRESEED="${PRESEED}
profiles:
- name: default
  devices:
    root:
      path: /
      pool: default
      type: disk
    eth0:
      name: eth0
      network: lxdbr0
      type: nic"

    echo "  Preseed config:"
    echo "$PRESEED" | sed 's/^/    /'
    echo "$PRESEED" | sudo lxd init --preseed

    echo "  LXD initialized (driver: ${STORAGE_DRIVER})"
fi

# Verify storage pool is ready
$LXC storage list
$LXC network list

if ! groups | grep -qw lxd; then
    sudo usermod -aG lxd "$USER"
fi

# Pre-download VM image to local cache so 'lxc init' uses a local image.
if ! $LXC image list --format csv 2>/dev/null | grep -q .; then
    echo "  Downloading VM image to local cache..."
    $LXC image copy ubuntu:focal local: --vm --alias focal-vm
    echo "  VM image cached locally"
fi

# ============================================================
# Step 4: Create template VM, push files, then clone
# ============================================================
echo ""
echo "=== Step 4: Creating template VM and pushing CI files ==="

TEMPLATE_VM="sonic-worker-1"
WORKERS=()

# --- 4a: Download large CI files to host cache ---
CI_CACHE="$HOME/ci-cache"
mkdir -p "$CI_CACHE"
for f in cEOS64-lab-4.32.5M.tar docker-sonic-mgmt.gz; do
    if [ ! -f "$CI_CACHE/$f" ]; then
        echo "  Downloading $f from yanbox..."
        curl -f -o "$CI_CACHE/$f" "$YANBOX_URL/$f"
    else
        echo "  $f already cached"
    fi
done
# Download VS image (supports override via VS_IMAGE_URL env var)
if [ ! -f "$CI_CACHE/sonic-vs.img.gz" ]; then
    VS_DL_URL="${VS_IMAGE_URL:-$YANBOX_URL/sonic-vs.img.gz}"
    echo "  Downloading sonic-vs.img.gz from $VS_DL_URL..."
    curl -f -o "$CI_CACHE/sonic-vs.img.gz" "$VS_DL_URL"
else
    echo "  sonic-vs.img.gz already cached"
fi

# --- 4b: Create and boot template VM ---
if ! $LXC info "$TEMPLATE_VM" &>/dev/null; then
    echo "  Creating $TEMPLATE_VM (${VM_RAM_MB}MB RAM, ${VM_CPUS} vCPUs, ${VM_DISK_GB}GB disk)..."
    $LXC init focal-vm "$TEMPLATE_VM" --vm \
        -c limits.memory="${VM_RAM_MB}MiB" \
        -c limits.cpu="$VM_CPUS" \
        -c security.secureboot=false \
        -c raw.qemu='-cpu host' \
        -d root,size="${VM_DISK_GB}GiB"
    $LXC start "$TEMPLATE_VM"
fi

echo "  Waiting for $TEMPLATE_VM to boot..."
for attempt in $(seq 1 60); do
    IP=$($LXC list "$TEMPLATE_VM" --format csv -c 4 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1) || true
    if [ -n "$IP" ]; then break; fi
    sleep 5
done
if [ -z "$IP" ]; then
    echo "  ERROR: $TEMPLATE_VM did not get an IP after 5 minutes" >&2
    exit 1
fi
echo "  $TEMPLATE_VM booted at $IP"

$LXC exec "$TEMPLATE_VM" -- cloud-init status --wait 2>/dev/null || true
echo "  $TEMPLATE_VM cloud-init done"

# --- 4c: Push scripts and CI files, then run prepare stage in template ---
echo "  Pushing scripts and CI files to $TEMPLATE_VM..."
$LXC file push "$SCRIPT_DIR/setup-testbed.sh" "${TEMPLATE_VM}/home/ubuntu/setup-testbed.sh"
$LXC file push "$SCRIPT_DIR/setup-testbed-ci.sh" "${TEMPLATE_VM}/home/ubuntu/setup-testbed-ci.sh"
$LXC file push "$SCRIPT_DIR/setup-local-env.sh" "${TEMPLATE_VM}/home/ubuntu/setup-local-env.sh"
$LXC file push "$SCRIPT_DIR/deploy-testbed.sh" "${TEMPLATE_VM}/home/ubuntu/deploy-testbed.sh"

$LXC exec "$TEMPLATE_VM" -- bash -c "chmod +x /home/ubuntu/setup-testbed.sh /home/ubuntu/setup-testbed-ci.sh /home/ubuntu/setup-local-env.sh /home/ubuntu/deploy-testbed.sh"
$LXC exec "$TEMPLATE_VM" -- bash -c "useradd -m -s /bin/bash tor-ci 2>/dev/null || true && mkdir -p /home/tor-ci/ci-files && chown -R tor-ci:tor-ci /home/tor-ci"

for f in sonic-vs.img.gz cEOS64-lab-4.32.5M.tar docker-sonic-mgmt.gz; do
    echo "  Pushing $f to $TEMPLATE_VM..."
    $LXC file push "$CI_CACHE/$f" "${TEMPLATE_VM}/home/tor-ci/ci-files/$f"
done
$LXC exec "$TEMPLATE_VM" -- chown -R tor-ci:tor-ci /home/tor-ci/ci-files

# Run setup-testbed.sh (install packages, create tor-ci, run setup-testbed-ci.sh)
# This does: packages → tor-ci user → download → images → clone sonic-mgmt → docker load
echo "  Running prepare stage in template (packages, images, clone, docker load)..."
$LXC exec "$TEMPLATE_VM" -- bash -c \
    "cd /home/ubuntu && ./setup-testbed.sh $YANBOX_IP $SONIC_MGMT_BRANCH $SONIC_MGMT_REPO"

# Copy deploy-testbed.sh into tor-ci's home so clones inherit it
$LXC exec "$TEMPLATE_VM" -- bash -c \
    "cp /home/ubuntu/deploy-testbed.sh /home/tor-ci/deploy-testbed.sh && \
     chown tor-ci:tor-ci /home/tor-ci/deploy-testbed.sh && \
     chmod +x /home/tor-ci/deploy-testbed.sh"
echo "  Template VM prepared (packages installed, images ready, docker loaded)"

# --- 4c2: Generate per-worker scripts using split_tests.py ---
# Now that sonic-mgmt is cloned in the template VM, we can parse the actual
# test source files with ast to count test functions (incl. parametrize).
# split_tests.py groups tests by directory (one pytest call per dir) and
# load-balances directories across workers by actual test weight.
echo ""
echo "  Generating per-worker scripts (ast-based test counting)..."
$LXC file push "$SCRIPT_DIR/split_tests.py" "${TEMPLATE_VM}/home/ubuntu/split_tests.py"
$LXC file push "$TEST_LIST_FILE" "${TEMPLATE_VM}/home/ubuntu/upstream_t0_tests.txt"
$LXC exec "$TEMPLATE_VM" -- python3 /home/ubuntu/split_tests.py \
    --test-list /home/ubuntu/upstream_t0_tests.txt \
    --tests-dir /data/sonic-mgmt/tests \
    --workers "$NUM_WORKERS" \
    --output-dir /home/tor-ci

# Pull generated scripts back to host LOG_DIR
for (( i=1; i<=NUM_WORKERS; i++ )); do
    $LXC file pull "${TEMPLATE_VM}/home/tor-ci/run_worker_${i}.sh" "$LOG_DIR/run_worker_${i}.sh"
done
echo "  Worker scripts generated and pulled to $LOG_DIR"

# --- 4d: Clean template state, stop, and clone ---
echo ""
echo "  Preparing template for cloning..."
# cloud-init clean flags:
#   --machine-id : reset /etc/machine-id → unique DHCP leases per clone
#   --logs       : remove cloud-init logs
#   --seed       : remove seed directory (instance metadata)
#   --configs all: remove all generated configs (network, ssh, datasource, fstab)
$LXC exec "$TEMPLATE_VM" -- cloud-init clean --machine-id --logs --seed --configs all

echo "  Stopping $TEMPLATE_VM for cloning..."
$LXC stop "$TEMPLATE_VM"

WORKERS+=("$TEMPLATE_VM")
for (( i=2; i<=NUM_WORKERS; i++ )); do
    VM="sonic-worker-${i}"
    WORKERS+=("$VM")
    if $LXC info "$VM" &>/dev/null; then
        echo "  $VM already exists, skipping clone"
    else
        echo "  Cloning $TEMPLATE_VM → $VM (ZFS COW)..."
        $LXC copy "$TEMPLATE_VM" "$VM"
    fi
done
echo "  All $NUM_WORKERS VMs created"

# --- 4e: Start all VMs and wait for boot ---
# Each VM regenerates machine-id on first boot (since /etc/machine-id is empty)
# This ensures unique DHCP leases → unique IPs
echo ""
echo "  Starting all VMs..."
for VM in "${WORKERS[@]}"; do
    $LXC start "$VM"
done

echo "  Waiting for all VMs to boot..."
for VM in "${WORKERS[@]}"; do
    IP=""
    for attempt in $(seq 1 60); do
        IP=$($LXC list "$VM" --format csv -c 4 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1) || true
        if [ -n "$IP" ]; then break; fi
        sleep 5
    done
    if [ -z "$IP" ]; then
        echo "  ERROR: $VM did not get an IP after 5 minutes" >&2
        exit 1
    fi
    echo "  $VM ready at $IP"
done

$LXC list

# --- 4f: Push per-worker run scripts ---
echo ""
echo "  Pushing per-worker run scripts..."
for (( i=0; i<NUM_WORKERS; i++ )); do
    GROUP_ID=$((i + 1))
    VM="${WORKERS[$i]}"
    $LXC file push "$LOG_DIR/run_worker_${GROUP_ID}.sh" "${VM}/home/tor-ci/run_worker.sh"
    $LXC exec "$VM" -- bash -c "chown tor-ci:tor-ci /home/tor-ci/run_worker.sh && chmod +x /home/tor-ci/run_worker.sh"
    echo "  $VM: run_worker_${GROUP_ID}.sh pushed"
done
echo ""
echo "  All VMs ready"

# ============================================================
# Step 5: Run full pipeline in each VM (parallel)
# ============================================================
echo ""
echo "=== Step 5: Running setup + deploy + test in $NUM_WORKERS VMs (parallel) ==="
echo ""

PIDS=()
for (( i=0; i<NUM_WORKERS; i++ )); do
    GROUP_ID=$((i + 1))
    VM="${WORKERS[$i]}"
    LOG_FILE="$LOG_DIR/worker_${GROUP_ID}.log"

    echo "--- Worker $GROUP_ID ($VM) ---"
    echo "    Log: $LOG_FILE"

    (
        $LXC exec "$VM" -- sudo -u tor-ci -H /home/tor-ci/run_worker.sh
    ) > "$LOG_FILE" 2>&1 &

    PIDS+=($!)
done

echo ""
echo "============================================"
echo "  All $NUM_WORKERS workers launched"
echo "  PIDs: ${PIDS[*]}"
echo "============================================"
echo ""
echo "Waiting for all workers to finish..."
echo "  Monitor:  tail -f $LOG_DIR/worker_*.log"
echo ""

# Poll workers with periodic heartbeat to prevent testflinger output_timeout
FAILURES=0
DONE=0
EXIT_CODES=()
for (( i=0; i<${#PIDS[@]}; i++ )); do EXIT_CODES+=("?"); done

while [ "$DONE" -lt "${#PIDS[@]}" ]; do
    sleep 60
    NOW=$(date '+%H:%M:%S')
    DONE=0
    for (( i=0; i<${#PIDS[@]}; i++ )); do
        PID=${PIDS[$i]}
        if [ "${EXIT_CODES[$i]}" != "?" ]; then
            DONE=$((DONE + 1))
            continue
        fi
        if ! kill -0 "$PID" 2>/dev/null; then
            # Capture exit code without triggering set -e (wait returns
            # the process's exit code, which is non-zero for failed tests)
            EXIT_CODES[$i]=0
            wait "$PID" 2>/dev/null || EXIT_CODES[$i]=$?
            DONE=$((DONE + 1))
            GID=$((i + 1))
            if [ "${EXIT_CODES[$i]}" -eq 0 ]; then
                echo "  [$NOW] Worker $GID (PID $PID): PASSED"
            else
                echo "  [$NOW] Worker $GID (PID $PID): FAILED (exit ${EXIT_CODES[$i]})"
                FAILURES=$((FAILURES + 1))
            fi
        fi
    done
    RUNNING=$((${#PIDS[@]} - DONE))
    if [ "$RUNNING" -gt 0 ]; then
        # Heartbeat: host stats + last line of each running worker log
        LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
        MEM=$(free -h | awk '/^Mem:/{printf "%s/%s (free %s)", $3, $2, $4}')
        echo "  [$NOW] $RUNNING/$NUM_WORKERS workers still running | load: $LOAD | mem: $MEM"
        for (( i=0; i<${#PIDS[@]}; i++ )); do
            [ "${EXIT_CODES[$i]}" != "?" ] && continue
            GID=$((i + 1))
            LAST=$(tail -1 "$LOG_DIR/worker_${GID}.log" 2>/dev/null | head -c 120)
            echo "    worker $GID: $LAST"
        done
    fi
done

echo ""
echo "============================================"
echo "  SUMMARY"
echo "============================================"
echo "Total workers: ${#PIDS[@]}"
echo "Failed:        $FAILURES"
echo "Logs:          $LOG_DIR/"
echo ""

# Print pytest summary from each worker log
echo "============================================"
echo "  TEST RESULTS"
echo "============================================"
for (( i=1; i<=NUM_WORKERS; i++ )); do
    LOG_FILE="$LOG_DIR/worker_${i}.log"
    if [ -f "$LOG_FILE" ]; then
        echo "--- Worker $i (${WORKERS[$((i-1))]}) ---"
        grep -E "passed|failed|error|skip" "$LOG_FILE" | tail -5 || echo "  (no summary found)"
        echo ""
    fi
done

# ============================================================
# Step 6: Upload all logs to FTP server
# ============================================================
echo ""
echo "=== Step 6: Uploading logs to FTP ==="
FTP_HOST="103.170.233.214"
FTP_PORT="2121"
FTP_USER="ci"
FTP_PASS="ci"
ARCHIVE_NAME="lxd-test-results-$(basename "$LOG_DIR").tar.gz"

# Copy the main script log into the results dir so it's included
cp "$HOME/run_lxd.log" "$LOG_DIR/run_lxd_parallel.log" 2>/dev/null || true

tar czf "/tmp/$ARCHIVE_NAME" -C "$(dirname "$LOG_DIR")" "$(basename "$LOG_DIR")"
echo "  Archive: /tmp/$ARCHIVE_NAME ($(du -h "/tmp/$ARCHIVE_NAME" | cut -f1))"

curl -T "/tmp/$ARCHIVE_NAME" "ftp://${FTP_USER}:${FTP_PASS}@${FTP_HOST}:${FTP_PORT}/${ARCHIVE_NAME}" && \
    echo "  Uploaded to ftp://${FTP_HOST}:${FTP_PORT}/${ARCHIVE_NAME}" || \
    echo "  WARN: FTP upload failed"

exit $FAILURES
