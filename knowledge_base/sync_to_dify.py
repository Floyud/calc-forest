#!/usr/bin/env python3
"""知识库同步脚本：将本地 knowledge_base/ 目录中的 markdown 文件上传到 Dify Knowledge。

用法:
    # 同步所有知识库文件
    python sync_to_dify.py --api-key YOUR_DATASET_API_KEY --dataset-id DATASET_ID

    # 先列出所有知识库
    python sync_to_dify.py --api-key YOUR_DATASET_API_KEY --list

    # 创建新知识库
    python sync_to_dify.py --api-key YOUR_DATASET_API_KEY --create "我的计算森林知识库"

    # 同步指定目录
    python sync_to_dify.py --api-key YOUR_DATASET_API_KEY --dataset-id DATASET_ID --dir 02_textbook_content

    # 删除远程已存在的同名文档并重新上传（全量同步）
    python sync_to_dify.py --api-key YOUR_DATASET_API_KEY --dataset-id DATASET_ID --full-sync

环境变量:
    DIFY_KB_API_KEY   - Dify Knowledge Base API Key（替代 --api-key）
    DIFY_DATASET_ID   - 目标知识库 ID（替代 --dataset-id）
    DIFY_BASE_URL     - Dify API 地址（默认 https://api.dify.ai/v1）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要安装 requests：pip install requests")
    sys.exit(1)


KB_ROOT = Path(__file__).parent
DEFAULT_BASE_URL = "https://api.dify.ai/v1"

# 每个 domain 的推荐分块配置（separator/overlap 影响 RAG 检索粒度）
DOMAIN_CHUNK_CONFIG: dict[str, dict] = {
    "01_error_taxonomy": {
        "separator": "\n---\n",
        "max_tokens": 800,
        "chunk_overlap": 100,
    },
    "02_textbook_content": {
        "separator": "\n---\n",
        "max_tokens": 1000,
        "chunk_overlap": 150,
    },
    "03_teaching_strategies": {
        "separator": "\n---\n",
        "max_tokens": 800,
        "chunk_overlap": 100,
    },
    "04_classroom_management": {
        "separator": "\n\n",
        "max_tokens": 800,
        "chunk_overlap": 100,
    },
    "05_growth_system": {
        "separator": "\n\n",
        "max_tokens": 600,
        "chunk_overlap": 80,
    },
    "06_grading_and_profile": {
        "separator": "\n\n",
        "max_tokens": 800,
        "chunk_overlap": 100,
    },
    "07_curriculum_planning": {
        "separator": "\n\n",
        "max_tokens": 600,
        "chunk_overlap": 80,
    },
}

DOC_LANGUAGE = "Chinese"


class DifyKBClient:
    """Dify Knowledge Base API 客户端。"""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def list_datasets(self, page: int = 1, limit: int = 50) -> dict:
        resp = requests.get(
            f"{self.base_url}/datasets",
            headers=self.headers,
            params={"page": page, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    def create_dataset(
        self,
        name: str,
        description: str = "",
        indexing_technique: str = "high_quality",
    ) -> dict:
        payload = {
            "name": name,
            "indexing_technique": indexing_technique,
            "permission": "only_me",
        }
        if description:
            payload["description"] = description
        resp = requests.post(
            f"{self.base_url}/datasets",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def list_documents(self, dataset_id: str) -> list[dict]:
        """列出知识库中的所有文档。"""
        docs = []
        page = 1
        while True:
            resp = requests.get(
                f"{self.base_url}/datasets/{dataset_id}/documents",
                headers=self.headers,
                params={"page": page, "limit": 100},
            )
            resp.raise_for_status()
            data = resp.json()
            docs.extend(data.get("data", []))
            if not data.get("has_more"):
                break
            page += 1
        return docs

    def delete_document(self, dataset_id: str, doc_id: str) -> None:
        """删除文档。"""
        resp = requests.delete(
            f"{self.base_url}/datasets/{dataset_id}/documents/{doc_id}",
            headers=self.headers,
        )
        resp.raise_for_status()

    def upload_file(
        self,
        dataset_id: str,
        filepath: Path,
        chunk_config: dict | None = None,
    ) -> dict:
        """上传 markdown 文件到知识库。"""
        if chunk_config is None:
            chunk_config = {
                "separator": "\n\n",
                "max_tokens": 800,
                "chunk_overlap": 100,
            }

        data_config = {
            "indexing_technique": "high_quality",
            "doc_form": "text_model",
            "doc_language": DOC_LANGUAGE,
            "process_rule": {
                "mode": "custom",
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": True},
                        {"id": "remove_urls_emails", "enabled": False},
                    ],
                    "segmentation": {
                        "separator": chunk_config["separator"],
                        "max_tokens": chunk_config["max_tokens"],
                        "chunk_overlap": chunk_config["chunk_overlap"],
                    },
                },
            },
        }

        with open(filepath, "rb") as f:
            files = {
                "file": (filepath.name, f, "text/markdown"),
                "data": (None, json.dumps(data_config), "text/plain"),
            }
            resp = requests.post(
                f"{self.base_url}/datasets/{dataset_id}/document/create-by-file",
                headers=self.headers,
                files=files,
            )

        if resp.status_code == 409:
            print(f"  ⚠️ 文档已存在: {filepath.name}")
            return {"skipped": True, "reason": "duplicate"}

        resp.raise_for_status()
        return resp.json()

    def wait_for_indexing(
        self,
        dataset_id: str,
        batch: str,
        timeout: int = 300,
    ) -> str:
        """等待索引完成。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            resp = requests.get(
                f"{self.base_url}/datasets/{dataset_id}/documents/{batch}/indexing-status",
                headers=self.headers,
            )
            resp.raise_for_status()
            raw = resp.json()
            items = raw if isinstance(raw, list) else raw.get("data", [])
            first = items[0] if items else {}
            status = first.get("indexing_status", "unknown")
            if status in ("completed", "error"):
                if status == "error":
                    err = first.get("error", "")
                    print(f"   ❌ 索引错误: {err[:200]}")
                return status
            time.sleep(3)
        return "timeout"


