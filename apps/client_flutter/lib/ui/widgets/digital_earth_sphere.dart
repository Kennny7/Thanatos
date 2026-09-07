// Thanatos/apps/client_flutter/lib/ui/widgets/digital_earth_sphere.dart

import 'dart:math';
import 'package:flutter/material.dart';
import 'holo_panel.dart';

/// Digital Earth Sphere HUD Window:
/// Renders a 3D rotating longitude/latitude wireframe globe that smoothly zooms
/// and locks onto user coordinates (e.g. Mumbai, India: 19.0760° N, 72.8777° E)
/// with tactical crosshairs, radar sweep circles, and telemetry readouts.
class DigitalEarthSphere extends StatefulWidget {
  final Color accentColor;
  final Color surfaceColor;
  final String locationName;
  final double latitude;
  final double longitude;
  final VoidCallback onClose;

  const DigitalEarthSphere({
    super.key,
    required this.accentColor,
    required this.surfaceColor,
    this.locationName = "Mumbai, India",
    this.latitude = 19.0760,
    this.longitude = 72.8777,
    required this.onClose,
  });

  @override
  State<DigitalEarthSphere> createState() => _DigitalEarthSphereState();
}

class _DigitalEarthSphereState extends State<DigitalEarthSphere>
    with SingleTickerProviderStateMixin {
  late AnimationController _rotationController;
  final bool _isLocked = true;
  double _zoomScale = 1.0;

  @override
  void initState() {
    super.initState();
    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 16),
    )..repeat();
  }

  @override
  void dispose() {
    _rotationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return HoloPanel(
      accentColor: widget.accentColor,
      surfaceColor: const Color(0xFF030712).withValues(alpha: 0.95),
      padding: const EdgeInsets.all(12),
      chamferSize: 8,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.public, color: widget.accentColor, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'DIGITAL EARTH // GEO-LOCATOR',
                    style: TextStyle(
                      color: widget.accentColor,
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      fontFamily: 'Courier',
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  GestureDetector(
                    onTap: () => setState(() => _zoomScale = _zoomScale == 1.0 ? 1.4 : 1.0),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        border: Border.all(color: widget.accentColor.withValues(alpha: 0.4)),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: Text(
                        _zoomScale > 1.0 ? 'ZOOM: 2X' : 'ZOOM: 1X',
                        style: TextStyle(color: widget.accentColor, fontSize: 8.5, fontFamily: 'Courier'),
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white54, size: 16),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    onPressed: widget.onClose,
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),

          // 3D Sphere Canvas
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: Container(
              height: 180,
              width: double.infinity,
              color: const Color(0xFF040A14),
              child: AnimatedBuilder(
                animation: _rotationController,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _EarthGlobePainter(
                      progress: _rotationController.value,
                      accentColor: widget.accentColor,
                      latitude: widget.latitude,
                      longitude: widget.longitude,
                      zoomScale: _zoomScale,
                      isLocked: _isLocked,
                    ),
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 8),

          // Coordinates Readout
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'TARGET: ${widget.locationName.toUpperCase()}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Courier',
                ),
              ),
              Text(
                '${widget.latitude.toStringAsFixed(4)}°N, ${widget.longitude.toStringAsFixed(4)}°E',
                style: const TextStyle(
                  color: Color(0xFF00E676),
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Courier',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EarthGlobePainter extends CustomPainter {
  final double progress;
  final Color accentColor;
  final double latitude;
  final double longitude;
  final double zoomScale;
  final bool isLocked;

  _EarthGlobePainter({
    required this.progress,
    required this.accentColor,
    required this.latitude,
    required this.longitude,
    required this.zoomScale,
    required this.isLocked,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2.0, size.height / 2.0);
    final radius = (min(size.width, size.height) / 2.2) * zoomScale;

    // 1. Draw outer glowing sphere perimeter
    final rimPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawCircle(center, radius, rimPaint);

    final atmosphereGlow = Paint()
      ..color = accentColor.withValues(alpha: 0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6.0
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4.0);
    canvas.drawCircle(center, radius, atmosphereGlow);

    // 2. Parallels (Latitudes)
    final gridPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.25)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;

    for (int lat = -60; lat <= 60; lat += 20) {
      final rad = lat * pi / 180.0;
      final yOffset = sin(rad) * radius;
      final rParallel = cos(rad) * radius;
      final rect = Rect.fromCenter(
        center: Offset(center.dx, center.dy - yOffset),
        width: rParallel * 2,
        height: rParallel * 0.45,
      );
      canvas.drawOval(rect, gridPaint);
    }

    // 3. Meridians (Longitudes) rotating
    final angleOffset = progress * 2.0 * pi;
    for (int lon = 0; lon < 180; lon += 30) {
      final currentAngle = (lon * pi / 180.0) + angleOffset;
      final xRadius = (cos(currentAngle) * radius).abs();
      final rect = Rect.fromCenter(
        center: center,
        width: max(xRadius * 2, 2.0),
        height: radius * 2,
      );
      canvas.drawOval(rect, gridPaint);
    }

    // 4. Radar Sweep Beam
    final sweepPaint = Paint()
      ..shader = SweepGradient(
        colors: [Colors.transparent, accentColor.withValues(alpha: 0.35)],
        stops: const [0.8, 1.0],
        transform: GradientRotation(progress * 2 * pi),
      ).createShader(Rect.fromCircle(center: center, radius: radius));
    canvas.drawCircle(center, radius, sweepPaint);

    // 5. Target Lock Marker for User Location
    final latRad = latitude * pi / 180.0;
    final targetY = center.dy - sin(latRad) * radius;
    final targetX = center.dx + cos(latRad) * radius * 0.4 * cos(angleOffset);

    final targetPaint = Paint()
      ..color = const Color(0xFF00E676)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(targetX, targetY), 4.0, targetPaint);

    final targetRing = Paint()
      ..color = const Color(0xFF00E676)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    canvas.drawCircle(Offset(targetX, targetY), 8.0, targetRing);

    // Crosshair lines through target
    canvas.drawLine(Offset(targetX - 12, targetY), Offset(targetX + 12, targetY), targetRing);
    canvas.drawLine(Offset(targetX, targetY - 12), Offset(targetX, targetY + 12), targetRing);
  }

  @override
  bool shouldRepaint(_EarthGlobePainter oldDelegate) => true;
}
