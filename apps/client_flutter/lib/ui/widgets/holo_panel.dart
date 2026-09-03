// Thanatos/apps/client_flutter/lib/ui/widgets/holo_panel.dart

import 'package:flutter/material.dart';

/// A Tony Stark / Jarvis style holographic HUD panel with 45° chamfered corners,
/// glowing neon edge framing, corner crosshair brackets, and optional technical classification strip.
class HoloPanel extends StatelessWidget {
  final Widget child;
  final Color accentColor;
  final Color? surfaceColor;
  final String? classificationTag;
  final double chamferSize;
  final EdgeInsetsGeometry padding;
  final bool showGlow;
  final VoidCallback? onTap;

  const HoloPanel({
    super.key,
    required this.child,
    required this.accentColor,
    this.surfaceColor,
    this.classificationTag,
    this.chamferSize = 12.0,
    this.padding = const EdgeInsets.all(16.0),
    this.showGlow = true,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bg = surfaceColor ?? const Color(0xFF050B14);

    Widget content = CustomPaint(
      painter: _ChamferedHudPainter(
        accentColor: accentColor,
        surfaceColor: bg,
        chamferSize: chamferSize,
        showGlow: showGlow,
      ),
      child: Padding(
        padding: padding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (classificationTag != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 4,
                        height: 10,
                        color: accentColor,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        classificationTag!.toUpperCase(),
                        style: TextStyle(
                          color: accentColor,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.8,
                          fontFamily: 'Courier',
                        ),
                      ),
                    ],
                  ),
                  Text(
                    'SEC_AUTH // VERIFIED',
                    style: TextStyle(
                      color: accentColor.withValues(alpha: 0.5),
                      fontSize: 8,
                      letterSpacing: 1.2,
                      fontFamily: 'Courier',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
            ],
            child,
          ],
        ),
      ),
    );

    if (onTap != null) {
      return GestureDetector(onTap: onTap, child: content);
    }
    return content;
  }
}

class _ChamferedHudPainter extends CustomPainter {
  final Color accentColor;
  final Color surfaceColor;
  final double chamferSize;
  final bool showGlow;

  _ChamferedHudPainter({
    required this.accentColor,
    required this.surfaceColor,
    required this.chamferSize,
    required this.showGlow,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final c = chamferSize;

    // Path for 45° chamfered polygon
    final path = Path()
      ..moveTo(c, 0)
      ..lineTo(w - c, 0)
      ..lineTo(w, c)
      ..lineTo(w, h - c)
      ..lineTo(w - c, h)
      ..lineTo(c, h)
      ..lineTo(0, h - c)
      ..lineTo(0, c)
      ..close();

    // Fill surface
    final fillPaint = Paint()
      ..color = surfaceColor
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, fillPaint);

    // Subtle holographic scanline pattern inside panel
    final scanlinePaint = Paint()
      ..color = accentColor.withValues(alpha: 0.03)
      ..strokeWidth = 0.8;
    for (double y = 4; y < h; y += 6) {
      canvas.drawLine(Offset(0, y), Offset(w, y), scanlinePaint);
    }

    // Glow aura along perimeter
    if (showGlow) {
      final glowPaint = Paint()
        ..color = accentColor.withValues(alpha: 0.25)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.0
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4.0);
      canvas.drawPath(path, glowPaint);
    }

    // Crisp neon edge wireframe
    final borderPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawPath(path, borderPaint);

    // Tactical corner brackets (+) crosshairs
    final crosshairPaint = Paint()
      ..color = accentColor
      ..strokeWidth = 1.4;

    const crossSize = 4.0;
    // Top-left crosshair
    canvas.drawLine(Offset(c - crossSize, c), Offset(c + crossSize, c), crosshairPaint);
    canvas.drawLine(Offset(c, c - crossSize), Offset(c, c + crossSize), crosshairPaint);

    // Bottom-right crosshair
    canvas.drawLine(Offset(w - c - crossSize, h - c), Offset(w - c + crossSize, h - c), crosshairPaint);
    canvas.drawLine(Offset(w - c, h - c - crossSize), Offset(w - c, h - c + crossSize), crosshairPaint);
  }

  @override
  bool shouldRepaint(_ChamferedHudPainter oldDelegate) =>
      oldDelegate.accentColor != accentColor ||
      oldDelegate.surfaceColor != surfaceColor ||
      oldDelegate.chamferSize != chamferSize;
}
