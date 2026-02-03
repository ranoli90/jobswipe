import 'package:dio/dio.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../datasources/local/secure_storage_service.dart';

class AuthRepository {
  final ApiClient _apiClient;
  final SecureStorageService _secureStorage;

  AuthRepository(this._apiClient, this._secureStorage);

  Future<String?> getAccessToken() async {
    return await _secureStorage.read('access_token');
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.login,
        data: {
          'username': email,
          'password': password,
        },
        options: Options(
          contentType: 'application/x-www-form-urlencoded',
        ),
      );

      final data = response.data;
      
      // Store tokens
      if (data['access_token'] != null) {
        await _secureStorage.write('access_token', data['access_token']);
      }
      if (data['refresh_token'] != null) {
        await _secureStorage.write('refresh_token', data['refresh_token']);
      }

      return data['user'] ?? data;
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String fullName,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiEndpoints.register,
        data: {
          'email': email,
          'password': password,
          'full_name': fullName,
        },
      );

      final data = response.data;
      
      // Store tokens
      if (data['access_token'] != null) {
        await _secureStorage.write('access_token', data['access_token']);
      }
      if (data['refresh_token'] != null) {
        await _secureStorage.write('refresh_token', data['refresh_token']);
      }

      return data['user'] ?? data;
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getCurrentUser);
      return response.data['user'] ?? response.data;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      await _apiClient.post(ApiEndpoints.logout);
    } catch (e) {
      // Ignore logout errors - clear tokens anyway
    } finally {
      await _secureStorage.delete('access_token');
      await _secureStorage.delete('refresh_token');
    }
  }

  Future<void> forgotPassword({required String email}) async {
    try {
      await _apiClient.post(
        ApiEndpoints.forgotPassword,
        data: {'email': email},
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      await _apiClient.post(
        ApiEndpoints.resetPassword,
        data: {
          'token': token,
          'new_password': newPassword,
        },
      );
    } catch (e) {
      rethrow;
    }
  }
}
