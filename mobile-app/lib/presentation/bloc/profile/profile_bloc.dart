import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:image_picker/image_picker.dart';
import '../../../data/profile_repository.dart';
import '../../../models/profile.dart';

// Profile Events
abstract class ProfileEvent extends Equatable {
  const ProfileEvent();

  @override
  List<Object?> get props => [];
}

class ProfileLoadRequested extends ProfileEvent {}

class ProfileUpdateRequested extends ProfileEvent {
  final Map<String, dynamic> data;

  const ProfileUpdateRequested(this.data);

  @override
  List<Object?> get props => [data];
}

class ProfileResumeUploadRequested extends ProfileEvent {
  final XFile file;

  const ProfileResumeUploadRequested(this.file);

  @override
  List<Object?> get props => [file];
}

class ProfileSkillsUpdateRequested extends ProfileEvent {
  final List<String> skills;

  const ProfileSkillsUpdateRequested(this.skills);

  @override
  List<Object?> get props => [skills];
}

class ProfileWorkExperienceUpdateRequested extends ProfileEvent {
  final List<Map<String, dynamic>> experience;

  const ProfileWorkExperienceUpdateRequested(this.experience);

  @override
  List<Object?> get props => [experience];
}

class ProfileEducationUpdateRequested extends ProfileEvent {
  final List<Map<String, dynamic>> education;

  const ProfileEducationUpdateRequested(this.education);

  @override
  List<Object?> get props => [education];
}

class ProfileEditModeToggled extends ProfileEvent {}

// Profile States
abstract class ProfileState extends Equatable {
  const ProfileState();

  @override
  List<Object?> get props => [];
}

class ProfileInitial extends ProfileState {}

class ProfileLoading extends ProfileState {}

class ProfileLoaded extends ProfileState {
  final User user;
  final bool isEditing;

  const ProfileLoaded(this.user, {this.isEditing = false});

  @override
  List<Object?> get props => [user, isEditing];
}

class ProfileUpdated extends ProfileState {
  final User user;
  final String message;
  final bool isEditing;

  const ProfileUpdated({
    required this.user,
    required this.message,
    this.isEditing = false,
  });

  @override
  List<Object?> get props => [user, message, isEditing];
}

class ProfileResumeUploaded extends ProfileState {
  final String resumeUrl;

  const ProfileResumeUploaded(this.resumeUrl);

  @override
  List<Object?> get props => [resumeUrl];
}

class ProfileError extends ProfileState {
  final String message;

  const ProfileError(this.message);

  @override
  List<Object?> get props => [message];
}

// Profile BLoC
class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  final ProfileRepository _profileRepository;

  ProfileBloc(this._profileRepository) : super(ProfileInitial()) {
    on<ProfileLoadRequested>(_onProfileLoadRequested);
    on<ProfileUpdateRequested>(_onProfileUpdateRequested);
    on<ProfileResumeUploadRequested>(_onProfileResumeUploadRequested);
    on<ProfileSkillsUpdateRequested>(_onProfileSkillsUpdateRequested);
    on<ProfileWorkExperienceUpdateRequested>(
      _onProfileWorkExperienceUpdateRequested,
    );
    on<ProfileEducationUpdateRequested>(_onProfileEducationUpdateRequested);
    on<ProfileEditModeToggled>(_onProfileEditModeToggled);
  }

  Future<void> _onProfileLoadRequested(
    ProfileLoadRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.getProfile();

    result.fold(
      (error) => emit(ProfileError(error)),
      (user) => emit(ProfileLoaded(user)),
    );
  }

  Future<void> _onProfileUpdateRequested(
    ProfileUpdateRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.updateProfile(event.data);

    result.fold(
      (error) => emit(ProfileError(error)),
      (user) => emit(ProfileUpdated(
        user: user,
        message: 'Profile updated successfully',
      )),
    );
  }

  Future<void> _onProfileResumeUploadRequested(
    ProfileResumeUploadRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.uploadResume(event.file);

    result.fold(
      (error) => emit(ProfileError(error)),
      (resumeUrl) => emit(ProfileResumeUploaded(resumeUrl)),
    );
  }

  Future<void> _onProfileSkillsUpdateRequested(
    ProfileSkillsUpdateRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.updateSkills(event.skills);

    result.fold(
      (error) => emit(ProfileError(error)),
      (_) {
        // Reload profile to get updated data
        add(ProfileLoadRequested());
      },
    );
  }

  Future<void> _onProfileWorkExperienceUpdateRequested(
    ProfileWorkExperienceUpdateRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.updateWorkExperience(
      event.experience,
    );

    result.fold(
      (error) => emit(ProfileError(error)),
      (_) {
        // Reload profile to get updated data
        add(ProfileLoadRequested());
      },
    );
  }

  Future<void> _onProfileEducationUpdateRequested(
    ProfileEducationUpdateRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(ProfileLoading());
    final result = await _profileRepository.updateEducation(event.education);

    result.fold(
      (error) => emit(ProfileError(error)),
      (_) {
        // Reload profile to get updated data
        add(ProfileLoadRequested());
      },
    );
  }

  Future<void> _onProfileEditModeToggled(
    ProfileEditModeToggled event,
    Emitter<ProfileState> emit,
  ) async {
    final currentState = state;
    if (currentState is ProfileLoaded) {
      emit(ProfileLoaded(currentState.user, isEditing: !currentState.isEditing));
    } else if (currentState is ProfileUpdated) {
      emit(ProfileUpdated(
        user: currentState.user,
        message: currentState.message,
        isEditing: !currentState.isEditing,
      ));
    }
  }
}
