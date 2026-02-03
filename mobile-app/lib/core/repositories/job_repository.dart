import 'package:dio/dio.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../datasources/local/database_service.dart';
import '../datasources/local/offline_service.dart';
import '../../models/job.dart';

class JobRepository {
  final ApiClient _apiClient;
  final DatabaseService _databaseService;
  final OfflineService _offlineService;

  JobRepository(this._apiClient, this._databaseService, this._offlineService);

  Future<List<Job>> getJobFeed({
    String? cursor,
    int pageSize = 20,
    CancelToken? cancelToken,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'limit': pageSize,
      };
      if (cursor != null) {
        queryParams['cursor'] = cursor;
      }

      final response = await _apiClient.get(
        ApiEndpoints.getJobFeed,
        queryParameters: queryParams,
        cancelToken: cancelToken,
      );

      final List<dynamic> jobsJson = response.data['jobs'] ?? response.data ?? [];
      final jobs = jobsJson.map((json) => Job.fromJson(json)).toList();

      // Cache jobs for offline access
      await _cacheJobs(jobs);

      return jobs;
    } catch (e) {
      // Try to return cached jobs if offline
      if (await _offlineService.isOffline()) {
        return await _getCachedJobs();
      }
      rethrow;
    }
  }

  Future<Job> getJobDetails(String jobId) async {
    try {
      final endpoint = ApiEndpoints.getJobDetails.replaceAll('{id}', jobId);
      final response = await _apiClient.get(endpoint);
      return Job.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  Future<List<Job>> getJobMatches() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getJobMatches);
      final List<dynamic> matchesJson = response.data['matches'] ?? response.data ?? [];
      return matchesJson.map((json) => Job.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> swipeJob(String jobId, String action) async {
    try {
      final endpoint = ApiEndpoints.swipeJob.replaceAll('{id}', jobId);
      await _apiClient.post(
        endpoint,
        data: {'action': action},
      );
    } catch (e) {
      // Queue for offline sync if network unavailable
      if (await _offlineService.isOffline()) {
        await _offlineService.queueSwipe(jobId, action);
        return;
      }
      rethrow;
    }
  }

  Future<void> _cacheJobs(List<Job> jobs) async {
    try {
      await _databaseService.insertJobs(jobs);
    } catch (e) {
      // Ignore cache errors
    }
  }

  Future<List<Job>> _getCachedJobs() async {
    try {
      return await _databaseService.getCachedJobs();
    } catch (e) {
      return [];
    }
  }
}
