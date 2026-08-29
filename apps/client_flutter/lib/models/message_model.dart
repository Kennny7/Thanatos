// Thanatos/apps/client_flutter/lib/models/message_model.dart

enum MessageSender { user, assistant, system }

class ChatMessage {
  final String id;
  final String content;
  final MessageSender sender;
  final DateTime timestamp;
  final String? thought;
  final String? speakerTag; // e.g. "Owner (You)", "Guest Speaker"
  final String? activeAgent;

  ChatMessage({
    required this.id,
    required this.content,
    required this.sender,
    required this.timestamp,
    this.thought,
    this.speakerTag,
    this.activeAgent,
  });

  ChatMessage copyWith({
    String? content,
    String? thought,
    String? speakerTag,
    String? activeAgent,
  }) {
    return ChatMessage(
      id: id,
      content: content ?? this.content,
      sender: sender,
      timestamp: timestamp,
      thought: thought ?? this.thought,
      speakerTag: speakerTag ?? this.speakerTag,
      activeAgent: activeAgent ?? this.activeAgent,
    );
  }
}
