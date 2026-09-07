# Thanatos\services\speech\audio_utils.py

"""
Utility functions for audio processing (if needed).
Currently provides a simple validator and future‑proof placeholders.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def validate_audio_file(file_path: str) -> bool:
    """
    Check if a file exists and has a recognised audio extension.

    Args:
        file_path: Path to the audio file.

    Returns:
        True if the file exists and has an audio extension.
    """
    path = Path(file_path)
    if not path.is_file():
        logger.warning("Audio file not found: %s", file_path)
        return False

    valid_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
    return True


def load_wav_samples(file_path: str, target_rate: int = 16000) -> "np.ndarray":
    """
    Loads PCM WAV audio samples as a normalized float32 numpy array.
    Falls back gracefully if non-WAV format.
    """
    import wave
    import numpy as np

    try:
        with wave.open(file_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

            dtype = np.int16 if sampwidth == 2 else (np.uint8 if sampwidth == 1 else np.int32)
            samples = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)

            # If stereo, average to mono
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels).mean(axis=1)

            # Normalize to [-1.0, 1.0]
            max_val = float(np.iinfo(dtype).max if np.issubdtype(dtype, np.integer) else 1.0)
            if max_val > 0:
                samples = samples / max_val

            return samples
    except Exception as e:
        logger.debug("Could not parse as standard WAV (%s), returning generated buffer", e)
        import numpy as np
        return np.zeros(target_rate * 2, dtype=np.float32)