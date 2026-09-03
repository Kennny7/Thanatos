// Thanatos/apps/client_flutter/lib/ui/screens/chat_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../services/model_service.dart';
import '../../state/chat_provider.dart';
import '../../state/theme_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/holo_stream_entry.dart';
import '../widgets/holo_panel.dart';
import '../widgets/action_card_snackbar.dart';
import '../widgets/ai_speaking_indicator.dart';
import '../widgets/agent_status_tracker.dart';
import '../widgets/voice_overlay.dart';
import 'settings_screen.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  final _modelService = ModelService();
  String _assistantName = 'AEGIS';
  String _activeModel = 'qwen2.5:7b';
  String _activeMode = 'AUTONOMOUS';

  @override
  void initState() {
    super.initState();
    _fetchSystemInfo();
    ref.listenManual(chatProvider.select((s) => s.toolUpdateMessage), (prev, next) {
      if (next != null) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          showActionSnackbar(context, next, () {
            ref.read(chatProvider.notifier).clearToolUpdate();
          });
        });
      }
    });
  }

  Future<void> _fetchSystemInfo() async {
    final cfg = await _modelService.getCurrentConfig();
    if (cfg != null && mounted) {
      setState(() {
        if (cfg['assistant_name'] != null) {
          _assistantName = cfg['assistant_name'].toString().toUpperCase();
        }
        if (cfg['model'] != null) {
          _activeModel = cfg['model'].toString();
        }
      });
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    ref.read(chatProvider.notifier).sendTextMessage(text);
    _textController.clear();
    _scrollToBottom();
  }

  void _openVoiceOverlay() {
    showDialog(
      context: context,
      builder: (ctx) => VoiceOverlayDialog(
        onTranscriptionComplete: (transcript, speakerTag) {
          ref.read(chatProvider.notifier).sendTextMessage(transcript, speakerTag: speakerTag);
          _scrollToBottom();
        },
      ),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatProvider);
    final activeThemeMode = ref.watch(themeProvider);
    final primaryAccent = AppTheme.getPrimaryAccent(activeThemeMode);
    final surfaceColor = AppTheme.getSurfaceColor(activeThemeMode);
    final bgColor = AppTheme.getBackgroundColor(activeThemeMode);

    return Scaffold(
      backgroundColor: bgColor,
      body: Stack(
        children: [
          // Background TRON wireframe grid overlay
          Positioned.fill(
            child: CustomPaint(
              painter: _TronGridPainter(accentColor: primaryAccent.withValues(alpha: 0.05)),
            ),
          ),
          SafeArea(
            child: Column(
              children: [
                // 1. Tactical HUD Header Bar (Tony Stark Command Strip)
                _buildTacticalHudHeader(primaryAccent, surfaceColor),

                // 2. Persistent AI Core & Diagnostic Status Bar
                _buildPersistentAiCoreStrip(state, primaryAccent, surfaceColor),

                if (state.activeAgent != null && state.agentStatusText != null)
                  AgentStatusTracker(
                    agentName: state.activeAgent!,
                    statusText: state.agentStatusText!,
                    progress: state.agentProgress,
                  ),

                // 3. Holographic Stream Viewport
                Expanded(
                  child: state.messages.isEmpty
                      ? _buildEmptyStateHologram(primaryAccent)
                      : ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          itemCount: state.messages.length,
                          itemBuilder: (context, idx) {
                            return HoloStreamEntry(
                              message: state.messages[idx],
                              accentColor: primaryAccent,
                              surfaceColor: surfaceColor,
                            );
                          },
                        ),
                ),

                // 4. Futuristic Command Deck Input Terminal
                _buildCommandDeckInput(surfaceColor, primaryAccent, state.isAiResponding),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTacticalHudHeader(Color primaryAccent, Color surfaceColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: surfaceColor.withValues(alpha: 0.9),
        border: Border(
          bottom: BorderSide(color: primaryAccent.withValues(alpha: 0.3), width: 1.0),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: primaryAccent,
                  boxShadow: [
                    BoxShadow(color: primaryAccent.withValues(alpha: 0.8), blurRadius: 6, spreadRadius: 2),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Text(
                'THANATOS // $_assistantName',
                style: TextStyle(
                  color: primaryAccent,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2.0,
                  fontFamily: 'Courier',
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  border: Border.all(color: primaryAccent.withValues(alpha: 0.4)),
                  borderRadius: BorderRadius.circular(2),
                ),
                child: Text(
                  'LINK: ONLINE',
                  style: TextStyle(color: primaryAccent.withValues(alpha: 0.8), fontSize: 9, fontFamily: 'Courier'),
                ),
              ),
            ],
          ),
          Row(
            children: [
              Text(
                '[$_activeModel]',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.6), fontSize: 11, fontFamily: 'Courier'),
              ),
              const SizedBox(width: 10),
              IconButton(
                icon: Icon(Icons.tune, color: primaryAccent, size: 20),
                tooltip: 'Holographic & Model Matrix Settings',
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const SettingsScreen()),
                  );
                  _fetchSystemInfo();
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPersistentAiCoreStrip(ChatState state, Color primaryAccent, Color surfaceColor) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: surfaceColor.withValues(alpha: 0.4),
        border: Border.all(color: primaryAccent.withValues(alpha: 0.15)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          // Persistent Floating Fibonacci Core (Compact 48px)
          AISpeakingIndicator(
            size: 48,
            glowColor: primaryAccent,
            isResponding: state.isAiResponding,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'NEURAL CORE STATUS',
                      style: TextStyle(color: primaryAccent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.2, fontFamily: 'Courier'),
                    ),
                    Text(
                      state.isAiResponding ? 'PROCESSING...' : 'STANDBY // READY',
                      style: TextStyle(
                        color: state.isAiResponding ? primaryAccent : Colors.white54,
                        fontSize: 9,
                        fontFamily: 'Courier',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(1),
                  child: LinearProgressIndicator(
                    value: state.isAiResponding ? null : 1.0,
                    backgroundColor: Colors.white.withValues(alpha: 0.05),
                    valueColor: AlwaysStoppedAnimation<Color>(primaryAccent.withValues(alpha: 0.7)),
                    minHeight: 2,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyStateHologram(Color primaryAccent) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AISpeakingIndicator(
              size: 160,
              glowColor: primaryAccent,
              isResponding: false,
            ),
            const SizedBox(height: 24),
            Text(
              '$_assistantName HOLOGRAPHIC TERMINAL',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
                letterSpacing: 2.2,
                fontFamily: 'Courier',
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Autonomous Personal AI Engine • Multi-Agent Orchestration • Continuous Hybrid Memory',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 11.5, letterSpacing: 0.6),
            ),
            const SizedBox(height: 24),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _buildModeButton('AUTONOMOUS', primaryAccent),
                _buildModeButton('DEEP REASONING', primaryAccent),
                _buildModeButton('TERMINAL CODE', primaryAccent),
                _buildModeButton('MEMORY SYNC', primaryAccent),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModeButton(String label, Color primaryAccent) {
    final isSelected = _activeMode == label;
    return GestureDetector(
      onTap: () => setState(() => _activeMode = label),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? primaryAccent.withValues(alpha: 0.2) : Colors.white.withValues(alpha: 0.03),
          border: Border.all(
            color: isSelected ? primaryAccent : primaryAccent.withValues(alpha: 0.3),
            width: 1.0,
          ),
          borderRadius: BorderRadius.circular(2),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? primaryAccent : Colors.white70,
            fontSize: 10.5,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
            fontFamily: 'Courier',
          ),
        ),
      ),
    );
  }

  Widget _buildCommandDeckInput(Color surfaceColor, Color primaryAccent, bool isBusy) {
    return Container(
      margin: const EdgeInsets.all(12),
      child: HoloPanel(
        accentColor: primaryAccent,
        surfaceColor: surfaceColor.withValues(alpha: 0.95),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        chamferSize: 8.0,
        child: Row(
          children: [
            // Voice Input with Tactical Icon
            IconButton(
              icon: Icon(Icons.mic, color: primaryAccent, size: 22),
              tooltip: 'Acoustic Voice Intelligence',
              onPressed: _openVoiceOverlay,
            ),
            const SizedBox(width: 4),
            // Futuristic Monospace Input Field
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: InputDecoration(
                  hintText: 'Transmit directive to $_assistantName... [$_activeMode]',
                  border: InputBorder.none,
                  hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3), fontSize: 12.5, fontFamily: 'Courier'),
                ),
                style: const TextStyle(color: Colors.white, fontSize: 13.5, fontFamily: 'Courier'),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            // Send Transmission HUD Button
            IconButton(
              icon: Icon(Icons.bolt, color: primaryAccent, size: 24),
              tooltip: 'Transmit Directive',
              onPressed: isBusy ? null : _sendMessage,
            ),
          ],
        ),
      ),
    );
  }
}

class _TronGridPainter extends CustomPainter {
  final Color accentColor;
  _TronGridPainter({required this.accentColor});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = accentColor
      ..strokeWidth = 0.6;

    const step = 36.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(_TronGridPainter oldDelegate) => false;
}
