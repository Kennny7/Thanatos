# tests/unit/test_memory_rag.py

import pytest
from services.memory.memory_manager import MemoryManager


def test_memory_add_and_search():
    mem = MemoryManager(persist_directory="./scratch/test_memory_store", collection_name="test_col")
    mem_id = mem.add_memory("User is interested in machine learning and fresher jobs in Pune.", metadata={"tag": "interest"})
    assert mem_id is not None

    results = mem.search("Pune jobs", k=1)
    assert len(results) >= 1
    assert "Pune" in results[0]["text"]


def test_user_profile_context():
    mem = MemoryManager(persist_directory="./scratch/test_memory_store", collection_name="test_col")
    ctx = mem.get_relevant_context("job application")
    assert "CANDIDATE PROFILE" in ctx
    assert "Technical Skills" in ctx