def collect_kb_files(kb_root: Path, target_dir: str | None = None) -> list[tuple[Path, str]]:
    files = []
    for domain_dir in sorted(kb_root.iterdir()):
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        if target_dir and domain != target_dir:
            continue
        for md_file in sorted(domain_dir.glob("*.md")):
            files.append((md_file, domain))
    return files


def sync_files(
    client: DifyKBClient,
    dataset_id: str,
    files: list[tuple[Path, str]],
    full_sync: bool = False,
) -> None:
    remote_docs = {}
    if full_sync:
        print("📋 获取远程文档列表...")
        try:
            existing = client.list_documents(dataset_id)
            remote_docs = {d["name"]: d["id"] for d in existing}
            print(f"   远程已有 {len(remote_docs)} 个文档")
        except Exception as e:
            print(f"   ⚠️ 获取远程文档失败: {e}")

    total = len(files)
    success = 0
    skipped = 0
    failed = 0

    for i, (filepath, domain) in enumerate(files, 1):
        print(f"\n[{i}/{total}] {filepath.name} (domain: {domain})")
        print(f"   大小: {filepath.stat().st_size:,} bytes")

        # 全量同步：先删除远程同名文档
        if full_sync and filepath.name in remote_docs:
            doc_id = remote_docs[filepath.name]
            print(f"   🗑️ 删除远程已有文档: {doc_id}")
            try:
                client.delete_document(dataset_id, doc_id)
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                print(f"   ⚠️ 删除失败: {e}")

        # 获取分块配置
        chunk_config = DOMAIN_CHUNK_CONFIG.get(domain, {
            "separator": "\n\n",
            "max_tokens": 800,
            "chunk_overlap": 100,
        })
        print(f"   分块: separator={repr(chunk_config['separator'])}, "
              f"max_tokens={chunk_config['max_tokens']}, "
              f"overlap={chunk_config['chunk_overlap']}")

        # 上传
        try:
            result = client.upload_file(dataset_id, filepath, chunk_config)
            if result.get("skipped"):
                skipped += 1
                continue

            doc_id = result.get("document", {}).get("id", "?")
            batch = result.get("batch", "?")
            print(f"   ✅ 上传成功: doc_id={doc_id}, batch={batch}")

            # 等待索引完成
            print(f"   ⏳ 等待索引...")
            status = client.wait_for_indexing(dataset_id, batch)
            if status == "completed":
                print(f"   ✅ 索引完成")
                success += 1
            else:
                print(f"   ⚠️ 索引状态: {status}")
                success += 1  # 上传本身成功了

            # 避免请求过快
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"同步完成: ✅ {success} 成功, ⏭️ {skipped} 跳过, ❌ {failed} 失败")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="同步本地知识库到 Dify Knowledge")
    parser.add_argument("--api-key", default=os.getenv("DIFY_KB_API_KEY", ""),
                        help="Dify Knowledge API Key")
    parser.add_argument("--base-url", default=os.getenv("DIFY_BASE_URL", DEFAULT_BASE_URL),
                        help="Dify API 地址")
    parser.add_argument("--dataset-id", default=os.getenv("DIFY_DATASET_ID", ""),
                        help="目标知识库 ID")
    parser.add_argument("--list", action="store_true", help="列出所有知识库")
    parser.add_argument("--create", metavar="NAME", help="创建新知识库")
    parser.add_argument("--dir", help="只同步指定 domain 目录")
    parser.add_argument("--full-sync", action="store_true",
                        help="全量同步（删除远程已有同名文档再上传）")
    parser.add_argument("--dry-run", action="store_true", help="只列出要同步的文件")
    args = parser.parse_args()

    # 验证参数
    if not args.api_key:
        print("❌ 必须提供 API Key（--api-key 或 DIFY_KB_API_KEY 环境变量）")
        sys.exit(1)

    client = DifyKBClient(args.api_key, args.base_url)

    # 列出知识库
    if args.list:
        print("📋 知识库列表:")
        data = client.list_datasets()
        for ds in data.get("data", []):
            print(f"  - {ds['name']}")
            print(f"    ID: {ds['id']}")
            print(f"    文档数: {ds.get('document_count', 0)}")
            print(f"    索引方式: {ds.get('indexing_technique', '?')}")
            print()
        print(f"总计: {data.get('total', 0)} 个知识库")
        return

    # 创建知识库
    if args.create:
        print(f"📦 创建知识库: {args.create}")
        result = client.create_dataset(args.create)
        ds_id = result["id"]
        print(f"✅ 创建成功!")
        print(f"   ID: {ds_id}")
        print(f"\n使用以下命令同步:")
        print(f"   python {__file__} --api-key YOUR_KEY --dataset-id {ds_id}")
        return

    # 同步文件
    if not args.dataset_id:
        print("❌ 必须提供 dataset-id（--dataset-id 或 DIFY_DATASET_ID 环境变量）")
        print("   使用 --list 查看已有知识库，或使用 --create 创建新知识库")
        sys.exit(1)

    files = collect_kb_files(KB_ROOT, args.dir)

    if not files:
        print("❌ 没有找到 markdown 文件")
        sys.exit(1)

    print(f"📚 找到 {len(files)} 个知识库文件:")
    for filepath, domain in files:
        print(f"  - [{domain}] {filepath.name} ({filepath.stat().st_size:,} bytes)")

    if args.dry_run:
        print("\n(dry-run 模式，不执行上传)")
        return

    print(f"\n🎯 目标知识库: {args.dataset_id}")
    print(f"📍 API 地址: {args.base_url}")
    print(f"🔄 全量同步: {'是' if args.full_sync else '否（增量）'}")
    print()

    sync_files(client, args.dataset_id, files, args.full_sync)


if __name__ == "__main__":
    main()
