// Thanatos/apps/client_flutter/lib/ui/widgets/tactical_voice_deck.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'heart_rate_waveform.dart';
import 'holo_panel.dart';
import '../../models/message_model.dart';
import '../../state/chat_provider.dart';
import '../../services/speech_service.dart';

class TacticalVoiceDeck extends ConsumerStatefulWidget {
  final Color primaryAccent;
  final Color surfaceColor;
  final VoidCallback onSwitchToTextMode;

  const TacticalVoiceDeck({
    super.key,
    required this.primaryAccent,
    required this.surfaceColor,
    required this.onSwitchToTextMode,
  });

  @override
  ConsumerState<TacticalVoiceDeck> createState() => _TacticalVoiceDeckState();
}

class _TacticalVoiceDeckState extends ConsumerState<TacticalVoiceDeck> {
  final _speechService = SpeechService();
  StreamSubscription<String>? _textSub;
  StreamSubscription<SpeechStatus>? _statusSub;
  StreamSubscription<double>? _soundLevelSub;
  bool _isListening = false;
  bool _cameraActive = false;
  bool _showTerminalLogs = true;
  double _currentSoundLevel = 0.0;
  String _speakerTag = "Owner (Boss)";
  bool _isAuthorized = true;
  String _vadStatus = "STANDBY // MONITORING";
  String _liveTranscript = "Waiting for acoustic transmission...";
  String _visionStatus = "CAMERA HUD OFFLINE";
  String _mouthStatus = "STATIC";

