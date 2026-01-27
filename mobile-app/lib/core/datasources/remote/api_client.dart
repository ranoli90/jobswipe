import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'package:dio_smart_retry/dio_smart_retry.dart';
import '../local/secure_storage_service.dart';

class ApiClient {
  final Dio _dio;
  final SecureStorageService _secureStorage;

  ApiClient(this._dio, this._secureStorage) {
    _setupInterceptors();
  }

  void _setupInterceptors() {
    // Auth interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Add auth token if available
        final token = await _secureStorage.read('access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token expired, try refresh
          try {
            final refreshToken = await _secureStorage.read('refresh_token');
            if (refreshToken != null) {
              final refreshResponse = await _dio.post(
                '/v1/auth/refresh',
                data: {'refresh_token': refreshToken},
                options: Options(
                  headers: {'Authorization': null}, // Don't add token for refresh
                ),
              );

              final newAccessToken = refreshResponse.data['access_token'];
              final newRefreshToken = refreshResponse.data['refresh_token'];

              await _secureStorage.write('access_token', newAccessToken);
              await _secureStorage.write('refresh_token', newRefreshToken);

              // Retry original request with new token
              final opts = Options(
                method: error.requestOptions.method,
                headers: {...error.requestOptions.headers, 'Authorization': 'Bearer $newAccessToken'},
              );

              final cloneReq = await _dio.request(
                error.requestOptions.path,
                options: opts,
                data: error.requestOptions.data,
                queryParameters: error.requestOptions.queryParameters,
              );

              return handler.resolve(cloneReq);
            }
          } catch (e) {
            // Refresh failed, logout user
            await _secureStorage.delete('access_token');
            await _secureStorage.delete('refresh_token');
          }
        }
        return handler.next(error);
      },
    ));

    // Error handling interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) {
        // Transform Dio errors to custom exceptions
        if (error.type == DioExceptionType.connectionTimeout ||
            error.type == DioExceptionType.sendTimeout ||
            error.type == DioExceptionType.receiveTimeout) {
          throw NetworkException('Network timeout. Please check your connection.');
        } else if (error.type == DioExceptionType.connectionError) {
          throw NetworkException('No internet connection. Please check your network.');
        } else if (error.response != null) {
          final statusCode = error.response!.statusCode;
          final data = error.response!.data;

          if (statusCode == 400) {
            throw BadRequestException(data['message'] ?? 'Bad request');
          } else if (statusCode == 401) {
            throw UnauthorizedException(data['message'] ?? 'Unauthorized');
          } else if (statusCode == 403) {
            throw ForbiddenException(data['message'] ?? 'Forbidden');
          } else if (statusCode == 404) {
            throw NotFoundException(data['message'] ?? 'Not found');
          } else if (statusCode == 422) {
            throw ValidationException(data['message'] ?? 'Validation error', data['errors']);
          } else if (statusCode == 429) {
            throw RateLimitException(data['message'] ?? 'Too many requests');
          } else if (statusCode! >= 500) {
            throw ServerException(data['message'] ?? 'Server error');
          }
        }

        return handler.next(error);
      },
    ));

    // Logger interceptor
    _dio.interceptors.add(PrettyDioLogger(
      requestHeader: true,
      requestBody: true,
      responseBody: true,
      responseHeader: false,
      error: true,
      compact: true,
      maxWidth: 90,
    ));

    // Retry interceptor
    _dio.interceptors.add(
      RetryInterceptor(
        dio: _dio,
        logPrint: print, // Use print for logging
        retries: 3, // Number of retries
        retryDelays: const [
          Duration(seconds: 1), // Initial delay
          Duration(seconds: 2), // Second retry delay
          Duration(seconds: 3), // Third retry delay
        ],
        retryEvaluator: (error, attempt) {
          // Retry on network errors, 5xx status codes, and specific 4xx codes
          return error.type == DioExceptionType.connectionTimeout ||
                 error.type == DioExceptionType.sendTimeout ||
                 error.type == DioExceptionType.receiveTimeout ||
                 error.type == DioExceptionType.connectionError ||
                 (error.response?.statusCode != null &&
                  (error.response!.statusCode! >= 500 ||
                   error.response!.statusCode == 429)); // Rate limit
        },
      ),
    );
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters, Options? options}) {
    return _dio.get(path, queryParameters: queryParameters, options: options);
  }

  Future<Response> post(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) {
    return _dio.post(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response> put(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) {
    return _dio.put(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response> delete(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) {
    return _dio.delete(path, data: data, queryParameters: queryParameters, options: options);
  }
}