# Thanatos\services\speech\speech_service.py

"""
Unified SpeechService that exposes both STT and TTS.
This is the public API for the rest of the project.
"""

import asyncio
import logging
from typing import Optional

from .stt import STTEngine
from .tts import TTSEngine

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Facade for speech‑related operations: transcription and synthesis.
    Models are loaded lazily.
    """
    def __init__(
        self,
        stt_model_size: str = "base",
        stt_device: str = "cpu",
        stt_compute_type: str = "int8",
        tts_voice: str = "en-US-AriaNeural",
    ) -> None:
        self._stt_engine = STTEngine(
            model_size=stt_model_size,
            device=stt_device,
            compute_type=stt_compute_type,
        )
        self._tts_engine = TTSEngine(voice=tts_voice)

    def transcribe(self, audio_file_path: str) -> str:
        """
        Synchronous transcription.

        Args:
            audio_file_path: Path to audio file.

        Returns:
            Transcribed text.
        """
        logger.info("Starting transcription of %s", audio_file_path)
        return self._stt_engine.transcribe(audio_file_path)

    async def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Asynchronous TTS synthesis.

        Args:
            text: Text to convert to speech.
            voice: Override the default voice. If None, uses the engine's voice.

        Returns:
            MP3 audio bytes.
        """
        logger.info("Starting TTS synthesis for %d chars", len(text))
        return await self._tts_engine.synthesize(text, voice=voice)
