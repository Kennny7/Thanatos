# tests/unit/test_enhancements.py

import os
import pytest
from services.memory.vector_store import VectorStore
from services.memory.auto_scaler import auto_scaler
from services.document.pdf_generator import pdf_generator
from services.mesh.node_manager import MeshNodeManager


def test_pdf_resume_and_cover_letter_generation(tmp_path):
    resume_pdf = os.path.join(tmp_path, "resume.pdf")
    cover_pdf = os.path.join(tmp_path, "cover.pdf")

    pdf_generator.generate_resume_pdf(
        source_tex_or_md="### Summary\nExperienced AI Engineer with 3+ years in LLMs and RAG pipelines.\n• Developed multi-agent orchestration.",
        output_pdf_path=resume_pdf,
        candidate_name="Khushal Pareta",
    )
    assert os.path.exists(resume_pdf)
    assert os.path.getsize(resume_pdf) > 500

    pdf_generator.generate_cover_letter_pdf(
        cover_letter_text="Dear Hiring Lead,\n\nI am writing to express my strong interest in the AI Engineer role.",
        applicant_name="Khushal Pareta",
        job_title="AI Engineer",
        company="DeepLogic AI Labs",
        output_pdf_path=cover_pdf,
    )
    assert os.path.exists(cover_pdf)
    assert os.path.getsize(cover_pdf) > 500


def test_milvus_lite_vector_store(tmp_path):
    vs = VectorStore(
        persist_directory=str(tmp_path),
        collection_name="test_memories",
        preferred_backend="milvus",
    )
    diag = vs.verify_and_diagnose()
    assert diag["status"] == "ready"
    assert "Milvus" in diag["backend"]

    # Ingest and search
    doc_ids = vs.add_documents(
        texts=["LLM agent orchestration and distributed compute on LAN mesh."],
        metadatas=[{"category": "architecture"}],
    )
    assert len(doc_ids) == 1

    hits = vs.search(query="mesh compute", k=1)
    assert len(hits) >= 1
    assert "LLM agent" in hits[0]["text"]


def test_auto_scaler_threshold():
    scale_info = auto_scaler.check_scale(current_doc_count=1200)
    assert scale_info["needs_scale"] is True
    assert "Milvus" in scale_info["recommended_backends"]["vector"]

    scale_info_low = auto_scaler.check_scale(current_doc_count=50)
    assert scale_info_low["needs_scale"] is False


def test_mesh_node_manager(tmp_path):
    state_file = os.path.join(tmp_path, "mesh_nodes.json")
    mgr = MeshNodeManager(state_file=state_file)

    # Register worker node
    entry = mgr.register_node(node_id="phone_worker", host="192.168.1.55", port=8002, role="worker")
    assert entry["endpoint"] == "http://192.168.1.55:8002"
    assert len(mgr.list_nodes()) == 1

    # Local specs
    specs = mgr.get_local_specs()
    assert "os" in specs
    assert "machine" in specs

    # Unregister
    assert mgr.unregister_node("phone_worker") is True
    assert len(mgr.list_nodes()) == 0
