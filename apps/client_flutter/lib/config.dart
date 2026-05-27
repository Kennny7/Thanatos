import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static String get websocketUrl {
    // Default fallback if .env not loaded
    const fallback = 'ws://localhost:8000/ws';
    try {
      final url = dotenv.env['WEBSOCKET_URL'];
      return url?.isNotEmpty == true ? url! : fallback;
    } catch (_) {
      return fallback;
    }
  }
}