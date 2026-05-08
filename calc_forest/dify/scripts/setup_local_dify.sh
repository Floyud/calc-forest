#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:18080}"
INIT_PASSWORD="${INIT_PASSWORD:-CalcForest2026!}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@calcforest.local}"
ADMIN_NAME="${ADMIN_NAME:-Calc Forest Admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-CalcForestAdmin1!}"
COOKIE_JAR="${COOKIE_JAR:-/tmp/opencode/dify-cookies.txt}"

rm -f "$COOKIE_JAR"

curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/console/api/init" \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"$INIT_PASSWORD\"}"

curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/console/api/setup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"name\":\"$ADMIN_NAME\",\"password\":\"$ADMIN_PASSWORD\",\"language\":\"zh-Hans\"}"
