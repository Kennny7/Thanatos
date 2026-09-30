# Thanatos/services/memory/vector_store.py

import json
import logging
import math
import os
import re
from typing import Any, Dict, List, Optional
import uuid
from config.settings import app_config

logger = logging.getLogger(__name__)


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _simple_text_embedding(text: str, dim: int = 128) -> List[float]:
    """Lightweight deterministic text embedding for local environments."""
    words = re.findall(r"\w+", text.lower())
    vec = [0.0] * dim
    for w in words:
        h = hash(w)
        idx = abs(h) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class VectorStore:
    """
    Unified Vector Store supporting Milvus Lite (primary high-performance vector DB),
    ChromaDB, and resilient local JSON fallback.
    Includes threshold monitoring for automated Docker scaling.
    """

    def __init__(
        self,
        persist_directory: str = app_config.memory_persist_dir,
        collection_name: str = app_config.memory_collection,
        preferred_backend: Optional[str] = None,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.preferred_backend = preferred_backend or getattr(app_config, "vector_db_backend", "milvus")
        self.active_backend = "fallback"

        self._milvus_store = None
        self._chroma_client = None
        self._chroma_collection = None
        self._fallback_docs: List[Dict[str, Any]] = []

        self._status_summary: Dict[str, Any] = {}
        self._init_backend()

    def _init_backend(self) -> None:
        """Autonomously initialize, verify, and report vector database health."""
        os.makedirs(self.persist_directory, exist_ok=True)

        # 1. Try Milvus Lite / Standalone if preferred
        if self.preferred_backend in ("milvus", "auto"):
            try:
                from services.memory.milvus_store import MilvusVectorStore
                milvus_db_path = os.path.join(self.persist_directory, "milvus_v2_store.db")
                m_store = MilvusVectorStore(uri=milvus_db_path, collection_name=self.collection_name)
                if m_store.is_available():
                    self._milvus_store = m_store
                    self.active_backend = "milvus"
                    status = m_store.get_status()
                    self._status_summary = {
                        "backend": "Milvus Lite (Scalable Vector DB)",
                        "status": "ready",
                        "is_new": status.get("is_new", False),
                        "persist_directory": os.path.abspath(milvus_db_path),
                        "collection": self.collection_name,
                        "doc_count": status.get("doc_count", 0),
                    }
                    logger.info("Initialized Milvus Lite vector store at: %s", milvus_db_path)
                    return
            except Exception as e:
                logger.warning("Milvus Lite initialization bypassed (%s), trying ChromaDB...", e)

        # 2. Try ChromaDB
        if self.preferred_backend in ("chroma", "auto", "milvus"):
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(path=self.persist_directory)
                existing_cols = [c.name for c in self._chroma_client.list_collections()]
                is_new = self.collection_name not in existing_cols

                self._chroma_collection = self._chroma_client.get_or_create_collection(name=self.collection_name)
                self.active_backend = "chroma"
                count = self._chroma_collection.count()

                action_desc = "created new collection" if is_new else f"loaded existing collection with {count} documents"
                logger.info("ChromaDB vector store initialized in '%s' (%s: '%s')", self.persist_directory, action_desc, self.collection_name)
                self._status_summary = {
                    "backend": "ChromaDB (Persistent SQLite)",
                    "status": "ready",
                    "is_new": is_new,
                    "persist_directory": os.path.abspath(self.persist_directory),
                    "collection": self.collection_name,
                    "doc_count": count,
                }
                return
            except Exception as e:
                logger.warning("ChromaDB not available or failed (%s), using local fast fallback store.", e)

        # 3. Fast Resilient JSON Fallback Store
        self.active_backend = "fallback"
        self._load_fallback_store()
        self._status_summary = {
            "backend": "Local JSON Fallback Store",
            "status": "fallback",
            "persist_directory": os.path.abspath(self.persist_directory),
            "collection": self.collection_name,
            "doc_count": len(self._fallback_docs),
        }

    def verify_and_diagnose(self) -> Dict[str, Any]:
        """Return diagnostic health information for startup inspection and UI/CLI display."""
        if self.active_backend == "milvus" and self._milvus_store:
            m_stat = self._milvus_store.get_status()
            self._status_summary["doc_count"] = m_stat.get("doc_count", 0)
        elif self.active_backend == "chroma" and self._chroma_collection is not None:
            try:
                self._status_summary["doc_count"] = self._chroma_collection.count()
            except Exception:
                pass
        else:
            self._status_summary["doc_count"] = len(self._fallback_docs)
        return self._status_summary

    def check_scale_threshold(self) -> Dict[str, Any]:
        """Check if vector volume calls for Docker autoscaling."""
        from services.memory.auto_scaler import auto_scaler
        current_docs = self.verify_and_diagnose().get("doc_count", 0)
        return auto_scaler.check_scale(current_docs)

    def _load_fallback_store(self) -> None:
        os.makedirs(self.persist_directory, exist_ok=True)
        store_path = os.path.join(self.persist_directory, f"{self.collection_name}.json")
        if os.path.exists(store_path):
            try:
                with open(store_path, "r", encoding="utf-8") as f:
                    self._fallback_docs = json.load(f)
            except Exception:
                self._fallback_docs = []

    def _save_fallback_store(self) -> None:
        os.makedirs(self.persist_directory, exist_ok=True)
        store_path = os.path.join(self.persist_directory, f"{self.collection_name}.json")
        try:
            with open(store_path, "w", encoding="utf-8") as f:
                json.dump(self._fallback_docs, f, indent=2)
        except Exception as e:
            logger.warning("Could not save fallback vector store: %s", e)

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if not texts:
            return []

        doc_ids = ids or [str(uuid.uuid4()) for _ in texts]
        metas = metadatas or [{} for _ in texts]

        # Milvus Backend
        if self.active_backend == "milvus" and self._milvus_store:
            try:
                res = self._milvus_store.add_documents(texts=texts, metadatas=metas, ids=doc_ids)
                if res:
                    return res
            except Exception as e:
                logger.warning("Milvus add failed (%s), trying fallbacks", e)

        # ChromaDB Backend
        if self.active_backend == "chroma" and self._chroma_collection is not None:
            try:
                self._chroma_collection.add(documents=texts, metadatas=metas, ids=doc_ids)
                return doc_ids
            except Exception as e:
                logger.warning("ChromaDB add failed (%s), falling back to local memory store", e)

        # Fallback storage
        for doc_id, text, meta in zip(doc_ids, texts, metas):
            emb = _simple_text_embedding(text)
            self._fallback_docs.append({
                "id": doc_id,
                "text": text,
                "metadata": meta,
                "embedding": emb,
            })
        self._save_fallback_store()
        return doc_ids

    def search(self, query: str, k: int = 3, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        # Milvus Backend
        if self.active_backend == "milvus" and self._milvus_store:
            try:
                results = self._milvus_store.search(query=query, k=k)
                if results:
                    return results
            except Exception as e:
                logger.warning("Milvus search failed (%s), trying fallback", e)

        # ChromaDB Backend
        if self.active_backend == "chroma" and self._chroma_collection is not None:
            try:
                kwargs: Dict[str, Any] = {"query_texts": [query], "n_results": k}
                if filter_metadata:
                    kwargs["where"] = filter_metadata
                results = self._chroma_collection.query(**kwargs)
                formatted = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]
                    for doc, meta, dist in zip(docs, metas, distances):
                        score = max(0.0, 1.0 - (dist if dist is not None else 0.5))
                        formatted.append({"text": doc, "metadata": meta, "score": round(score, 3)})
                return formatted
            except Exception as e:
                logger.warning("Chroma query failed: %s, using fallback", e)

        # Fallback semantic search
        query_emb = _simple_text_embedding(query)
        scored = []
        for item in self._fallback_docs:
            if filter_metadata:
                match = all(item["metadata"].get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue
            sim = _cosine_similarity(query_emb, item["embedding"])
            scored.append({"text": item["text"], "metadata": item["metadata"], "score": round(sim, 3)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]
