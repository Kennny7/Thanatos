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
    Speaker Diarization, Voice Recognition, and Authorization Engine.
    Distinguishes the primary system owner ("Owner / Boss"),
    authorized secondary delegates ("Authorized Users"), and unauthorized third-party guests.
    """

    def __init__(self, profile_dir: str = app_config.speaker_enrollment_dir) -> None:
        self.profile_dir = profile_dir
        self.owner_profile_path = os.path.join(self.profile_dir, "owner_voice.json")
        self.authorized_profiles_path = os.path.join(self.profile_dir, "authorized_speakers.json")
        self.owner_features: Optional[List[float]] = None
        self.authorized_speakers: Dict[str, Dict[str, Any]] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        # Load primary owner profile
        if os.path.exists(self.owner_profile_path):
            try:
                with open(self.owner_profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.owner_features = data.get("features")
                    logger.info("Owner voice profile loaded from %s", self.owner_profile_path)
            except Exception as e:
                logger.warning("Could not load owner voice profile: %s", e)

        # Load authorized delegates list
        if os.path.exists(self.authorized_profiles_path):
            try:
                with open(self.authorized_profiles_path, "r", encoding="utf-8") as f:
                    self.authorized_speakers = json.load(f)
                    logger.info("Loaded %d authorized speaker profiles", len(self.authorized_speakers))
            except Exception as e:
                logger.warning("Could not load authorized speakers: %s", e)

    def enroll_owner_voice(self, audio_samples: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Enroll or update the owner's (boss) biometric voice fingerprint."""
        features = _extract_voice_features(audio_samples, sample_rate)
        self.owner_features = features
        os.makedirs(self.profile_dir, exist_ok=True)
        with open(self.owner_profile_path, "w", encoding="utf-8") as f:
            json.dump({"features": features, "sample_rate": sample_rate}, f, indent=2)
        logger.info("Enrolled owner voice profile successfully.")
        return {"status": "success", "message": "Owner (Boss) voice enrolled successfully."}

    def enroll_authorized_speaker(
        self,
        name: str,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
        role: str = "delegate",
    ) -> Dict[str, Any]:
        """Enroll an authorized delegate permitted to issue directives."""
        features = _extract_voice_features(audio_samples, sample_rate)
        os.makedirs(self.profile_dir, exist_ok=True)
        self.authorized_speakers[name] = {
            "name": name,
            "role": role,
            "features": features,
            "sample_rate": sample_rate,
        }
        with open(self.authorized_profiles_path, "w", encoding="utf-8") as f:
            json.dump(self.authorized_speakers, f, indent=2)
        logger.info("Enrolled authorized speaker '%s' (%s).", name, role)
        return {"status": "success", "message": f"Speaker '{name}' authorized successfully."}

    def remove_authorized_speaker(self, name: str) -> bool:
        """Revoke authorization for a speaker."""
        if name in self.authorized_speakers:
            del self.authorized_speakers[name]
            os.makedirs(self.profile_dir, exist_ok=True)
            with open(self.authorized_profiles_path, "w", encoding="utf-8") as f:
                json.dump(self.authorized_speakers, f, indent=2)
            logger.info("Revoked authorization for speaker '%s'.", name)
            return True
        return False

    def list_authorized_speakers(self) -> List[Dict[str, str]]:
        """List all currently authorized speakers."""
        items = []
        if self.owner_features:
            items.append({"name": "Owner (Boss)", "role": "primary_owner", "is_owner": True})
        for name, data in self.authorized_speakers.items():
            items.append({"name": name, "role": data.get("role", "delegate"), "is_owner": False})
        return items

    def is_enrolled(self) -> bool:
        return self.owner_features is not None

    def detect_voice_activity(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
        energy_threshold: float = 0.012,
    ) -> Dict[str, Any]:
        """
        Lightweight Voice Activity Detection (VAD) computing RMS energy,
        dominant frequency peak, and binary speech activity flag.
        """
        if len(audio_samples) == 0:
            return {"is_speech": False, "rms": 0.0, "dominant_hz": 0.0}

        samples = audio_samples.astype(np.float32)
        rms = float(np.sqrt(np.mean(samples ** 2)))
        
        # Dominant frequency estimation via FFT
        fft_vals = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
        peak_idx = int(np.argmax(fft_vals)) if len(fft_vals) > 0 else 0
        dominant_hz = float(freqs[peak_idx]) if peak_idx < len(freqs) else 0.0

        is_speech = bool(rms > energy_threshold and 75.0 <= dominant_hz <= 3800.0)
        return {
            "is_speech": is_speech,
            "rms": round(rms, 4),
            "dominant_hz": round(dominant_hz, 1),
        }

    def verify_speaker(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
        threshold: float = 2.6,
    ) -> Dict[str, Any]:
        """
        Evaluates an audio snippet to determine if the speaker is:
        1. Owner (Boss) - Full Access
        2. Authorized Delegate - Permitted Access
        3. Unauthorized Guest - Directive Execution Blocked
        """
        if len(audio_samples) == 0:
            return {
                "speaker": "Unknown",
                "is_owner": False,
                "is_authorized": False,
                "confidence": 0.0,
                "action": "deny",
                "reason": "Empty audio",
            }

        feat = _extract_voice_features(audio_samples, sample_rate)

        # Compare against Owner and all Authorized delegates to find the closest match
        candidates = []
        if self.owner_features is not None:
            owner_dist = _euclidean_distance(feat, self.owner_features)
            candidates.append({
                "speaker": "Owner (Boss)",
                "is_owner": True,
                "is_authorized": True,
                "dist": owner_dist,
            })

        for name, entry in self.authorized_speakers.items():
            ref_feat = entry.get("features", [])
            if ref_feat:
                dist = _euclidean_distance(feat, ref_feat)
                candidates.append({
                    "speaker": f"Authorized ({name})",
                    "is_owner": False,
                    "is_authorized": True,
                    "dist": dist,
                })

        if candidates:
            best = min(candidates, key=lambda c: c["dist"])
            if best["dist"] < threshold:
                conf = max(0.6, min(0.99, 1.0 - (best["dist"] / 5.0)))
                return {
                    "speaker": best["speaker"],
                    "is_owner": best["is_owner"],
                    "is_authorized": True,
                    "confidence": round(conf, 2),
                    "action": "allow",
                    "reason": f"Voice matched {best['speaker']} profile",
                }

        # If no profile enrolled yet, default to allowing with warning
        if self.owner_features is None and not self.authorized_speakers:
            return {
                "speaker": "Primary User (Default)",
                "is_owner": True,
                "is_authorized": True,
                "confidence": 0.80,
                "action": "allow",
                "reason": "No voice profiles enrolled yet; defaulting to open mode",
            }

        # Unauthorized third party
        return {
            "speaker": "Unauthorized Guest",
            "is_owner": False,
            "is_authorized": False,
            "confidence": 0.90,
            "action": "deny",
            "reason": "Speaker voice does not match Owner or any Authorized Delegate",
        }

    def diarize_audio(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
        segment_duration_sec: float = 3.0,
    ) -> List[Dict[str, Any]]:
        """
        Segments audio into speaker turns and classifies each as Owner, Authorized, or Guest.
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

            ver = self.verify_speaker(chunk, sample_rate)

            segments.append({
                "segment_index": i,
                "start_time_sec": round(start_sample / sample_rate, 2),
                "end_time_sec": round(end_sample / sample_rate, 2),
                "speaker": ver["speaker"],
                "is_authorized": ver["is_authorized"],
                "confidence": ver["confidence"],
            })

        return segments
