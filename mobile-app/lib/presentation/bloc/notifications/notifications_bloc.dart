import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../core/repositories/notification_repository.dart';
import '../../../models/notification.dart';

// Notifications Events
abstract class NotificationsEvent extends Equatable {
  const NotificationsEvent();

  @override
  List<Object?> get props => [];
}

class NotificationsLoadRequested extends NotificationsEvent {}

class NotificationsRefreshRequested extends NotificationsEvent {}

class NotificationsMarkAsReadRequested extends NotificationsEvent {
  final String notificationId;

  const NotificationsMarkAsReadRequested(this.notificationId);

  @override
  List<Object?> get props => [notificationId];
}

class NotificationsMarkAllAsReadRequested extends NotificationsEvent {}

class NotificationsDeleteRequested extends NotificationsEvent {
  final String notificationId;

  const NotificationsDeleteRequested(this.notificationId);

  @override
  List<Object?> get props => [notificationId];
}

// Notifications States
abstract class NotificationsState extends Equatable {
  const NotificationsState();

  @override
  List<Object?> get props => [];
}

class NotificationsInitial extends NotificationsState {}

class NotificationsLoading extends NotificationsState {}

class NotificationsLoaded extends NotificationsState {
  final List<JobSwipeNotification> notifications;
  final int unreadCount;

  const NotificationsLoaded({
    required this.notifications,
    this.unreadCount = 0,
  });

  @override
  List<Object?> get props => [notifications, unreadCount];

  NotificationsLoaded copyWith({
    List<JobSwipeNotification>? notifications,
    int? unreadCount,
  }) {
    return NotificationsLoaded(
      notifications: notifications ?? this.notifications,
      unreadCount: unreadCount ?? this.unreadCount,
    );
  }
}

class NotificationsError extends NotificationsState {
  final String message;
  final List<JobSwipeNotification> notifications;

  const NotificationsError({
    required this.message,
    this.notifications = const [],
  });

  @override
  List<Object?> get props => [message, notifications];
}

class NotificationsActionSuccess extends NotificationsState {
  final String message;

  const NotificationsActionSuccess(this.message);

  @override
  List<Object?> get props => [message];
}

// Notifications BLoC
class NotificationsBloc extends Bloc<NotificationsEvent, NotificationsState> {
  final NotificationRepository _notificationRepository;

  NotificationsBloc(this._notificationRepository)
      : super(NotificationsInitial()) {
    on<NotificationsLoadRequested>(_onLoadRequested);
    on<NotificationsRefreshRequested>(_onRefreshRequested);
    on<NotificationsMarkAsReadRequested>(_onMarkAsReadRequested);
    on<NotificationsMarkAllAsReadRequested>(_onMarkAllAsReadRequested);
    on<NotificationsDeleteRequested>(_onDeleteRequested);
  }

  Future<void> _onLoadRequested(
    NotificationsLoadRequested event,
    Emitter<NotificationsState> emit,
  ) async {
    emit(NotificationsLoading());
    try {
      final notifications = await _notificationRepository.getNotifications();
      final unreadCount = await _notificationRepository.getUnreadCount();
      emit(NotificationsLoaded(
        notifications: notifications,
        unreadCount: unreadCount,
      ));
    } catch (error) {
      emit(NotificationsError(message: error.toString()));
    }
  }

  Future<void> _onRefreshRequested(
    NotificationsRefreshRequested event,
    Emitter<NotificationsState> emit,
  ) async {
    final currentState = state;
    if (currentState is NotificationsLoaded) {
      // Keep current data while loading
      emit(currentState);
    }

    try {
      final notifications = await _notificationRepository.getNotifications();
      final unreadCount = await _notificationRepository.getUnreadCount();
      emit(NotificationsLoaded(
        notifications: notifications,
        unreadCount: unreadCount,
      ));
    } catch (error) {
      if (currentState is NotificationsLoaded) {
        emit(NotificationsError(
          message: error.toString(),
          notifications: currentState.notifications,
        ));
      } else {
        emit(NotificationsError(message: error.toString()));
      }
    }
  }

  Future<void> _onMarkAsReadRequested(
    NotificationsMarkAsReadRequested event,
    Emitter<NotificationsState> emit,
  ) async {
    final currentState = state;
    if (currentState is! NotificationsLoaded) return;

    try {
      await _notificationRepository.markAsRead(event.notificationId);

      // Update local state
      final updatedNotifications = currentState.notifications.map((n) {
        if (n.id == event.notificationId) {
          return n.copyWith(isRead: true);
        }
        return n;
      }).toList();

      final unreadCount = updatedNotifications.where((n) => !n.isRead).length;

      emit(currentState.copyWith(
        notifications: updatedNotifications,
        unreadCount: unreadCount,
      ));
    } catch (error) {
      emit(NotificationsError(
        message: error.toString(),
        notifications: currentState.notifications,
      ));
    }
  }

  Future<void> _onMarkAllAsReadRequested(
    NotificationsMarkAllAsReadRequested event,
    Emitter<NotificationsState> emit,
  ) async {
    final currentState = state;
    if (currentState is! NotificationsLoaded) return;

    try {
      await _notificationRepository.markAllAsRead();

      // Update local state
      final updatedNotifications = currentState.notifications.map((n) {
        return n.copyWith(isRead: true);
      }).toList();

      emit(currentState.copyWith(
        notifications: updatedNotifications,
        unreadCount: 0,
      ));

      emit(const NotificationsActionSuccess('All notifications marked as read'));
      emit(currentState.copyWith(
        notifications: updatedNotifications,
        unreadCount: 0,
      ));
    } catch (error) {
      emit(NotificationsError(
        message: error.toString(),
        notifications: currentState.notifications,
      ));
    }
  }

  Future<void> _onDeleteRequested(
    NotificationsDeleteRequested event,
    Emitter<NotificationsState> emit,
  ) async {
    final currentState = state;
    if (currentState is! NotificationsLoaded) return;

    try {
      await _notificationRepository.deleteNotification(event.notificationId);

      // Update local state
      final updatedNotifications = currentState.notifications
          .where((n) => n.id != event.notificationId)
          .toList();

      final unreadCount = updatedNotifications.where((n) => !n.isRead).length;

      emit(currentState.copyWith(
        notifications: updatedNotifications,
        unreadCount: unreadCount,
      ));

      emit(const NotificationsActionSuccess('Notification deleted'));
      emit(currentState.copyWith(
        notifications: updatedNotifications,
        unreadCount: unreadCount,
      ));
    } catch (error) {
      emit(NotificationsError(
        message: error.toString(),
        notifications: currentState.notifications,
      ));
    }
  }
}
