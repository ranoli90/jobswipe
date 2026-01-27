class Application {
  final String id;
  final String jobId;
  final String status;
  final int attemptCount;
  final String? lastError;
  final String? assignedWorker;
  final DateTime createdAt;
  final DateTime updatedAt;

  Application({
    required this.id,
    required this.jobId,
    required this.status,
    required this.attemptCount,
    this.lastError,
    this.assignedWorker,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Application.fromJson(Map<String, dynamic> json) {
    return Application(
      id: json['id'] as String,
      jobId: json['job_id'] as String,
      status: json['status'] as String,
      attemptCount: json['attempt_count'] as int,
      lastError: json['last_error'] as String?,
      assignedWorker: json['assigned_worker'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
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
    };
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