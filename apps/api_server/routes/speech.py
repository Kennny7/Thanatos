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
    """Check if owner voice profile is enrolled."""
    return {
        "is_enrolled": speech_service.speaker_id.is_enrolled(),
        "profile_path": speech_service.speaker_id.owner_profile_path,
    }