  Timer? _simulatedVadTimer;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    final available = await _speechService.initialize();
    if (available && mounted) {
      _textSub = _speechService.onText.listen((text) {
        if (!mounted) return;
        setState(() {
          _liveTranscript = text;
          _vadStatus = "SPEECH DETECTED // 120 Hz";
        });
        _sendSpokenDirective(text);
      });
      _statusSub = _speechService.onStatus.listen((status) {
        if (!mounted) return;
        if (status == SpeechStatus.listening) {
          setState(() {
            _isListening = true;
            _vadStatus = "VAD ACTIVE: LISTENING...";
          });
        } else {
          setState(() {
            _isListening = false;
            _currentSoundLevel = 0.0;
            _vadStatus = "STANDBY // READY";
          });
        }
      });
      _soundLevelSub = _speechService.onSoundLevelChange.listen((level) {
        if (!mounted) return;
        setState(() {
          _currentSoundLevel = level;
          if (level > 1.5) {
            _vadStatus = "ACOUSTIC SIGNAL DETECTED";
          }
        });
      });
    }
  }

  @override
  void dispose() {
    _simulatedVadTimer?.cancel();
    _textSub?.cancel();
    _statusSub?.cancel();
    _soundLevelSub?.cancel();
    super.dispose();
  }

  void _toggleMic() async {
    if (_isListening) {
      await _speechService.stopListening();
      setState(() {
        _isListening = false;
        _currentSoundLevel = 0.0;
        _vadStatus = "STANDBY // READY";
      });
      _simulatedVadTimer?.cancel();
    } else {
      setState(() {
        _isListening = true;
        _vadStatus = "VAD ACTIVE: LISTENING...";
        _liveTranscript = "Listening to acoustic input...";
      });
      await _speechService.startListening();

      // Fallback timer if speech recognition is running in simulation
      _simulatedVadTimer?.cancel();
      _simulatedVadTimer = Timer(const Duration(milliseconds: 2500), () {
        if (!mounted) return;
        setState(() {
          _vadStatus = "SPEECH DETECTED // 120 Hz";
          _speakerTag = "Owner (Boss)";
          _isAuthorized = true;
        });
      });
    }
  }

  void _sendSpokenDirective(String text) {
    if (text.trim().isEmpty) return;
    ref.read(chatProvider.notifier).sendTextMessage(
          text,
          speakerTag: _speakerTag,
        );
    setState(() {
      _liveTranscript = "Directive dispatched to neural core.";
      _isListening = false;
      _vadStatus = "PROCESSING DIRECTIVE...";
    });
  }

  void _toggleCamera() {
    setState(() {
      _cameraActive = !_cameraActive;
      if (_cameraActive) {
        _visionStatus = "TRACKING: FACE LOCKED [BOSS]";
        _mouthStatus = "MOUTH: ACTIVE (SPEECH SYNC)";
      } else {
        _visionStatus = "CAMERA HUD OFFLINE";
        _mouthStatus = "STATIC";
      }
    });
  }

  WaveformMode _getWaveformMode(bool isAiResponding) {
    if (isAiResponding) return WaveformMode.aiSpeaking;
    if (_isListening) return WaveformMode.userSpeaking;
    return WaveformMode.idle;
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatProvider);
    final waveformMode = _getWaveformMode(state.isAiResponding);

    final authColor = _isAuthorized
        ? const Color(0xFF00E676)
        : const Color(0xFFFF1744);

    return Expanded(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          children: [
            // 1. Tactical Status Strip
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: widget.primaryAccent.withValues(alpha: 0.12),
                    border: Border.all(color: widget.primaryAccent.withValues(alpha: 0.4)),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _isListening ? Colors.redAccent : widget.primaryAccent,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _vadStatus,
                        style: TextStyle(
                          color: widget.primaryAccent,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'Courier',
                          letterSpacing: 1.1,
                        ),
                      ),
                    ],
                  ),
                ),
                // Speaker Biometrics Tag
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: authColor.withValues(alpha: 0.15),
                    border: Border.all(color: authColor.withValues(alpha: 0.6)),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Text(
                    'SPEAKER: $_speakerTag [${_isAuthorized ? "AUTHORIZED" : "BLOCKED"}]',
                    style: TextStyle(
                      color: authColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Courier',
                      letterSpacing: 1.0,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),

            // 2. Frequency / Acoustic Waveform Visualizer
            HoloPanel(
              accentColor: widget.primaryAccent,
              surfaceColor: widget.surfaceColor.withValues(alpha: 0.7),
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              chamferSize: 10,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'ACOUSTIC SPECTRUM // FREQUENCY ANALYZER',
                          style: TextStyle(
                            color: widget.primaryAccent.withValues(alpha: 0.9),
                            fontSize: 10.5,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.4,
                            fontFamily: 'Courier',
                          ),
                        ),
                        Text(
                          _isListening
                              ? '${(_currentSoundLevel * 10).toInt()} dB • 1.2 kHz'
                              : 'STANDBY // FLATLINE',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.6),
                            fontSize: 10,
                            fontFamily: 'Courier',
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  HeartRateWaveform(
                    mode: waveformMode,
                    accentColor: widget.primaryAccent,
                    height: 150,
                    soundLevel: _currentSoundLevel,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 3. Optional Camera Viewfinder HUD
            if (_cameraActive)
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                child: HoloPanel(
                  accentColor: const Color(0xFF00E676),
                  surfaceColor: Colors.black.withValues(alpha: 0.8),
                  padding: const EdgeInsets.all(12),
                  chamferSize: 8,
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'OPTICAL BIOMETRIC TRACKER // CAMERA HUD',
                            style: TextStyle(
                              color: Color(0xFF00E676),
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.2,
                              fontFamily: 'Courier',
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, color: Colors.white54, size: 16),
                            onPressed: _toggleCamera,
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Viewfinder Simulator Frame
                      Container(
                        height: 120,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: const Color(0xFF080D14),
                          border: Border.all(color: const Color(0xFF00E676).withValues(alpha: 0.3)),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            // Face Bounding Box
                            Container(
                              width: 80,
                              height: 90,
                              decoration: BoxDecoration(
                                border: Border.all(color: const Color(0xFF00E676), width: 1.5),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Align(
                                alignment: Alignment.bottomCenter,
                                child: Container(
                                  width: 48,
                                  height: 18,
                                  margin: const EdgeInsets.only(bottom: 8),
                                  decoration: BoxDecoration(
                                    border: Border.all(
                                      color: _mouthStatus.contains("ACTIVE")
                                          ? Colors.cyanAccent
                                          : Colors.white24,
                                      width: 1.2,
                                    ),
                                  ),
                                  child: Center(
                                    child: Text(
                                      'MOUTH',
                                      style: TextStyle(
                                        color: _mouthStatus.contains("ACTIVE")
                                            ? Colors.cyanAccent
                                            : Colors.white38,
                                        fontSize: 7,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            // Optical Crosshairs
                            Positioned(
                              top: 8,
                              left: 12,
                              child: Text(
                                _visionStatus,
                                style: const TextStyle(
                                  color: Color(0xFF00E676),
                                  fontSize: 9.5,
                                  fontFamily: 'Courier',
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Positioned(
                              bottom: 8,
                              right: 12,
                              child: Text(
                                _mouthStatus,
                                style: const TextStyle(
                                  color: Colors.cyanAccent,
                                  fontSize: 9.5,
                                  fontFamily: 'Courier',
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            // 4. Closable Mini Terminal Window: Live Log Stream
            if (_showTerminalLogs)
              Container(
                margin: const EdgeInsets.only(bottom: 20),
                child: HoloPanel(
                  accentColor: widget.primaryAccent.withValues(alpha: 0.6),
                  surfaceColor: const Color(0xFF040810).withValues(alpha: 0.95),
                  padding: const EdgeInsets.all(12),
                  chamferSize: 8,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  color: Color(0xFF00E676),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'MINI TERMINAL // LIVE DIALOGUE LOG',
                                style: TextStyle(
                                  color: widget.primaryAccent,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1.2,
                                  fontFamily: 'Courier',
                                ),
                              ),
                            ],
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, color: Colors.white54, size: 16),
                            tooltip: 'Close Terminal Window',
                            onPressed: () => setState(() => _showTerminalLogs = false),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.6),
                          border: Border.all(color: Colors.white10),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '> OPERATOR [SPEECH IN]:',
                              style: TextStyle(
                                color: widget.primaryAccent.withValues(alpha: 0.8),
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'Courier',
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              _liveTranscript,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12.5,
                                fontFamily: 'Courier',
                                height: 1.35,
                              ),
                            ),
                            if (state.messages.isNotEmpty && state.messages.last.sender == MessageSender.assistant) ...[
                              const Divider(color: Colors.white12, height: 16),
                              Text(
                                '> CORE [SYNTHESIS OUT]:',
                                style: const TextStyle(
                                  color: Color(0xFF00E676),
                                  fontSize: 9.5,
                                  fontWeight: FontWeight.bold,
                                  fontFamily: 'Courier',
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                state.messages.last.content,
                                maxLines: 5,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: Colors.white.withValues(alpha: 0.85),
                                  fontSize: 12,
                                  fontFamily: 'Courier',
                                  height: 1.35,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 12),

            // 5. Voice Command Deck HUD Controls
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Terminal Logs Toggle
                IconButton.filledTonal(
                  icon: Icon(
                    _showTerminalLogs ? Icons.terminal : Icons.terminal_outlined,
                    color: _showTerminalLogs ? widget.primaryAccent : Colors.white60,
                  ),
                  tooltip: _showTerminalLogs ? 'Hide Live Terminal Log' : 'Show Live Terminal Log',
                  onPressed: () => setState(() => _showTerminalLogs = !_showTerminalLogs),
                  style: IconButton.styleFrom(
                    backgroundColor: widget.surfaceColor,
                    side: BorderSide(
                      color: _showTerminalLogs ? widget.primaryAccent : Colors.white24,
                    ),
                  ),
                ),
                const SizedBox(width: 14),

                // Camera Toggle
                IconButton.filledTonal(
                  icon: Icon(
                    _cameraActive ? Icons.videocam : Icons.videocam_off,
                    color: _cameraActive ? const Color(0xFF00E676) : Colors.white60,
                  ),
                  tooltip: 'Toggle Optical Facial & Lip Tracker',
                  onPressed: _toggleCamera,
                  style: IconButton.styleFrom(
                    backgroundColor: widget.surfaceColor,
                    side: BorderSide(
                      color: _cameraActive ? const Color(0xFF00E676) : Colors.white24,
                    ),
                  ),
                ),
                const SizedBox(width: 20),

                // Main Tactile Voice Push-to-Talk Button
                GestureDetector(
                  onTap: _toggleMic,
                  child: Container(
                    width: 76,
                    height: 76,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _isListening
                          ? Colors.redAccent.withValues(alpha: 0.25)
                          : widget.primaryAccent.withValues(alpha: 0.15),
                      border: Border.all(
                        color: _isListening ? Colors.redAccent : widget.primaryAccent,
                        width: 2.2,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: (_isListening ? Colors.redAccent : widget.primaryAccent)
                              .withValues(alpha: 0.5),
                          blurRadius: 18,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Center(
                      child: Icon(
                        _isListening ? Icons.graphic_eq : Icons.mic,
                        color: _isListening ? Colors.redAccent : widget.primaryAccent,
                        size: 36,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 20),

                // Switch back to Text Mode button
                IconButton.filledTonal(
                  icon: const Icon(Icons.keyboard, color: Colors.white70),
                  tooltip: 'Switch to Text Terminal Mode',
                  onPressed: widget.onSwitchToTextMode,
                  style: IconButton.styleFrom(
                    backgroundColor: widget.surfaceColor,
                    side: const BorderSide(color: Colors.white24),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _isListening ? 'TAP TO COMPLETE VOICE TRANSMISSION' : 'TAP MICROPHONE TO ENGAGE VOICE TRANSMISSION',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.5),
                fontSize: 9.5,
                fontFamily: 'Courier',
                letterSpacing: 1.1,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
