import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../core/data/application_repository.dart';
import '../../../models/application.dart';

// Applications Events
abstract class ApplicationsEvent extends Equatable {
  const ApplicationsEvent();

  @override
  List<Object?> get props => [];
}

class ApplicationsLoadRequested extends ApplicationsEvent {}

class ApplicationsRefreshRequested extends ApplicationsEvent {}

class ApplicationsDetailRequested extends ApplicationsEvent {
  final String applicationId;

  const ApplicationsDetailRequested(this.applicationId);

  @override
  List<Object?> get props => [applicationId];
}

class ApplicationsCancelRequested extends ApplicationsEvent {
  final String applicationId;

  const ApplicationsCancelRequested(this.applicationId);

  @override
  List<Object?> get props => [applicationId];
}

class ApplicationsAuditLogRequested extends ApplicationsEvent {
  final String applicationId;

  const ApplicationsAuditLogRequested(this.applicationId);

  @override
  List<Object?> get props => [applicationId];
}

class ApplicationsApplyRequested extends ApplicationsEvent {
  final String jobId;

  const ApplicationsApplyRequested(this.jobId);

  @override
  List<Object?> get props => [jobId];
}

// Applications States
abstract class ApplicationsState extends Equatable {
  const ApplicationsState();

  @override
  List<Object?> get props => [];
}

class ApplicationsInitial extends ApplicationsState {}

class ApplicationsLoading extends ApplicationsState {}

class ApplicationsLoaded extends ApplicationsState {
  final List<Application> applications;

  const ApplicationsLoaded(this.applications);

  @override
  List<Object?> get props => [applications];
}

class ApplicationsDetailLoaded extends ApplicationsState {
  final Application application;

  const ApplicationsDetailLoaded(this.application);

  @override
  List<Object?> get props => [application];
}

class ApplicationsAuditLogLoaded extends ApplicationsState {
  final String applicationId;
  final List<Map<String, dynamic>> auditLog;

  const ApplicationsAuditLogLoaded({
    required this.applicationId,
    required this.auditLog,
  });

  @override
  List<Object?> get props => [applicationId, auditLog];
}

class ApplicationsError extends ApplicationsState {
  final String message;

  const ApplicationsError(this.message);

  @override
  List<Object?> get props => [message];
}

class ApplicationsSuccess extends ApplicationsState {
  final String message;

  const ApplicationsSuccess(this.message);

  @override
  List<Object?> get props => [message];
}

// Applications BLoC
class ApplicationsBloc extends Bloc<ApplicationsEvent, ApplicationsState> {
  final ApplicationRepository _applicationRepository;

  ApplicationsBloc(this._applicationRepository) : super(ApplicationsInitial()) {
    on<ApplicationsLoadRequested>(_onApplicationsLoadRequested);
    on<ApplicationsRefreshRequested>(_onApplicationsRefreshRequested);
    on<ApplicationsDetailRequested>(_onApplicationsDetailRequested);
    on<ApplicationsCancelRequested>(_onApplicationsCancelRequested);
    on<ApplicationsAuditLogRequested>(_onApplicationsAuditLogRequested);
    on<ApplicationsApplyRequested>(_onApplicationsApplyRequested);
  }

  Future<void> _onApplicationsLoadRequested(
    ApplicationsLoadRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      final applications = await _applicationRepository.getApplications();
      emit(ApplicationsLoaded(applications));
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }

  Future<void> _onApplicationsRefreshRequested(
    ApplicationsRefreshRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      final applications = await _applicationRepository.getApplications();
      emit(ApplicationsLoaded(applications));
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }

  Future<void> _onApplicationsDetailRequested(
    ApplicationsDetailRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      final application = await _applicationRepository.getApplicationDetails(
        event.applicationId,
      );
      emit(ApplicationsDetailLoaded(application));
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }

  Future<void> _onApplicationsCancelRequested(
    ApplicationsCancelRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      await _applicationRepository.cancelApplication(
        event.applicationId,
      );
      emit(ApplicationsSuccess('Application cancelled successfully'));
      // Reload applications
      add(ApplicationsLoadRequested());
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }

  Future<void> _onApplicationsAuditLogRequested(
    ApplicationsAuditLogRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      final auditLog = await _applicationRepository.getApplicationAuditLog(
        event.applicationId,
      );
      emit(ApplicationsAuditLogLoaded(
        applicationId: event.applicationId,
        auditLog: auditLog.cast<Map<String, dynamic>>(),
      ));
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }

  Future<void> _onApplicationsApplyRequested(
    ApplicationsApplyRequested event,
    Emitter<ApplicationsState> emit,
  ) async {
    emit(ApplicationsLoading());
    try {
      await _applicationRepository.createApplication(
        event.jobId,
      );
      emit(ApplicationsSuccess('Application submitted successfully'));
      // Reload applications
      add(ApplicationsLoadRequested());
    } catch (error) {
      emit(ApplicationsError(error.toString()));
    }
  }
}
