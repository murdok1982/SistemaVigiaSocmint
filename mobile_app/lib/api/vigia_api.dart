import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class VigiaApi {
  static const String baseUrl = 'https://api.vigia-system.int';
  static const String wsUrl = 'wss://api.vigia-system.int/ws';
  
  final Dio _dio;
  final FlutterSecureStorage _storage;

  VigiaApi({Dio? dio, FlutterSecureStorage? storage})
      : _dio = dio ?? Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
          headers: {'Content-Type': 'application/json'},
        )),
        _storage = storage ?? const FlutterSecureStorage();

  Future<Map<String, dynamic>> login(String username, String password, {String? mfaToken}) async {
    try {
      final response = await _dio.post('/api/auth/login', data: {
        'username': username,
        'password': password,
        if (mfaToken != null) 'mfa_token': mfaToken,
      });
      
      final data = response.data;
      await _storage.write(key: 'access_token', value: data['access_token']);
      await _storage.write(key: 'refresh_token', value: data['refresh_token']);
      return data;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Error de autenticación');
    }
  }

  Future<List<dynamic>> getAlerts({String? riskLevel, int page = 1}) async {
    final token = await _storage.read(key: 'access_token');
    try {
      final response = await _dio.get(
        '/api/alerts',
        queryParameters: {
          if (riskLevel != null) 'risk_level': riskLevel,
          'page': page,
          'page_size': 20,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      return response.data['items'] ?? [];
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _refreshToken();
        return getAlerts(riskLevel: riskLevel, page: page);
      }
      throw Exception('Error cargando alertas');
    }
  }

  Future<void> _refreshToken() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    try {
      final response = await _dio.post(
        '/api/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      await _storage.write(key: 'access_token', value: response.data['access_token']);
    } catch (e) {
      await _storage.deleteAll();
      throw Exception('Sesión expirada');
    }
  }

  Future<Map<String, dynamic>> getAlertDetails(String alertId) async {
    final token = await _storage.read(key: 'access_token');
    try {
      final response = await _dio.get(
        '/api/alerts/$alertId',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      return response.data;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Error cargando detalles');
    }
  }

  Future<void> reviewAlert(String alertId, String action, String notes) async {
    final token = await _storage.read(key: 'access_token');
    try {
      await _dio.post(
        '/api/alerts/$alertId/review',
        data: {
          'action': action,
          'notes': notes,
          'analyst_id': 'mobile_analyst',
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Error revisando alerta');
    }
  }
}
