"""Dependency-free TF-IDF retriever.

Kept deliberately simple: retrieval quality is not the subject of this project,
the permission layer is. Swap this for an embedding retriever behind the same
`search(query, candidates, k)` signature and nothing else changes.
"""
import math
import re
from collections import Counter


def _tok(s: str):
    return re.findall(r"[a-z0-9]+", s.lower())


class TfidfRetriever:
    def __init__(self, docs):
        self.docs = docs
        toks = [_tok(d.text + " " + d.title) for d in docs]
        df = Counter()
        for t in toks:
            for w in set(t):
                df[w] += 1
        n = len(docs)
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}
        self.vecs = [self._vec(t) for t in toks]

    def _vec(self, toks):
        if not toks:
            return {}
        tf = Counter(toks)
        return {w: (f / len(toks)) * self.idf.get(w, 0.0) for w, f in tf.items()}

    @staticmethod
    def _cos(a, b):
        if not a or not b:
            return 0.0
        num = sum(v * b.get(w, 0.0) for w, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return num / (na * nb) if na and nb else 0.0

    def search(self, query, candidates=None, k=6):
        """Return top-k docs. `candidates` restricts the index (used to filter
        BEFORE retrieval); None searches the whole corpus."""
        qv = self._vec(_tok(query))
        idxs = range(len(self.docs)) if candidates is None else candidates
        scored = sorted(((self._cos(qv, self.vecs[i]), i) for i in idxs), reverse=True)
        return [self.docs[i] for s, i in scored[:k] if s > 0]
