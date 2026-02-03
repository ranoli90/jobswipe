import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../models/notification.dart';
import '../../bloc/notifications/notifications_bloc.dart';
import '../../widgets/bottom_nav_bar.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<NotificationsBloc>().add(NotificationsLoadRequested());
  }

  void _onRefresh() {
    context.read<NotificationsBloc>().add(NotificationsRefreshRequested());
  }

  void _onMarkAsRead(String notificationId) {
    context.read<NotificationsBloc>().add(
      NotificationsMarkAsReadRequested(notificationId),
    );
  }

  void _onMarkAllAsRead() {
    context.read<NotificationsBloc>().add(NotificationsMarkAllAsReadRequested());
  }

  void _onDeleteNotification(String notificationId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Notification'),
        content: const Text('Are you sure you want to delete this notification?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.read<NotificationsBloc>().add(
                NotificationsDeleteRequested(notificationId),
              );
            },
            child: const Text('Delete', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }

  void _onNotificationTap(JobSwipeNotification notification) {
    // Mark as read when tapped
    if (!notification.isRead) {
      _onMarkAsRead(notification.id);
    }

    // Navigate based on notification type
    switch (notification.type) {
      case NotificationType.applicationUpdate:
        if (notification.data?['application_id'] != null) {
          Navigator.of(context).pushNamed(
            '/applications/detail',
            arguments: notification.data!['application_id'],
          );
        }
        break;
      case NotificationType.jobMatch:
        if (notification.data?['job_id'] != null) {
          Navigator.of(context).pushNamed(
            '/jobs/detail',
            arguments: notification.data!['job_id'],
          );
        }
        break;
      case NotificationType.profile:
        Navigator.of(context).pushNamed('/profile');
        break;
      default:
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return BottomNavScaffold(
      currentIndex: 0, // Notifications accessible from any tab
      appBar: AppBar(
        title: Text(
          'Notifications',
          style: AppTypography.titleLarge.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: true,
        elevation: 0,
        backgroundColor: AppColors.surface,
        actions: [
          BlocBuilder<NotificationsBloc, NotificationsState>(
            builder: (context, state) {
              if (state is NotificationsLoaded && 
                  state.notifications.any((n) => !n.isRead)) {
                return TextButton(
                  onPressed: _onMarkAllAsRead,
                  child: Text(
                    'Mark all read',
                    style: AppTypography.bodyMedium.copyWith(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: BlocListener<NotificationsBloc, NotificationsState>(
        listener: (context, state) {
          if (state is NotificationsError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }

          if (state is NotificationsActionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.success,
              ),
            );
          }
        },
        child: BlocBuilder<NotificationsBloc, NotificationsState>(
          builder: (context, state) {
            if (state is NotificationsLoading) {
              return const Center(
                child: CircularProgressIndicator(),
              );
            }

            if (state is NotificationsError && state.notifications.isEmpty) {
              return _buildErrorState(state.message);
            }

            if (state is NotificationsLoaded || 
                (state is NotificationsError && state.notifications.isNotEmpty)) {
              final notifications = state is NotificationsLoaded 
                  ? state.notifications 
                  : (state as NotificationsError).notifications;

              if (notifications.isEmpty) {
                return _buildEmptyState();
              }

              return RefreshIndicator(
                onRefresh: () async => _onRefresh(),
                child: ListView.builder(
                  padding: const EdgeInsets.all(AppTokens.spacingMd),
                  itemCount: notifications.length,
                  itemBuilder: (context, index) {
                    final notification = notifications[index];
                    return _buildNotificationCard(notification);
                  },
                ),
              );
            }

            return _buildEmptyState();
          },
        ),
      ),
    );
  }

  Widget _buildNotificationCard(JobSwipeNotification notification) {
    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      background: Container(
        margin: const EdgeInsets.only(bottom: AppTokens.spacingMd),
        decoration: BoxDecoration(
          color: AppColors.error,
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: AppTokens.spacingLg),
        child: const Icon(
          Icons.delete_outline,
          color: Colors.white,
        ),
      ),
      onDismissed: (_) => _onDeleteNotification(notification.id),
      child: GestureDetector(
        onTap: () => _onNotificationTap(notification),
        child: Container(
          margin: const EdgeInsets.only(bottom: AppTokens.spacingMd),
          decoration: BoxDecoration(
            color: notification.isRead 
                ? AppColors.surface 
                : AppColors.primary.withOpacity(0.05),
            borderRadius: BorderRadius.circular(AppTokens.radiusMd),
            border: Border.all(
              color: notification.isRead 
                  ? AppColors.divider 
                  : AppColors.primary.withOpacity(0.2),
            ),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(AppTokens.spacingMd),
            leading: Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: _getIconBackgroundColor(notification.type),
                borderRadius: BorderRadius.circular(AppTokens.radiusMd),
              ),
              child: Icon(
                _getIconForType(notification.type),
                color: _getIconColor(notification.type),
                size: 24,
              ),
            ),
            title: Text(
              notification.title,
              style: AppTypography.bodyLarge.copyWith(
                fontWeight: notification.isRead ? FontWeight.normal : FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: AppTokens.spacingXs),
                Text(
                  notification.message,
                  style: AppTypography.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: AppTokens.spacingXs),
                Text(
                  _formatTimestamp(notification.createdAt),
                  style: AppTypography.labelSmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
            trailing: notification.isRead
                ? null
                : Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.notifications_none_outlined,
            size: 64,
            color: AppColors.textSecondary.withOpacity(0.5),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          Text(
            'No notifications yet',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingXs),
          Text(
            'We\'ll notify you when something important happens',
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textSecondary.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: AppColors.error,
          ),
          const SizedBox(height: AppTokens.spacingMd),
          Text(
            'Failed to load notifications',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          ElevatedButton(
            onPressed: _onRefresh,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  IconData _getIconForType(NotificationType type) {
    switch (type) {
      case NotificationType.applicationUpdate:
        return Icons.work_outline;
      case NotificationType.jobMatch:
        return Icons.favorite_border;
      case NotificationType.message:
        return Icons.message_outlined;
      case NotificationType.system:
        return Icons.info_outline;
      case NotificationType.profile:
        return Icons.person_outline;
    }
  }

  Color _getIconBackgroundColor(NotificationType type) {
    switch (type) {
      case NotificationType.applicationUpdate:
        return AppColors.primary.withOpacity(0.1);
      case NotificationType.jobMatch:
        return AppColors.success.withOpacity(0.1);
      case NotificationType.message:
        return AppColors.accent.withOpacity(0.1);
      case NotificationType.system:
        return AppColors.warning.withOpacity(0.1);
      case NotificationType.profile:
        return AppColors.secondary.withOpacity(0.1);
    }
  }

  Color _getIconColor(NotificationType type) {
    switch (type) {
      case NotificationType.applicationUpdate:
        return AppColors.primary;
      case NotificationType.jobMatch:
        return AppColors.success;
      case NotificationType.message:
        return AppColors.accent;
      case NotificationType.system:
        return AppColors.warning;
      case NotificationType.profile:
        return AppColors.secondary;
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM d, yyyy').format(timestamp);
    }
  }
}
