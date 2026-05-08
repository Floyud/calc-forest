#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:18080}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@calcforest.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-CalcForestAdmin1!}"
COOKIE_JAR="${COOKIE_JAR:-/tmp/opencode/dify-cookies.txt}"
WORKFLOW_FILE="${1:-/mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/dify/my_calc_forest_dify_night_build.yml}"

ENCODED_PASSWORD=$(ADMIN_PASSWORD="$ADMIN_PASSWORD" /home/lyzhang/miniconda3/envs/pyt0/bin/python - <<'PY'
import base64
import os

print(base64.b64encode(os.environ["ADMIN_PASSWORD"].encode("utf-8")).decode("utf-8"))
PY
)

rm -f "$COOKIE_JAR"

curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/console/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ENCODED_PASSWORD\",\"remember_me\":false}"

CSRF_TOKEN=$(awk '$6=="csrf_token"{print $7}' "$COOKIE_JAR")

YAML_CONTENT=$(WORKFLOW_FILE="$WORKFLOW_FILE" /home/lyzhang/miniconda3/envs/pyt0/bin/python - <<'PY'
import json
import os
from pathlib import Path

workflow_file = Path(os.environ["WORKFLOW_FILE"])
content = workflow_file.read_text(encoding="utf-8")
print(json.dumps(content, ensure_ascii=False))
PY
)

PAYLOAD=$(printf '{"mode":"yaml-content","yaml_content":%s}' "$YAML_CONTENT")

curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/console/api/apps/imports" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d "$PAYLOAD"
