import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../api/vigia_api.dart';
import '../widgets/alert_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final _api = VigiaApi();
  List<dynamic> _alerts = [];
  bool _isLoading = true;
  String _selectedFilter = 'ALL';

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() => _isLoading = true);
    try {
      final alerts = await _api.getAlerts(
        riskLevel: _selectedFilter == 'ALL' ? null : _selectedFilter,
      );
      setState(() {
        _alerts = alerts;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final redCount = _alerts.where((a) => a['risk_level'] == 'ROJO').length;
    final orangeCount = _alerts.where((a) => a['risk_level'] == 'NARANJA').length;
    final yellowCount = _alerts.where((a) => a['risk_level'] == 'AMARILLO').length;

    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      appBar: AppBar(
        title: const Text('VIGÍA - Centro de Monitoreo'),
        backgroundColor: const Color(0xFF1E1E1E),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAlerts,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              // Logout
              final storage = await _api.storage;
              await storage.deleteAll();
              if (mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Stats bar
          Container(
            padding: const EdgeInsets.all(16),
            color: const Color(0xFF1E1E1E),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatCard('ROJO', redCount.toString(), Colors.red),
                _buildStatCard('NARANJA', orangeCount.toString(), Colors.orange),
                _buildStatCard('AMARILLO', yellowCount.toString(), Colors.yellow),
                _buildStatCard('TOTAL', _alerts.length.toString(), Colors.white),
              ],
            ),
          ),
          // Filters
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: ['ALL', 'ROJO', 'NARANJA', 'AMARILLO', 'VERDE']
                    .map((filter) => Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(filter),
                            selected: _selectedFilter == filter,
                            onSelected: (selected) {
                              setState(() {
                                _selectedFilter = selected ? filter : 'ALL';
                              });
                              _loadAlerts();
                            },
                            backgroundColor: _getFilterColor(filter),
                            selectedColor: const Color(0xFFFFB300),
                          ),
                        ))
                    .toList(),
              ),
            ),
          ),
          // Alerts list
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _alerts.isEmpty
                    ? const Center(
                        child: Text(
                          'No hay alertas',
                          style: TextStyle(color: Colors.grey),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _alerts.length,
                        itemBuilder: (context, index) {
                          final alert = _alerts[index];
                          return AlertCard(
                            alert: alert,
                            onTap: () => _showAlertDetails(alert),
                          );
                        },
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFFFFB300),
        onPressed: () {
          // Launch analysis
        },
        child: const Icon(Icons.play_arrow, color: Colors.black),
      ),
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
      ],
    );
  }

  Color _getFilterColor(String filter) {
    switch (filter) {
      case 'ROJO':
        return Colors.red.withOpacity(0.2);
      case 'NARANJA':
        return Colors.orange.withOpacity(0.2);
      case 'AMARILLO':
        return Colors.yellow.withOpacity(0.2);
      case 'VERDE':
        return Colors.green.withOpacity(0.2);
      default:
        return Colors.grey.withOpacity(0.2);
    }
  }

  void _showAlertDetails(dynamic alert) async {
    try {
      final details = await _api.getAlertDetails(alert['id']);
      if (mounted) {
        showModalBottomSheet(
          context: context,
          backgroundColor: const Color(0xFF1E1E1E),
          builder: (context) => Container(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Alerta ${details['risk_level']}',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: _getRiskColor(details['risk_level']),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  details['content_full'] ?? details['content_excerpt'],
                  style: const TextStyle(color: Colors.white),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton(
                      onPressed: () async {
                        await _api.reviewAlert(
                          details['id'],
                          'ESCALAR',
                          'Revisado desde móvil',
                        );
                        Navigator.pop(context);
                        _loadAlerts();
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                      ),
                      child: const Text('ESCALAR'),
                    ),
                    ElevatedButton(
                      onPressed: () async {
                        await _api.reviewAlert(
                          details['id'],
                          'ARCHIVAR',
                          'Revisado desde móvil',
                        );
                        Navigator.pop(context);
                        _loadAlerts();
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.grey,
                      ),
                      child: const Text('ARCHIVAR'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  Color _getRiskColor(String level) {
    switch (level) {
      case 'ROJO':
        return Colors.red;
      case 'NARANJA':
        return Colors.orange;
      case 'AMARILLO':
        return Colors.yellow;
      default:
        return Colors.green;
    }
  }
}
