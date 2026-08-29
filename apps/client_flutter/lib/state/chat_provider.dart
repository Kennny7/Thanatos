// Thanatos/apps/client_flutter/lib/state/chat_provider.dart

import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../models/message_model.dart';
import '../services/websocket_service.dart';

class ChatState {
  final List<ChatMessage> messages;
  final bool isAiResponding;
  final String? activeAgent;
  final String? agentStatusText;
  final double agentProgress;
  final String? toolUpdateMessage;

  ChatState({
    required this.messages,
    this.isAiResponding = false,
    this.activeAgent,
    this.agentStatusText,
    this.agentProgress = 0.0,
    this.toolUpdateMessage,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isAiResponding,
    String? activeAgent,
    String? agentStatusText,
    double? agentProgress,
    String? toolUpdateMessage,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isAiResponding: isAiResponding ?? this.isAiResponding,
      activeAgent: activeAgent,
      agentStatusText: agentStatusText,
      agentProgress: agentProgress ?? this.agentProgress,
      toolUpdateMessage: toolUpdateMessage,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  final WebSocketService _wsService;
  StreamSubscription? _wsSub;

  ChatNotifier(this._wsService) : super(ChatState(messages: [])) {
    _initWebSocket();
  }

  void _initWebSocket() {
    _wsService.connect();
    _wsSub = _wsService.stream.listen((event) {
      _handleIncomingMessage(event);
    }, onError: (err) {
      state = state.copyWith(isAiResponding: false);
    });
  }

  void _handleIncomingMessage(dynamic raw) {
    try {
      final data = json.decode(raw.toString());
      final type = data['type'];

      if (type == 'assistant_chunk') {
        final content = data['content'] ?? '';
        _appendAssistantChunk(content);
      } else if (type == 'agent_status') {
        state = state.copyWith(
          activeAgent: data['agent'],
          agentStatusText: data['status'],
          agentProgress: (data['progress'] as num?)?.toDouble() ?? 0.5,
          isAiResponding: true,
        );
      } else if (type == 'thought') {
        _appendThought(data['content'] ?? '');
      } else if (type == 'tool_call') {
        state = state.copyWith(toolUpdateMessage: 'Running tool: ${data['name']}');
      }
    } catch (e) {
      // Fallback plain string
      _appendAssistantChunk(raw.toString());
    }
  }

  void sendTextMessage(String text, {String? speakerTag}) {
    if (text.trim().isEmpty) return;

    final userMsg = ChatMessage(
      id: const Uuid().v4(),
      content: text,
      sender: MessageSender.user,
      timestamp: DateTime.now(),
      speakerTag: speakerTag ?? 'Owner (You)',
    );

    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isAiResponding: true,
      activeAgent: 'Coordinator',
      agentStatusText: 'Analyzing request...',
      agentProgress: 0.1,
    );

    _wsService.send(json.encode({
      'type': 'user_message',
      'content': text,
    }));
  }

  void _appendAssistantChunk(String chunk) {
    if (state.messages.isNotEmpty && state.messages.last.sender == MessageSender.assistant) {
      final lastMsg = state.messages.last;
      final updated = lastMsg.copyWith(content: lastMsg.content + chunk);
      state = state.copyWith(
        messages: [...state.messages.sublist(0, state.messages.length - 1), updated],
        isAiResponding: false,
        activeAgent: null,
        agentStatusText: null,
      );
    } else {
      final newAssistantMsg = ChatMessage(
        id: const Uuid().v4(),
        content: chunk,
        sender: MessageSender.assistant,
        timestamp: DateTime.now(),
      );
      state = state.copyWith(
        messages: [...state.messages, newAssistantMsg],
        isAiResponding: false,
        activeAgent: null,
        agentStatusText: null,
      );
    }
  }

  void _appendThought(String thought) {
    if (state.messages.isNotEmpty && state.messages.last.sender == MessageSender.assistant) {
      final lastMsg = state.messages.last;
      final updated = lastMsg.copyWith(thought: (lastMsg.thought ?? '') + thought);
      state = state.copyWith(
        messages: [...state.messages.sublist(0, state.messages.length - 1), updated],
      );
    }
  }

  void clearToolUpdate() {
    state = state.copyWith(toolUpdateMessage: null);
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    super.dispose();
  }
}

final websocketServiceProvider = Provider((ref) => WebSocketService());
final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final ws = ref.watch(websocketServiceProvider);
  return ChatNotifier(ws);
});
