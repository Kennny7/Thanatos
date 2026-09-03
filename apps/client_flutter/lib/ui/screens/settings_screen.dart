// Thanatos/apps/client_flutter/lib/ui/screens/settings_screen.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../services/model_service.dart';
import '../../state/theme_provider.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _modelService = ModelService();

  String _selectedProvider = 'ollama';
  String _selectedModel = 'qwen2.5:7b';
  final _serverUrlController = TextEditingController(text: 'http://localhost:8000');
  final _assistantNameController = TextEditingController(text: 'Aegis');
  final _pullModelController = TextEditingController();
  double _temperature = 0.2;

  List<String> _models = [
    'qwen2.5:7b',
    'llama3.1:8b',
    'deepseek-r1:7b',
    'deepseek-r1:14b',
    'phi3:latest',
  ];

  bool _isLoadingModels = false;
  bool _isPullingModel = false;
  String? _pullStatus;
  StreamSubscription? _pullSub;

  HardwareSpec? _hardwareSpec;
  String _selectedTaskType = 'general';

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoadingModels = true);
    final results = await Future.wait([
      _modelService.fetchInstalledOllamaModels(),
      _modelService.getHardwareSpecs(),
      _modelService.getCurrentConfig(),
    ]);

    final installed = results[0] as List<String>;
    final hw = results[1] as HardwareSpec?;
    final config = results[2] as Map<String, dynamic>?;

    setState(() {
      _isLoadingModels = false;
      if (installed.isNotEmpty) {
        _models = installed;
        if (!_models.contains(_selectedModel)) {
          _selectedModel = _models.first;
        }
      }
      _hardwareSpec = hw;
      if (config != null) {
        if (config['model'] != null) _selectedModel = config['model'];
        if (config['provider'] != null) _selectedProvider = config['provider'];
        if (config['assistant_name'] != null) {
          _assistantNameController.text = config['assistant_name'];
        }
        if (config['temperature'] != null) {
          _temperature = (config['temperature'] as num).toDouble();
        }
      }
    });
  }

  void _pullModel() {
    final modelName = _pullModelController.text.trim();
    if (modelName.isEmpty) return;

    setState(() {
      _isPullingModel = true;
      _pullStatus = 'Connecting to Ollama...';
    });

    _pullSub?.cancel();
    _pullSub = _modelService.pullModel(modelName).listen(
      (status) {
        setState(() => _pullStatus = status);
      },
      onError: (err) {
        setState(() {
          _isPullingModel = false;
          _pullStatus = 'Error pulling model: $err';
        });
      },
      onDone: () {
        setState(() {
          _isPullingModel = false;
          _pullStatus = 'Model $modelName pulled successfully!';
          if (!_models.contains(modelName)) {
            _models.add(modelName);
            _selectedModel = modelName;
          }
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Model $modelName is ready for use!')),
          );
        }
      },
    );
  }

  Future<void> _requestRecommendation() async {
    final rec = await _modelService.getRecommendation(_selectedTaskType);
    if (rec != null && mounted) {
      _showRecommendationDialog(rec);
    }
  }

  void _showRecommendationDialog(ModelRecommendation rec) {
    showDialog(
      context: context,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        final accent = theme.colorScheme.primary;
        return AlertDialog(
          backgroundColor: theme.cardTheme.color ?? const Color(0xFF050B14),
          shape: RoundedRectangleBorder(
            side: BorderSide(color: accent, width: 1.2),
            borderRadius: BorderRadius.circular(8),
          ),
          title: Text(
            'INTELLIGENT MODEL RECOMMENDATION',
            style: TextStyle(color: accent, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Recommended: ${rec.recommendedModel}',
                style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(rec.reason, style: const TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  rec.confirmationMessage,
                  style: TextStyle(color: accent.withOpacity(0.9), fontSize: 12),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: accent),
              onPressed: () {
                setState(() {
                  if (!_models.contains(rec.recommendedModel)) {
                    _models.insert(0, rec.recommendedModel);
                  }
                  _selectedModel = rec.recommendedModel;
                });
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Switched active model to ${rec.recommendedModel}')),
                );
              },
              child: const Text('Apply & Switch', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _serverUrlController.dispose();
    _assistantNameController.dispose();
    _pullModelController.dispose();
    _pullSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final activeThemeMode = ref.watch(themeProvider);
    final primaryAccent = AppTheme.getPrimaryAccent(activeThemeMode);
    final surfaceColor = AppTheme.getSurfaceColor(activeThemeMode);

    return Scaffold(
      appBar: AppBar(
        title: const Text('SYSTEM & HARDWARE CONFIGURATION'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Section 1: Futuristic Themes
          _buildSectionHeader('FUTURISTIC THEME ENGINE', primaryAccent),
          Card(
            color: surfaceColor,
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Select Visual Holographic Interface', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _buildThemeChip('TRON LEGACY', AppThemeMode.tronLegacy, const Color(0xFF00F0FF), activeThemeMode),
                      _buildThemeChip('CYBERPUNK AMBER', AppThemeMode.cyberpunkAmber, const Color(0xFFFF9E00), activeThemeMode),
                      _buildThemeChip('DEEP MATRIX', AppThemeMode.deepMatrix, const Color(0xFF00FF66), activeThemeMode),
                      _buildThemeChip('OBSIDIAN PURPLE', AppThemeMode.obsidianPurple, const Color(0xFF9D4EDD), activeThemeMode),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),

          // Section 2: Assistant Persona
          _buildSectionHeader('ASSISTANT PERSONA & IDENTITY', primaryAccent),
          Card(
            color: surfaceColor,
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _assistantNameController,
                    decoration: InputDecoration(
                      labelText: 'Assistant Name (Customizable)',
                      labelStyle: TextStyle(color: primaryAccent.withOpacity(0.8)),
                      hintText: 'e.g. Aegis, Thanatos, Jarvis, Athena',
                      prefixIcon: Icon(Icons.psychology, color: primaryAccent),
                      enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent.withOpacity(0.4))),
                      focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent)),
                    ),
                    style: const TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),

          // Section 3: LLM Model & Hardware Profile
          _buildSectionHeader('LOCAL & CLOUD LLM CONFIGURATION', primaryAccent),
          Card(
            color: surfaceColor,
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Dynamic Ollama Model Selection', style: TextStyle(color: Colors.white70, fontSize: 13)),
                      if (_isLoadingModels)
                        SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: primaryAccent))
                      else
                        IconButton(
                          icon: Icon(Icons.refresh, size: 18, color: primaryAccent),
                          tooltip: 'Refresh installed models',
                          onPressed: _loadInitialData,
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<String>(
                    value: _models.contains(_selectedModel) ? _selectedModel : (_models.isNotEmpty ? _models.first : null),
                    dropdownColor: surfaceColor,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent.withOpacity(0.4))),
                    ),
                    items: _models.map((m) => DropdownMenuItem(value: m, child: Text(m, style: const TextStyle(color: Colors.white)))).toList(),
                    onChanged: (val) => setState(() => _selectedModel = val ?? _selectedModel),
                  ),
                  const SizedBox(height: 16),

                  // Model Puller
                  const Text('Pull New Model from Ollama', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _pullModelController,
                          decoration: InputDecoration(
                            hintText: 'e.g. llama3.2:3b, qwen2.5-coder:7b',
                            hintStyle: const TextStyle(color: Colors.white30, fontSize: 13),
                            isDense: true,
                            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent.withOpacity(0.3))),
                            focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent)),
                          ),
                          style: const TextStyle(color: Colors.white, fontSize: 13),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: primaryAccent, padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12)),
                        onPressed: _isPullingModel ? null : _pullModel,
                        child: _isPullingModel
                            ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                            : const Text('Pull', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                  if (_pullStatus != null) ...[
                    const SizedBox(height: 8),
                    Text(_pullStatus!, style: TextStyle(color: primaryAccent, fontSize: 12, fontFamily: 'Courier')),
                  ],
                  const SizedBox(height: 16),

                  // Task Recommendation
                  const Text('Intelligent Model Recommender', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _selectedTaskType,
                          dropdownColor: surfaceColor,
                          decoration: InputDecoration(
                            isDense: true,
                            border: OutlineInputBorder(borderSide: BorderSide(color: primaryAccent.withOpacity(0.3))),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'general', child: Text('General Assistance', style: TextStyle(color: Colors.white, fontSize: 13))),
                            DropdownMenuItem(value: 'coding', child: Text('Software Engineering', style: TextStyle(color: Colors.white, fontSize: 13))),
                            DropdownMenuItem(value: 'reasoning', child: Text('Deep Reasoning & Math', style: TextStyle(color: Colors.white, fontSize: 13))),
                            DropdownMenuItem(value: 'fast_dialogue', child: Text('Fast Voice / Chat', style: TextStyle(color: Colors.white, fontSize: 13))),
                          ],
                          onChanged: (val) => setState(() => _selectedTaskType = val ?? 'general'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton(
                        style: OutlinedButton.styleFrom(side: BorderSide(color: primaryAccent)),
                        onPressed: _requestRecommendation,
                        child: Text('Recommend', style: TextStyle(color: primaryAccent, fontSize: 12)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  Text('Temperature: ${_temperature.toStringAsFixed(2)}', style: const TextStyle(color: Colors.white70)),
                  Slider(
                    value: _temperature,
                    min: 0.0,
                    max: 1.0,
                    divisions: 10,
                    activeColor: primaryAccent,
                    onChanged: (v) => setState(() => _temperature = v),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),

          // Section 4: Hardware Specs
          if (_hardwareSpec != null) ...[
            _buildSectionHeader('DETECTED HARDWARE METRICS', primaryAccent),
            Card(
              color: surfaceColor,
              child: Padding(
                padding: const EdgeInsets.all(14.0),
                child: Column(
                  children: [
                    _buildMetricRow('Operating System', '${_hardwareSpec!.os} (${_hardwareSpec!.cpuCount} Cores)', primaryAccent),
                    const Divider(color: Colors.white10),
                    _buildMetricRow('RAM Capacity', '${_hardwareSpec!.availableRamGb} GB Avail / ${_hardwareSpec!.totalRamGb} GB Total', primaryAccent),
                    const Divider(color: Colors.white10),
                    _buildMetricRow('Dedicated GPU', _hardwareSpec!.hasGpu ? (_hardwareSpec!.gpus.isNotEmpty ? '${_hardwareSpec!.gpus[0]["name"]} (${_hardwareSpec!.gpus[0]["vram_gb"]} GB VRAM)' : 'CUDA Active') : 'CPU Mode', primaryAccent),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 18),
          ],

          // Save button
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: primaryAccent,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
            ),
            onPressed: () async {
              final messenger = ScaffoldMessenger.of(context);
              final nav = Navigator.of(context);
              final asstName = _assistantNameController.text.trim();
              final ok = await _modelService.updateConfig(
                provider: _selectedProvider,
                model: _selectedModel,
                temperature: _temperature,
                assistantName: asstName,
              );
              messenger.showSnackBar(
                SnackBar(content: Text(ok ? 'Configuration saved! Persona: $asstName' : 'Saved locally')),
              );
              nav.pop();
            },
            child: const Text('APPLY & SAVE SETTINGS', style: TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, Color color) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        title,
        style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5, fontFamily: 'Courier'),
      ),
    );
  }

  Widget _buildThemeChip(String label, AppThemeMode mode, Color color, AppThemeMode currentMode) {
    final isSelected = mode == currentMode;
    return ChoiceChip(
      label: Text(label, style: TextStyle(color: isSelected ? Colors.black : Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
      selected: isSelected,
      selectedColor: color,
      backgroundColor: Colors.white.withOpacity(0.05),
      side: BorderSide(color: color.withOpacity(isSelected ? 1.0 : 0.4), width: 1.0),
      onSelected: (_) {
        ref.read(themeProvider.notifier).setTheme(mode);
      },
    );
  }

  Widget _buildMetricRow(String label, String value, Color accent) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white60, fontSize: 12)),
          Text(value, style: TextStyle(color: accent, fontSize: 12, fontWeight: FontWeight.bold, fontFamily: 'Courier')),
        ],
      ),
    );
  }
}
