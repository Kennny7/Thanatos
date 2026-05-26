// Wraps the speech_to_text package for cross‑platform voice recognition.

import 'dart:async';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:speech_to_text/speech_recognition_result.dart';

/// Service to handle voice input and convert to text.
class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;
  bool _isListening = false;

//  final _textController = StreamController<String>.broadcast();
//  final _statusController = StreamController<SpeechStatus>.broadcast();
    final _textController = StreamController<String>.broadcast();
    final _statusController = StreamController<SpeechStatus>.broadcast();
    final _errorController = StreamController<String>.broadcast();

//   Stream<String> get onText => _textController.stream;
//   Stream<SpeechStatus> get onStatus => _statusController.stream;
    Stream<String> get onText => _textController.stream;
    Stream<SpeechStatus> get onStatus => _statusController.stream;
    Stream<String> get onError => _errorController.stream;


  bool get isListening => _isListening;
  bool get isAvailable => _speech.isAvailable;

  /// Initialize speech recognizer (call once).
  Future<bool> initialize() async {
    if (_isInitialized) return true;
    _isInitialized = await _speech.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          _isListening = false;
          _statusController.add(SpeechStatus.notListening);
        }
      },
      // onError: (error) => _statusController.add(SpeechStatus.error(error.errorMsg)),
      onError: (error) {
        _errorController.add(error.errorMsg);
        _statusController.add(SpeechStatus.error);
        _isListening = false;
        },
    );
    return _isInitialized;
  }

  /// Start listening. Returns immediately; results streamed via [onText].
  Future<void> startListening() async {
    if (!_isInitialized || _isListening) return;
    _isListening = true;
    _statusController.add(SpeechStatus.listening);

    await _speech.listen(
      onResult: (SpeechRecognitionResult result) {
        // Send partial and final transcripts
        if (result.finalResult) {
          _textController.add(result.recognizedWords);
          _isListening = false;
          _statusController.add(SpeechStatus.notListening);
        } else {
          // Only send if meaningful
          if (result.recognizedWords.isNotEmpty) {
            _textController.add(result.recognizedWords); // could be partial
          }
        }
      },
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 3),
      partialResults: true,
      localeId: 'en_US',
      cancelOnError: true,
      listenMode: stt.ListenMode.confirmation,
    );
  }

  /// Stop listening and finalize the recognized text.
  Future<void> stopListening() async {
    if (!_isListening) return;
    await _speech.stop();
    _isListening = false;
    _statusController.add(SpeechStatus.notListening);
  }

  /// Cancel listening without finalizing.
  Future<void> cancelListening() async {
    await _speech.cancel();
    _isListening = false;
    _statusController.add(SpeechStatus.notListening);
  }

//   Future<void> dispose() async {
//     await cancelListening();
//     await _textController.close();
//     await _statusController.close();
//   }
    Future<void> dispose() async {
    await cancelListening();
    await _textController.close();
    await _statusController.close();
    await _errorController.close();
    }
}

enum SpeechStatus { listening, notListening, error }
extension SpeechStatusX on SpeechStatus {
  String get message {
    switch (this) {
      case SpeechStatus.listening:
        return 'Listening…';
      case SpeechStatus.notListening:
        return 'Tap mic to speak';
      case SpeechStatus.error:
        return 'Speech recognition error';
    }
  }
}