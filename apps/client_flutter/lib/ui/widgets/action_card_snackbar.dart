// A reusable Snackbar that shows tool updates with a dismiss action.

import 'package:flutter/material.dart';

void showActionSnackbar(BuildContext context, String message, VoidCallback onDismiss) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Row(
        children: [
          const Icon(Icons.build_circle, color: Colors.white),
          const SizedBox(width: 8),
          Expanded(child: Text(message, style: const TextStyle(color: Colors.white))),
        ],
      ),
      backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
      behavior: SnackBarBehavior.floating,
      duration: const Duration(seconds: 4),
      action: SnackBarAction(
        label: 'DISMISS',
        textColor: Theme.of(context).colorScheme.onSecondaryContainer,
        onPressed: onDismiss,
      ),
    ),
  );
}