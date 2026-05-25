# Thanatos\services\speech\stt.py

"""
Speech‑to‑Text using faster‑whisper.
Model is loaded lazily and kept in memory after first use.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class STTEngine:
    """
    Handles transcription of audio files using faster‑whisper.
    Supports model sizes: tiny, base, small, medium, large.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """
        Args:
            model_size: Whisper model size (default 'base').
            device: 'cpu' or 'cuda'.
            compute_type: quantization type ('int8', 'float16', etc.).
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[object] = None  # faster_whisper.WhisperModel

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            logger.info(
                "Loading faster‑whisper model '%s' on %s (compute_type=%s)",
                self.model_size,
                self.device,
                self.compute_type,
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as e:
            logger.exception("Failed to load faster‑whisper model")
            raise RuntimeError("Could not load STT model") from e

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file and return the text.

        Args:
            audio_file_path: Path to the audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text.

        Raises:
            FileNotFoundError: If the audio file does not exist.
            RuntimeError: On transcription failure.
        """
        if not os.path.isfile(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        self._load_model()
        try:
            segments, _ = self._model.transcribe(audio_file_path, beam_size=5)
            transcript = " ".join(segment.text for segment in segments)
            logger.debug("Transcription completed: %d chars", len(transcript))
            return transcript.strip()
        except Exception as e:
            logger.exception("Transcription failed for %s", audio_file_path)
            raise RuntimeError(f"Transcription failed: {str(e)}") from e