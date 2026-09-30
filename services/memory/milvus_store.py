# Thanatos/services/memory/milvus_store.py

import json
import logging
import math
import os
import re
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


def _simple_text_embedding(text: str, dim: int = 128) -> List[float]:
    words = re.findall(r"\w+", text.lower())
    vec = [0.0] * dim
    for w in words:
        h = hash(w)
        idx = abs(h) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class MilvusVectorStore:
    """
    Milvus Vector Store implementation.
    Supports:
      1. Milvus Lite (local standalone file `milvus_store.db` via `pymilvus`)
      2. Milvus Standalone Server (e.g. `http://localhost:19530`)
      3. Seamless fallback if pymilvus is not yet installed in local environment.
    """

    def __init__(
        self,
        uri: str = "./memory_store/milvus_local.db",
        collection_name: str = "thanatos_memories",
        dim: int = 128,
    ) -> None:
        self.uri = uri
        self.collection_name = collection_name
        self.dim = dim
        self._client = None
        self._status: Dict[str, Any] = {}
        self._init_milvus()

    def _init_milvus(self) -> None:
        try:
            from pymilvus import MilvusClient
            os.makedirs(os.path.dirname(os.path.abspath(self.uri)), exist_ok=True)
            self._client = MilvusClient(uri=self.uri)

            if not self._client.has_collection(self.collection_name):
                self._client.create_collection(
                    collection_name=self.collection_name,
                    dimension=self.dim,
                    metric_type="COSINE",
                    auto_id=False,
                    id_type="string",
                    max_length=128,
                )
                is_new = True
            else:
                is_new = False

            stats = self._client.get_collection_stats(self.collection_name)
            row_count = stats.get("row_count", 0)

            self._status = {
                "backend": "Milvus Vector Store (Lite / Server)",
                "status": "ready",
                "uri": self.uri,
                "collection": self.collection_name,
                "doc_count": row_count,
                "is_new": is_new,
            }
            logger.info("Milvus client initialized on %s (Collection: %s)", self.uri, self.collection_name)
        except Exception as e:
            logger.warning("Milvus connection failed (%s). Milvus requires pymilvus or running server.", e)
            self._status = {
                "backend": "Milvus Vector Store",
                "status": "unavailable",
                "uri": self.uri,
                "collection": self.collection_name,
                "doc_count": 0,
                "error": str(e),
            }

    def is_available(self) -> bool:
        return self._client is not None and self._status.get("status") == "ready"

    def get_status(self) -> Dict[str, Any]:
        if self._client and self.is_available():
            try:
                stats = self._client.get_collection_stats(self.collection_name)
                self._status["doc_count"] = stats.get("row_count", 0)
            except Exception:
                pass
        return self._status

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if not self.is_available() or not texts:
            return []

        doc_ids = ids or [str(uuid.uuid4()) for _ in texts]
        metas = metadatas or [{} for _ in texts]

        data = []
        for doc_id, text, meta in zip(doc_ids, texts, metas):
            emb = _simple_text_embedding(text, dim=self.dim)
            data.append({
                "id": doc_id,
                "vector": emb,
                "text": text,
                "metadata": json.dumps(meta),
            })

        try:
            self._client.insert(collection_name=self.collection_name, data=data)
            return doc_ids
        except Exception as e:
            logger.error("Error inserting into Milvus: %s", e)
            return []

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not self.is_available() or not query.strip():
            return []

        query_emb = _simple_text_embedding(query, dim=self.dim)
        try:
            res = self._client.search(
                collection_name=self.collection_name,
                data=[query_emb],
                limit=k,
                output_fields=["text", "metadata"],
            )
            formatted = []
            if res and len(res) > 0:
                for hit in res[0]:
                    entity = hit.get("entity", {})
                    meta_raw = entity.get("metadata", "{}")
                    try:
                        meta = json.loads(meta_raw)
                    except Exception:
                        meta = {}
                    formatted.append({
                        "text": entity.get("text", ""),
                        "metadata": meta,
                        "score": round(hit.get("distance", 0.0), 3),
                    })
            return formatted
        except Exception as e:
            logger.error("Error searching in Milvus: %s", e)
            return []
