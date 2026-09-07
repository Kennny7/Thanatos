# Thanatos/apps/api_server/routes/speech.py

import logging
import os
import tempfile
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from services.speech.speech_service import speech_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/speech", tags=["Speech & Voice"])


class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    diarize: bool = Form(True),
) -> Dict[str, Any]:
    """
    Transcribe uploaded audio with AEC filtering and multi-speaker diarization.
    """
    suffix = os.path.splitext(file.filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        if diarize:
            res = speech_service.process_voice_input(tmp_path)
        else:
            text = speech_service.transcribe(tmp_path)
            res = {"transcript": text, "primary_speaker": "User", "segments": []}
        return res
    except Exception as e:
        logger.exception("Transcription endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@router.post("/synthesize")
async def synthesize_speech(payload: SynthesizeRequest):
    """Convert text to MP3 audio stream."""
    try:
        mp3_bytes = await speech_service.synthesize(payload.text, voice=payload.voice)
        return Response(content=mp3_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.exception("TTS synthesis error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll-voice")
async def enroll_owner_voice(file: UploadFile = File(...)):
    """Enroll the primary user's voice profile for speaker diarization."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        result = speech_service.enroll_voice(tmp_path)
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/voice-status")
async def get_voice_status() -> Dict[str, Any]:
    """Check if owner voice profile is enrolled and retrieve authorized delegates count."""
    return {
        "is_enrolled": speech_service.speaker_id.is_enrolled(),
        "profile_path": speech_service.speaker_id.owner_profile_path,
        "authorized_speakers": speech_service.speaker_id.list_authorized_speakers(),
    }


@router.post("/verify-speaker")
async def verify_speaker_route(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Verify if the audio speaker is the Owner, an Authorized Delegate, or Unauthorized Guest."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        return speech_service.verify_audio(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/enroll-authorized")
async def enroll_authorized_route(
    name: str = Form(...),
    role: str = Form("delegate"),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Enroll an authorized delegate's voice profile."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        return speech_service.enroll_authorized(name=name, audio_file_path=tmp_path, role=role)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/authorized-speakers")
async def get_authorized_speakers() -> Dict[str, Any]:
    """List all enrolled and authorized speakers."""
    return {
        "speakers": speech_service.speaker_id.list_authorized_speakers(),
    }


@router.delete("/authorized-speakers/{name}")
async def revoke_authorized_speaker(name: str) -> Dict[str, Any]:
    """Revoke authorization for a speaker."""
    success = speech_service.speaker_id.remove_authorized_speaker(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Speaker '{name}' not found in authorized list.")
    return {"status": "success", "message": f"Authorization for '{name}' revoked."}


class FrameAnalysisRequest(BaseModel):
    frame_b64: str


@router.post("/analyze-frame")
async def analyze_camera_frame(payload: FrameAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze real-time webcam frame:
    - Face detection & boss identification
    - Lip movement / mouth activity tracking
    """
    from services.vision.speaker_vision import speaker_vision
    try:
        result = speaker_vision.analyze_frame(payload.frame_b64)
        return result
    except Exception as e:
        logger.warning("Frame analysis error: %s", e)
        return {
            "face_detected": False,
            "is_boss": False,
            "mouth_moving": False,
            "status": "ERROR",
            "error": str(e),
        }


@router.post("/enroll-boss-face")
async def enroll_boss_face_route(payload: FrameAnalysisRequest) -> Dict[str, Any]:
    """Enroll boss face biometric signature from camera frame."""
    from services.vision.speaker_vision import speaker_vision
    return speaker_vision.enroll_boss_face(payload.frame_b64)

