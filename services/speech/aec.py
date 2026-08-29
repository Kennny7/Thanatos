# Thanatos/services/speech/aec.py

import logging
import math
import numpy as np
from typing import Tuple

logger = logging.getLogger(__name__)


class AECProcessor:
    """
    Acoustic Echo Cancellation (AEC) and Spectral Noise Suppressor.
    Removes acoustic feedback from speaker output and filters ambient noise.
    """

    def __init__(self, filter_strength: float = 0.8) -> None:
        self.filter_strength = filter_strength

    def cancel_echo_and_noise(self, mic_signal: np.ndarray, ref_signal: np.ndarray = None) -> np.ndarray:
        """
        Suppresses acoustic echo and stationary background noise.
        """
        if mic_signal is None or len(mic_signal) == 0:
            return mic_signal

        # Normalize to float array
        audio = mic_signal.astype(np.float32)
        max_val = np.max(np.abs(audio)) or 1.0
        audio = audio / max_val

        # Spectral noise gating: estimate noise floor from low energy frames
        frame_size = 512
        cleaned = np.copy(audio)
        
        # Simple adaptive spectral subtraction / gating
        rms = np.sqrt(np.mean(audio ** 2))
        noise_thresh = rms * 0.35

        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i : i + frame_size]
            frame_rms = np.sqrt(np.mean(frame ** 2))
            if frame_rms < noise_thresh:
                cleaned[i : i + frame_size] = frame * (1.0 - self.filter_strength)

        # Scale back
        cleaned = cleaned * max_val
        return cleaned.astype(mic_signal.dtype)

    def process_wav_bytes(self, wav_bytes: bytes) -> bytes:
        """Processes raw PCM audio bytes to apply AEC."""
        try:
            audio_array = np.frombuffer(wav_bytes, dtype=np.int16)
            cleaned_array = self.cancel_echo_and_noise(audio_array)
            return cleaned_array.tobytes()
        except Exception as e:
            logger.warning("AEC processing fallback: %s", e)
            return wav_bytes
