#!/bin/bash
# Build all rock (OCI) containers in parallel.
# Run this after a full normal build completes.
# Usage: ./build_rocks.sh
set -e
exec make -j"${SONIC_BUILD_JOBS:-4}" -f Makefile.rocks
