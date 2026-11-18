"""Graph-augmented retrieval combining entity neighbors with similarity matching."""

from __future__ import annotations
from typing import List, Optional
from memory.knowledge_graph import KnowledgeGraph, Triple


class GraphRetriever:
    """Retrieves relevant subgraph context for query keywords."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def retrieve_context(self, query: str, max_depth: int = 1) -> List[str]:
        """Identifies entities in query and expands subgraph neighbors into readable statements."""
        query_words = set(w.lower() for w in query.replace(",", " ").replace(".", " ").split())
        matched_entities = [
            e for e in self.graph.get_all_entities()
            if e.lower() in query_words
        ]

        statements = []
        seen = set()

        for entity in matched_entities:
            subgraph = self.graph.find_connected_subgraph(entity, max_depth=max_depth)
            for t in subgraph:
                stmt = f"{t.subject} {t.predicate.lower()} {t.object}"
                if stmt not in seen:
                    seen.add(stmt)
                    statements.append(stmt)

        return statements
