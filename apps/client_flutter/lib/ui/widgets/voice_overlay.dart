// Thanatos/apps/client_flutter/lib/ui/widgets/voice_overlay.dart

import 'package:flutter/material.dart';

class VoiceOverlayDialog extends StatefulWidget {
  final Function(String transcript, String speakerTag) onTranscriptionComplete;

  const VoiceOverlayDialog({super.key, required this.onTranscriptionComplete});

  @override
  State<VoiceOverlayDialog> createState() => _VoiceOverlayDialogState();
}

class _VoiceOverlayDialogState extends State<VoiceOverlayDialog> with SingleTickerProviderStateMixin {
  bool isListening = true;
  String currentSpeaker = "Owner (You)";
  bool aecActive = true;
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF1E1E2E),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Voice Intelligence',
                  style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green, width: 0.8),
                  ),
                  child: const Text('AEC Active', style: TextStyle(color: Colors.greenAccent, fontSize: 11)),
                )
              ],
            ),
            const SizedBox(height: 28),
            AnimatedBuilder(
              animation: _animController,
              builder: (context, child) {
                return Container(
                  width: 90 + (_animController.value * 20),
                  height: 90 + (_animController.value * 20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF6C63FF).withOpacity(0.2),
                    border: Border.all(color: const Color(0xFF6C63FF), width: 2),
                  ),
                  child: const Icon(Icons.mic, color: Color(0xFF6C63FF), size: 44),
                );
              },
            ),
            const SizedBox(height: 20),
            Text(
              isListening ? 'Listening with AEC & Diarization...' : 'Processing audio...',
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
            const SizedBox(height: 12),
            Chip(
              avatar: const Icon(Icons.person, size: 16, color: Colors.white),
              label: Text(currentSpeaker, style: const TextStyle(color: Colors.white, fontSize: 12)),
              backgroundColor: const Color(0xFF2E2E3E),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel', style: TextStyle(color: Colors.white60)),
                ),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6C63FF),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () {
                    Navigator.of(context).pop();
                    widget.onTranscriptionComplete("Search for freshers jobs in Pune and apply", "Owner (You)");
                  },
                  icon: const Icon(Icons.send, size: 16),
                  label: const Text('Process Voice'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
