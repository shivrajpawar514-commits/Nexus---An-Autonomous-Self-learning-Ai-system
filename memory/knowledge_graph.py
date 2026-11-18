"""Knowledge Graph Memory storing entity-relation-entity triples for multi-hop reasoning."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class Triple(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "agent"
    timestamp: float = Field(default_factory=time.time)


class KnowledgeGraph:
    """Directed multi-relational knowledge graph."""

    def __init__(self):
        self._triples: List[Triple] = []
        # Adjacency mapping: subject -> list of (predicate, object, confidence)
        self._out_edges: Dict[str, List[Triple]] = {}
        # Inverted mapping: object -> list of (subject, predicate, confidence)
        self._in_edges: Dict[str, List[Triple]] = {}

    def add_triple(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: str = "agent",
    ) -> Triple:
        """Add a directed triple to the knowledge graph."""
        sub = subject.strip()
        pred = predicate.strip().upper()
        obj = object.strip()

        # Check existing duplicate
        for t in self._out_edges.get(sub, []):
            if t.predicate == pred and t.object == obj:
                t.confidence = max(t.confidence, confidence)
                return t

        triple = Triple(
            subject=sub,
            predicate=pred,
            object=obj,
            confidence=confidence,
            source=source,
            timestamp=time.time(),
        )
        self._triples.append(triple)

        if sub not in self._out_edges:
            self._out_edges[sub] = []
        self._out_edges[sub].append(triple)

        if obj not in self._in_edges:
            self._in_edges[obj] = []
        self._in_edges[obj].append(triple)

        return triple

    def query_triples(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Triple]:
        """Query triples matching subject, predicate, or object filters."""
        results = self._triples
        if subject:
            results = [t for t in results if t.subject.lower() == subject.lower()]
        if predicate:
            results = [t for t in results if t.predicate.upper() == predicate.upper()]
        if object:
            results = [t for t in results if t.object.lower() == object.lower()]
        return results

    def find_connected_subgraph(self, start_entity: str, max_depth: int = 2) -> List[Triple]:
        """Explore outward from an entity up to max_depth hops."""
        visited_entities: Set[str] = {start_entity.strip()}
        subgraph: List[Triple] = []
        current_frontier = {start_entity.strip()}

        for _ in range(max_depth):
            next_frontier = set()
            for entity in current_frontier:
                # Outgoing edges
                for t in self._out_edges.get(entity, []):
                    if t not in subgraph:
                        subgraph.append(t)
                    if t.object not in visited_entities:
                        visited_entities.add(t.object)
                        next_frontier.add(t.object)
                # Incoming edges
                for t in self._in_edges.get(entity, []):
                    if t not in subgraph:
                        subgraph.append(t)
                    if t.subject not in visited_entities:
                        visited_entities.add(t.subject)
                        next_frontier.add(t.subject)
            current_frontier = next_frontier
            if not current_frontier:
                break

        return subgraph

    def find_path(self, start_entity: str, end_entity: str, max_depth: int = 4) -> Optional[List[Triple]]:
        """Breadth-first search finding shortest relational path between two entities."""
        start = start_entity.strip()
        target = end_entity.strip()

        if start == target:
            return []

        queue: List[Tuple[str, List[Triple]]] = [(start, [])]
        visited: Set[str] = {start}

        while queue:
            current, path = queue.pop(0)
            if len(path) >= max_depth:
                continue

            for t in self._out_edges.get(current, []):
                if t.object == target:
                    return path + [t]
                if t.object not in visited:
                    visited.add(t.object)
                    queue.append((t.object, path + [t]))

        return None

    def get_all_entities(self) -> List[str]:
        entities = set(self._out_edges.keys()).union(set(self._in_edges.keys()))
        return sorted(list(entities))

    def count(self) -> int:
        return len(self._triples)

    def export_graph_json(self) -> Dict[str, Any]:
        """Export nodes and edges for visualization tools."""
        entities = self.get_all_entities()
        nodes = [{"id": e, "label": e} for e in entities]
        edges = [
            {
                "source": t.subject,
                "target": t.object,
                "label": t.predicate,
                "confidence": t.confidence,
            }
            for t in self._triples
        ]
        return {"nodes": nodes, "edges": edges}
