# ADR 003: Relational Knowledge Graph Subsystem for Multi-Hop Memory Retrieval

## Status
Accepted

## Context
While episodic memory stores full trajectory JSON records and semantic memory scores flat lesson texts with TF-IDF/recency factors, complex autonomous workflows require multi-hop relationship traversal (e.g., determining that `Tool A` produces an intermediate artifact that satisfies the prerequisite for `Tool B`, or tracing root causes through causal dependency chains).

## Decision
We implement:
1. **Relational Knowledge Graph (`KnowledgeGraph`)**: Stores directed `(Subject, Predicate, Object)` triples with confidence scores and bidirectionally indexed adjacency lists.
2. **Pathfinding & Neighborhood Expansion**: Implements breadth-first search pathfinding (`find_path`) and $k$-hop subgraph extraction (`find_connected_subgraph`).
3. **Automated Triple Extraction (`GraphExtractor`)**: Regex and pattern-based relationship extraction (`REQUIRES`, `PREVENTS`, `CAUSES`, `USES`, `PRODUCES`) mining reflection post-mortems.
4. **Graph-Augmented Retrieval (`GraphRetriever`)**: Expands matched entities from task prompts into relational context strings.
5. **Observability**: Exposes `/api/knowledge-graph` endpoint exporting node and edge datasets for web-based graph visualizers.

## Consequences
- Enables structured entity reasoning and multi-step causal deduction.
- Provides graphical topological views of learned agent knowledge.
- Preserves backward compatibility with existing episodic and semantic memory layers.
