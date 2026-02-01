import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';
import '../../../core/data/job_repository.dart';
import '../../../models/job.dart';

// Jobs Events
abstract class JobsEvent extends Equatable {
  const JobsEvent();

  @override
  List<Object?> get props => [];
}

class JobsFeedRequested extends JobsEvent {
  final String? cursor;
  final int limit;

  const JobsFeedRequested({
    this.cursor,
    this.limit = 20,
  });

  @override
  List<Object?> get props => [cursor, limit];
}

class JobsRefreshRequested extends JobsEvent {}

class JobsSwipeRequested extends JobsEvent {
  final String jobId;
  final String action; // 'like' or 'dislike'

  const JobsSwipeRequested({
    required this.jobId,
    required this.action,
  });

  @override
  List<Object?> get props => [jobId, action];
}

class JobsMatchesRequested extends JobsEvent {}

class JobsJobDetailRequested extends JobsEvent {
  final String jobId;

  const JobsJobDetailRequested(this.jobId);

  @override
  List<Object?> get props => [jobId];
}

// Jobs States
abstract class JobsState extends Equatable {
  const JobsState();

  @override
  List<Object?> get props => [];
}

class JobsInitial extends JobsState {}

class JobsLoading extends JobsState {}

class JobsLoaded extends JobsState {
  final List<Job> jobs;
  final String? nextCursor;
  final bool hasMore;

  const JobsLoaded({
    required this.jobs,
    this.nextCursor,
    this.hasMore = true,
  });

  @override
  List<Object?> get props => [jobs, nextCursor, hasMore];

  JobsLoaded copyWith({
    List<Job>? jobs,
    String? nextCursor,
    bool? hasMore,
  }) {
    return JobsLoaded(
      jobs: jobs ?? this.jobs,
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}

class JobsError extends JobsState {
  final String message;

  const JobsError(this.message);

  @override
  List<Object?> get props => [message];
}

class JobsMatchLoaded extends JobsState {
  final List<Job> matches;

  const JobsMatchLoaded(this.matches);

  @override
  List<Object?> get props => [matches];
}

class JobsJobDetailLoaded extends JobsState {
  final Job job;

  const JobsJobDetailLoaded(this.job);

  @override
  List<Object?> get props => [job];
}

// Jobs BLoC
class JobsBloc extends Bloc<JobsEvent, JobsState> {
  final JobRepository _jobRepository;
  CancelToken? _cancelToken;

  JobsBloc(this._jobRepository) : super(JobsInitial()) {
    on<JobsFeedRequested>(_onJobsFeedRequested);
    on<JobsRefreshRequested>(_onJobsRefreshRequested);
    on<JobsSwipeRequested>(_onJobsSwipeRequested);
    on<JobsMatchesRequested>(_onJobsMatchesRequested);
    on<JobsJobDetailRequested>(_onJobsJobDetailRequested);
  }

  Future<void> _onJobsFeedRequested(
    JobsFeedRequested event,
    Emitter<JobsState> emit,
  ) async {
    if (state is JobsLoading) return;

    // Cancel any ongoing request
    _cancelToken?.cancel('New request received');
    _cancelToken = CancelToken();

    emit(JobsLoading());
    try {
      final jobs = await _jobRepository.getJobFeed(
        cursor: event.cursor,
        pageSize: event.limit,
        cancelToken: _cancelToken,
      );

      // Extract next cursor from the last job if available
      final nextCursor = jobs.isNotEmpty ? jobs.last.id : null;
      emit(JobsLoaded(
        jobs: jobs,
        nextCursor: nextCursor,
        hasMore: jobs.length >= event.limit,
      ));
    } catch (error) {
      if (error is DioException && error.type == DioExceptionType.cancel) {
        return; // Ignore cancellation errors
      }
      emit(JobsError(error.toString()));
    }
  }

  Future<void> _onJobsRefreshRequested(
    JobsRefreshRequested event,
    Emitter<JobsState> emit,
  ) async {
    emit(JobsLoading());
    try {
      final jobs = await _jobRepository.getJobFeed(pageSize: 20);

      final nextCursor = jobs.isNotEmpty ? jobs.last.id : null;
      emit(JobsLoaded(
        jobs: jobs,
        nextCursor: nextCursor,
        hasMore: jobs.length >= 20,
      ));
    } catch (error) {
      emit(JobsError(error.toString()));
    }
  }

  Future<void> _onJobsSwipeRequested(
    JobsSwipeRequested event,
    Emitter<JobsState> emit,
  ) async {
    if (state is! JobsLoaded) return;

    final currentState = state as JobsLoaded;
    try {
      await _jobRepository.swipeJob(event.jobId, event.action);

      // Remove the swiped job from the list
      final updatedJobs = currentState.jobs
          .where((job) => job.id != event.jobId)
          .toList();
      emit(currentState.copyWith(jobs: updatedJobs));
    } catch (error) {
      emit(JobsError(error.toString()));
    }
  }

  Future<void> _onJobsMatchesRequested(
    JobsMatchesRequested event,
    Emitter<JobsState> emit,
  ) async {
    emit(JobsLoading());
    try {
      final matches = await _jobRepository.getJobMatches();
      emit(JobsMatchLoaded(matches));
    } catch (error) {
      emit(JobsError(error.toString()));
    }
  }

  Future<void> _onJobsJobDetailRequested(
    JobsJobDetailRequested event,
    Emitter<JobsState> emit,
  ) async {
    emit(JobsLoading());
    try {
      final job = await _jobRepository.getJobDetails(event.jobId);
      emit(JobsJobDetailLoaded(job));
    } catch (error) {
      emit(JobsError(error.toString()));
    }
  }
}
