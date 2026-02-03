import 'package:image_picker/image_picker.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../../models/profile.dart';
import 'package:dio/dio.dart';

class ProfileRepository {
  final ApiClient _apiClient;

  ProfileRepository(this._apiClient);

  Future<Profile> getProfile() async {
    try {
      final response = await _apiClient.get(ApiEndpoints.getProfile);
      return Profile.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  Future<Profile> updateProfile(Map<String, dynamic> data) async {
    try {
      final response = await _apiClient.put(
        ApiEndpoints.updateProfile,
        data: data,
      );
      return Profile.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  Future<String> uploadResume(XFile file) async {
    try {
      final formData = FormData.fromMap({
        'resume': await MultipartFile.fromFile(
          file.path,
          filename: file.name,
        ),
      });

      final response = await _apiClient.post(
        ApiEndpoints.uploadResume,
        data: formData,
        options: Options(
          contentType: 'multipart/form-data',
        ),
      );

      return response.data['resume_url'] ?? '';
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateSkills(List<String> skills) async {
    try {
      await _apiClient.put(
        ApiEndpoints.updateProfile,
        data: {'skills': skills},
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateWorkExperience(List<Map<String, dynamic>> experience) async {
    try {
      await _apiClient.put(
        ApiEndpoints.updateProfile,
        data: {'work_experience': experience},
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateEducation(List<Map<String, dynamic>> education) async {
    try {
      await _apiClient.put(
        ApiEndpoints.updateProfile,
        data: {'education': education},
      );
    } catch (e) {
      rethrow;
    }
  }
}
