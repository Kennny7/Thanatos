// Riverpod provider that ties together WebSocket events and speech, updating the message list.

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/message_model.dart';
import '../services/websocket_service.dart';
import '../services/speech_service.dart';

// Providers for services
final webSocketServiceProvider = Provider<WebSocketService>((ref) {
  final service = WebSocketService();
  ref.onDispose(() => service.dispose());
  return service;
});

final speechServiceProvider = Provider<SpeechService>((ref) {
  final service = SpeechService();
  ref.onDispose(() => service.dispose());
  return service;
});

// State class
class ChatState {
  final List<ChatMessage> messages;
  final bool isAiResponding; // true while assistant is streaming
  final String? toolUpdateMessage; // latest tool_update for snackbar
  final bool isListening; // mic active

  const ChatState({
    this.messages = const [],
    this.isAiResponding = false,
    this.toolUpdateMessage,
    this.isListening = false,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isAiResponding,
    String? toolUpdateMessage,
    bool? isListening,
    bool clearToolUpdate = false,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isAiResponding: isAiResponding ?? this.isAiResponding,
      toolUpdateMessage:
          clearToolUpdate ? null : toolUpdateMessage ?? this.toolUpdateMessage,
      isListening: isListening ?? this.isListening,
    );
  }
}

// Notifier
class ChatNotifier extends StateNotifier<ChatState> {
  final WebSocketService _wsService;
  final SpeechService _speechService;
//   StreamSubscription<WsEvent>? _wsSub;
//   StreamSubscription<String>? _speechTextSub;
    StreamSubscription<WsEvent>? _wsSub;
    StreamSubscription<String>? _speechTextSub;
    StreamSubscription<String>? _speechErrorSub;


  ChatNotifier(this._wsService, this._speechService)
      : super(const ChatState()) {
    _initWebSocket();
  }

  void _initWebSocket() {
    _wsSub = _wsService.eventStream.listen(_handleWsEvent);
    _wsService.connect(); // start connection
  }

  void _handleWsEvent(WsEvent event) {
    switch (event) {
      case TextChunkEvent(:final content):
        _appendChunk(content);
        break;
      case ToolUpdateEvent(:final toolName, :final description):
        final toolMsg = description ?? 'Opening $toolName...';
        state = state.copyWith(toolUpdateMessage: toolMsg);
        break;
      case ConnectionErrorEvent(:final message):
        // Could show a persistent error; we'll just log for now
        break;
      case ConnectionStateChanged(:final connected):
        // Handle reconnection if needed
        break;
    }
  }

  void _appendChunk(String content) {
    final messages = List<ChatMessage>.from(state.messages);
    if (messages.isEmpty || messages.last.role != MessageRole.assistant) {
      // Create a new assistant message placeholder
      final newMsg = ChatMessage.assistantPlaceholder().copyWith(text: content);
      messages.add(newMsg);
      state = state.copyWith(
          messages: messages, isAiResponding: true);
      return;
    }
    // Update last assistant message
    final last = messages.last;
    final updated = last.copyWith(text: last.text + content);
    messages[messages.length - 1] = updated;
    state = state.copyWith(messages: messages, isAiResponding: true);
  }

  /// Send a user message (text) and reset AI streaming.
  void sendTextMessage(String text) {
    if (text.trim().isEmpty) return;
    final userMsg = ChatMessage.userMessage(text);
    final messages = List<ChatMessage>.from(state.messages)..add(userMsg);
    state = state.copyWith(messages: messages, isAiResponding: true);
    _wsService.sendMessage(text);
  }

  /// Mark the current assistant message as complete.
  void finishAiResponse() {
    if (!state.isAiResponding) return;
    final messages = List<ChatMessage>.from(state.messages);
    if (messages.isNotEmpty && messages.last.role == MessageRole.assistant) {
      messages[messages.length - 1] =
          messages.last.copyWith(isPartial: false);
    }
    state = state.copyWith(messages: messages, isAiResponding: false);
  }

  /// Voice input handling
  Future<void> toggleListening() async {
    if (state.isListening) {
      await _speechService.stopListening();
      state = state.copyWith(isListening: false);
    } else {
      final available = await _speechService.initialize();
      if (!available) return;
    //   _speechTextSub?.cancel();
    //   _speechTextSub = _speechService.onText.listen((text) {
    _speechTextSub?.cancel();
    _speechErrorSub?.cancel();

    _speechTextSub = _speechService.onText.listen((text) {
        // When final result arrives, send it
        if (text.isNotEmpty && !state.isListening) {
          sendTextMessage(text);
        }
      });

    _speechErrorSub = _speechService.onError.listen((error) {
      print('Speech recognition error: $error');
    });
      await _speechService.startListening();
      state = state.copyWith(isListening: true);
    }
  }

  /// Dismiss tool update snackbar.
  void clearToolUpdate() {
    state = state.copyWith(clearToolUpdate: true);
  }

//   @override
//   void dispose() {
//     _wsSub?.cancel();
//     _speechTextSub?.cancel();
//     super.dispose();
//   }
    @override
    void dispose() {
    _wsSub?.cancel();
    _speechTextSub?.cancel();
    _speechErrorSub?.cancel();
    super.dispose();
    }
}

// Provider
final chatProvider =
    StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final ws = ref.watch(webSocketServiceProvider);
  final speech = ref.watch(speechServiceProvider);
  return ChatNotifier(ws, speech);
});