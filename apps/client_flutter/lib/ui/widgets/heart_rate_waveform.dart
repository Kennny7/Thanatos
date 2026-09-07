// Thanatos/apps/client_flutter/lib/ui/widgets/heart_rate_waveform.dart

import 'dart:math';
import 'package:flutter/material.dart';

enum WaveformMode {
  idle,
  userSpeaking,
  aiSpeaking,
}

/// Real-time acoustic sound frequency analyzer widget.
/// Renders a laser-traced audio spectrum line that remains flat/calm when idle or silent,
/// modulates dynamically with input decibels/amplitude when mic is active,
/// and animates harmonic frequency bands during AI speech.
class HeartRateWaveform extends StatefulWidget {
  final WaveformMode mode;
  final Color accentColor;
  final double height;
  final double soundLevel; // Decibel level / amplitude (0.0 to ~100.0 or 0.0 to 1.0)

  const HeartRateWaveform({
    super.key,
    this.mode = WaveformMode.idle,
    this.accentColor = const Color(0xFF00E5FF),
    this.height = 140,
    this.soundLevel = 0.0,
  });

  @override
  State<HeartRateWaveform> createState() => _HeartRateWaveformState();
}

class _HeartRateWaveformState extends State<HeartRateWaveform>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: Size(double.infinity, widget.height),
          painter: _AcousticFrequencyPainter(
            progress: _controller.value,
            mode: widget.mode,
            accentColor: widget.accentColor,
            soundLevel: widget.soundLevel,
          ),
        );
      },
    );
  }
}

class _AcousticFrequencyPainter extends CustomPainter {
  final double progress;
  final WaveformMode mode;
  final Color accentColor;
  final double soundLevel;

  _AcousticFrequencyPainter({
    required this.progress,
    required this.mode,
    required this.accentColor,
    required this.soundLevel,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.width;
    final height = size.height;
    final midY = height / 2.0;

    // 1. Draw subtle background tactical grid lines
    final gridPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.07)
      ..strokeWidth = 0.8;

    const gridStep = 18.0;
    for (double x = 0; x < width; x += gridStep) {
      canvas.drawLine(Offset(x, 0), Offset(x, height), gridPaint);
    }
    for (double y = 0; y < height; y += gridStep) {
      canvas.drawLine(Offset(0, y), Offset(width, y), gridPaint);
    }

    // 2. Compute dynamic frequency waveform
    final path = Path();
    final glowPath = Path();

    final isMicActive = mode == WaveformMode.userSpeaking;
    final isAiSpeaking = mode == WaveformMode.aiSpeaking;

    // Normalize sound level: speech_to_text gives roughly 0 to 10 or dB
    final normalizedLevel = isMicActive ? (soundLevel.abs().clamp(0.0, 10.0) / 10.0) : 0.0;
    final double phase = progress * 2.0 * pi;
    bool started = false;

    // Step across waveform with high resolution
    for (double x = 0; x <= width; x += 2.0) {
      final normX = x / width;
      double dy = 0.0;

      if (isMicActive) {
        // True acoustic voice wave: flat if silent, high-frequency spikes when voice input is detected
        if (normalizedLevel > 0.05) {
          final carrier = sin(normX * 36.0 + phase * 4.0);
          final harmonic1 = sin(normX * 72.0 - phase * 2.5) * 0.45;
          final harmonic2 = cos(normX * 18.0 + phase * 1.5) * 0.3;
          final envelope = sin(normX * pi); // taper edges
          final totalAmp = (carrier + harmonic1 + harmonic2) * envelope * (height * 0.38) * normalizedLevel;
          dy = totalAmp;
        } else {
          // Subtle baseline flicker when mic is listening but room is quiet
          dy = sin(normX * 16.0 + phase) * 0.6;
        }
      } else if (isAiSpeaking) {
        // AI vocal synthesis harmonic spectrum
        final primaryWave = sin(normX * 24.0 + phase * 3.0);
        final modulation = sin(normX * 8.0 - phase * 1.5);
        final envelope = sin(normX * pi);
        dy = primaryWave * modulation * envelope * (height * 0.32);
      } else {
        // Idle mode / Mic OFF: Flatline laser level with microscopic calibration ripple
        dy = sin(normX * 4.0 + phase * 0.5) * 0.3;
      }

      final y = (midY + dy).clamp(4.0, height - 4.0);

      if (!started) {
        path.moveTo(x, y);
        glowPath.moveTo(x, y);
        started = true;
      } else {
        path.lineTo(x, y);
        glowPath.lineTo(x, y);
      }
    }

    // 3. Draw outer neon luminescence
    final glowPaint = Paint()
      ..color = (isMicActive && normalizedLevel > 0.1)
          ? Colors.redAccent.withValues(alpha: 0.4)
          : accentColor.withValues(alpha: 0.3)
      ..strokeWidth = 4.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3.5);
    canvas.drawPath(glowPath, glowPaint);

    // 4. Draw crisp laser trace line
    final linePaint = Paint()
      ..color = (isMicActive && normalizedLevel > 0.1) ? Colors.redAccent : accentColor
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(path, linePaint);

    // 5. Draw laser scanning dot
    final scanX = (progress * width) % width;
    final dotColor = (isMicActive && normalizedLevel > 0.1) ? Colors.white : accentColor;
    final scanPaint = Paint()
      ..color = dotColor
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(scanX, midY), 3.0, scanPaint);
  }

  @override
  bool shouldRepaint(_AcousticFrequencyPainter oldDelegate) => true;
}
