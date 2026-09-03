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
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class VectorStore:
    """
    Robust Vector Store supporting ChromaDB with seamless in-memory / JSON file fallback.
    """

    def __init__(
        self,
        persist_directory: str = app_config.memory_persist_dir,
        collection_name: str = app_config.memory_collection,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._use_chroma = False
        self._chroma_client = None
        self._collection = None
        self._fallback_docs: List[Dict[str, Any]] = []

        self._init_backend()

    def _init_backend(self) -> None:
        try:
            import chromadb
            os.makedirs(self.persist_directory, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._chroma_client.get_or_create_collection(name=self.collection_name)
            self._use_chroma = True
            logger.info("ChromaDB vector store initialized in %s", self.persist_directory)
        except Exception as e:
            logger.warning("ChromaDB not available (%s), using local fast fallback store.", e)
            self._use_chroma = False
            self._load_fallback_store()

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

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(documents=texts, metadatas=metas, ids=doc_ids)
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

        if self._use_chroma and self._collection is not None:
            try:
                kwargs: Dict[str, Any] = {"query_texts": [query], "n_results": k}
                if filter_metadata:
                    kwargs["where"] = filter_metadata
                results = self._collection.query(**kwargs)
                formatted = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]
                    for doc, meta, dist in zip(docs, metas, distances):
                        # Convert distance to similarity score
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
