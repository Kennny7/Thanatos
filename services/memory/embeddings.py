# Thanatos\services\memory\embeddings.py

"""
Local embedding function using sentence-transformers/all-MiniLM-L6-v2.
Runs on CPU by default.
"""

from typing import List

import chromadb
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer


class MiniLMEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB embedding function wrapper around the all-MiniLM-L6-v2 model
    from HuggingFace. Forces execution on the specified device (default: CPU).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu") -> None:
        """
        Args:
            model_name: HuggingFace sentence-transformers model identifier.
            device: 'cpu', 'cuda', etc. Defaults to 'cpu' for local usage.
        """
        # Explicitly load on the given device; no GPU by default.
        self.model = SentenceTransformer(model_name_or_path=model_name, device=device)

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.

        Args:
            input: List of strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        if not input:
            return []
        # encode returns a numpy array; convert to list of lists.
        embeddings = self.model.encode(
            input,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32,          # sensible default for CPU
        )
        return embeddings.tolist()