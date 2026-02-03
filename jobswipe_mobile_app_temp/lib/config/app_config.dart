import 'package:flutter_dotenv/flutter_dotenv.dart';

/// App Configuration
/// 
/// This file contains configuration settings for different environments.
/// The environment can be configured either via:
/// 1. .env file (for development)
/// 2. --dart-define flags (for production builds)
/// 
/// Usage:
/// - Development: Uses .env file automatically
/// - Production: flutter build apk --dart-define=ENV=production

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
  static String get baseUrl {
    // Check dart-define first (for production builds)
    const dartBaseUrl = String.fromEnvironment('API_BASE_URL');
    if (dartBaseUrl.isNotEmpty) return dartBaseUrl;
    
    // Check .env file
    final envBaseUrl = dotenv.env['API_BASE_URL'];
    if (envBaseUrl != null && envBaseUrl.isNotEmpty) {
      return '$envBaseUrl/api';
    }
    
    // Fallback to environment-based defaults
    switch (env) {
      case 'production':
        return 'https://jobswipe-9obhra.fly.dev/api';
      case 'staging':
        return 'https://jobswipe-backend-staging.fly.dev/api';
      default:
        return 'http://localhost:8000/api';
    }
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
