// This service manages a persistent WebSocket connection, parses incoming JSON, and exposes streams for UI updates.

import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;

import '../config.dart';

/// Possible events received from the backend.
sealed class WsEvent {
  const WsEvent();
}

class TextChunkEvent extends WsEvent {
  final String content;
  const TextChunkEvent(this.content);
}

class ToolUpdateEvent extends WsEvent {
  final String toolName;
  final Map<String, dynamic>? args;
  final String? description;
  const ToolUpdateEvent({
    required this.toolName,
    this.args,
    this.description,
  });
}

class ConnectionErrorEvent extends WsEvent {
  final String message;
  const ConnectionErrorEvent(this.message);
}

class ConnectionStateChanged extends WsEvent {
  final bool connected;
  const ConnectionStateChanged(this.connected);
}

/// Service that handles WebSocket lifecycle, parsing, and reconnection.
class WebSocketService {
  final String url;
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  bool _disposed = false;
  int _reconnectAttempts = 0;
  static const _maxReconnectDelay = Duration(seconds: 30);

  final _eventController = StreamController<WsEvent>.broadcast();
  Stream<WsEvent> get eventStream => _eventController.stream;

  WebSocketService({String? url}) : url = url ?? AppConfig.websocketUrl;

  /// Connect to the WebSocket server.
  Future<void> connect() async {
    if (_disposed) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _reconnectAttempts = 0;
      _eventController.add(const ConnectionStateChanged(true));

      await for (final message in _channel!.stream) {
        _handleMessage(message);
      }
      // Stream closed (server disconnected)
    } catch (e) {
      _eventController.add(ConnectionErrorEvent('Connection failed: $e'));
      _eventController.add(const ConnectionStateChanged(false));
    } finally {
      // Cleanup and schedule reconnect if not disposed
      await _channel?.sink.close();
      _scheduleReconnect();
    }
  }

  void _handleMessage(dynamic raw) {
    try {
      final Map<String, dynamic> json =
          raw is String ? jsonDecode(raw) : jsonDecode(raw as String);
      final type = json['type'] as String?;
      if (type == 'chunk') {
        final content = json['content'] as String? ?? '';
        _eventController.add(TextChunkEvent(content));
      } else if (type == 'tool_update') {
        final tool = json['tool'] as String? ?? 'unknown';
        final args = json['args'] as Map<String, dynamic>?;
        final desc = json['description'] as String?;
        _eventController.add(ToolUpdateEvent(
          toolName: tool,
          args: args,
          description: desc,
        ));
      }
      // Ignore unknown types gracefully
    } catch (e) {
      _eventController
          .add(ConnectionErrorEvent('Failed to parse message: $e'));
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    _reconnectAttempts++;
    final delay = Duration(
      seconds: (_reconnectAttempts * 2).clamp(1, _maxReconnectDelay.inSeconds),
    );
    _reconnectTimer = Timer(delay, connect);
  }

  /// Send a text message to the backend.
  void sendMessage(String text) {
    final data = jsonEncode({'type': 'user_message', 'content': text});
    _channel?.sink.add(data);
  }

  /// Graceful shutdown.
  Future<void> dispose() async {
    _disposed = true;
    _reconnectTimer?.cancel();
    await _channel?.sink.close(status.goingAway);
    await _eventController.close();
  }
}