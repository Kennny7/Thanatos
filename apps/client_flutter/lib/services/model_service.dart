// Thanatos/apps/client_flutter/lib/services/model_service.dart

import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class HardwareSpec {
  final String os;
  final int cpuCount;
  final double totalRamGb;
  final double availableRamGb;
  final bool hasGpu;
  final List<dynamic> gpus;

  HardwareSpec({
    required this.os,
    required this.cpuCount,
    required this.totalRamGb,
    required this.availableRamGb,
    required this.hasGpu,
    required this.gpus,
  });

  factory HardwareSpec.fromJson(Map<String, dynamic> json) {
    return HardwareSpec(
      os: json['os'] ?? 'Unknown',
      cpuCount: json['cpu_count'] ?? 4,
      totalRamGb: (json['total_ram_gb'] as num?)?.toDouble() ?? 8.0,
      availableRamGb: (json['available_ram_gb'] as num?)?.toDouble() ?? 4.0,
      hasGpu: json['has_gpu'] ?? false,
      gpus: json['gpus'] ?? [],
    );
  }
}

class ModelRecommendation {
  final String taskType;
  final String recommendedModel;
  final String reason;
  final String confirmationMessage;
  final bool promptUserConfirmation;

  ModelRecommendation({
    required this.taskType,
    required this.recommendedModel,
    required this.reason,
    required this.confirmationMessage,
    required this.promptUserConfirmation,
  });

  factory ModelRecommendation.fromJson(Map<String, dynamic> json) {
    return ModelRecommendation(
      taskType: json['task_type'] ?? 'general',
      recommendedModel: json['recommended_model'] ?? 'qwen2.5:7b',
      reason: json['reason'] ?? '',
      confirmationMessage: json['confirmation_message'] ?? '',
      promptUserConfirmation: json['prompt_user_confirmation'] ?? true,
    );
  }
}

class ModelService {
  final String baseUrl;

  ModelService({String? baseUrl})
      : baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  /// Fetch list of models currently installed in local Ollama daemon
  Future<List<String>> fetchInstalledOllamaModels() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/config/ollama/tags')).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        final list = data['models'] as List?;
        if (list != null && list.isNotEmpty) {
          return list.map((e) => e.toString()).toList();
        }
      }
    } catch (_) {}
    return ['qwen2.5:7b', 'llama3.1:8b', 'deepseek-r1:7b', 'deepseek-r1:14b', 'phi3:latest'];
  }

  /// Query host hardware specifications
  Future<HardwareSpec?> getHardwareSpecs() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/config/hardware-spec')).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        return HardwareSpec.fromJson(json.decode(res.body));
      }
    } catch (_) {}
    return null;
  }

  /// Request task & hardware-informed model recommendation
  Future<ModelRecommendation?> getRecommendation(String taskType) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/api/config/recommend-model'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'task_type': taskType}),
      ).timeout(const Duration(seconds: 5));

      if (res.statusCode == 200) {
        return ModelRecommendation.fromJson(json.decode(res.body));
      }
    } catch (_) {}
    return null;
  }

  /// Pull a new model from Ollama library with streaming progress callback
  Stream<String> pullModel(String modelName) async* {
    final client = http.Client();
    try {
      final request = http.Request('POST', Uri.parse('$baseUrl/api/config/ollama/pull'));
      request.headers['Content-Type'] = 'application/json';
      request.body = json.encode({'model': modelName});

      final response = await client.send(request);
      final lines = response.stream.toStringStream().transform(const LineSplitter());

      await for (final line in lines) {
        if (line.startsWith('data: ')) {
          final jsonStr = line.substring(6).trim();
          try {
            final data = json.decode(jsonStr);
            if (data['status'] != null) {
              final status = data['status'];
              final completed = data['completed'];
              final total = data['total'];
              if (completed != null && total != null && total > 0) {
                final pct = ((completed / total) * 100).toStringAsFixed(1);
                yield '$status ($pct%)';
              } else {
                yield status;
              }
            }
          } catch (_) {
            yield line;
          }
        }
      }
    } finally {
      client.close();
    }
  }

  /// Update active LLM configuration
  Future<bool> updateConfig({
    required String provider,
    required String model,
    required double temperature,
    String? assistantName,
    String? userName,
  }) async {
    try {
      final payload = {
        'provider': provider,
        'model': model,
        'temperature': temperature,
        if (assistantName != null) 'assistant_name': assistantName,
        if (userName != null) 'user_name': userName,
      };
      final res = await http.post(
        Uri.parse('$baseUrl/api/config/llm'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 4));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Fetch active assistant persona and configuration
  Future<Map<String, dynamic>?> getCurrentConfig() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/config')).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        return json.decode(res.body);
      }
    } catch (_) {}
    return null;
  }
}
