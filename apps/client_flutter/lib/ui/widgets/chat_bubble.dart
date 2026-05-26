// A Material 3 chat bubble with user / assistant styling and streaming indication.

import 'package:flutter/material.dart';
import '../../models/message_model.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final bool showStreamingIndicator;

  const ChatBubble({
    super.key,
    required this.message,
    this.showStreamingIndicator = false,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final colorScheme = Theme.of(context).colorScheme;
    final backgroundColor =
        isUser ? colorScheme.primaryContainer : colorScheme.surfaceVariant;
    final textColor =
        isUser ? colorScheme.onPrimaryContainer : colorScheme.onSurfaceVariant;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: isUser
                ? const Radius.circular(20)
                : const Radius.circular(4),
            bottomRight: isUser
                ? const Radius.circular(4)
                : const Radius.circular(20),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (message.isPartial && showStreamingIndicator)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: _StreamingDot(),
              ),
            Text(
              message.text,
              style: TextStyle(color: textColor),
            ),
          ],
        ),
      ),
    );
  }
}

class _StreamingDot extends StatefulWidget {
  @override
  State<_StreamingDot> createState() => _StreamingDotState();
}

class _StreamingDotState extends State<_StreamingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 8,
        height: 8,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}