// Thanatos/apps/client_flutter/lib/ui/widgets/voice_overlay.dart

import 'dart:math';
import 'package:flutter/material.dart';

class VoiceOverlayDialog extends StatefulWidget {
  final Function(String transcript, String speakerTag) onTranscriptionComplete;

  const VoiceOverlayDialog({super.key, required this.onTranscriptionComplete});

  @override
  State<VoiceOverlayDialog> createState() => _VoiceOverlayDialogState();
}

class _VoiceOverlayDialogState extends State<VoiceOverlayDialog>
    with SingleTickerProviderStateMixin {
  bool isListening = true;
  final String currentSpeaker = "Owner (You)";
  late AnimationController _animController;
  final TextEditingController _voiceInputController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat();
  }

  @override
  void dispose() {
    _animController.dispose();
    _voiceInputController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;

    return Dialog(
      backgroundColor: Colors.transparent,
      elevation: 0,
      insetPadding: const EdgeInsets.all(16),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 420),
        padding: const EdgeInsets.all(24.0),
        decoration: BoxDecoration(
          color: const Color(0xFF030508).withValues(alpha: 0.95),
          border: Border.all(color: accent, width: 1.2),
          borderRadius: BorderRadius.circular(4),
          boxShadow: [
            BoxShadow(color: accent.withValues(alpha: 0.25), blurRadius: 20, spreadRadius: 2),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // HUD Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'ACOUSTIC INTELLIGENCE // HUD',
                  style: TextStyle(
                    color: accent,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.8,
                    fontFamily: 'Courier',
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    border: Border.all(color: accent, width: 0.8),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Text(
                    'AEC: -28dB',
                    style: TextStyle(color: accent, fontSize: 9, fontFamily: 'Courier'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 28),

            // Rotating Gyroscopic Arc Rings Visualizer
            AnimatedBuilder(
              animation: _animController,
              builder: (context, child) {
                return SizedBox(
                  width: 140,
                  height: 140,
                  child: CustomPaint(
                    painter: _GyroscopicRingsPainter(
                      progress: _animController.value,
                      accentColor: accent,
                    ),
                    child: Center(
                      child: Icon(Icons.mic, color: accent, size: 36),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 24),

            // Telemetry Status
            Text(
              isListening ? 'CAPTURE: LISTENING FOR VOICE STREAM...' : 'DECODING ACOUSTIC FRAMES...',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.8),
                fontSize: 11,
                letterSpacing: 1.2,
                fontFamily: 'Courier',
              ),
            ),
            const SizedBox(height: 8),

            // Speaker Diarization Badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                border: Border.all(color: accent.withValues(alpha: 0.3)),
                borderRadius: BorderRadius.circular(2),
              ),
              child: Text(
                'SPEAKER: $currentSpeaker [MATCH: 99.4%]',
                style: TextStyle(color: accent, fontSize: 10, fontFamily: 'Courier'),
              ),
            ),
            const SizedBox(height: 16),

            // Quick Speech Dictation / Direct Edit
            TextField(
              controller: _voiceInputController,
              decoration: InputDecoration(
                hintText: 'Or type vocal command directly...',
                hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3), fontSize: 12, fontFamily: 'Courier'),
                enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: accent.withValues(alpha: 0.3))),
                focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: accent)),
              ),
              style: const TextStyle(color: Colors.white, fontSize: 13, fontFamily: 'Courier'),
            ),
            const SizedBox(height: 24),

            // Tactical Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(
                    '[ABORT]',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontFamily: 'Courier', fontSize: 11),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: accent,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
                  ),
                  onPressed: () {
                    final text = _voiceInputController.text.trim();
                    final query = text.isNotEmpty ? text : "Scan environment and report system status";
                    Navigator.of(context).pop();
                    widget.onTranscriptionComplete(query, currentSpeaker);
                  },
                  child: const Text(
                    'TRANSMIT DIRECTIVE',
                    style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 11, fontFamily: 'Courier'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _GyroscopicRingsPainter extends CustomPainter {
  final double progress;
  final Color accentColor;

  _GyroscopicRingsPainter({required this.progress, required this.accentColor});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final baseRadius = size.width / 2 * 0.85;

    final ringPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.35)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    // Outer rotating segmented ring
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(progress * 2 * pi);
    for (int i = 0; i < 4; i++) {
      final startAngle = i * (pi / 2) + 0.15;
      const sweepAngle = (pi / 2) - 0.3;
      canvas.drawArc(
        Rect.fromCircle(center: Offset.zero, radius: baseRadius),
        startAngle,
        sweepAngle,
        false,
        ringPaint,
      );
    }
    canvas.restore();

    // Inner counter-rotating ring
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(-progress * 3 * pi);
    final innerPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    for (int i = 0; i < 6; i++) {
      final startAngle = i * (pi / 3) + 0.1;
      const sweepAngle = (pi / 3) - 0.2;
      canvas.drawArc(
        Rect.fromCircle(center: Offset.zero, radius: baseRadius * 0.72),
        startAngle,
        sweepAngle,
        false,
        innerPaint,
      );
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(_GyroscopicRingsPainter oldDelegate) =>
      oldDelegate.progress != progress || oldDelegate.accentColor != accentColor;
}
