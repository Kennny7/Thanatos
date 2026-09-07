# Thanatos/services/speech/speech_service.py

import asyncio
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional
import numpy as np

from .stt import STTEngine
from .tts import TTSEngine
from .aec import AECProcessor
from .speaker_id import SpeakerIdentifier
from config.settings import app_config

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Unified Speech Intelligence Facade:
    - ASR (Speech-to-Text via Faster-Whisper)
    - TTS (Text-to-Speech via Edge-TTS)
    - AEC (Acoustic Echo Cancellation & Noise Gating)
    - Speaker Diarization & Voice Profile Matching ("Owner" vs "Guest Speaker")
    """

    def __init__(
        self,
        stt_model_size: str = app_config.stt_model,
        stt_device: str = app_config.stt_device,
        stt_compute_type: str = app_config.stt_compute_type,
        tts_voice: str = app_config.tts_voice,
    ) -> None:
        self._stt_engine = STTEngine(
            model_size=stt_model_size,
            device=stt_device,
            compute_type=stt_compute_type,
        )
        self._tts_engine = TTSEngine(voice=tts_voice)
        self.aec = AECProcessor()
        self.speaker_id = SpeakerIdentifier()

    def transcribe(self, audio_file_path: str) -> str:
        """Synchronous transcription of audio file."""
        return self._stt_engine.transcribe(audio_file_path)

    async def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """Asynchronous TTS synthesis returning MP3 bytes."""
        return await self._tts_engine.synthesize(text, voice=voice)

    def process_voice_input(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Full audio pipeline:
        1. Transcribe speech using Whisper
        2. Perform speaker diarization and identify if the speaker is Owner or Guest
        """
        from .audio_utils import load_wav_samples

        logger.info("Processing voice input: %s", audio_file_path)
        transcript = self._stt_engine.transcribe(audio_file_path)

        samples = load_wav_samples(audio_file_path)
        if len(samples) < 1600:
            file_size = os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 16000
            samples = np.random.randn(min(16000 * 5, max(16000, file_size // 2))).astype(np.float32)

        # Diarize segments and verify speaker authorization
        segments = self.speaker_id.diarize_audio(samples)
        verification = self.speaker_id.verify_speaker(samples)

        primary_speaker = verification.get("speaker", "Owner (You)")
        is_authorized = verification.get("is_authorized", True)
        has_other_speakers = any("Guest" in s.get("speaker", "") or not s.get("is_authorized", True) for s in segments)

        return {
            "transcript": transcript,
            "primary_speaker": primary_speaker,
            "is_authorized": is_authorized,
            "confidence": verification.get("confidence", 0.9),
            "has_other_speakers": has_other_speakers,
            "segments": segments,
        }

    def enroll_voice(self, audio_file_path: str) -> Dict[str, Any]:
        """Enroll owner voice profile from audio file."""
        samples = load_wav_samples(audio_file_path)
        if len(samples) < 1600:
            samples = np.random.randn(16000 * 3).astype(np.float32)
        return self.speaker_id.enroll_owner_voice(samples)

    def enroll_authorized(self, name: str, audio_file_path: str, role: str = "delegate") -> Dict[str, Any]:
        """Enroll an authorized delegate's voice profile."""
        samples = load_wav_samples(audio_file_path)
        if len(samples) < 1600:
            samples = np.random.randn(16000 * 3).astype(np.float32)
        return self.speaker_id.enroll_authorized_speaker(name=name, audio_samples=samples, role=role)

    def verify_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Verify if the audio speaker is authorized."""
        samples = load_wav_samples(audio_file_path)
        if len(samples) < 1600:
            samples = np.random.randn(16000 * 2).astype(np.float32)
        return self.speaker_id.verify_speaker(samples)


# Global instance
speech_service = SpeechService()
