# Thanatos\services\speech\tts.py

"""
Text‑to‑Speech using Microsoft Edge TTS (edge‑tts).
Outputs MP3 bytes.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional

import edge_tts

logger = logging.getLogger(__name__)

# Common high‑quality voices. You can extend this list.
DEFAULT_VOICE = "en-US-AriaNeural"

class TTSEngine:
    """
    Synthesises speech from text using Edge TTS.
    Always returns MP3 audio bytes.
    """

    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        """
        Args:
            voice: Edge TTS voice name (default 'en-US-AriaNeural').
        """
        # self.voice = voice
        self.default_voice = voice

    async def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:

        """
        Convert text to MP3 audio bytes.

        Args:
            text: The text to speak.
            voice: Override the default voice. If None, uses the default.            

        Returns:
            MP3 audio as bytes.

        Raises:
            ValueError: If text is empty.
            RuntimeError: On TTS synthesis failure.
        """
        if not text or not text.strip():
            raise ValueError("Text must not be empty")

        selected_voice = voice if voice else self.default_voice

        try:
            # communicate = edge_tts.Communicate(text, self.voice)
            communicate = edge_tts.Communicate(text, selected_voice)

            # Stream audio chunks into a temporary file, then read the bytes.
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_path = tmp.name

            try:
                await communicate.save(temp_path)
                with open(temp_path, "rb") as f:
                    audio_bytes = f.read()
                logger.debug("TTS synthesised %d bytes of MP3 audio", len(audio_bytes))
                return audio_bytes
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.exception("TTS synthesis failed")
            raise RuntimeError(f"TTS synthesis failed: {str(e)}") from e