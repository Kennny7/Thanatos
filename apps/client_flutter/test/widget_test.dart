// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:thanatos_client/main.dart';
import 'package:thanatos_client/services/websocket_service.dart';
import 'package:thanatos_client/state/chat_provider.dart';

class MockWebSocketService extends WebSocketService {
  @override
  Future<void> connect() async {
    // No-op for testing to avoid actual network socket connections
  }
}

void main() {
  testWidgets('ThanatosApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          websocketServiceProvider.overrideWithValue(MockWebSocketService()),
        ],
        child: const ThanatosApp(),
      ),
    );
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
