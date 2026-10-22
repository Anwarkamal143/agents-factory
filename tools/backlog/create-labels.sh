#!/usr/bin/env bash
# Create or update every label in labels.json on the current GitHub repo (idempotent).
set -euo pipefail
LABELS="${1:-docs/backlog/labels.json}"
python3 - "$LABELS" <<'PY' | while IFS=$'\t' read -r name color desc; do
import json, sys
for l in json.load(open(sys.argv[1])):
    print("\t".join([l["name"], l["color"], l["description"]]))
PY
  gh label create "$name" --color "$color" --description "$desc" --force
done
