// Thanatos/apps/client_flutter/lib/ui/theme/app_theme.dart

import 'package:flutter/material.dart';

enum AppThemeMode {
  tronLegacy,
  cyberpunkAmber,
  deepMatrix,
  obsidianPurple,
}

class AppTheme {
  static ThemeData getTheme(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.tronLegacy:
        return _tronLegacyTheme;
      case AppThemeMode.cyberpunkAmber:
        return _cyberpunkAmberTheme;
      case AppThemeMode.deepMatrix:
        return _deepMatrixTheme;
      case AppThemeMode.obsidianPurple:
        return _obsidianPurpleTheme;
    }
  }

  static Color getPrimaryAccent(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.tronLegacy:
        return const Color(0xFF00F0FF); // Neon Tron Cyan
      case AppThemeMode.cyberpunkAmber:
        return const Color(0xFFFF9E00); // High Voltage Amber
      case AppThemeMode.deepMatrix:
        return const Color(0xFF00FF66); // Terminal Matrix Green
      case AppThemeMode.obsidianPurple:
        return const Color(0xFF9D4EDD); // Violet Cyber Glow
    }
  }

  static Color getSecondaryAccent(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.tronLegacy:
        return const Color(0xFFFF6200); // Tron Disc Orange
      case AppThemeMode.cyberpunkAmber:
        return const Color(0xFFFF0055); // Neon Red/Magenta
      case AppThemeMode.deepMatrix:
        return const Color(0xFF008F11); // Darker Phosphor Green
      case AppThemeMode.obsidianPurple:
        return const Color(0xFF00B4D8); // Cyan Accent
    }
  }

  static Color getSurfaceColor(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.tronLegacy:
        return const Color(0xFF050B14);
      case AppThemeMode.cyberpunkAmber:
        return const Color(0xFF140D05);
      case AppThemeMode.deepMatrix:
        return const Color(0xFF051008);
      case AppThemeMode.obsidianPurple:
        return const Color(0xFF0F0A1C);
    }
  }

  static Color getBackgroundColor(AppThemeMode mode) {
    switch (mode) {
      case AppThemeMode.tronLegacy:
        return const Color(0xFF000205); // True deep pitch black with subtle blue cast
      case AppThemeMode.cyberpunkAmber:
        return const Color(0xFF080500);
      case AppThemeMode.deepMatrix:
        return const Color(0xFF000502);
      case AppThemeMode.obsidianPurple:
        return const Color(0xFF06030B);
    }
  }

  // --- Theme 1: TRON LEGACY (Minimalist pitch black with vector glow lines) ---
  static final ThemeData _tronLegacyTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: const Color(0xFF000205),
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF00F0FF),
      secondary: Color(0xFFFF6200),
      surface: Color(0xFF050B14),
      onPrimary: Colors.black,
      onSurface: Color(0xFFE0F7FA),
    ),
    fontFamily: 'Courier',
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF050B14),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: Color(0xFF00F0FF),
        fontSize: 16,
        fontWeight: FontWeight.bold,
        letterSpacing: 2.0,
      ),
      iconTheme: IconThemeData(color: Color(0xFF00F0FF)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF050B14),
      elevation: 0,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0x6600F0FF), width: 1.0),
        borderRadius: BorderRadius.circular(4),
      ),
    ),
  );

  // --- Theme 2: CYBERPUNK AMBER (High-contrast industrial HUD) ---
  static final ThemeData _cyberpunkAmberTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: const Color(0xFF080500),
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFFFF9E00),
      secondary: Color(0xFFFF0055),
      surface: Color(0xFF140D05),
      onPrimary: Colors.black,
      onSurface: Color(0xFFFFE8D6),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF140D05),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: Color(0xFFFF9E00),
        fontSize: 16,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.5,
      ),
      iconTheme: IconThemeData(color: Color(0xFFFF9E00)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF140D05),
      elevation: 0,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0x66FF9E00), width: 1.0),
        borderRadius: BorderRadius.circular(6),
      ),
    ),
  );

  // --- Theme 3: DEEP MATRIX (Cyber terminal phosphor style) ---
  static final ThemeData _deepMatrixTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: const Color(0xFF000502),
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF00FF66),
      secondary: Color(0xFF008F11),
      surface: Color(0xFF051008),
      onPrimary: Colors.black,
      onSurface: Color(0xFFD8F3DC),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF051008),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: Color(0xFF00FF66),
        fontSize: 16,
        fontWeight: FontWeight.bold,
        letterSpacing: 2.0,
      ),
      iconTheme: IconThemeData(color: Color(0xFF00FF66)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF051008),
      elevation: 0,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0x5500FF66), width: 1.0),
        borderRadius: BorderRadius.circular(4),
      ),
    ),
  );

  // --- Theme 4: OBSIDIAN PURPLE (Deep cosmic synthetic vibe) ---
  static final ThemeData _obsidianPurpleTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: const Color(0xFF06030B),
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF9D4EDD),
      secondary: Color(0xFF00B4D8),
      surface: Color(0xFF0F0A1C),
      onPrimary: Colors.white,
      onSurface: Color(0xFFF3EAFF),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF0F0A1C),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: Color(0xFFC77DFF),
        fontSize: 16,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
      ),
      iconTheme: IconThemeData(color: Color(0xFFC77DFF)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF0F0A1C),
      elevation: 0,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0x559D4EDD), width: 1.0),
        borderRadius: BorderRadius.circular(10),
      ),
    ),
  );
}
