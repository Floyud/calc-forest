# =============================================================
#  我的计算森林 — FastAPI Backend
# =============================================================
FROM python:3.11-slim AS base

# 系统依赖 (jinja2 + 可能的 texlive-fonts)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY app/ ./app/
COPY templates/ ./templates/
COPY data/ ./data/

# 知识库 (如果构建时需要; 运行时通过 volume 挂载)
COPY knowledge_base/ ./knowledge_base/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
