import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../../models/application.dart';
import '../../bloc/applications/applications_bloc.dart';

class ApplicationDetailScreen extends StatefulWidget {
  final String applicationId;

  const ApplicationDetailScreen({
    super.key,
    required this.applicationId,
  });

  @override
  State<ApplicationDetailScreen> createState() => _ApplicationDetailScreenState();
}

class _ApplicationDetailScreenState extends State<ApplicationDetailScreen> {
  @override
  void initState() {
    super.initState();
    context.read<ApplicationsBloc>().add(
      ApplicationsDetailRequested(widget.applicationId),
    );
  }

  void _onCancelApplication() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Application'),
        content: const Text(
          'Are you sure you want to cancel this application? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.read<ApplicationsBloc>().add(
                ApplicationsCancelRequested(widget.applicationId),
              );
            },
            child: const Text(
              'Yes, Cancel',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }

  void _onViewAuditLog() {
    context.read<ApplicationsBloc>().add(
      ApplicationsAuditLogRequested(widget.applicationId),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Application Details',
          style: AppTypography.titleLarge.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: true,
        elevation: 0,
        backgroundColor: AppColors.surface,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: _onViewAuditLog,
            tooltip: 'View Audit Log',
          ),
        ],
      ),
      body: BlocListener<ApplicationsBloc, ApplicationsState>(
        listener: (context, state) {
          if (state is ApplicationsSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.success,
              ),
            );
            if (state.message.contains('cancelled')) {
              Navigator.of(context).pop();
            }
          }

          if (state is ApplicationsError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }

          if (state is ApplicationsAuditLogLoaded) {
            _showAuditLogDialog(state.auditLog);
          }
        },
        child: BlocBuilder<ApplicationsBloc, ApplicationsState>(
          builder: (context, state) {
            if (state is ApplicationsLoading) {
              return const Center(
                child: CircularProgressIndicator(),
              );
            }

            if (state is ApplicationsDetailLoaded) {
              return _buildApplicationDetails(state.application);
            }

            if (state is ApplicationsError) {
              return _buildErrorState(state.message);
            }

            return const Center(
              child: CircularProgressIndicator(),
            );
          },
        ),
      ),
    );
  }

  Widget _buildApplicationDetails(Application application) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppTokens.spacingLg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Job info card
          _buildJobInfoCard(application),
          const SizedBox(height: AppTokens.spacingLg),

          // Status section
          _buildStatusSection(application),
          const SizedBox(height: AppTokens.spacingLg),

          // Application details
          _buildDetailsSection(application),
          const SizedBox(height: AppTokens.spacingLg),

          // Cover letter preview
          if (application.coverLetter != null && application.coverLetter!.isNotEmpty)
            _buildCoverLetterSection(application.coverLetter!),

          const SizedBox(height: AppTokens.spacingXl),

          // Cancel button
          if (application.status.toLowerCase() != 'cancelled' &&
              application.status.toLowerCase() != 'completed')
            SizedBox(
              width: double.infinity,
              height: 56,
              child: OutlinedButton.icon(
                onPressed: _onCancelApplication,
                icon: const Icon(Icons.cancel_outlined, color: AppColors.error),
                label: Text(
                  'Cancel Application',
                  style: AppTypography.titleMedium.copyWith(
                    color: AppColors.error,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.error),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppTokens.radiusLg),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildJobInfoCard(Application application) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingLg),
      decoration: BoxDecoration(
        gradient: AppColors.primaryGradient,
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
        boxShadow: AppTokens.shadowMd,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            application.jobTitle ?? 'Unknown Position',
            style: AppTypography.headlineSmall.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: AppTokens.spacingXs),
          Text(
            application.companyName ?? 'Unknown Company',
            style: AppTypography.bodyLarge.copyWith(
              color: Colors.white.withValues(alpha: 0.9),
            ),
          ),
          if (application.jobLocation != null) ...[
            const SizedBox(height: AppTokens.spacingSm),
            Row(
              children: [
                Icon(
                  Icons.location_on_outlined,
                  size: 16,
                  color: Colors.white.withValues(alpha: 0.8),
                ),
                const SizedBox(width: 4),
                Text(
                  application.jobLocation!,
                  style: AppTypography.bodyMedium.copyWith(
                    color: Colors.white.withValues(alpha: 0.8),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusSection(Application application) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingLg),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Application Status',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppTokens.spacingMd,
                  vertical: AppTokens.spacingSm,
                ),
                decoration: BoxDecoration(
                  color: _getStatusColor(application.status).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _getStatusIcon(application.status),
                      size: 20,
                      color: _getStatusColor(application.status),
                    ),
                    const SizedBox(width: AppTokens.spacingXs),
                    Text(
                      _formatStatus(application.status),
                      style: AppTypography.bodyMedium.copyWith(
                        color: _getStatusColor(application.status),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppTokens.spacingMd),
          // Progress indicator
          LinearProgressIndicator(
            value: _getProgressValue(application.status),
            backgroundColor: AppColors.divider,
            valueColor: AlwaysStoppedAnimation<Color>(
              _getStatusColor(application.status),
            ),
            borderRadius: BorderRadius.circular(AppTokens.radiusSm),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsSection(Application application) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingLg),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Application Details',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          _buildDetailRow(
            'Applied On',
            application.appliedAt != null
                ? DateFormat('MMM d, yyyy').format(application.appliedAt!)
                : 'Unknown date',
          ),
          const Divider(height: AppTokens.spacingLg),
          if (application.autoApply)
            _buildDetailRow('Application Type', 'Auto-Applied'),
          if (application.resumeUrl != null)
            _buildDetailRow('Resume', 'Uploaded'),
          if (application.source != null)
            _buildDetailRow('Source', application.source!),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppTokens.spacingXs),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCoverLetterSection(String coverLetter) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingLg),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cover Letter',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          Text(
            coverLetter,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textPrimary,
              height: 1.5,
            ),
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
            'Failed to load application',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTokens.spacingXs),
          Text(
            message,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textSecondary.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppTokens.spacingLg),
          ElevatedButton(
            onPressed: () {
              context.read<ApplicationsBloc>().add(
                ApplicationsDetailRequested(widget.applicationId),
              );
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  void _showAuditLogDialog(List<Map<String, dynamic>> auditLog) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Application History'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.separated(
            shrinkWrap: true,
            itemCount: auditLog.length,
            separatorBuilder: (_, __) => const Divider(),
            itemBuilder: (context, index) {
              final log = auditLog[index];
              return ListTile(
                leading: Icon(
                  _getAuditLogIcon(log['action'] ?? ''),
                  color: AppColors.primary,
                ),
                title: Text(
                  log['action'] ?? 'Unknown',
                  style: AppTypography.bodyMedium.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: Text(
                  log['timestamp'] != null
                      ? DateFormat('MMM d, yyyy HH:mm').format(
                          DateTime.parse(log['timestamp']),
                        )
                      : 'Unknown date',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return AppColors.warning;
      case 'in_progress':
        return AppColors.primary;
      case 'completed':
        return AppColors.success;
      case 'failed':
        return AppColors.error;
      case 'cancelled':
        return AppColors.textSecondary;
      default:
        return AppColors.textSecondary;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return Icons.pending_outlined;
      case 'in_progress':
        return Icons.sync_outlined;
      case 'completed':
        return Icons.check_circle_outline;
      case 'failed':
        return Icons.error_outline;
      case 'cancelled':
        return Icons.cancel_outlined;
      default:
        return Icons.help_outline;
    }
  }

  IconData _getAuditLogIcon(String action) {
    switch (action.toLowerCase()) {
      case 'created':
        return Icons.add_circle_outline;
      case 'updated':
        return Icons.edit_outlined;
      case 'cancelled':
        return Icons.cancel_outlined;
      case 'submitted':
        return Icons.send_outlined;
      case 'reviewed':
        return Icons.visibility_outlined;
      default:
        return Icons.info_outline;
    }
  }

  String _formatStatus(String status) {
    return status.split('_').map((word) {
      if (word.isEmpty) return '';
      return word[0].toUpperCase() + word.substring(1);
    }).join(' ');
  }

  double _getProgressValue(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return 0.25;
      case 'in_progress':
        return 0.6;
      case 'completed':
        return 1.0;
      case 'failed':
      case 'cancelled':
        return 1.0;
      default:
        return 0.0;
    }
  }
}
