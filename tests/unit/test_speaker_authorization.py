# tests/unit/test_speaker_authorization.py

import os
import shutil
import tempfile
import numpy as np
import pytest
from services.speech.speaker_id import SpeakerIdentifier


@pytest.fixture
def temp_profile_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


def test_speaker_enrollment_and_authorization(temp_profile_dir):
    spk_id = SpeakerIdentifier(profile_dir=temp_profile_dir)
    assert not spk_id.is_enrolled()

    # Generate synthetic voice features
    rng = np.random.RandomState(42)
    owner_samples = (rng.randn(16000 * 2) * 0.1).astype(np.float32)

    # Enroll owner (Boss)
    res = spk_id.enroll_owner_voice(owner_samples)
    assert res["status"] == "success"
    assert spk_id.is_enrolled()

    # Verify same voice belongs to owner
    ver_owner = spk_id.verify_speaker(owner_samples)
    assert ver_owner["is_owner"] is True
    assert ver_owner["is_authorized"] is True
    assert ver_owner["action"] == "allow"
    assert "Owner" in ver_owner["speaker"]

    # Enroll an authorized delegate (e.g. Alice)
    rng_alice = np.random.RandomState(999)
    alice_samples = (rng_alice.randn(16000 * 2) * 0.1).astype(np.float32)
    res_alice = spk_id.enroll_authorized_speaker("Alice", alice_samples, role="assistant_operator")
    assert res_alice["status"] == "success"

    # Verify Alice is authorized
    ver_alice = spk_id.verify_speaker(alice_samples)
    assert ver_alice["is_authorized"] is True
    assert ver_alice["action"] == "allow"
    assert "Alice" in ver_alice["speaker"]

    # Check authorized speakers list
    speakers = spk_id.list_authorized_speakers()
    assert any(s["name"] == "Owner (Boss)" for s in speakers)
    assert any(s["name"] == "Alice" for s in speakers)

    # Test VAD
    vad = spk_id.detect_voice_activity(owner_samples)
    assert "is_speech" in vad
    assert "rms" in vad
    assert "dominant_hz" in vad
