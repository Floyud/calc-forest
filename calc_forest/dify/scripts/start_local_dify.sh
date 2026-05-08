#!/usr/bin/env bash
set -euo pipefail

DIFY_SRC_DIR="${DIFY_SRC_DIR:-/tmp/opencode/dify-src}"
EXPOSE_NGINX_PORT="${EXPOSE_NGINX_PORT:-18080}"
EXPOSE_NGINX_SSL_PORT="${EXPOSE_NGINX_SSL_PORT:-18443}"
INIT_PASSWORD="${INIT_PASSWORD:-CalcForest2026!}"

if [ ! -d "$DIFY_SRC_DIR/docker" ]; then
  git clone --depth 1 --filter=blob:none https://github.com/langgenius/dify.git "$DIFY_SRC_DIR"
fi

cd "$DIFY_SRC_DIR/docker"

if [ ! -f ".env" ]; then
  cp ".env.example" ".env"
fi

perl -0pi -e "s/^EXPOSE_NGINX_PORT=.*/EXPOSE_NGINX_PORT=${EXPOSE_NGINX_PORT}/m; s/^EXPOSE_NGINX_SSL_PORT=.*/EXPOSE_NGINX_SSL_PORT=${EXPOSE_NGINX_SSL_PORT}/m; s/^INIT_PASSWORD=.*/INIT_PASSWORD=${INIT_PASSWORD}/m;" ".env"

docker compose up -d
docker compose ps
