import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../../models/application.dart';

class ApplicationRepository {
  final ApiClient _apiClient;

  ApplicationRepository(this._apiClient);

  Future<List<Application>> getApplications() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getApplications);
      final List<dynamic> applicationsJson = 
          response.data['applications'] ?? response.data ?? [];
      return applicationsJson.map((json) => Application.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }

  Future<Application> getApplicationDetails(String applicationId) async {
    try {
      final endpoint = ApiEndpoints.getApplicationDetails
          .replaceAll('{id}', applicationId);
      final response = await _apiClient.get(endpoint);
      return Application.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  Future<void> cancelApplication(String applicationId) async {
    try {
      final endpoint = ApiEndpoints.cancelApplication
          .replaceAll('{id}', applicationId);
      await _apiClient.post(endpoint);
    } catch (e) {
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getApplicationAuditLog(
    String applicationId,
  ) async {
    try {
      final endpoint = ApiEndpoints.getApplicationAuditLog
          .replaceAll('{id}', applicationId);
      final response = await _apiClient.get(endpoint);
      final List<dynamic> auditLog = response.data['audit_log'] ?? response.data ?? [];
      return auditLog.cast<Map<String, dynamic>>();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> createApplication(String jobId) async {
    try {
      await _apiClient.post(
        ApiEndpoints.createApplication,
        data: {'job_id': jobId},
      );
    } catch (e) {
      rethrow;
    }
  }
}
