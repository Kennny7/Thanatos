// Thanatos/apps/client_flutter/lib/ui/screens/settings_screen.dart

import 'package:flutter/material.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _selectedProvider = 'ollama';
  String _selectedModel = 'qwen2.5:7b';
  final _serverUrlController = TextEditingController(text: 'http://localhost:8000');
  final _ollamaUrlController = TextEditingController(text: 'http://localhost:11434');
  double _temperature = 0.1;

  final List<String> _models = [
    'qwen2.5:7b',
    'llama3.1:8b',
    'deepseek-r1:7b',
    'deepseek-r1:14b',
    'deepseek-r1:32b',
    'phi3:latest',
    'deepseek-chat',
  ];

  @override
  void dispose() {
    _serverUrlController.dispose();
    _ollamaUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings & Model Configuration'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSectionHeader('LLM Model & Hardware Profile'),
          Card(
            color: const Color(0xFF1E1E2E),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Active LLM Provider', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<String>(
                    value: _selectedProvider,
                    dropdownColor: const Color(0xFF2E2E3E),
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    items: const [
                      DropdownMenuItem(value: 'ollama', child: Text('Ollama Local (7B/14B/30B)')),
                      DropdownMenuItem(value: 'deepseek', child: Text('DeepSeek API (Cloud)')),
                      DropdownMenuItem(value: 'openai', child: Text('OpenAI Compatible')),
                    ],
                    onChanged: (val) => setState(() => _selectedProvider = val ?? 'ollama'),
                  ),
                  const SizedBox(height: 16),
                  const Text('Model Selection', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<String>(
                    value: _selectedModel,
                    dropdownColor: const Color(0xFF2E2E3E),
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    items: _models.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                    onChanged: (val) => setState(() => _selectedModel = val ?? 'qwen2.5:7b'),
                  ),
                  const SizedBox(height: 16),
                  Text('Temperature: ${_temperature.toStringAsFixed(2)}', style: const TextStyle(color: Colors.white70)),
                  Slider(
                    value: _temperature,
                    min: 0.0,
                    max: 1.0,
                    divisions: 10,
                    activeColor: const Color(0xFF6C63FF),
                    onChanged: (v) => setState(() => _temperature = v),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('Server & Endpoints'),
          Card(
            color: const Color(0xFF1E1E2E),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  TextField(
                    controller: _serverUrlController,
                    decoration: const InputDecoration(
                      labelText: 'Thanatos API Server URL',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.cloud),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _ollamaUrlController,
                    decoration: const InputDecoration(
                      labelText: 'Ollama Endpoint URL',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.computer),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('Voice & Speaker Diarization'),
          Card(
            color: const Color(0xFF1E1E2E),
            child: ListTile(
              leading: const Icon(Icons.record_voice_over, color: Color(0xFF6C63FF)),
              title: const Text('Owner Voice Profile', style: TextStyle(color: Colors.white)),
              subtitle: const Text('Enrolled — "Owner (You)" recognized with AEC', style: TextStyle(color: Colors.white54, fontSize: 12)),
              trailing: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF6C63FF)),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Voice enrollment ready! Record a 5-sec voice sample.')),
                  );
                },
                child: const Text('Re-Enroll', style: TextStyle(color: Colors.white)),
              ),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF6C63FF),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Configuration saved! Active Model: $_selectedModel')),
              );
              Navigator.of(context).pop();
            },
            child: const Text('Save Changes', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(color: Color(0xFF6C63FF), fontSize: 14, fontWeight: FontWeight.bold),
      ),
    );
  }
}
