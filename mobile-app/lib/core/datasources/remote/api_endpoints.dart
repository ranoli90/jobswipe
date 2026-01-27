class ApiEndpoints {
  // Base URL is configured in Dio

  // Auth endpoints
  static const String login = '/v1/auth/login';
  static const String register = '/v1/auth/register';
  static const String logout = '/v1/auth/logout';
  static const String getCurrentUser = '/v1/auth/me';
  static const String refreshToken = '/v1/auth/refresh';
  static const String verifyEmail = '/v1/auth/verify-email';
  static const String forgotPassword = '/v1/auth/forgot-password';
  static const String resetPassword = '/v1/auth/reset-password';

  // Profile endpoints
  static const String getProfile = '/v1/profile';
  static const String updateProfile = '/v1/profile';
  static const String uploadResume = '/v1/profile/resume';

  // Jobs endpoints
  static const String getJobs = '/v1/jobs';
  static const String getJobFeed = '/v1/jobs/feed';
  static const String getJobDetails = '/v1/jobs/{id}';
  static const String getJobMatches = '/v1/jobs/matches';
  static const String swipeJob = '/v1/jobs/{id}/swipe';
  static const String searchJobs = '/v1/jobs/search';
  static const String saveJob = '/v1/jobs/{id}/save';
  static const String unsaveJob = '/v1/jobs/{id}/unsave';

  // Applications endpoints
  static const String getApplications = '/v1/applications';
  static const String createApplication = '/v1/applications';
  static const String getApplicationDetails = '/v1/applications/{id}/status';
  static const String cancelApplication = '/v1/applications/{id}/cancel';
  static const String getApplicationAuditLog = '/v1/applications/{id}/audit';
  static const String updateApplication = '/v1/applications/{id}';
  static const String deleteApplication = '/v1/applications/{id}';

  // Notifications endpoints
  static const String getNotifications = '/v1/notifications';
  static const String markNotificationRead = '/v1/notifications/{id}/read';
  static const String markAllNotificationsRead = '/v1/notifications/mark-all-read';
  static const String getUnreadCount = '/v1/notifications/unread-count';
  static const String getNotificationPreferences = '/v1/notifications/preferences';
  static const String updateNotificationPreferences = '/v1/notifications/preferences';
  static const String registerDeviceToken = '/v1/notifications/device-token';
  static const String unregisterDeviceToken = '/v1/notifications/device-token/{deviceId}';

  // Health check
  static const String health = '/health';
}