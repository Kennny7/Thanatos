import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static String get websocketUrl {
    const fallback = 'ws://localhost:8000/ws';
    try {
      final url = dotenv.env['WEBSOCKET_URL'];
      return url?.isNotEmpty == true ? url! : fallback;
    } catch (_) {
      return fallback;
    }
  }

  static String get apiBaseUrl {
    const fallback = 'http://localhost:8000';
    try {
      final url = dotenv.env['API_BASE_URL'];
      return url?.isNotEmpty == true ? url! : fallback;
    } catch (_) {
      return fallback;
    }
  }
}