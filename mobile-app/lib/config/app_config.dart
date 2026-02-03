import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Environment variables class
/// 
/// This class provides centralized access to environment variables
/// using dart-define for compile-time configuration and .env for development.
class Env {
  /// API Base URL configured via dart-define or .env
  /// 
  /// Default value is for Android emulator (10.0.2.2 maps to host localhost)
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}

/// App Configuration
/// 
/// This file contains configuration settings for different environments.
/// The environment can be configured either via:
/// 1. .env file (for development)
/// 2. --dart-define flags (for production builds)
/// 
/// Usage:
/// - Development: Uses .env file automatically
/// - Production: flutter build apk --dart-define=API_BASE_URL=https://api.example.com --dart-define=ENV=production

class AppConfig {
  // Environment - check dart-define first, then .env, then default
  static String get env {
    const dartEnv = String.fromEnvironment('ENV');
    if (dartEnv.isNotEmpty) return dartEnv;
    
    final envValue = dotenv.env['ENVIRONMENT'];
    if (envValue != null && envValue.isNotEmpty) return envValue;
    
    return 'development';
  }
  
  // API Configuration
  // Uses Env.apiBaseUrl as the source of truth, with /api suffix appended
  static String get baseUrl {
    // Get the base URL from Env (which checks dart-define first, then default)
    final baseUrlWithoutApi = Env.apiBaseUrl;
    
    // Check if .env has a custom API_BASE_URL that differs from the default
    final envBaseUrl = dotenv.env['API_BASE_URL'];
    if (envBaseUrl != null && envBaseUrl.isNotEmpty && envBaseUrl != 'http://10.0.2.2:8000') {
      // Use .env value if it's a custom value (not the default)
      return '$envBaseUrl/api';
    }
    
    // For default or dart-define values, append /api suffix
    // Remove trailing slash if present to avoid double slashes
    final cleanUrl = baseUrlWithoutApi.endsWith('/') 
        ? baseUrlWithoutApi.substring(0, baseUrlWithoutApi.length - 1)
        : baseUrlWithoutApi;
    return '$cleanUrl/api';
  }

  /// Get API version from environment or default
  static String get apiVersion {
    const dartVersion = String.fromEnvironment('API_VERSION');
    if (dartVersion.isNotEmpty) return dartVersion;
    
    final envVersion = dotenv.env['API_VERSION'];
    if (envVersion != null && envVersion.isNotEmpty) return envVersion;
    
    return 'v1';
  }
  
  // Feature Flags
  static bool get isProduction => env == 'production';
  static bool get isDevelopment => env == 'development';
  static bool get isStaging => env == 'staging';
  
  // API Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);
  
  // Cache Configuration
  static const Duration cacheMaxAge = Duration(hours: 1);
  static const int cacheMaxSize = 100; // Maximum number of cached items
  
  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;
  
  // App Info
  static const String appName = 'JobSwipe';
  static const String appVersion = '1.0.0';
  
  // Support
  static const String supportEmail = 'support@jobswipe.com';
}
