# Vision Microservice

## Overview
The `vision` microservice provides camera-based visual verification and biometric authentication, complementing voice speaker authorization for multimodal security.

## Key Modules
- `speaker_vision.py`: Visual speaker confirmation and presence detection.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To test module importing and class instantiation:
```bash
uv run python -c "from services.vision.speaker_vision import SpeakerVision; sv = SpeakerVision(); print('Vision service operational')"
```
