// A 3D dynamic Fibonacci data sphere with harmonic oscillations, audio/thought reactivity,
// and holographic vector wireframe interconnects (like in TRON Legacy).

import 'dart:math';
import 'package:flutter/material.dart';

class Point3D {
  double x, y, z;
  Point3D(this.x, this.y, this.z);
}

class AISpeakingIndicator extends StatefulWidget {
  final double size;
  final Color? glowColor;
  final bool isResponding;
  final double audioLevel; // 0.0 to 1.0 (reactive to sound or thought activity)

  const AISpeakingIndicator({
    super.key,
    this.size = 140,
    this.glowColor,
    this.isResponding = false,
    this.audioLevel = 0.0,
  });

  @override
  State<AISpeakingIndicator> createState() => _AISpeakingIndicatorState();
}

class _AISpeakingIndicatorState extends State<AISpeakingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late List<Point3D> _spherePoints;
  static const int _pointCount = 110;

  @override
  void initState() {
    super.initState();
    _initFibonacciSphere();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 12),
    )..repeat();
  }

  void _initFibonacciSphere() {
    _spherePoints = [];
    final phi = (1 + sqrt(5)) / 2; // Golden ratio
    for (int i = 0; i < _pointCount; i++) {
      final y = 1 - (i / (_pointCount - 1)) * 2; // -1 to 1
      final radiusAtY = sqrt(max(0.0, 1 - y * y));
      final theta = 2 * pi * i / phi;

      final x = cos(theta) * radiusAtY;
      final z = sin(theta) * radiusAtY;
      _spherePoints.add(Point3D(x, y, z));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final primaryGlow = widget.glowColor ?? theme.colorScheme.primary;

    return AnimatedBuilder(
      animation: _controller,
      builder: (_, child) {
        final time = _controller.value * 2 * pi;
        return SizedBox(
          width: widget.size,
          height: widget.size,
          child: CustomPaint(
            painter: _FibonacciDataSpherePainter(
              points: _spherePoints,
              time: time,
              glowColor: primaryGlow,
              isResponding: widget.isResponding,
              audioLevel: widget.audioLevel,
            ),
          ),
        );
      },
    );
  }
}

class _FibonacciDataSpherePainter extends CustomPainter {
  final List<Point3D> points;
  final double time;
  final Color glowColor;
  final bool isResponding;
  final double audioLevel;

  _FibonacciDataSpherePainter({
    required this.points,
    required this.time,
    required this.glowColor,
    required this.isResponding,
    required this.audioLevel,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final baseRadius = (size.width / 2) * 0.72;

    // Non-repeating multi-axis continuous rotation matrix angles
    final rotX = time * 0.45 + sin(time * 0.3) * 0.2;
    final rotY = time * 0.85 + cos(time * 0.25) * 0.3;
    final rotZ = sin(time * 0.4) * 0.4;

    // Pulse factor driven by audio level & harmonic breathing
    final breath = 1.0 + 0.08 * sin(time * 2.0) + (audioLevel * 0.25) + (isResponding ? 0.12 * sin(time * 6.0) : 0.0);
    final currentRadius = baseRadius * breath;

    // Core glow halo
    final corePaint = Paint()
      ..shader = RadialGradient(
        colors: [
          glowColor.withOpacity(0.35 + (audioLevel * 0.3)),
          glowColor.withOpacity(0.08),
          Colors.transparent,
        ],
        stops: const [0.0, 0.5, 1.0],
      ).createShader(Rect.fromCircle(center: center, radius: currentRadius * 0.9));
    canvas.drawCircle(center, currentRadius * 0.85, corePaint);

    // Projected 2D screen points with depth tracking
    final projected = <_ScreenPoint>[];

    for (int i = 0; i < points.length; i++) {
      final p = points[i];

      // Harmonic radial deformation (non-repetitive wave ripples across sphere surface)
      final wave = 0.08 * sin(time * 3.0 + p.x * 4.0 + p.y * 3.0);
      final r = currentRadius * (1.0 + wave);

      var px = p.x * r;
      var py = p.y * r;
      var pz = p.z * r;

      // Rotate around X
      final y1 = py * cos(rotX) - pz * sin(rotX);
      final z1 = py * sin(rotX) + pz * cos(rotX);

      // Rotate around Y
      final x2 = px * cos(rotY) + z1 * sin(rotY);
      final z2 = -px * sin(rotY) + z1 * cos(rotY);

      // Rotate around Z
      final x3 = x2 * cos(rotZ) - y1 * sin(rotZ);
      final y3 = x2 * sin(rotZ) + y1 * cos(rotZ);

      // Perspective projection
      final cameraDist = currentRadius * 2.6;
      final perspective = cameraDist / (cameraDist + z2);
      final screenX = center.dx + x3 * perspective;
      final screenY = center.dy + y3 * perspective;

      // Depth alpha (closer particles are brighter and sharper)
      final normalizedZ = (z2 / currentRadius).clamp(-1.0, 1.0); // -1 back, +1 front
      final alpha = ((normalizedZ + 1.0) / 2.0).clamp(0.15, 1.0);

      projected.add(_ScreenPoint(
        offset: Offset(screenX, screenY),
        alpha: alpha,
        z: z2,
      ));
    }

    // Sort by depth (render back elements first)
    projected.sort((a, b) => a.z.compareTo(b.z));

    // Vector line connections between neighboring nodes (TRON grid wireframe effect)
    final linePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.7;

    final maxConnectionDistance = currentRadius * 0.42;
    final maxDistSq = maxConnectionDistance * maxConnectionDistance;

    for (int i = 0; i < projected.length; i += 2) {
      for (int j = i + 1; j < min(i + 7, projected.length); j++) {
        final p1 = projected[i];
        final p2 = projected[j];
        final dx = p1.offset.dx - p2.offset.dx;
        final dy = p1.offset.dy - p2.offset.dy;
        final distSq = dx * dx + dy * dy;

        if (distSq < maxDistSq) {
          final lineAlpha = (1.0 - (distSq / maxDistSq)) * min(p1.alpha, p2.alpha) * 0.45;
          linePaint.color = glowColor.withOpacity(lineAlpha.clamp(0.0, 0.8));
          canvas.drawLine(p1.offset, p2.offset, linePaint);
        }
      }
    }

    // Render 3D data nodes / particles
    final particlePaint = Paint()..style = PaintingStyle.fill;
    for (final sp in projected) {
      final nodeSize = 1.2 + (sp.alpha * 1.8);
      particlePaint.color = glowColor.withOpacity(sp.alpha);
      canvas.drawCircle(sp.offset, nodeSize, particlePaint);

      // Extra luminous ring for closest nodes
      if (sp.alpha > 0.85) {
        canvas.drawCircle(
          sp.offset,
          nodeSize * 2.2,
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 0.6
            ..color = glowColor.withOpacity(0.3),
        );
      }
    }
  }

  @override
  bool shouldRepaint(_FibonacciDataSpherePainter oldDelegate) => true;
}

class _ScreenPoint {
  final Offset offset;
  final double alpha;
  final double z;
  _ScreenPoint({required this.offset, required this.alpha, required this.z});
}