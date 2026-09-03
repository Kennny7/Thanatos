// Entry point with dynamic futuristic theming and Riverpod state management.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'state/theme_provider.dart';
import 'ui/theme/app_theme.dart';
import 'ui/screens/chat_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await dotenv.load(fileName: ".env");
  } catch (_) {
    // Graceful fallback if .env is missing in current path
  }
  runApp(const ProviderScope(child: ThanatosApp()));
}

class ThanatosApp extends ConsumerWidget {
  const ThanatosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activeThemeMode = ref.watch(themeProvider);
    final themeData = AppTheme.getTheme(activeThemeMode);

    return MaterialApp(
      title: 'Thanatos',
      debugShowCheckedModeBanner: false,
      theme: themeData,
      darkTheme: themeData,
      themeMode: ThemeMode.dark,
      home: const ChatScreen(),
    );
  }
}