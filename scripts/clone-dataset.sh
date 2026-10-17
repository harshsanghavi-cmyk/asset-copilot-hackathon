#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
dataset_path="$project_root/dataset"
revision=009e2b596782150f420021f9472ab37e3a2953ee
if [[ -e "$dataset_path" ]]; then
  current_revision="$(git -C "$dataset_path" rev-parse HEAD)"
  if [[ "$current_revision" != "$revision" ]]; then
    echo "Existing dataset is a different revision; preserving it unchanged." >&2
    exit 1
  fi
  echo "Pinned dataset already present; unchanged."
  exit 0
fi
git clone --no-checkout https://github.com/FlytBaseAILabs/flytbase-ahc-swe-asset-intelligence-dataset "$dataset_path"
git -C "$dataset_path" checkout --detach "$revision"
