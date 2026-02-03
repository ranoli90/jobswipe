class Application {
  final String id;
  final String jobId;
  final String status;
  final int attemptCount;
  final String? lastError;
  final String? assignedWorker;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  // Extended fields for UI
  final String? jobTitle;
  final String? companyName;
  final String? jobLocation;
  final String? coverLetter;
  final String? resumeUrl;
  final bool autoApply;
  final String? source;
  final DateTime? appliedAt;

  Application({
    required this.id,
    required this.jobId,
    required this.status,
    required this.attemptCount,
    this.lastError,
    this.assignedWorker,
    required this.createdAt,
    required this.updatedAt,
    this.jobTitle,
    this.companyName,
    this.jobLocation,
    this.coverLetter,
    this.resumeUrl,
    this.autoApply = false,
    this.source,
    this.appliedAt,
  });

  factory Application.fromJson(Map<String, dynamic> json) {
    return Application(
      id: json['id'] as String,
      jobId: json['job_id'] as String,
      status: json['status'] as String,
      attemptCount: json['attempt_count'] as int? ?? 0,
      lastError: json['last_error'] as String?,
      assignedWorker: json['assigned_worker'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      jobTitle: json['job_title'] as String? ?? json['job']?['title'] as String?,
      companyName: json['company_name'] as String? ?? json['job']?['company'] as String?,
      jobLocation: json['job_location'] as String? ?? json['job']?['location'] as String?,
      coverLetter: json['cover_letter'] as String?,
      resumeUrl: json['resume_url'] as String?,
      autoApply: json['auto_apply'] as bool? ?? false,
      source: json['source'] as String?,
      appliedAt: json['applied_at'] != null 
          ? DateTime.parse(json['applied_at'] as String) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'job_id': jobId,
      'status': status,
      'attempt_count': attemptCount,
      'last_error': lastError,
      'assigned_worker': assignedWorker,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'job_title': jobTitle,
      'company_name': companyName,
      'job_location': jobLocation,
      'cover_letter': coverLetter,
      'resume_url': resumeUrl,
      'auto_apply': autoApply,
      'source': source,
      'applied_at': appliedAt?.toIso8601String(),
    };
  }

  Application copyWith({
    String? id,
    String? jobId,
    String? status,
    int? attemptCount,
    String? lastError,
    String? assignedWorker,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? jobTitle,
    String? companyName,
    String? jobLocation,
    String? coverLetter,
    String? resumeUrl,
    bool? autoApply,
    String? source,
    DateTime? appliedAt,
  }) {
    return Application(
      id: id ?? this.id,
      jobId: jobId ?? this.jobId,
      status: status ?? this.status,
      attemptCount: attemptCount ?? this.attemptCount,
      lastError: lastError ?? this.lastError,
      assignedWorker: assignedWorker ?? this.assignedWorker,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      jobTitle: jobTitle ?? this.jobTitle,
      companyName: companyName ?? this.companyName,
      jobLocation: jobLocation ?? this.jobLocation,
      coverLetter: coverLetter ?? this.coverLetter,
      resumeUrl: resumeUrl ?? this.resumeUrl,
      autoApply: autoApply ?? this.autoApply,
      source: source ?? this.source,
      appliedAt: appliedAt ?? this.appliedAt,
    );
  }
}

class ApplicationAuditLog {
  final String id;
  final String step;
  final Map<String, dynamic> payload;
  final Map<String, dynamic> artifacts;
  final DateTime timestamp;
  final bool success;

  ApplicationAuditLog({
    required this.id,
    required this.step,
    required this.payload,
    required this.artifacts,
    required this.timestamp,
    required this.success,
  });

  factory ApplicationAuditLog.fromJson(Map<String, dynamic> json) {
    return ApplicationAuditLog(
      id: json['id'] as String,
      step: json['step'] as String,
      payload: json['payload'] as Map<String, dynamic>,
      artifacts: json['artifacts'] as Map<String, dynamic>,
      timestamp: DateTime.parse(json['timestamp'] as String),
      success: json['success'] as bool? ?? !json['step'].toString().toLowerCase().contains('error'),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'step': step,
      'payload': payload,
      'artifacts': artifacts,
      'timestamp': timestamp.toIso8601String(),
      'success': success,
    };
  }
}