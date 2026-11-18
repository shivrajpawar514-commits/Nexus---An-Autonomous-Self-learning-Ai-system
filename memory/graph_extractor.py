"""Automated extraction of knowledge graph relations from execution logs and lessons."""

from __future__ import annotations
import re
from typing import List, Optional
from memory.knowledge_graph import KnowledgeGraph, Triple


class GraphExtractor:
    """Heuristic and regex parser to extract semantic relations from agent lessons and observations."""

    RELATION_PATTERNS = [
        # Entity REQUIRES Entity
        (r"([A-Za-z0-9_]+)\s+requires\s+([A-Za-z0-9_]+)", "REQUIRES"),
        # Entity PREVENTS Entity
        (r"([A-Za-z0-9_]+)\s+prevents\s+([A-Za-z0-9_]+)", "PREVENTS"),
        # Entity CAUSES Entity
        (r"([A-Za-z0-9_]+)\s+causes\s+([A-Za-z0-9_]+)", "CAUSES"),
        # Entity USES Entity
        (r"([A-Za-z0-9_]+)\s+uses\s+([A-Za-z0-9_]+)", "USES"),
        # Entity PRODUCES Entity
        (r"([A-Za-z0-9_]+)\s+produces\s+([A-Za-z0-9_]+)", "PRODUCES"),
    ]

    def __init__(self, graph: Optional[KnowledgeGraph] = None):
        self.graph = graph or KnowledgeGraph()

    def extract_from_text(self, text: str, source: str = "text") -> List[Triple]:
        """Extract entity-relation-entity triples from plain English text."""
        extracted: List[Triple] = []
        for pattern, predicate in self.RELATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for sub, obj in matches:
                if len(sub) > 1 and len(obj) > 1:
                    t = self.graph.add_triple(
                        subject=sub.strip(),
                        predicate=predicate,
                        object=obj.strip(),
                        confidence=0.85,
                        source=source,
                    )
                    extracted.append(t)
        return extracted
