class Notification {
  final String id;
  final String? taskId;
  final String type;
  final String title;
  final String message;
  final Map<String, dynamic>? metadata;
  final bool read;
  final bool delivered;
  final DateTime createdAt;
  final DateTime? readAt;

  Notification({
    required this.id,
    this.taskId,
    required this.type,
    required this.title,
    required this.message,
    this.metadata,
    required this.read,
    required this.delivered,
    required this.createdAt,
    this.readAt,
  });

  factory Notification.fromJson(Map<String, dynamic> json) {
    return Notification(
      id: json['id'] as String,
      taskId: json['task_id'] as String?,
      type: json['type'] as String,
      title: json['title'] as String,
      message: json['message'] as String,
      metadata: json['metadata'] as Map<String, dynamic>?,
      read: json['read'] as bool? ?? false,
      delivered: json['delivered'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at'] as String) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'task_id': taskId,
      'type': type,
      'title': title,
      'message': message,
      'metadata': metadata,
      'read': read,
      'delivered': delivered,
      'created_at': createdAt.toIso8601String(),
      'read_at': readAt?.toIso8601String(),
    };
  }

  Notification copyWith({
    String? id,
    String? taskId,
    String? type,
    String? title,
    String? message,
    Map<String, dynamic>? metadata,
    bool? read,
    bool? delivered,
    DateTime? createdAt,
    DateTime? readAt,
  }) {
    return Notification(
      id: id ?? this.id,
      taskId: taskId ?? this.taskId,
      type: type ?? this.type,
      title: title ?? this.title,
      message: message ?? this.message,
      metadata: metadata ?? this.metadata,
      read: read ?? this.read,
      delivered: delivered ?? this.delivered,
      createdAt: createdAt ?? this.createdAt,
      readAt: readAt ?? this.readAt,
    );
  }
}