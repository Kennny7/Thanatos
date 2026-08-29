// Thanatos/apps/client_flutter/lib/ui/widgets/chat_bubble.dart

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
    final isUser = message.sender == MessageSender.user;
    final backgroundColor = isUser ? const Color(0xFF6C63FF) : const Color(0xFF2E2E3E);
    final textColor = Colors.white;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.82,
        ),
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
            bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.12),
              blurRadius: 4,
              offset: const Offset(0, 2),
            )
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (message.speakerTag != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isUser ? Icons.person : Icons.record_voice_over,
                      size: 13,
                      color: Colors.white70,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      message.speakerTag!,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            if (message.thought != null && message.thought!.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black26,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white12),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.psychology, size: 14, color: Colors.amberAccent),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        message.thought!,
                        style: const TextStyle(color: Colors.amberAccent, fontSize: 11, fontStyle: FontStyle.italic),
                      ),
                    ),
                  ],
                ),
              ),
            SelectableText(
              message.content,
              style: TextStyle(color: textColor, fontSize: 14, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }
}
