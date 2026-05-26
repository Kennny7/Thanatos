// Entry point with flutter_dotenv loading and Material 3 theming.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'ui/screens/chat_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Load .env from assets (make sure it's declared in pubspec.yaml)
  await dotenv.load(fileName: ".env");
  runApp(const ProviderScope(child: ThanatosApp()));
}

class ThanatosApp extends StatelessWidget {
  const ThanatosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Thanatos',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF6C63FF),
        brightness: Brightness.dark,
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF6C63FF),
        brightness: Brightness.dark,
      ),
      themeMode: ThemeMode.dark,
      home: const ChatScreen(),
    );
  }
}