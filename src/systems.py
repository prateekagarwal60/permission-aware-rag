"""Three reference systems, increasing permission maturity.

  naive             retrieve from the whole corpus, ignore who is asking.
  gen_filter        retrieve everything, then ask the model to self-censor
                    the documents the user may not see.  Data is still in context.
  retrieval_filter  filter the corpus by permission BEFORE retrieval, so
                    restricted documents never enter context at all.

The difference between gen_filter and retrieval_filter is the point: it is not
model quality, it is whether restricted data ever reaches the context window.
"""
from .world import allowed


class BaseRAG:
    name = "base"

    def __init__(self, retriever, llm, corpus, matrix, k=6):
        self.r = retriever
        self.llm = llm
        self.corpus = corpus
        self.matrix = matrix
        self.k = k

    def answer(self, persona, query):
        raise NotImplementedError


class NaiveRAG(BaseRAG):
    name = "naive"

    def answer(self, persona, query):
        docs = self.r.search(query, None, self.k)
        ans = self.llm.generate(persona, query, docs, enforce=False)
        return ans, [d.id for d in docs]


class GenFilterRAG(BaseRAG):
    name = "gen_filter"

    def answer(self, persona, query):
        docs = self.r.search(query, None, self.k)  # retrieves restricted docs too
        allow_ids = {d.id for d in docs if allowed(persona, d, self.matrix)}
        ans = self.llm.generate(persona, query, docs, enforce=True, allow_ids=allow_ids)
        return ans, [d.id for d in docs]


class RetrievalFilterRAG(BaseRAG):
    name = "retrieval_filter"

    def answer(self, persona, query):
        cand = [i for i, d in enumerate(self.corpus) if allowed(persona, d, self.matrix)]
        docs = self.r.search(query, cand, self.k)  # restricted docs never in the candidate set
        ans = self.llm.generate(persona, query, docs, enforce=False)
        return ans, [d.id for d in docs]


SYSTEMS = [NaiveRAG, GenFilterRAG, RetrievalFilterRAG]
