#!/bin/bash
# Build a single rock (OCI) container image.
# Usage: ./build_rock.sh <rock_dir>
#   e.g. ./build_rock.sh dockers/docker-database
#
# Expects Pass 1+2 artifacts under target/ (debs, files, python-wheels, manifests).
# Produces target/<rockname>.gz

set -euo pipefail
set -x

rockdir="$1"
rockname=$(basename "$rockdir")
rockfullname="${rockname}_1.0.0_amd64.rock"

# Copy shared files into the rock build directory
mkdir -p "$rockdir"/{debs,files,python-wheels}
cp -r target/debs/noble/*          "$rockdir/debs/"
cp -r target/files/noble/*         "$rockdir/files/"
cp -r target/python-wheels/noble/* "$rockdir/python-wheels/"
echo "export IMAGE_VERSION=$(git rev-parse --abbrev-ref HEAD)-$(git rev-parse HEAD)" > "$rockdir/envs"

# Build the rock
pushd "$rockdir"
rockcraft clean
rockcraft pack
sudo rockcraft.skopeo --insecure-policy copy "oci-archive:$rockfullname" "docker-daemon:$rockname:latest"
rm -rf ./debs/ ./files/ ./python-wheels/
popd

# Export as docker-save .gz
docker save "$rockname:latest" | pigz -c > "target/${rockname}.gz"
docker rmi -f "$rockname:latest"
rm -f "$rockdir/envs"
