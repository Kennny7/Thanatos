// A futuristic animated sphere (like Jarvis/Ultron core) that appears when the AI is generating a response. 
// It uses a CustomPainter with rotating particles and pulsing glow.

import 'dart:math';
import 'package:flutter/material.dart';

class AISpeakingIndicator extends StatefulWidget {
  final double size;
  final Color? glowColor;

  const AISpeakingIndicator({
    super.key,
    this.size = 120,
    this.glowColor,
  });

  @override
  State<AISpeakingIndicator> createState() => _AISpeakingIndicatorState();
}

class _AISpeakingIndicatorState extends State<AISpeakingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulse;
  late Animation<double> _rotation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();

    _pulse = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _rotation = Tween<double>(begin: 0, end: 2 * pi).animate(
      CurvedAnimation(parent: _controller, curve: Curves.linear),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = widget.glowColor ?? theme.colorScheme.primary;
    return AnimatedBuilder(
      animation: _controller,
      builder: (_, child) {
        return SizedBox(
          width: widget.size,
          height: widget.size,
          child: CustomPaint(
            painter: _SpherePainter(
              rotation: _rotation.value,
              pulse: _pulse.value,
              glowColor: color,
            ),
          ),
        );
      },
    );
  }
}

class _SpherePainter extends CustomPainter {
  final double rotation;
  final double pulse;
  final Color glowColor;

  _SpherePainter({
    required this.rotation,
    required this.pulse,
    required this.glowColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 * 0.7;

    // Draw glowing rings
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Outer ring with rotation
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(rotation);
    paint.color = glowColor.withOpacity(0.4);
    canvas.drawCircle(Offset.zero, radius * pulse, paint);
    canvas.drawCircle(Offset.zero, radius * 0.7 * pulse, paint..color = glowColor.withOpacity(0.6));
    canvas.restore();

    // Inner sphere with particles
    final particlePaint = Paint()
      ..style = PaintingStyle.fill
      ..color = glowColor;
    final random = Random(42); // fixed seed for consistent pattern
    final particleCount = 20;
    for (int i = 0; i < particleCount; i++) {
      final angle = random.nextDouble() * 2 * pi + rotation;
      final dist = random.nextDouble() * radius * 0.8 * pulse;
      final dx = center.dx + cos(angle) * dist;
      final dy = center.dy + sin(angle) * dist;
      canvas.drawCircle(Offset(dx, dy), 2.5, particlePaint);
    }

    // Central core
    final corePaint = Paint()
      ..style = PaintingStyle.fill
      ..shader = RadialGradient(
        colors: [glowColor.withOpacity(0.9), glowColor.withOpacity(0.2)],
      ).createShader(Rect.fromCircle(center: center, radius: radius * 0.3));
    canvas.drawCircle(center, radius * 0.3 * pulse, corePaint);
  }

  @override
  bool shouldRepaint(_SpherePainter oldDelegate) => true;
}