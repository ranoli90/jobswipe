import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/job.dart';

enum JobsStatus {
  initial,
  loading,
  loaded,
  error,
}

class JobsState {
  final JobsStatus status;
  final List<Job> jobs;
  final int currentIndex;
  final List<String> likedJobIds;
  final List<String> dislikedJobIds;
  final String? errorMessage;

  const JobsState({
    this.status = JobsStatus.initial,
    this.jobs = const [],
    this.currentIndex = 0,
    this.likedJobIds = const [],
    this.dislikedJobIds = const [],
    this.errorMessage,
  });

  Job? get currentJob {
    if (currentIndex < jobs.length && currentIndex >= 0) {
      return jobs[currentIndex];
    }
    return null;
  }

  bool get hasMoreJobs => currentIndex < jobs.length - 1;

  JobsState copyWith({
    JobsStatus? status,
    List<Job>? jobs,
    int? currentIndex,
    List<String>? likedJobIds,
    List<String>? dislikedJobIds,
    String? errorMessage,
  }) {
    return JobsState(
      status: status ?? this.status,
      jobs: jobs ?? this.jobs,
      currentIndex: currentIndex ?? this.currentIndex,
      likedJobIds: likedJobIds ?? this.likedJobIds,
      dislikedJobIds: dislikedJobIds ?? this.dislikedJobIds,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class JobsNotifier extends StateNotifier<JobsState> {
  JobsNotifier() : super(const JobsState());

  Future<void> loadJobs() async {
    state = state.copyWith(status: JobsStatus.loading);

    try {
      // Simulate API call - replace with actual job fetching logic
      await Future.delayed(const Duration(seconds: 1));

      // Mock job data
      final mockJobs = [
        Job(
          id: '1',
          title: 'Senior Flutter Developer',
          company: 'Tech Corp',
          location: 'San Francisco, CA',
          snippet: 'We are looking for an experienced Flutter developer to join our team...',
          score: 0.95,
          applyUrl: 'https://example.com/apply/1',
        ),
        Job(
          id: '2',
          title: 'Mobile App Developer',
          company: 'StartupXYZ',
          location: 'Remote',
          snippet: 'Join our fast-growing startup and build amazing mobile experiences...',
          score: 0.88,
          applyUrl: 'https://example.com/apply/2',
        ),
        Job(
          id: '3',
          title: 'iOS Developer',
          company: 'Apple Inc',
          location: 'Cupertino, CA',
          snippet: 'Work on the next generation of iOS applications...',
          score: 0.92,
          applyUrl: 'https://example.com/apply/3',
        ),
        Job(
          id: '4',
          title: 'Android Developer',
          company: 'Google',
          location: 'Mountain View, CA',
          snippet: 'Build innovative Android applications used by millions...',
          score: 0.90,
          applyUrl: 'https://example.com/apply/4',
        ),
        Job(
          id: '5',
          title: 'Full Stack Developer',
          company: 'Amazon',
          location: 'Seattle, WA',
          snippet: 'Develop scalable web and mobile applications...',
          score: 0.85,
          applyUrl: 'https://example.com/apply/5',
        ),
      ];

      state = state.copyWith(
        status: JobsStatus.loaded,
        jobs: mockJobs,
      );
    } catch (e) {
      state = state.copyWith(
        status: JobsStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  void likeJob(String jobId) {
    final updatedLikedIds = [...state.likedJobIds, jobId];
    state = state.copyWith(
      likedJobIds: updatedLikedIds,
      currentIndex: state.currentIndex + 1,
    );
  }

  void dislikeJob(String jobId) {
    final updatedDislikedIds = [...state.dislikedJobIds, jobId];
    state = state.copyWith(
      dislikedJobIds: updatedDislikedIds,
      currentIndex: state.currentIndex + 1,
    );
  }

  void undoSwipe() {
    if (state.currentIndex > 0) {
      final newIndex = state.currentIndex - 1;
      final jobId = state.jobs[newIndex].id;
      
      final updatedLikedIds = state.likedJobIds.where((id) => id != jobId).toList();
      final updatedDislikedIds = state.dislikedJobIds.where((id) => id != jobId).toList();
      
      state = state.copyWith(
        currentIndex: newIndex,
        likedJobIds: updatedLikedIds,
        dislikedJobIds: updatedDislikedIds,
      );
    }
  }

  void resetJobs() {
    state = const JobsState();
  }

  void clearError() {
    state = state.copyWith(errorMessage: null);
  }
}

final jobsProvider = StateNotifierProvider<JobsNotifier, JobsState>((ref) {
  return JobsNotifier();
});

final jobsStatusProvider = Provider<JobsStatus>((ref) {
  return ref.watch(jobsProvider).status;
});

final currentJobProvider = Provider<Job?>((ref) {
  return ref.watch(jobsProvider).currentJob;
});

final hasMoreJobsProvider = Provider<bool>((ref) {
  return ref.watch(jobsProvider).hasMoreJobs;
});

final likedJobsProvider = Provider<List<String>>((ref) {
  return ref.watch(jobsProvider).likedJobIds;
});

final dislikedJobsProvider = Provider<List<String>>((ref) {
  return ref.watch(jobsProvider).dislikedJobIds;
});
