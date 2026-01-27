import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../models/job.dart';

class JobCardWidget extends StatelessWidget {
  final Job job;
  final VoidCallback onLike;
  final VoidCallback onDislike;
  final VoidCallback onTap;

  const JobCardWidget({
    super.key,
    required this.job,
    required this.onLike,
    required this.onDislike,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(
          horizontal: AppTokens.spacingLg,
          vertical: AppTokens.spacingMd,
        ),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppTokens.radiusLg),
          boxShadow: AppTokens.shadowMd,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Company logo
            if (job.logoUrl != null)
              Padding(
                padding: const EdgeInsets.all(AppTokens.spacingLg),
                child: Center(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                    child: CachedNetworkImage(
                      imageUrl: job.logoUrl!,
                      width: 80,
                      height: 80,
                      fit: BoxFit.cover,
                      placeholder: (context, url) => Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: AppColors.divider,
                          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                        ),
                        child: const Icon(Icons.business, size: 40),
                      ),
                      errorWidget: (context, url, error) => Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: AppColors.divider,
                          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                        ),
                        child: const Icon(Icons.business, size: 40),
                      ),
                    ),
                  ),
                ),
              ),

            // Job details
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(AppTokens.spacingLg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Match score
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppTokens.spacingSm,
                        vertical: AppTokens.spacingXs,
                      ),
                      decoration: BoxDecoration(
                        gradient: _getMatchScoreGradient(),
                        borderRadius: BorderRadius.circular(AppTokens.radiusSm),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.star,
                            color: Colors.white,
                            size: 16,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${(job.matchScore * 100).toInt()}% Match',
                            style: AppTypography.labelMedium.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppTokens.spacingMd),

                    // Job title
                    Text(
                      job.title,
                      style: AppTypography.headlineSmall.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: AppTokens.spacingXs),

                    // Company name
                    Text(
                      job.company,
                      style: AppTypography.bodyLarge.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: AppTokens.spacingSm),

                    // Location
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on_outlined,
                          size: 16,
                          color: AppColors.textSecondary,
                        ),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            job.location,
                            style: AppTypography.bodyMedium.copyWith(
                              color: AppColors.textSecondary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppTokens.spacingSm),

                    // Salary range
                    if (job.salaryRange != null)
                      Row(
                        children: [
                          const Icon(
                            Icons.attach_money_outlined,
                            size: 16,
                            color: AppColors.success,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            job.salaryRange!,
                            style: AppTypography.bodyMedium.copyWith(
                              color: AppColors.success,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    const SizedBox(height: AppTokens.spacingSm),

                    // Job type
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppTokens.spacingSm,
                        vertical: AppTokens.spacingXs,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(AppTokens.radiusSm),
                      ),
                      child: Text(
                        job.type,
                        style: AppTypography.labelSmall.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(height: AppTokens.spacingMd),

                    // Skills
                    if (job.skills.isNotEmpty)
                      Wrap(
                        spacing: AppTokens.spacingXs,
                        runSpacing: AppTokens.spacingXs,
                        children: job.skills
                            .take(3)
                            .map(
                              (skill) => Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: AppTokens.spacingSm,
                                  vertical: AppTokens.spacingXs,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.background,
                                  borderRadius: BorderRadius.circular(AppTokens.radiusSm),
                                ),
                                child: Text(
                                  skill,
                                  style: AppTypography.labelSmall.copyWith(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ),
                            )
                            .toList(),
                      ),
                  ],
                ),
              ),
            ),

            // Action buttons
            Padding(
              padding: const EdgeInsets.all(AppTokens.spacingMd),
              child: Row(
                children: [
                  Expanded(
                    child: _buildActionButton(
                      icon: Icons.close_outlined,
                      label: 'Pass',
                      color: AppColors.error,
                      onTap: onDislike,
                    ),
                  ),
                  const SizedBox(width: AppTokens.spacingMd),
                  Expanded(
                    child: _buildActionButton(
                      icon: Icons.favorite_border,
                      label: 'Like',
                      color: AppColors.success,
                      onTap: onLike,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  LinearGradient _getMatchScoreGradient() {
    if (job.matchScore >= 0.8) {
      return AppColors.successGradient;
    } else if (job.matchScore >= 0.6) {
      return AppColors.primaryGradient;
    } else if (job.matchScore >= 0.4) {
      return AppColors.warningGradient;
    } else {
      return AppColors.errorGradient;
    }
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: AppTokens.spacingMd),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTypography.labelSmall.copyWith(
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
