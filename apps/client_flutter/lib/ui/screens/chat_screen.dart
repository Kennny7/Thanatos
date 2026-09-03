// Thanatos/apps/client_flutter/lib/ui/screens/chat_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../services/model_service.dart';
import '../../state/chat_provider.dart';
import '../../state/theme_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/chat_bubble.dart';
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

  @override
  void initState() {
    super.initState();
    _fetchAssistantName();
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

  Future<void> _fetchAssistantName() async {
    final cfg = await _modelService.getCurrentConfig();
    if (cfg != null && cfg['assistant_name'] != null && mounted) {
      setState(() {
        _assistantName = cfg['assistant_name'].toString().toUpperCase();
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
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: primaryAccent,
                boxShadow: [
                  BoxShadow(color: primaryAccent.withOpacity(0.8), blurRadius: 6, spreadRadius: 2),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text('THANATOS // $_assistantName'),
          ],
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.tune, color: primaryAccent),
            tooltip: 'System, Model & Theme Settings',
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
              _fetchAssistantName();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // Background TRON wireframe grid overlay
          Positioned.fill(
            child: CustomPaint(
              painter: _TronGridPainter(accentColor: primaryAccent.withOpacity(0.06)),
            ),
          ),
          Column(
            children: [
              if (state.activeAgent != null && state.agentStatusText != null)
                AgentStatusTracker(
                  agentName: state.activeAgent!,
                  statusText: state.agentStatusText!,
                  progress: state.agentProgress,
                ),
              Expanded(
                child: state.messages.isEmpty
                    ? Center(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              AISpeakingIndicator(
                                size: 140,
                                glowColor: primaryAccent,
                                isResponding: state.isAiResponding,
                              ),
                              const SizedBox(height: 20),
                              Text(
                                '$_assistantName AUTONOMOUS CORE',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 2.0,
                                  fontFamily: 'Courier',
                                ),
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Personal AI Assistant with Continuous Memory & Dynamic Model Orchestration',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.white54, fontSize: 12),
                              ),
                              const SizedBox(height: 24),
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                alignment: WrapAlignment.center,
                                children: [
                                  _buildQuickChip('Deconstruct a complex idea', primaryAccent),
                                  _buildQuickChip('Automate OS workflow', primaryAccent),
                                  _buildQuickChip('Remember my preferences', primaryAccent),
                                  _buildQuickChip('Code / Architecture review', primaryAccent),
                                ],
                              ),
                            ],
                          ),
                        ),
                      )
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        itemCount: state.messages.length,
                        itemBuilder: (context, idx) {
                          return ChatBubble(message: state.messages[idx]);
                        },
                      ),
              ),
              _buildInputBar(surfaceColor, primaryAccent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickChip(String label, Color accent) {
    return ActionChip(
      label: Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      backgroundColor: Colors.white.withOpacity(0.04),
      side: BorderSide(color: accent.withOpacity(0.3), width: 0.8),
      onPressed: () {
        _textController.text = label;
      },
    );
  }

  Widget _buildInputBar(Color surfaceColor, Color primaryAccent) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: surfaceColor,
        border: Border(
          top: BorderSide(color: primaryAccent.withOpacity(0.3), width: 1.0),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            IconButton(
              icon: Icon(Icons.mic, color: primaryAccent),
              tooltip: 'Voice Input with Echo Cancellation & Diarization',
              onPressed: _openVoiceOverlay,
            ),
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: InputDecoration(
                  hintText: 'Transmit command or query to $_assistantName...',
                  border: InputBorder.none,
                  hintStyle: const TextStyle(color: Colors.white30, fontSize: 13),
                ),
                style: const TextStyle(color: Colors.white, fontSize: 14),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            IconButton(
              icon: Icon(Icons.send, color: primaryAccent),
              tooltip: 'Send Transmission',
              onPressed: _sendMessage,
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
