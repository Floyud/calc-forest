#!/usr/bin/env bash
set -euo pipefail

cd /mnt/d/Ubuntu_WSL/Teaching_agent/development

nohup /home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/opencode/calc_forest_api.log 2>&1 &

echo "FastAPI started on 0.0.0.0:8000"
