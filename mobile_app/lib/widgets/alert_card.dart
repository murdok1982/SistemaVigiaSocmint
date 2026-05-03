import 'package:flutter/material.dart';

class AlertCard extends StatelessWidget {
  final Map<String, dynamic> alert;
  final VoidCallback onTap;

  const AlertCard({super.key, required this.alert, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final riskLevel = alert['risk_level'] ?? 'VERDE';
    final score = (alert['risk_score'] ?? 0.0).toDouble();
    final color = _getColor(riskLevel);

    return Card(
      color: const Color(0xFF1E1E1E),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: color),
                    ),
                    child: Text(
                      riskLevel,
                      style: TextStyle(
                        color: color,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  Text(
                    '${(score * 100).toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: color,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                alert['content_excerpt'] ?? '',
                style: const TextStyle(color: Colors.white70),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    alert['platform'] ?? '',
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                  Text(
                    _formatDate(alert['created_at']),
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getColor(String level) {
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

  String _formatDate(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '';
    }
  }
}
