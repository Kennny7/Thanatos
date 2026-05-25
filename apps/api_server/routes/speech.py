# Thanatos/apps/api_server/routes/speech.py

"""
Speech-to-Text and Text-to-Speech endpoints.
Uses the services/speech/ module for real processing.
"""

import base64
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.speech import SpeechService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["speech"])

# ---------- Models (preserved from original) ----------
class STTRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio bytes")


class STTResponse(BaseModel):
    text: str


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesise")
    voice: str = Field(default="default", description="Voice profile name")


class TTSResponse(BaseModel):
    audio_data: str = Field(
        ..., description="Base64 encoded MP3 audio data"
    )

# ---------- Service instance ----------
speech_service = SpeechService(
    stt_model_size="base",          # adjust for your hardware
    stt_device="cpu",
    tts_voice="en-US-AriaNeural",   # default voice
)


# ---------- Endpoints ----------
@router.post("/stt", response_model=STTResponse)
async def speech_to_text(request: STTRequest) -> STTResponse:
    """
    Convert base64-encoded audio to text.
    """
    try:
        # Decode base64 data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

        # Write to a temporary file – faster-whisper needs a file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        try:
            transcript = speech_service.transcribe(temp_path)
        finally:
            # Always clean up the temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return STTResponse(text=transcript)

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.exception("STT processing failed")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during STT")
        raise HTTPException(status_code=500, detail="Internal server error during STT")


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest) -> TTSResponse:
    """
    Convert text to spoken MP3 audio.
    The result is base64-encoded MP3 data.
    """
    try:
        # Determine voice (use provided or fall back to default)
        voice = None if request.voice == "default" else request.voice
        audio_bytes = await speech_service.synthesize(request.text, voice=voice)
        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResponse(audio_data=encoded)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.exception("TTS synthesis failed")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during TTS")
        raise HTTPException(status_code=500, detail="Internal server error during TTS")


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Query(..., min_length=1, description="Text to speak"),
    voice: Optional[str] = Query(None, description="Voice profile override"),
):
    """
    Convenience endpoint that returns raw MP3 audio bytes.
    The Flutter client can play this directly without base64 decoding.
    """
    try:
        audio_bytes = await speech_service.synthesize(text, voice=voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during TTS (synthesize)")
        raise HTTPException(status_code=500, detail="Internal server error during TTS")