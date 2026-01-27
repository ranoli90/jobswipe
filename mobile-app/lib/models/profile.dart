class Profile {
  final String id;
  final String? fullName;
  final String? phone;
  final String? location;
  final String? headline;
  final List<dynamic>? workExperience;
  final List<dynamic>? education;
  final List<String>? skills;
  final String? resumeFileUrl;
  final DateTime? parsedAt;
  final ProfilePreferences? preferences;

  Profile({
    required this.id,
    this.fullName,
    this.phone,
    this.location,
    this.headline,
    this.workExperience,
    this.education,
    this.skills,
    this.resumeFileUrl,
    this.parsedAt,
    this.preferences,
  });

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'] as String,
      fullName: json['full_name'] as String?,
      phone: json['phone'] as String?,
      location: json['location'] as String?,
      headline: json['headline'] as String?,
      workExperience: json['work_experience'] as List<dynamic>?,
      education: json['education'] as List<dynamic>?,
      skills: (json['skills'] as List<dynamic>?)?.cast<String>(),
      resumeFileUrl: json['resume_file_url'] as String?,
      parsedAt: json['parsed_at'] != null ? DateTime.parse(json['parsed_at'] as String) : null,
      preferences: json['preferences'] != null ? ProfilePreferences.fromJson(json['preferences'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'phone': phone,
      'location': location,
      'headline': headline,
      'work_experience': workExperience,
      'education': education,
      'skills': skills,
      'resume_file_url': resumeFileUrl,
      'parsed_at': parsedAt?.toIso8601String(),
      'preferences': preferences?.toJson(),
    };
  }
}

class ProfilePreferences {
  final List<String>? jobTypes;
  final String? remotePreference;
  final String? experienceLevel;

  ProfilePreferences({
    this.jobTypes,
    this.remotePreference,
    this.experienceLevel,
  });

  factory ProfilePreferences.fromJson(Map<String, dynamic> json) {
    return ProfilePreferences(
      jobTypes: (json['job_types'] as List<dynamic>?)?.cast<String>(),
      remotePreference: json['remote_preference'] as String?,
      experienceLevel: json['experience_level'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'job_types': jobTypes,
      'remote_preference': remotePreference,
      'experience_level': experienceLevel,
    };
  }
}

class ProfileUpdate {
  final String? fullName;
  final String? phone;
  final String? location;
  final String? headline;
  final List<String>? skills;
  final List<dynamic>? experience;
  final List<dynamic>? education;
  final ProfilePreferences? preferences;

  ProfileUpdate({
    this.fullName,
    this.phone,
    this.location,
    this.headline,
    this.skills,
    this.experience,
    this.education,
    this.preferences,
  });

  Map<String, dynamic> toJson() {
    return {
      'full_name': fullName,
      'phone': phone,
      'location': location,
      'headline': headline,
      'skills': skills,
      'experience': experience,
      'education': education,
      'preferences': preferences?.toJson(),
    };
  }
}