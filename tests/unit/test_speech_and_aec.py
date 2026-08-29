# tests/unit/test_speech_and_aec.py

import numpy as np
import pytest
from services.speech.aec import AECProcessor
from services.speech.speaker_id import SpeakerIdentifier, _extract_voice_features


def test_aec_processor():
    aec = AECProcessor()
    # Create test signal with noise
    samples = np.sin(np.linspace(0, 100, 4000)).astype(np.float32)
    noise = np.random.normal(0, 0.05, 4000).astype(np.float32)
    mic_signal = samples + noise

    cleaned = aec.cancel_echo_and_noise(mic_signal)
    assert len(cleaned) == len(mic_signal)


def test_speaker_identifier_enrollment_and_diarization():
    speaker_id = SpeakerIdentifier(profile_dir="./scratch/test_voice_profiles")
    # Owner sample
    owner_samples = np.sin(np.linspace(0, 50, 16000 * 2)).astype(np.float32)
    res = speaker_id.enroll_owner_voice(owner_samples)
    assert res["status"] == "success"
    assert speaker_id.is_enrolled() is True

    # Diarize test audio
    test_audio = np.random.randn(16000 * 6).astype(np.float32)
    segments = speaker_id.diarize_audio(test_audio, segment_duration_sec=3.0)
    assert len(segments) >= 2
    assert "speaker" in segments[0]
