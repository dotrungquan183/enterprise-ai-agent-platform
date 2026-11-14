import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class HybridRAGEngine:
    def __init__(self, kb_path: str = "data/knowledge_base.md"):
        self.kb_path = kb_path
        self.chunks = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self._build_index()

    def _build_index(self):
        if not os.path.exists(self.kb_path):
            self.chunks = ["Chưa có dữ liệu tài liệu nội bộ."]
        else:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            sections = [s.strip() for s in raw_text.split("## ") if s.strip()]
            self.chunks = [f"## {s}" for s in sections]

        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

    def retrieve(self, query: str, top_k: int = 2) -> list:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.01:
                results.append({
                    "chunk_content": self.chunks[idx],
                    "similarity_score": round(float(scores[idx]), 4)
                })
        return results
