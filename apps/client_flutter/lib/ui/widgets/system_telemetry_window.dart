// Thanatos/apps/client_flutter/lib/ui/widgets/system_telemetry_window.dart

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../config.dart';
import 'holo_panel.dart';

/// System Telemetry HUD Window:
/// Fetches and displays real, genuine hardware metrics from the Thanatos backend:
/// - CPU Usage percentage & Logical Cores
/// - Total RAM, Used RAM, and Available RAM
/// - Disk Storage consumption
/// - Count of active registered skills and tools
/// Closable and adjustable.
class SystemTelemetryWindow extends StatefulWidget {
  final Color accentColor;
  final Color surfaceColor;
  final VoidCallback onClose;

  const SystemTelemetryWindow({
    super.key,
    required this.accentColor,
    required this.surfaceColor,
    required this.onClose,
  });

  @override
  State<SystemTelemetryWindow> createState() => _SystemTelemetryWindowState();
}

class _SystemTelemetryWindowState extends State<SystemTelemetryWindow> {
  Timer? _pollTimer;
  Map<String, dynamic>? _metrics;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchMetrics();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchMetrics());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchMetrics() async {
    try {
      final res = await http
          .get(Uri.parse('${AppConfig.apiBaseUrl}/api/system/live-metrics'))
          .timeout(const Duration(seconds: 2));
      if (res.statusCode == 200 && mounted) {
        setState(() {
          _metrics = json.decode(res.body);
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cpuPercent = (_metrics?['cpu']?['percent'] as num?)?.toDouble() ?? 0.0;
    final cpuCores = _metrics?['cpu']?['logical_cores'] ?? 4;
    final ramUsed = (_metrics?['ram']?['used_gb'] as num?)?.toDouble() ?? 0.0;
    final ramTotal = (_metrics?['ram']?['total_gb'] as num?)?.toDouble() ?? 0.0;
    final ramPercent = (_metrics?['ram']?['percent'] as num?)?.toDouble() ?? 0.0;
    final diskPercent = (_metrics?['disk']?['percent'] as num?)?.toDouble() ?? 0.0;
    final diskTotal = (_metrics?['disk']?['total_gb'] as num?)?.toDouble() ?? 0.0;
    final toolsCount = _metrics?['telemetry']?['active_skills_count'] ?? 0;
    final toolsList = (_metrics?['telemetry']?['tools'] as List?)?.map((e) => e.toString()).toList() ?? [];

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
                  Icon(Icons.memory, color: widget.accentColor, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'SYSTEM TELEMETRY // LIVE HARDWARE',
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
                  Container(
                    width: 7,
                    height: 7,
                    decoration: const BoxDecoration(
                      color: Color(0xFF00E676),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text(
                    'LIVE',
                    style: TextStyle(color: Color(0xFF00E676), fontSize: 9, fontWeight: FontWeight.bold, fontFamily: 'Courier'),
                  ),
                  const SizedBox(width: 8),
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
          const SizedBox(height: 10),

          if (_isLoading && _metrics == null)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else ...[
            // CPU Gauge Row
            _buildMetricBar(
              label: 'CPU LOAD',
              valueText: '${cpuPercent.toStringAsFixed(1)}% ($cpuCores Cores)',
              progress: (cpuPercent / 100.0).clamp(0.0, 1.0),
              color: cpuPercent > 80 ? Colors.redAccent : widget.accentColor,
            ),
            const SizedBox(height: 8),

            // RAM Gauge Row
            _buildMetricBar(
              label: 'MEMORY (RAM)',
              valueText: '${ramUsed.toStringAsFixed(1)} / ${ramTotal.toStringAsFixed(1)} GB (${ramPercent.toStringAsFixed(0)}%)',
              progress: (ramPercent / 100.0).clamp(0.0, 1.0),
              color: ramPercent > 85 ? Colors.orangeAccent : const Color(0xFF00E676),
            ),
            const SizedBox(height: 8),

            // Disk Gauge Row
            _buildMetricBar(
              label: 'STORAGE DISK',
              valueText: '${diskPercent.toStringAsFixed(0)}% of ${diskTotal.toStringAsFixed(0)} GB',
              progress: (diskPercent / 100.0).clamp(0.0, 1.0),
              color: widget.accentColor.withValues(alpha: 0.8),
            ),
            const SizedBox(height: 10),

            // Registered Tools & Skills Strip
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.5),
                border: Border.all(color: Colors.white10),
                borderRadius: BorderRadius.circular(2),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'LOADED CAPABILITIES // TOOLS ($toolsCount)',
                        style: TextStyle(color: widget.accentColor, fontSize: 9.5, fontWeight: FontWeight.bold, fontFamily: 'Courier'),
                      ),
                      const Text('STATUS: ACTIVE', style: TextStyle(color: Color(0xFF00E676), fontSize: 8.5, fontFamily: 'Courier')),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 4,
                    runSpacing: 4,
                    children: toolsList.map((tool) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: widget.accentColor.withValues(alpha: 0.12),
                          border: Border.all(color: widget.accentColor.withValues(alpha: 0.3)),
                          borderRadius: BorderRadius.circular(2),
                        ),
                        child: Text(
                          tool,
                          style: TextStyle(color: widget.accentColor, fontSize: 8.5, fontFamily: 'Courier'),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMetricBar({
    required String label,
    required String valueText,
    required double progress,
    required Color color,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(color: Colors.white70, fontSize: 9.5, fontFamily: 'Courier', fontWeight: FontWeight.bold),
            ),
            Text(
              valueText,
              style: TextStyle(color: color, fontSize: 9.5, fontFamily: 'Courier', fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 3),
        ClipRRect(
          borderRadius: BorderRadius.circular(1),
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor: Colors.white.withValues(alpha: 0.08),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 4,
          ),
        ),
      ],
    );
  }
}
