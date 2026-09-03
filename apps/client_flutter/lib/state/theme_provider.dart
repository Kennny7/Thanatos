// Thanatos/apps/client_flutter/lib/state/theme_provider.dart

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../ui/theme/app_theme.dart';

class ThemeNotifier extends StateNotifier<AppThemeMode> {
  ThemeNotifier() : super(AppThemeMode.tronLegacy);

  void setTheme(AppThemeMode mode) {
    state = mode;
  }
}

final themeProvider = StateNotifierProvider<ThemeNotifier, AppThemeMode>((ref) {
  return ThemeNotifier();
});
