#!/usr/bin/env bash
# Build the submitted controller and use the public checker without modifications.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
kit_dir="${1:?Pass the path to the unzipped official g1-builder-kit}"
kit_dir="$(cd "$kit_dir" && pwd)"
test -f "$kit_dir/sim.sh"
docker buildx build --platform linux/arm64 --load \
  --build-arg "SOURCE_COMMIT=$(git -C "$project_dir" rev-parse HEAD)" \
  -f "$project_dir/runner/Dockerfile" -t shishimai-g1:submission-v1 "$project_dir"
mkdir -p "$kit_dir/containers/upload/environment"
cp "$project_dir/scene.xml" "$kit_dir/containers/upload/environment/scene.xml"
cp -R "$project_dir/assets" "$kit_dir/containers/upload/environment/"
cd "$kit_dir"
bash sim.sh --image shishimai-g1:submission-v1 --seconds 60 \
  --scene containers/upload/environment/scene.xml --output containers/sim/output/shishimai-standing
bash sim.sh --image shishimai-g1:submission-v1 --seconds 60 --counterfactuals \
  --scene containers/upload/environment/scene.xml --output containers/sim/output/shishimai-counterfactuals
