#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
image_tag="${1:-skillflow/haitun-agent-method:ubuntu24.04}"
haitun_source="$(cd "$script_dir/../../../haitun-agent" && pwd)"

docker build -f "$script_dir/Dockerfile" -t "$image_tag" "$haitun_source"
printf 'Built %s\n' "$image_tag"
