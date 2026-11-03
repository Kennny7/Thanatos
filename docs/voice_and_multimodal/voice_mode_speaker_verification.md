# Voice Mode, Speaker Verification, and Computer Vision System

This document describes the design, implementation, and operating principles of Thanatos Voice Mode, acoustic Voice Activity Detection (VAD), speaker biometric diarization and authorization, and the optional real-time camera face and mouth tracking subsystem.

---

## Table of Contents

- [1. System Architecture](#1-system-architecture)
- [2. Text Mode vs Voice Mode Separation](#2-text-mode-vs-voice-mode-separation)
- [3. Acoustic Frequency and Heart Rate Waveform Visualizer](#3-acoustic-frequency-and-heart-rate-waveform-visualizer)
- [4. Voice Activity Detection (VAD) Engine](#4-voice-activity-detection-vad-engine)
- [5. Speaker Diarization and Biometric Authorization](#5-speaker-diarization-and-biometric-authorization)
- [6. Multi-Speaker Authorization Model](#6-multi-speaker-authorization-model)
- [7. Optional Real-Time Computer Vision Tracking](#7-optional-real-time-computer-vision-tracking)
- [8. REST and WebSocket API Reference](#8-rest-and-websocket-api-reference)
- [9. Setup and Configuration Guide](#9-setup-and-configuration-guide)

---

## 1. System Architecture

Thanatos provides two distinct interaction modalities:
1. Text Terminal Mode: Conventional conversation stream with holographic logs and keyboard input.
2. Tactical Voice Mode: Full-duplex voice intelligence interface featuring a real-time electrocardiogram (ECG) sound frequency wave, continuous Voice Activity Detection (VAD), biometric speaker identification, and optional visual face and lip-movement verification.

```
+-----------------------------------------------------------------------+
|                            User Interface                             |
|       [Text Mode Viewport]         |       [Tactical Voice Deck]      |
|  - Holographic Chat Stream         |  - ECG Frequency Waveform Line   |
|  - Command Deck Input              |  - Live VAD Status Monitor       |
|                                    |  - Speaker Identification Badge  |
|                                    |  - Optional Camera Viewfinder    |
+------------------------------------+----------------------------------+
                                     |
                                     v
+-----------------------------------------------------------------------+
|                    Audio & Speech Intelligence Layer                  |
|  - Acoustic Echo Cancellation (AECProcessor, Spectral Gating)         |
|  - Voice Activity Detection (Energy & Dominant Frequency Tracker)     |
|  - Speaker Biometrics (SpeakerIdentifier: Owner vs Authorized vs Guest)|
|  - Speech-to-Text Engine (Faster-Whisper ASR)                         |
|  - Text-to-Speech Engine (Edge-TTS Neural Synthesis)                  |
+-----------------------------------------------------------------------+
                                     |
                                     v
+-----------------------------------------------------------------------+
|                     Optional Vision Tracking Layer                    |
|  - Face Detection & Verification (SpeakerVisionTracker)               |
|  - Lip Movement & Mouth Aspect Ratio (MAR) Optical Variance           |
|  - Audio-Visual Cross-Modal Verification                              |
+-----------------------------------------------------------------------+
                                     |
                                     v
+-----------------------------------------------------------------------+
|                     Agent Coordination & Execution                    |
|  - Authorization Guard: Block directives from unauthorized guests     |
|  - Autonomous Multi-Agent Coordinator & ReAct Loop                    |
|  - Real-Time Live Web and News Search via DuckDuckGo and Google News  |
+-----------------------------------------------------------------------+
```

---

## 2. Text Mode vs Voice Mode Separation

Thanatos segregates textual messaging and voice operations into distinct operational modes rather than combining them into a simple push-to-talk button:

### Text Mode
- Optimized for code generation, multi-step agent graphs, and dense markdown responses.
- Displays full conversation history via the holographic stream viewport.
- Command Deck input field allows keyboard shortcuts and slash commands.

### Voice Mode
- Optimized for hands-free command and audio dialogue.
- Displays an animated frequency and cardiogram waveform line that reacts dynamically to ambient audio and speech.
- Displays real-time acoustic transcription and synthesized audio playback.
- Enforces biometric speaker validation to restrict unauthorized voices from issuing system directives.

The user can toggle between Text Mode and Voice Mode at any time using the mode selector in the top tactical HUD header bar.

---

## 3. Acoustic Frequency and Heart Rate Waveform Visualizer

The voice deck features a custom hardware-accelerated canvas visualizer (`HeartRateWaveform`) that renders a stylized medical cardiogram / oscilloscope trace:

1. Baseline Grid: Subtle tactical grid background representing frequency calibration bins.
2. Cardiac Electrical Cycle (P-Q-R-S-T):
   - P-Wave: Depolarization baseline shift.
   - Q-R-S Complex: Sharp vertical pulse spike representing sound amplitude and heart rate burst.
   - T-Wave: Repolarization wave returning to baseline.
3. Frequency Micro-Ripples: Superimposed high-frequency sine harmonics simulating acoustic pitch variations.
4. Operational States:
   - Standby Mode: Low-amplitude, steady rhythm representing ambient room monitoring.
   - User Speaking Mode: High-amplitude deflection with dynamic frequency flutter matching user vocal output.
   - AI Speaking Mode: Harmonic resonance waves indicating neural TTS vocal transmission.

---

## 4. Voice Activity Detection (VAD) Engine

Located in `services/speech/speaker_id.py`, the VAD engine operates on incoming audio buffers:

### Mathematical Principles
1. Root Mean Square (RMS) Energy:
   $$RMS = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x[i]^2}$$
   Measures instantaneous acoustic energy against a calibrated floor (default threshold: 0.012).

2. Fast Fourier Transform (FFT) Spectral Analysis:
   $$X[k] = \sum_{n=0}^{N-1} x[n] e^{-j 2\pi k n / N}$$
   Identifies the dominant spectral frequency $f_{peak}$. Speech is validated only if $f_{peak}$ resides within human vocal fundamental and formant ranges (75 Hz to 3800 Hz).

3. Binary Activity State:
   An audio frame is classified as active speech if:
   $$Active = (RMS > 0.012) \land (75 \le f_{peak} \le 3800)$$

---

## 5. Speaker Diarization and Biometric Authorization

To prevent unauthorized individuals or background television audio from executing commands, Thanatos implements acoustic speaker diarization and voice verification.

### Feature Extraction
Each audio segment is transformed into a 16-dimensional acoustic fingerprint:
1. Zero-Crossing Rate (ZCR): Indicates noisiness and high-frequency spectral density.
2. Root Mean Square (RMS) Energy: Amplitude envelope.
3. Spectral Centroid: Center of mass of the frequency spectrum normalized to 4 kHz.
4. 13 Sub-Band Log Energies: Discrete logarithmic energy allocations across sub-bands (similar to MFCC filter banks).

### Distance Calculation
Biometric comparison utilizes Euclidean distance across normalized feature vectors:
$$D(v_1, v_2) = \sqrt{\sum_{i=1}^{16} (v_{1}[i] - v_{2}[i])^2}$$

---

## 6. Multi-Speaker Authorization Model

Thanatos recognizes three speaker tiers:

1. Primary Owner (Boss):
   - Highest authority level.
   - Voice profile enrolled in `profiles/speech/owner_voice.json`.
   - Has unrestricted command execution privileges.

2. Authorized Delegates:
   - Approved team members, family, or operators.
   - Profiles stored in `profiles/speech/authorized_speakers.json`.
   - Permitted to issue conversational and system commands.

3. Unauthorized Guests:
   - Third-party speakers whose acoustic distance exceeds threshold (2.6).
   - Directives are flagged with `is_authorized: false`.
   - The agent loop intercepts unauthorized messages and issues an access restriction notification without executing the prompt.

---

## 7. Optional Real-Time Computer Vision Tracking

Located in `services/vision/speaker_vision.py`, the visual subsystem provides cross-modal verification using a webcam feed:

### Capabilities
1. Facial Detection and Identification:
   - Utilizes Haar feature cascades or OpenCV face detection to track the primary user.
   - Compares the facial crop against the enrolled boss profile (`boss_face.json`).

2. Lip and Mouth Movement Tracking (Mouth Aspect Ratio & Optical Variance):
   - Isolates the lower third of the face bounding box (mouth region).
   - Computes inter-frame absolute pixel difference:
     $$\Delta_{mouth} = \frac{1}{W \times H} \sum |I_{t}(x, y) - I_{t-1}(x, y)|$$
   - When $\Delta_{mouth} > 3.8$, the mouth is classified as actively speaking.

3. Cross-Modal Confirmation Matrix:
   - Boss Face Visible + Mouth Moving: Confirmed boss speech. Directive processed.
   - Boss Face Visible + Mouth Static: Sound originated off-camera or from speakerphone. Security warning logged.
   - Unknown Face + Mouth Moving: Guest speaker detected visually.
   - No Face Visible: Audio-only fallback mode.

---

## 8. REST and WebSocket API Reference

### Speech Endpoints

#### POST /speech/transcribe
Transcribes uploaded WAV/MP3 audio with optional multi-speaker diarization.
- Form Data:
  - `file`: Audio binary.
  - `diarize`: Boolean (default `true`).
- Response:
  ```json
  {
    "transcript": "tell me some trending news",
    "primary_speaker": "Owner (Boss)",
    "is_authorized": true,
    "confidence": 0.94,
    "has_other_speakers": false,
    "segments": []
  }
  ```

#### POST /speech/verify-speaker
Verifies whether an uploaded audio sample matches an authorized speaker.
- Form Data:
  - `file`: WAV audio sample.
- Response:
  ```json
  {
    "speaker": "Owner (Boss)",
    "is_owner": true,
    "is_authorized": true,
    "confidence": 0.95,
    "action": "allow",
    "reason": "Voice matched Owner (Boss) profile"
  }
  ```

#### POST /speech/enroll-authorized
Enrolls a secondary authorized speaker.
- Form Data:
  - `name`: Speaker identifier (e.g. "Alice").
  - `role`: Role description (e.g. "operator").
  - `file`: WAV audio sample.

#### GET /speech/authorized-speakers
Returns all registered speakers and their authorization roles.

#### DELETE /speech/authorized-speakers/{name}
Revokes authorization for a delegate speaker.

### Vision Endpoints

#### POST /speech/analyze-frame
Submits a base64 camera frame for real-time face and lip-movement analysis.
- JSON Body:
  ```json
  {
    "frame_b64": "data:image/jpeg;base64,..."
  }
  ```
- Response:
  ```json
  {
    "face_detected": true,
    "is_boss": true,
    "mouth_moving": true,
    "status": "VERIFIED_BOSS_SPEAKING",
    "confidence": 0.92,
    "motion_score": 5.4,
    "bounding_box": [120, 80, 200, 220]
  }
  ```

#### POST /speech/enroll-boss-face
Enrolls the primary owner's facial biometric template from a camera frame.

---

## 9. Setup and Configuration Guide

### 1. Python Environment Setup
Activate the virtual environment and install dependencies:
```bash
venv\Scripts\activate
pip install httpx numpy pydantic
```

For optional computer vision tracking:
```bash
pip install opencv-python
```

### 2. Enrolling the Owner (Boss) Voice
To enroll the owner's voice profile:
1. Navigate to Voice Mode in the client UI.
2. Ensure clear microphone input in a quiet environment.
3. Send an enrollment audio sample through the settings panel or POST to `/speech/enroll-voice`.
4. The profile will be saved to `profiles/speech/owner_voice.json`.

### 3. Adding Authorized Delegates
To authorize additional speakers:
```bash
curl -X POST http://localhost:8000/speech/enroll-authorized \
  -F "name=Alice" \
  -F "role=delegate" \
  -F "file=@alice_voice_sample.wav"
```

### 4. Running the System
Start the FastAPI server:
```bash
uvicorn apps.api_server.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the Flutter client:
```bash
cd apps/client_flutter
flutter run -d chrome
```
