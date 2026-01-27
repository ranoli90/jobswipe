/// App Configuration
/// 
/// This file contains configuration settings for different environments.
/// The environment is determined at build time using --dart-define flags.
/// 
/// Usage:
/// - Development: flutter run --dart-define=ENV=development
/// - Production: flutter run --dart-define=ENV=production
/// - Build for production: flutter build apk --dart-define=ENV=production

class AppConfig {
  // Environment
  static const String env = String.fromEnvironment('ENV', defaultValue: 'development');
  
  // API Configuration
  static String get baseUrl {
    switch (env) {
      case 'production':
        return 'https://jobswipe.fly.dev';
      case 'staging':
        return 'https://jobswipe-staging.fly.dev';
      default:
        return 'http://localhost:8000';
    }
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
  static const String privacyPolicyUrl = 'https://jobswipe.com/privacy';
  static const String termsOfServiceUrl = 'https://jobswipe.com/terms';
  
  // Social Links
  static const String twitterUrl = 'https://twitter.com/jobswipe';
  static const String linkedInUrl = 'https://linkedin.com/company/jobswipe';
  static const String instagramUrl = 'https://instagram.com/jobswipe';
}
