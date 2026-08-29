// Thanatos/apps/client_flutter/lib/ui/screens/chat_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../state/chat_provider.dart';
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

  @override
  void initState() {
    super.initState();
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

    return Scaffold(
      appBar: AppBar(
        title: const Text('Thanatos AI Assistant'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Model & System Settings',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: Column(
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
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AISpeakingIndicator(size: 110),
                        const SizedBox(height: 16),
                        const Text(
                          'Thanatos Autonomous Engine',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Ask to search jobs, tailor resumes, edit novels, or control tasks.',
                          style: TextStyle(color: Colors.white60, fontSize: 13),
                        ),
                      ],
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
          _buildInputBar(),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        color: Color(0xFF1E1E2E),
        border: Border(top: BorderSide(color: Colors.white10, width: 0.8)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.mic, color: Color(0xFF6C63FF)),
              tooltip: 'Voice Input with AEC & Diarization',
              onPressed: _openVoiceOverlay,
            ),
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: const InputDecoration(
                  hintText: 'Ask Thanatos anything...',
                  border: InputBorder.none,
                  hintStyle: TextStyle(color: Colors.white38),
                ),
                style: const TextStyle(color: Colors.white),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.send, color: Color(0xFF6C63FF)),
              onPressed: _sendMessage,
            ),
          ],
        ),
      ),
    );
  }
}
