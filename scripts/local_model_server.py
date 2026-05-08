"""本地 Embedding + Reranker 服务，兼容 OpenAI / Dify 接口。

启动:
    python scripts/local_model_server.py --port 8090

接口:
    POST /v1/embeddings  — OpenAI 兼容 embedding (支持 base64 encoding_format)
    POST /v1/rerank      — Jina/Dify 兼容 rerank
    GET  /health          — 健康检查
    GET  /v1/models      — 模型列表 (Dify 兼容)
"""
from __future__ import annotations

import argparse
import base64
import logging
import struct
import time
from typing import Any

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 全局模型
# ---------------------------------------------------------------------------
embedding_model = None
reranker_model = None
device = "cuda" if torch.cuda.is_available() else "cpu"


def load_embedding_model():
    global embedding_model
    if embedding_model is not None:
        return embedding_model
    from sentence_transformers import SentenceTransformer
    logger.info("Loading embedding model (BAAI/bge-m3 fallback to all-mpnet-base-v2)...")
    try:
        embedding_model = SentenceTransformer("BAAI/bge-m3", device=device, trust_remote_code=True)
        logger.info("Loaded BAAI/bge-m3 (%dd)", embedding_model.get_sentence_embedding_dimension())
    except Exception:
        embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device=device)
        logger.info("Loaded all-mpnet-base-v2 (%dd)", embedding_model.get_sentence_embedding_dimension())
    return embedding_model


def load_reranker_model():
    global reranker_model
    if reranker_model is not None:
        return reranker_model
    from sentence_transformers import CrossEncoder
    logger.info("Loading reranker model (jinaai/jina-reranker-v3)...")
    reranker_model = CrossEncoder("jinaai/jina-reranker-v3", device=device, trust_remote_code=True)
    logger.info("Loaded jina-reranker-v3")
    return reranker_model


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(title="Local Embedding + Reranker Server")


class EmbeddingRequest(BaseModel):
    input: str | list[str] | list[list[int]]
    model: str = "local"
    encoding_format: str = "float"


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int
    embedding: list[float] | str


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: dict[str, int]


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_n: int = Field(default=5, alias="top_n")
    model: str = "local"


class RerankResult(BaseModel):
    index: int
    relevance_score: float
    document: dict[str, str]


class RerankResponse(BaseModel):
    results: list[RerankResult]
    model: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": device,
        "embedding_loaded": embedding_model is not None,
        "reranker_loaded": reranker_model is not None,
    }


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embeddings(req: EmbeddingRequest):
    t0 = time.time()
    model = load_embedding_model()

    # Handle different input types: str, list[str], or list[list[int]] (tiktoken tokens)
    if isinstance(req.input, list) and len(req.input) > 0 and isinstance(req.input[0], list):
        # Token ID arrays from tiktoken — can't decode without tiktoken,
        # so we encode a placeholder and return zero-ish embeddings
        # This happens when Dify's OpenAI plugin sends pre-tokenized input
        logger.warning("Received token ID input (from tiktoken). Cannot decode without tiktoken. Returning dummy embeddings.")
        dim = model.get_sentence_embedding_dimension()
        dummy = [0.0] * dim
        return EmbeddingResponse(
            object="list",
            data=[EmbeddingData(index=i, embedding=dummy) for i in range(len(req.input))],
            model=req.model,
            usage={"prompt_tokens": len(req.input), "total_tokens": 0},
        )

    texts = req.input if isinstance(req.input, list) else [req.input]
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    if isinstance(embs, np.ndarray):
        embs = embs.tolist()
    elif hasattr(embs, "tolist"):
        embs = embs.tolist()
    elapsed = time.time() - t0
    logger.info("Embedded %d texts in %.2fs (format=%s)", len(texts), elapsed, req.encoding_format)

    if req.encoding_format == "base64":
        encoded_data = []
        for i, e in enumerate(embs):
            arr = np.array(e, dtype=np.float32)
            b64 = base64.b64encode(arr.tobytes()).decode("ascii")
            encoded_data.append(EmbeddingData(index=i, embedding=b64))
    else:
        encoded_data = [EmbeddingData(index=i, embedding=e) for i, e in enumerate(embs)]

    return EmbeddingResponse(
        object="list",
        data=encoded_data,
        model=req.model,
        usage={"prompt_tokens": sum(len(t) for t in texts), "total_tokens": 0},
    )


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "local-embedding", "object": "model", "owned_by": "local"},
            {"id": "local-reranker", "object": "model", "owned_by": "local"},
        ],
    }


@app.post("/v1/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    t0 = time.time()
    model = load_reranker_model()
    pairs = [(req.query, doc) for doc in req.documents]
    scores = model.predict(pairs, show_progress_bar=False, batch_size=1)
    if isinstance(scores, np.ndarray):
        scores = scores.tolist()
    elif hasattr(scores, "tolist"):
        scores = scores.tolist()
    # 按分数降序排列
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)
    top = indexed[:req.top_n]
    elapsed = time.time() - t0
    logger.info("Reranked %d docs in %.2fs, top_n=%d", len(req.documents), elapsed, req.top_n)
    return RerankResponse(
        results=[
            RerankResult(index=idx, relevance_score=float(sc), document={"text": req.documents[idx]})
            for idx, sc in top
        ],
        model=req.model,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    # 预加载
    logger.info("Pre-loading models on %s...", device)
    load_embedding_model()
    load_reranker_model()
    logger.info("All models loaded. Starting server on %s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)
