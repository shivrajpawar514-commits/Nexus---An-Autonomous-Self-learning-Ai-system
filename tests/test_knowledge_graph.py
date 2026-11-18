"""Unit tests for Knowledge Graph memory, triple extraction, and graph-augmented retrieval."""

import pytest
from memory.knowledge_graph import KnowledgeGraph, Triple
from memory.graph_extractor import GraphExtractor
from memory.graph_retriever import GraphRetriever


def test_knowledge_graph_crud_and_query():
    kg = KnowledgeGraph()
    t1 = kg.add_triple("Agent", "USES", "Calculator", 0.95)
    t2 = kg.add_triple("Agent", "USES", "PythonSandbox", 0.9)
    t3 = kg.add_triple("PythonSandbox", "PREVENTS", "FilesystemEscape", 1.0)

    assert kg.count() == 3
    assert len(kg.get_all_entities()) == 4

    # Query by subject
    agent_triples = kg.query_triples(subject="Agent")
    assert len(agent_triples) == 2

    # Query by predicate
    prevents_triples = kg.query_triples(predicate="PREVENTS")
    assert len(prevents_triples) == 1
    assert prevents_triples[0].object == "FilesystemEscape"


def test_knowledge_graph_subgraph_and_pathfinding():
    kg = KnowledgeGraph()
    kg.add_triple("A", "LEADS_TO", "B")
    kg.add_triple("B", "LEADS_TO", "C")
    kg.add_triple("C", "LEADS_TO", "D")

    # Breadth-first shortest path
    path = kg.find_path("A", "D")
    assert path is not None
    assert len(path) == 3
    assert [t.subject for t in path] == ["A", "B", "C"]

    # Connected subgraph from B
    subgraph = kg.find_connected_subgraph("B", max_depth=1)
    assert len(subgraph) >= 2


def test_graph_extractor_from_text():
    kg = KnowledgeGraph()
    extractor = GraphExtractor(kg)

    text = "The orchestrator requires database_adapter to persist runs. Furthermore, PythonSandbox prevents security_breach."
    triples = extractor.extract_from_text(text)

    assert len(triples) >= 2
    preds = [t.predicate for t in triples]
    assert "REQUIRES" in preds
    assert "PREVENTS" in preds


def test_graph_retriever_neighborhood():
    kg = KnowledgeGraph()
    kg.add_triple("Calculator", "USES", "ASTParser", 0.9)
    kg.add_triple("Calculator", "PREVENTS", "ZeroDivisionError", 0.95)

    retriever = GraphRetriever(kg)
    context = retriever.retrieve_context("How does the Calculator perform safely?")

    assert len(context) >= 2
    joined = " ".join(context)
    assert "calculator uses astparser" in joined.lower()
