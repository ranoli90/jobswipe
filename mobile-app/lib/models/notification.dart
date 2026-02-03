/// Notification types for the app
enum NotificationType {
  applicationUpdate,
  jobMatch,
  message,
  system,
  profile,
}

class JobSwipeNotification {
  final String id;
  final String? taskId;
  final NotificationType type;
  final String title;
  final String message;
  final Map<String, dynamic>? data;
  final bool isRead;
  final bool delivered;
  final DateTime createdAt;
  final DateTime? readAt;

  JobSwipeNotification({
    required this.id,
    this.taskId,
    required this.type,
    required this.title,
    required this.message,
    this.data,
    required this.isRead,
    required this.delivered,
    required this.createdAt,
    this.readAt,
  });

  /// Parse type string to enum
  static NotificationType _parseType(String type) {
    switch (type.toLowerCase()) {
      case 'application_update':
      case 'application':
        return NotificationType.applicationUpdate;
      case 'job_match':
      case 'job':
        return NotificationType.jobMatch;
      case 'message':
        return NotificationType.message;
      case 'profile':
        return NotificationType.profile;
      case 'system':
      default:
        return NotificationType.system;
    }
  }

  factory JobSwipeNotification.fromJson(Map<String, dynamic> json) {
    return JobSwipeNotification(
      id: json['id'] as String,
      taskId: json['task_id'] as String?,
      type: _parseType(json['type'] as String),
      title: json['title'] as String,
      message: json['message'] as String,
      data: json['metadata'] as Map<String, dynamic>? ?? json['data'] as Map<String, dynamic>?,
      isRead: json['read'] as bool? ?? false,
      delivered: json['delivered'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at'] as String) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'task_id': taskId,
      'type': type.toString().split('.').last,
      'title': title,
      'message': message,
      'metadata': data,
      'read': isRead,
      'delivered': delivered,
      'created_at': createdAt.toIso8601String(),
      'read_at': readAt?.toIso8601String(),
    };
  }

  JobSwipeNotification copyWith({
    String? id,
    String? taskId,
    NotificationType? type,
    String? title,
    String? message,
    Map<String, dynamic>? data,
    bool? isRead,
    bool? delivered,
    DateTime? createdAt,
    DateTime? readAt,
  }) {
    return JobSwipeNotification(
      id: id ?? this.id,
      taskId: taskId ?? this.taskId,
      type: type ?? this.type,
      title: title ?? this.title,
      message: message ?? this.message,
      data: data ?? this.data,
      isRead: isRead ?? this.isRead,
      delivered: delivered ?? this.delivered,
      createdAt: createdAt ?? this.createdAt,
      readAt: readAt ?? this.readAt,
    );
  }
}

/// Legacy Notification class for backward compatibility
typedef Notification = JobSwipeNotification;