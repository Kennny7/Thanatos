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
    if path.suffix.lower() not in valid_extensions:
        logger.warning("Unsupported audio extension: %s", path.suffix)
        return False

    return True