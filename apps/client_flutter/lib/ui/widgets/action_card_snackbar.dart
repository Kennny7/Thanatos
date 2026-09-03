// A floating tactical HUD alert ribbon for action tool calls and system alerts.

import 'package:flutter/material.dart';

void showActionSnackbar(BuildContext context, String message, VoidCallback onDismiss) {
  final theme = Theme.of(context);
  final accent = theme.colorScheme.primary;

  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      backgroundColor: const Color(0xFF030508).withValues(alpha: 0.95),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: accent, width: 1.0),
        borderRadius: BorderRadius.circular(2),
      ),
      duration: const Duration(seconds: 4),
      content: Row(
        children: [
          Icon(Icons.terminal, color: accent, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontFamily: 'Courier',
                letterSpacing: 0.5,
              ),
            ),
          ),
        ],
      ),
      action: SnackBarAction(
        label: '[ACK]',
        textColor: accent,
        onPressed: onDismiss,
      ),
    ),
  );
}