import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../bloc/jobs/jobs_bloc.dart';
import '../../../models/job.dart';

class JobDetailScreen extends StatelessWidget {
  final String jobId;

  const JobDetailScreen({
    super.key,
    required this.jobId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Job Details',
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
          onPressed: () {
            Navigator.of(context).pop();
          },
        ),
      ),
      body: BlocProvider(
        create: (context) => JobsBloc(
          RepositoryProvider.of(context),
        )..add(JobsJobDetailRequested(jobId)),
        child: BlocBuilder<JobsBloc, JobsState>(
          builder: (context, state) {
            if (state is JobsLoading) {
              return const Center(
                child: CircularProgressIndicator(),
              );
            }

            if (state is JobsError) {
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
                      'Failed to load job details',
                      style: AppTypography.bodyLarge.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: AppTokens.spacingMd),
                    ElevatedButton(
                      onPressed: () {
                        context.read<JobsBloc>().add(JobsJobDetailRequested(jobId));
                      },
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              );
            }

            if (state is JobsJobDetailLoaded) {
              final job = state.job;
              return SingleChildScrollView(
                padding: const EdgeInsets.all(AppTokens.spacingLg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildJobHeader(job),
                    const SizedBox(height: AppTokens.spacingLg),
                    _buildJobDetails(job),
                    const SizedBox(height: AppTokens.spacingLg),
                    _buildJobDescription(job),
                    const SizedBox(height: AppTokens.spacingLg),
                    _buildActionButtons(context, job),
                  ],
                ),
              );
            }

            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }

  Widget _buildJobHeader(Job job) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          job.title,
          style: AppTypography.headlineSmall.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: AppTokens.spacingSm),
        Text(
          job.company,
          style: AppTypography.bodyLarge.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: AppTokens.spacingSm),
        Row(
          children: [
            const Icon(
              Icons.location_on,
              size: 16,
              color: AppColors.textSecondary,
            ),
            const SizedBox(width: 4),
            Text(
              job.location,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppTokens.spacingSm),
        Row(
          children: [
            const Icon(
              Icons.attach_money,
              size: 16,
              color: AppColors.textSecondary,
            ),
            const SizedBox(width: 4),
            Text(
              job.salary,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildJobDetails(Job job) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingMd),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Job Details',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          _buildDetailRow('Employment Type', job.employmentType),
          const SizedBox(height: AppTokens.spacingSm),
          _buildDetailRow('Experience Level', job.experienceLevel),
          const SizedBox(height: AppTokens.spacingSm),
          _buildDetailRow('Industry', job.industry),
          const SizedBox(height: AppTokens.spacingSm),
          _buildDetailRow('Posted Date', job.postedDate),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 1,
          child: Text(
            label,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        Expanded(
          flex: 2,
          child: Text(
            value,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildJobDescription(Job job) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingMd),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Description',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTokens.spacingMd),
          Text(
            job.description,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textPrimary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, Job job) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () {
              // Apply for job
              _applyForJob(context, job);
            },
            child: Text(
              'Apply Now',
              style: AppTypography.bodyLarge.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: AppTokens.spacingMd),
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.onPrimary,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.radiusMd),
              ),
            ),
          ),
        ),
        const SizedBox(height: AppTokens.spacingMd),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () {
              // Save job
              _saveJob(context, job);
            },
            child: Text(
              'Save Job',
              style: AppTypography.bodyLarge.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: AppTokens.spacingMd),
              foregroundColor: AppColors.primary,
              side: BorderSide(color: AppColors.primary),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppTokens.radiusMd),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _applyForJob(BuildContext context, Job job) {
    // TODO: Implement job application logic
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Application for ${job.title} will be processed'),
        backgroundColor: AppColors.success,
      ),
    );
  }

  void _saveJob(BuildContext context, Job job) {
    // TODO: Implement save job logic
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('${job.title} saved to your jobs'),
        backgroundColor: AppColors.success,
      ),
    );
  }
}
