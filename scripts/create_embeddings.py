"""
create_embeddings.py
--------------------
Multilingual embedding generator for Tamil classical literature.
"""

import os
from typing import List
import numpy as np

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class MultilingualEmbeddingService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    def _lazy_load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                if hasattr(self._model, "get_embedding_dimension"):
                    self._dimension = self._model.get_embedding_dimension()
                elif hasattr(self._model, "get_sentence_embedding_dimension"):
                    self._dimension = self._model.get_sentence_embedding_dimension()
            except Exception as e:
                print(f"[!] Warning: Could not load SentenceTransformer ({e}).")
                raise e

    def get_dimension(self) -> int:
        self._lazy_load()
        return self._dimension

    def encode_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        self._lazy_load()
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.tolist()

    def encode_query(self, query_text: str) -> List[float]:
        self._lazy_load()
        emb = self._model.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return emb.tolist()


class ChromaMultilingualEmbeddingFunction:
    def __init__(self, model_service: MultilingualEmbeddingService = None):
        self.service = model_service or MultilingualEmbeddingService()

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.service.encode_documents(input)

    def name(self) -> str:
        return f"multilingual_{self.service.model_name.replace('/', '_')}"
