import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/profile.dart';

enum ProfileStatus {
  initial,
  loading,
  loaded,
  updating,
  error,
}

class ProfileState {
  final ProfileStatus status;
  final Profile? profile;
  final String? errorMessage;

  const ProfileState({
    this.status = ProfileStatus.initial,
    this.profile,
    this.errorMessage,
  });

  ProfileState copyWith({
    ProfileStatus? status,
    Profile? profile,
    String? errorMessage,
  }) {
    return ProfileState(
      status: status ?? this.status,
      profile: profile ?? this.profile,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  ProfileNotifier() : super(const ProfileState());

  Future<void> loadProfile(String userId) async {
    state = state.copyWith(status: ProfileStatus.loading);

    try {
      // Simulate API call - replace with actual profile fetching logic
      await Future.delayed(const Duration(seconds: 1));

      // Mock profile data
      final profile = Profile(
        id: userId,
        fullName: 'John Doe',
        phone: '+1234567890',
        location: 'San Francisco, CA',
        headline: 'Senior Flutter Developer',
        workExperience: [
          {
            'company': 'Tech Corp',
            'position': 'Senior Developer',
            'startDate': '2020-01-01',
            'endDate': null,
            'description': 'Leading mobile development team',
          },
          {
            'company': 'StartupXYZ',
            'position': 'Flutter Developer',
            'startDate': '2018-06-01',
            'endDate': '2019-12-31',
            'description': 'Built cross-platform mobile apps',
          },
        ],
        education: [
          {
            'school': 'University of California',
            'degree': 'Bachelor of Science in Computer Science',
            'startDate': '2014-09-01',
            'endDate': '2018-05-31',
          },
        ],
        skills: [
          'Flutter',
          'Dart',
          'iOS',
          'Android',
          'Firebase',
          'REST APIs',
          'Git',
          'CI/CD',
        ],
        resumeFileUrl: 'https://example.com/resume.pdf',
        parsedAt: DateTime.now(),
        preferences: ProfilePreferences(
          jobTypes: ['Full-time', 'Contract'],
          remotePreference: 'Remote',
          experienceLevel: 'Senior',
        ),
      );

      state = state.copyWith(
        status: ProfileStatus.loaded,
        profile: profile,
      );
    } catch (e) {
      state = state.copyWith(
        status: ProfileStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> updateProfile(ProfileUpdate update) async {
    state = state.copyWith(status: ProfileStatus.updating);

    try {
      // Simulate API call - replace with actual profile update logic
      await Future.delayed(const Duration(seconds: 1));

      // Update the profile with new data
      final currentProfile = state.profile;
      if (currentProfile != null) {
        final updatedProfile = Profile(
          id: currentProfile.id,
          fullName: update.fullName ?? currentProfile.fullName,
          phone: update.phone ?? currentProfile.phone,
          location: update.location ?? currentProfile.location,
          headline: update.headline ?? currentProfile.headline,
          workExperience: update.experience ?? currentProfile.workExperience,
          education: update.education ?? currentProfile.education,
          skills: update.skills ?? currentProfile.skills,
          resumeFileUrl: currentProfile.resumeFileUrl,
          parsedAt: currentProfile.parsedAt,
          preferences: update.preferences ?? currentProfile.preferences,
        );

        state = state.copyWith(
          status: ProfileStatus.loaded,
          profile: updatedProfile,
        );
      }
    } catch (e) {
      state = state.copyWith(
        status: ProfileStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> uploadResume(String filePath) async {
    state = state.copyWith(status: ProfileStatus.updating);

    try {
      // Simulate file upload - replace with actual upload logic
      await Future.delayed(const Duration(seconds: 2));

      final currentProfile = state.profile;
      if (currentProfile != null) {
        final updatedProfile = Profile(
          id: currentProfile.id,
          fullName: currentProfile.fullName,
          phone: currentProfile.phone,
          location: currentProfile.location,
          headline: currentProfile.headline,
          workExperience: currentProfile.workExperience,
          education: currentProfile.education,
          skills: currentProfile.skills,
          resumeFileUrl: 'https://example.com/resume_updated.pdf',
          parsedAt: DateTime.now(),
          preferences: currentProfile.preferences,
        );

        state = state.copyWith(
          status: ProfileStatus.loaded,
          profile: updatedProfile,
        );
      }
    } catch (e) {
      state = state.copyWith(
        status: ProfileStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  void clearError() {
    state = state.copyWith(errorMessage: null);
  }
}

final profileProvider = StateNotifierProvider<ProfileNotifier, ProfileState>((ref) {
  return ProfileNotifier();
});

final profileStatusProvider = Provider<ProfileStatus>((ref) {
  return ref.watch(profileProvider).status;
});

final currentProfileProvider = Provider<Profile?>((ref) {
  return ref.watch(profileProvider).profile;
});
