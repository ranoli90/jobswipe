class ApiEndpoints {
  // Base URL is configured in Dio

  // Auth endpoints
  static const String login = '/api/v1/auth/login';
  static const String register = '/api/v1/auth/register';
  static const String logout = '/api/v1/auth/logout';
  static const String getCurrentUser = '/api/v1/auth/me';
  static const String refreshToken = '/api/v1/auth/refresh';
  static const String verifyEmail = '/api/v1/auth/verify-email';
  static const String forgotPassword = '/api/v1/auth/forgot-password';
  static const String resetPassword = '/api/v1/auth/reset-password';

  // Profile endpoints
  static const String getProfile = '/api/v1/profile';
  static const String updateProfile = '/api/v1/profile';
  static const String uploadResume = '/api/v1/profile/resume';

  // Jobs endpoints
  static const String getJobs = '/api/v1/jobs';
  static const String getJobFeed = '/api/v1/feed';
  static const String getJobDetails = '/api/v1/{id}';
  static const String getJobMatches = '/api/v1/matches';
  static const String swipeJob = '/api/v1/{id}/swipe';
  static const String searchJobs = '/api/v1/jobs/search';
  static const String saveJob = '/api/v1/jobs/{id}/save';
  static const String unsaveJob = '/api/v1/jobs/{id}/unsave';

  // Applications endpoints
  static const String getApplications = '/api/v1/applications';
  static const String createApplication = '/api/v1/applications';
  static const String getApplicationDetails = '/api/v1/applications/{id}/status';
  static const String cancelApplication = '/api/v1/applications/{id}/cancel';
  static const String getApplicationAuditLog = '/api/v1/applications/{id}/audit';
  static const String updateApplication = '/api/v1/applications/{id}';
  static const String deleteApplication = '/api/v1/applications/{id}';

  // Notifications endpoints
  static const String getNotifications = '/api/v1/notifications';
  static const String markNotificationRead = '/api/v1/notifications/{id}/read';
  static const String markAllNotificationsRead = '/api/v1/notifications/mark-all-read';
  static const String getUnreadCount = '/api/v1/notifications/unread-count';
  static const String getNotificationPreferences = '/api/v1/notifications/preferences';
  static const String updateNotificationPreferences = '/api/v1/notifications/preferences';
  static const String registerDeviceToken = '/api/v1/notifications/device-token';
  static const String unregisterDeviceToken = '/api/v1/notifications/device-token/{deviceId}';

  // Health check
  static const String health = '/health';
}