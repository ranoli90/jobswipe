import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../../models/notification.dart';

class NotificationRepository {
  final ApiClient _apiClient;

  NotificationRepository(this._apiClient);

  Future<List<JobSwipeNotification>> getNotifications() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getNotifications);
      final List<dynamic> notificationsJson = 
          response.data['notifications'] ?? response.data ?? [];
      return notificationsJson
          .map((json) => JobSwipeNotification.fromJson(json))
          .toList();
    } catch (e) {
      rethrow;
    }
  }

  Future<int> getUnreadCount() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getUnreadCount);
      return response.data['count'] ?? 0;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> markAsRead(String notificationId) async {
    try {
      final endpoint = ApiEndpoints.markNotificationRead
          .replaceAll('{id}', notificationId);
      await _apiClient.post(endpoint);
    } catch (e) {
      rethrow;
    }
  }

  Future<void> markAllAsRead() async {
    try {
      await _apiClient.post(ApiEndpoints.markAllNotificationsRead);
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteNotification(String notificationId) async {
    try {
      final endpoint = '/v1/notifications/$notificationId';
      await _apiClient.delete(endpoint);
    } catch (e) {
      rethrow;
    }
  }
}
