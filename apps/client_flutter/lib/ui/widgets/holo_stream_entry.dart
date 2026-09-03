// Thanatos/apps/client_flutter/lib/ui/widgets/holo_stream_entry.dart

import 'package:flutter/material.dart';
import '../../models/message_model.dart';

/// Replaces chat bubbles with a holographic tactical data transmission entry.
/// Inspired by Tony Stark HUD terminal readouts and military sci-fi telemetry streams.
class HoloStreamEntry extends StatefulWidget {
  final ChatMessage message;
  final Color accentColor;
  final Color surfaceColor;

  const HoloStreamEntry({
    super.key,
    required this.message,
    required this.accentColor,
    required this.surfaceColor,
  });

  @override
  State<HoloStreamEntry> createState() => _HoloStreamEntryState();
}

class _HoloStreamEntryState extends State<HoloStreamEntry> {
  bool _isThoughtExpanded = false;

  @override
  Widget build(BuildContext context) {
    final isUser = widget.message.sender == MessageSender.user;
    final originTag = isUser
        ? 'OPERATOR // DIRECT_LINK'
        : '${(widget.message.activeAgent ?? "CORE").toUpperCase()} // SYNAPSE';
    final timestampStr = '${widget.message.timestamp.hour.toString().padLeft(2, '0')}:${widget.message.timestamp.minute.toString().padLeft(2, '0')}:${widget.message.timestamp.second.toString().padLeft(2, '0')}';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 4.0),
      child: CustomPaint(
        painter: _TransmissionFramePainter(
          accentColor: widget.accentColor,
          surfaceColor: widget.surfaceColor.withValues(alpha: 0.85),
          isUser: isUser,
        ),
        child: Container(
          padding: const EdgeInsets.all(14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Tactical Metadata Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: isUser ? widget.accentColor : Colors.white,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        originTag,
                        style: TextStyle(
                          color: widget.accentColor,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                          fontFamily: 'Courier',
                        ),
                      ),
                    ],
                  ),
                  Text(
                    '[T+ $timestampStr]',
                    style: TextStyle(
                      color: widget.accentColor.withValues(alpha: 0.6),
                      fontSize: 10,
                      fontFamily: 'Courier',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // AI Neural Trace / Deep Reasoning accordion
              if (widget.message.thought != null && widget.message.thought!.isNotEmpty) ...[
                GestureDetector(
                  onTap: () => setState(() => _isThoughtExpanded = !_isThoughtExpanded),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 10.0),
                    padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 6.0),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.04),
                      border: Border.all(color: widget.accentColor.withValues(alpha: 0.3)),
                      borderRadius: BorderRadius.circular(2),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _isThoughtExpanded ? Icons.expand_less : Icons.expand_more,
                          color: widget.accentColor,
                          size: 16,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'NEURAL THOUGHT TRACE [LOGS]',
                          style: TextStyle(
                            color: widget.accentColor,
                            fontSize: 10,
                            letterSpacing: 1.2,
                            fontFamily: 'Courier',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                if (_isThoughtExpanded)
                  Container(
                    margin: const EdgeInsets.only(bottom: 12.0),
                    padding: const EdgeInsets.all(10.0),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.4),
                      border: Border(left: BorderSide(color: widget.accentColor, width: 2.0)),
                    ),
                    child: Text(
                      widget.message.thought!,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.75),
                        fontSize: 11,
                        fontFamily: 'Courier',
                        height: 1.4,
                      ),
                    ),
                  ),
              ],

              // Message Content
              SelectableText(
                widget.message.content,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13.5,
                  height: 1.45,
                  letterSpacing: 0.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TransmissionFramePainter extends CustomPainter {
  final Color accentColor;
  final Color surfaceColor;
  final bool isUser;

  _TransmissionFramePainter({
    required this.accentColor,
    required this.surfaceColor,
    required this.isUser,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    const c = 10.0;

    final path = Path()
      ..moveTo(c, 0)
      ..lineTo(w, 0)
      ..lineTo(w, h - c)
      ..lineTo(w - c, h)
      ..lineTo(0, h)
      ..lineTo(0, c)
      ..close();

    // Background surface fill
    final fillPaint = Paint()
      ..color = surfaceColor
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, fillPaint);

    // Left laser rail (thicker glowing accent line)
    final railPaint = Paint()
      ..color = accentColor
      ..strokeWidth = 2.5;
    canvas.drawLine(const Offset(0, c), Offset(0, h), railPaint);

    // Subtle edge border
    final borderPaint = Paint()
      ..color = accentColor.withValues(alpha: 0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;
    canvas.drawPath(path, borderPaint);
  }

  @override
  bool shouldRepaint(_TransmissionFramePainter oldDelegate) =>
      oldDelegate.accentColor != accentColor ||
      oldDelegate.surfaceColor != surfaceColor ||
      oldDelegate.isUser != isUser;
}
