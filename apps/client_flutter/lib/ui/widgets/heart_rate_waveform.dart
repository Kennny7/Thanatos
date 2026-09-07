// Thanatos/apps/client_flutter/lib/ui/widgets/heart_rate_waveform.dart

import 'dart:math';
import 'package:flutter/material.dart';

enum WaveformMode {
  idle,
  userSpeaking,
  aiSpeaking,
}

class HeartRateWaveform extends StatefulWidget {
  final WaveformMode mode;
  final Color accentColor;
  final double height;

  const HeartRateWaveform({
    super.key,
    this.mode = WaveformMode.idle,
    this.accentColor = const Color(0xFF00E5FF),
    this.height = 140,
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
      duration: const Duration(milliseconds: 2400),
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
          painter: _ECGWaveformPainter(
            progress: _controller.value,
            mode: widget.mode,
            accentColor: widget.accentColor,
          ),
        );
      },
    );
  }
}

class _ECGWaveformPainter extends CustomPainter {
  final double progress;
  final WaveformMode mode;
  final Color accentColor;

  _ECGWaveformPainter({
    required this.progress,
    required this.mode,
    required this.accentColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.width;
    final height = size.height;
    final midY = height / 2.0;

    // 1. Draw subtle background medical grid lines
    final gridPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.08)
      ..strokeWidth = 0.8;

    const gridStep = 18.0;
    for (double x = 0; x < width; x += gridStep) {
      canvas.drawLine(Offset(x, 0), Offset(x, height), gridPaint);
    }
    for (double y = 0; y < height; y += gridStep) {
      canvas.drawLine(Offset(0, y), Offset(width, y), gridPaint);
    }

    // 2. Compute dynamic heart rate ECG / sound frequency path
    final path = Path();
    final glowPath = Path();

    // Pulse parameters based on mode
    final double amplitudeScale = mode == WaveformMode.userSpeaking
        ? 1.4
        : (mode == WaveformMode.aiSpeaking ? 1.1 : 0.65);

    final double phase = progress * 2.0 * pi;
    bool started = false;

    for (double x = 0; x <= width; x += 2.0) {
      final normX = x / width;
      // Repeating heartbeat cycle across screen (3 cycles across width)
      final cyclePos = (normX * 3.2 - progress * 1.5) % 1.0;
      final cycle = cyclePos < 0 ? cyclePos + 1.0 : cyclePos;

      double dy = 0.0;

      if (cycle >= 0.18 && cycle < 0.24) {
        // P-Wave (mild atrial depolarization bump)
        final pNorm = (cycle - 0.18) / 0.06;
        dy = -sin(pNorm * pi) * 10.0 * amplitudeScale;
      } else if (cycle >= 0.28 && cycle < 0.31) {
        // Q-Wave (small initial downward dip)
        final qNorm = (cycle - 0.28) / 0.03;
        dy = sin(qNorm * pi) * 8.0 * amplitudeScale;
      } else if (cycle >= 0.31 && cycle < 0.36) {
        // R-Peak (high-amplitude ventricular spike)
        final rNorm = (cycle - 0.31) / 0.05;
        dy = -sin(rNorm * pi) * (height * 0.44) * amplitudeScale;
      } else if (cycle >= 0.36 && cycle < 0.40) {
        // S-Wave (sharp rebound dip)
        final sNorm = (cycle - 0.36) / 0.04;
        dy = sin(sNorm * pi) * 18.0 * amplitudeScale;
      } else if (cycle >= 0.48 && cycle < 0.60) {
        // T-Wave (ventricular repolarization wave)
        final tNorm = (cycle - 0.48) / 0.12;
        dy = -sin(tNorm * pi) * 16.0 * amplitudeScale;
      } else {
        // Sound frequency micro-ripple baseline
        final rippleFreq = mode == WaveformMode.userSpeaking ? 22.0 : 12.0;
        final rippleAmp = mode == WaveformMode.userSpeaking ? 3.5 : 1.2;
        dy = sin(normX * rippleFreq + phase) * rippleAmp;
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

    // 3. Draw Outer Neon Glow
    final glowPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.35)
      ..strokeWidth = 4.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4.0);
    canvas.drawPath(glowPath, glowPaint);

    // 4. Draw Crisp Laser Trace Line
    final linePaint = Paint()
      ..color = accentColor
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(path, linePaint);

    // 5. Draw Sweeping Pulse Laser Dot
    final scanX = (progress * width) % width;
    final scanPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.solid, 2.0);
    canvas.drawCircle(Offset(scanX, midY), 3.5, scanPaint);

    final auraPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.6)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(scanX, midY), 6.5, auraPaint);
  }

  @override
  bool shouldRepaint(_ECGWaveformPainter oldDelegate) => true;
}
