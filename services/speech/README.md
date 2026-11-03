# Speech Microservice

## Overview
The `speech` microservice handles voice-driven interactions for Thanatos, including real-time speech recognition (STT), speech synthesis (TTS), speaker identification, and acoustic echo cancellation (AEC).

## Key Modules
- `speech_service.py`: High-level voice pipeline coordinator.
- `stt.py`: Speech-to-Text transcriber.
- `tts.py`: Text-to-Speech audio synthesizer.
- `speaker_id.py`: Voice biometric verification and enrollment.
- `aec.py`: Acoustic Echo Cancellation and barge-in suppression.
- `audio_utils.py`: Raw PCM audio encoding, resampling, and format conversions.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run speech and echo cancellation unit tests:
```bash
uv run pytest tests/unit/test_speech_and_aec.py tests/unit/test_speaker_authorization.py
```
