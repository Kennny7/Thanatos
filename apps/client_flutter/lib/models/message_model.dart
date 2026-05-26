import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'message_model.freezed.dart';
part 'message_model.g.dart';

const _uuid = Uuid();

enum MessageRole { user, assistant }

@freezed
class ChatMessage with _$ChatMessage {
  const factory ChatMessage({
    required String id,
    required String text,
    required MessageRole role,
    required DateTime timestamp,
    @Default(false) bool isPartial, // true while assistant is streaming
  }) = _ChatMessage;

  factory ChatMessage.fromJson(Map<String, dynamic> json) =>
      _$ChatMessageFromJson(json);

  factory ChatMessage.userMessage(String text) => ChatMessage(
        id: _uuid.v4(),
        text: text,
        role: MessageRole.user,
        timestamp: DateTime.now(),
      );

  factory ChatMessage.assistantPlaceholder() => ChatMessage(
        id: _uuid.v4(),
        text: '',
        role: MessageRole.assistant,
        timestamp: DateTime.now(),
        isPartial: true,
      );
}