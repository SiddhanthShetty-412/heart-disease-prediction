import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

const String _defaultApiUrl = 'http://127.0.0.1:8000/api/predict/';

String getApiUrl() {
  const String envUrl = String.fromEnvironment('API_URL');
  if (envUrl.isNotEmpty) {
    return envUrl;
  }

  if (kIsWeb) {
    final Uri base = Uri.base;
    if (base.host != 'localhost' && base.host != '127.0.0.1') {
      return '${base.scheme}://${base.host}:8000/api/predict/';
    }
  }

  return _defaultApiUrl;
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Heart Disease Prediction',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.red),
        useMaterial3: true,
      ),
      home: const PredictionForm(),
    );
  }
}

class PredictionForm extends StatefulWidget {
  const PredictionForm({super.key});

  @override
  State<PredictionForm> createState() => _PredictionFormState();
}

class _PredictionFormState extends State<PredictionForm> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, TextEditingController> _controllers = {};
  String _result = '';
  bool _isLoading = false;

  final List<Map<String, dynamic>> _fields = [
    {'name': 'age', 'label': 'Age', 'type': 'int', 'min': 1, 'max': 120},
    {'name': 'gender', 'label': 'Gender (0=Female, 1=Male)', 'type': 'int', 'min': 0, 'max': 1},
    {'name': 'chest_pain', 'label': 'Chest Pain Type (0-3)', 'type': 'int', 'min': 0, 'max': 3},
    {'name': 'rest_bps', 'label': 'Resting Blood Pressure', 'type': 'int', 'min': 50, 'max': 300},
    {'name': 'cholestrol', 'label': 'Cholesterol', 'type': 'int', 'min': 100, 'max': 600},
    {'name': 'fasting_blood_sugar', 'label': 'Fasting Blood Sugar (0=No, 1=Yes)', 'type': 'int', 'min': 0, 'max': 1},
    {'name': 'rest_ecg', 'label': 'Rest ECG (0-2)', 'type': 'int', 'min': 0, 'max': 2},
    {'name': 'thalach', 'label': 'Max Heart Rate', 'type': 'int', 'min': 60, 'max': 250},
    {'name': 'exer_angina', 'label': 'Exercise Angina (0=No, 1=Yes)', 'type': 'int', 'min': 0, 'max': 1},
    {'name': 'old_peak', 'label': 'Old Peak', 'type': 'double', 'min': 0.0, 'max': 10.0},
    {'name': 'slope', 'label': 'Slope (0-2)', 'type': 'int', 'min': 0, 'max': 2},
    {'name': 'ca', 'label': 'CA (0-4)', 'type': 'int', 'min': 0, 'max': 4},
    {'name': 'thalassemia', 'label': 'Thalassemia (0-7)', 'type': 'int', 'min': 0, 'max': 7},
  ];

  @override
  void initState() {
    super.initState();
    for (var field in _fields) {
      _controllers[field['name']] = TextEditingController();
    }
  }

  @override
  void dispose() {
    for (var controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _result = '';
    });

    final data = <String, dynamic>{};
    for (var field in _fields) {
      final value = _controllers[field['name']]!.text;
      if (field['type'] == 'int') {
        data[field['name']] = int.parse(value);
      } else {
        data[field['name']] = double.parse(value);
      }
    }

    try {
      final response = await http.post(
        Uri.parse(getApiUrl()),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(data),
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        setState(() {
          _result = 'Prediction: ${result['prediction']}\nProbability: ${(result['probability'] * 100).toStringAsFixed(2)}%';
        });
      } else {
        setState(() {
          _result = 'Error: ${response.statusCode} - ${response.body}';
        });
      }
    } catch (e) {
      setState(() {
        _result = 'Error: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Heart Disease Prediction'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              Expanded(
                child: ListView(
                  children: _fields.map((field) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: TextFormField(
                        controller: _controllers[field['name']],
                        decoration: InputDecoration(
                          labelText: field['label'],
                          border: const OutlineInputBorder(),
                        ),
                        keyboardType: field['type'] == 'int' ? TextInputType.number : TextInputType.numberWithOptions(decimal: true),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter ${field['label']}';
                          }
                          final numValue = field['type'] == 'int' ? int.tryParse(value) : double.tryParse(value);
                          if (numValue == null) {
                            return 'Please enter a valid number';
                          }
                          if (numValue < field['min'] || numValue > field['max']) {
                            return 'Value must be between ${field['min']} and ${field['max']}';
                          }
                          return null;
                        },
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _isLoading ? null : _submitForm,
                child: _isLoading ? const CircularProgressIndicator() : const Text('Predict'),
              ),
              const SizedBox(height: 16),
              Text(
                _result,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
