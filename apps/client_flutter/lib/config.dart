import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static String? _customGatewayUrl;

  /// Dynamically update the backend server gateway address from within the app
  static void setGatewayUrl(String newUrl) {
    if (newUrl.trim().isNotEmpty) {
      _customGatewayUrl = newUrl.trim().replaceAll(RegExp(r'/+$'), '');
    }
  }

  static String get apiBaseUrl {
    if (_customGatewayUrl != null && _customGatewayUrl!.isNotEmpty) {
      return _customGatewayUrl!;
    }
    const fallback = 'http://localhost:8000';
    try {
      final url = dotenv.env['API_BASE_URL'];
      return url?.isNotEmpty == true ? url! : fallback;
    } catch (_) {
      return fallback;
    }
  }

  static String get websocketUrl {
    final base = apiBaseUrl;
    if (base.startsWith('https://')) {
      return base.replaceFirst('https://', 'wss://') + '/ws';
    } else if (base.startsWith('http://')) {
      return base.replaceFirst('http://', 'ws://') + '/ws';
    }
    const fallback = 'ws://localhost:8000/ws';
    try {
      final url = dotenv.env['WEBSOCKET_URL'];
      return url?.isNotEmpty == true ? url! : fallback;
    } catch (_) {
      return fallback;
    }
  }
}