// Thanatos/apps/client_flutter/lib/ui/widgets/agent_status_tracker.dart

import 'package:flutter/material.dart';

class AgentStatusTracker extends StatelessWidget {
  final String agentName;
  final String statusText;
  final double progress;
  final Color? accentColor;

  const AgentStatusTracker({
    super.key,
    required this.agentName,
    required this.statusText,
    required this.progress,
    this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = accentColor ?? theme.colorScheme.primary;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: accent.withValues(alpha: 0.4), width: 1.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              // Tactical agent badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.2),
                  border: Border.all(color: accent, width: 0.8),
                  borderRadius: BorderRadius.circular(2),
                ),
                child: Text(
                  agentName.toUpperCase(),
                  style: TextStyle(
                    color: accent,
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                    letterSpacing: 1.0,
                    fontFamily: 'Courier',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  statusText,
                  style: const TextStyle(color: Colors.white70, fontSize: 11.5, fontFamily: 'Courier'),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              SizedBox(
                width: 12,
                height: 12,
                child: CircularProgressIndicator(strokeWidth: 1.8, color: accent),
              ),
            ],
          ),
          const SizedBox(height: 6),
          // Tactical Segmented LED Progress Bar
          _buildSegmentedLedBar(progress, accent),
        ],
      ),
    );
  }

  Widget _buildSegmentedLedBar(double pct, Color accent) {
    const totalSegments = 16;
    final activeSegments = (pct.clamp(0.0, 1.0) * totalSegments).round();

    return Row(
      children: List.generate(totalSegments, (idx) {
        final isActive = idx < activeSegments;
        return Expanded(
          child: Container(
            height: 3.5,
            margin: const EdgeInsets.symmetric(horizontal: 1),
            decoration: BoxDecoration(
              color: isActive ? accent : Colors.white.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(1),
              boxShadow: isActive
                  ? [BoxShadow(color: accent.withValues(alpha: 0.6), blurRadius: 4)]
                  : null,
            ),
          ),
        );
      }),
    );
  }
}
