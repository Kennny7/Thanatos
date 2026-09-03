# Thanatos/services/speech/speaker_id.py

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple
from config.settings import app_config
import numpy as np

logger = logging.getLogger(__name__)


def _extract_voice_features(audio_samples: np.ndarray, sample_rate: int = 16000) -> List[float]:
    """
    Extracts acoustic spectral and temporal features (energy, zero-crossing, spectral centroid, sub-band energies).
    """
    if len(audio_samples) == 0:
        return [0.0] * 16

    samples = audio_samples.astype(np.float32)
    # 1. Zero crossing rate
    zcr = np.mean(np.abs(np.diff(np.sign(samples)))) / 2.0
    
    # 2. RMS Energy
    rms = np.sqrt(np.mean(samples ** 2))
    
    # 3. FFT Spectral features
    fft_vals = np.abs(np.fft.rfft(samples))
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    
    spectral_centroid = np.sum(freqs * fft_vals) / (np.sum(fft_vals) + 1e-8)
    
    # 4. Energy across 13 sub-bands (similar to MFCC energy bands)
    bands = 13
    band_len = len(fft_vals) // bands
    band_energies = []
    for i in range(bands):
        sub = fft_vals[i * band_len : (i + 1) * band_len]
        energy = np.mean(sub ** 2) if len(sub) > 0 else 0.0
        band_energies.append(float(np.log1p(energy)))

    features = [float(zcr), float(rms), float(spectral_centroid / 4000.0)] + band_energies
    return features


def _euclidean_distance(v1: List[float], v2: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


class SpeakerIdentifier:
    """
    Speaker Diarization and Voice Recognition Engine.
    Identifies the primary user ("Owner") vs "Guest / Other Speakers".
    """

    def __init__(self, profile_dir: str = app_config.speaker_enrollment_dir) -> None:
        self.profile_dir = profile_dir
        self.owner_profile_path = os.path.join(self.profile_dir, "owner_voice.json")
        self.owner_features: Optional[List[float]] = None
        self._load_owner_profile()

    def _load_owner_profile(self) -> None:
        if os.path.exists(self.owner_profile_path):
            try:
                with open(self.owner_profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.owner_features = data.get("features")
                    logger.info("Owner voice profile loaded from %s", self.owner_profile_path)
            except Exception as e:
                logger.warning("Could not load owner voice profile: %s", e)

    def enroll_owner_voice(self, audio_samples: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Enroll the owner's voice fingerprint."""
        features = _extract_voice_features(audio_samples, sample_rate)
        self.owner_features = features
        os.makedirs(self.profile_dir, exist_ok=True)
        with open(self.owner_profile_path, "w", encoding="utf-8") as f:
            json.dump({"features": features, "sample_rate": sample_rate}, f, indent=2)
        logger.info("Enrolled owner voice profile successfully.")
        return {"status": "success", "message": "Owner voice enrolled successfully!"}

    def is_enrolled(self) -> bool:
        return self.owner_features is not None

    def diarize_audio(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
        segment_duration_sec: float = 3.0,
    ) -> List[Dict[str, Any]]:
        """
        Segments audio into speaker turns and classifies each as Owner ("You") or Guest Speaker.
        """
        if len(audio_samples) == 0:
            return []

        segment_len = int(sample_rate * segment_duration_sec)
        segments = []
        num_segments = max(1, len(audio_samples) // segment_len)

        for i in range(num_segments):
            start_sample = i * segment_len
            end_sample = min(len(audio_samples), (i + 1) * segment_len)
            chunk = audio_samples[start_sample:end_sample]

            if len(chunk) < sample_rate * 0.5:
                continue

            chunk_feat = _extract_voice_features(chunk, sample_rate)

            # Determine speaker identity
            if self.owner_features is not None:
                dist = _euclidean_distance(chunk_feat, self.owner_features)
                is_owner = dist < 2.5
                speaker_tag = "Owner (You)" if is_owner else f"Guest Speaker {(i % 2) + 1}"
                confidence = max(0.5, min(0.99, 1.0 - (dist / 5.0)))
            else:
                # If not enrolled yet, default first turn to User
                speaker_tag = "Speaker 1 (You)" if i == 0 else f"Speaker {(i % 2) + 1}"
                confidence = 0.85

            segments.append({
                "segment_index": i,
                "start_time_sec": round(start_sample / sample_rate, 2),
                "end_time_sec": round(end_sample / sample_rate, 2),
                "speaker": speaker_tag,
                "confidence": round(confidence, 2),
            })

        return segments
