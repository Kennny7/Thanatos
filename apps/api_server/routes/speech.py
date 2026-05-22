"""
Placeholder REST endpoint for speech-to-text and text-to-speech.
Real implementation would call the services/speech/ module.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/speech", tags=["speech"])


class STTRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio bytes")


class STTResponse(BaseModel):
    text: str


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesise")
    voice: str = Field(default="default", description="Voice profile name")


class TTSResponse(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded WAV data")


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(request: STTRequest) -> STTResponse:
    """Mock STT: just echoes back a placeholder transcript."""
    # Real logic would decode audio and run speech recognition
    return STTResponse(text="[mock transcript]")


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest) -> TTSResponse:
    """Mock TTS: returns a dummy base64 string."""
    # Real logic would call TTS engine and return audio
    return TTSResponse(audio_data="UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=")