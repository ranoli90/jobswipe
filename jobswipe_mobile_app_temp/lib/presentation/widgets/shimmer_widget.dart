import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';

/// Base shimmer widget that wraps the shimmer effect
class ShimmerWidget extends StatelessWidget {
  final Widget child;
  final bool isLoading;

  const ShimmerWidget({
    super.key,
    required this.child,
    this.isLoading = true,
  });

  @override
  Widget build(BuildContext context) {
    if (!isLoading) return child;

    return Shimmer.fromColors(
      baseColor: AppColors.divider,
      highlightColor: AppColors.background,
      child: child,
    );
  }
}

/// Shimmer container with customizable shape
class ShimmerContainer extends StatelessWidget {
  final double width;
  final double height;
  final double borderRadius;

  const ShimmerContainer({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius = AppTokens.radiusMd,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.divider,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    );
  }
}

/// Shimmer circle for avatar-like elements
class ShimmerCircle extends StatelessWidget {
  final double size;

  const ShimmerCircle({
    super.key,
    required this.size,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppColors.divider,
        shape: BoxShape.circle,
      ),
    );
  }
}

/// Shimmer line for text-like elements
class ShimmerLine extends StatelessWidget {
  final double width;
  final double height;

  const ShimmerLine({
    super.key,
    this.width = double.infinity,
    this.height = 16,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.divider,
        borderRadius: BorderRadius.circular(height / 2),
      ),
    );
  }
}

/// Job card shimmer for loading state
class JobCardShimmer extends StatelessWidget {
  const JobCardShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    return ShimmerWidget(
      child: Container(
        margin: const EdgeInsets.symmetric(
          horizontal: AppTokens.spacingLg,
          vertical: AppTokens.spacingMd,
        ),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppTokens.radiusLg),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Logo area
            const Padding(
              padding: EdgeInsets.all(AppTokens.spacingLg),
              child: Center(
                child: ShimmerCircle(size: 80),
              ),
            ),

            // Content area
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(AppTokens.spacingLg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Match score
                    const ShimmerContainer(
                      width: 100,
                      height: 28,
                      borderRadius: AppTokens.radiusSm,
                    ),
                    const SizedBox(height: AppTokens.spacingMd),

                    // Title
                    const ShimmerLine(height: 24),
                    const SizedBox(height: AppTokens.spacingXs),

                    // Company name
                    const ShimmerLine(width: 150, height: 18),
                    const SizedBox(height: AppTokens.spacingSm),

                    // Location
                    const ShimmerLine(width: 120, height: 16),
                    const SizedBox(height: AppTokens.spacingSm),

                    // Salary
                    const ShimmerLine(width: 100, height: 16),
                    const SizedBox(height: AppTokens.spacingMd),

                    // Skills
                    Row(
                      children: [
                        ShimmerContainer(
                          width: 60,
                          height: 24,
                          borderRadius: AppTokens.radiusSm,
                        ),
                        const SizedBox(width: AppTokens.spacingXs),
                        ShimmerContainer(
                          width: 80,
                          height: 24,
                          borderRadius: AppTokens.radiusSm,
                        ),
                        const SizedBox(width: AppTokens.spacingXs),
                        ShimmerContainer(
                          width: 70,
                          height: 24,
                          borderRadius: AppTokens.radiusSm,
                        ),
                      ],
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
                    child: Container(
                      height: 48,
                      decoration: BoxDecoration(
                        color: AppColors.divider,
                        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppTokens.spacingMd),
                  Expanded(
                    child: Container(
                      height: 48,
                      decoration: BoxDecoration(
                        color: AppColors.divider,
                        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                      ),
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
}

/// Application list item shimmer
class ApplicationItemShimmer extends StatelessWidget {
  const ApplicationItemShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    return ShimmerWidget(
      child: Container(
        padding: const EdgeInsets.all(AppTokens.spacingMd),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        child: Row(
          children: [
            // Company logo
            const ShimmerCircle(size: 48),
            const SizedBox(width: AppTokens.spacingMd),

            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const ShimmerLine(width: 200, height: 18),
                  const SizedBox(height: AppTokens.spacingXs),
                  const ShimmerLine(width: 120, height: 14),
                  const SizedBox(height: AppTokens.spacingXs),
                  Row(
                    children: [
                      ShimmerContainer(
                        width: 80,
                        height: 20,
                        borderRadius: AppTokens.radiusSm,
                      ),
                      const SizedBox(width: AppTokens.spacingSm),
                      const ShimmerLine(width: 60, height: 12),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Profile shimmer loading widget
class ProfileShimmer extends StatelessWidget {
  const ProfileShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    return ShimmerWidget(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppTokens.spacingLg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Avatar
            const ShimmerCircle(size: 100),
            const SizedBox(height: AppTokens.spacingXl),

            // Form fields
            for (int i = 0; i < 5; i++) ...[
              const ShimmerLine(height: 56),
              const SizedBox(height: AppTokens.spacingMd),
            ],

            // Skills section
            const Align(
              alignment: Alignment.centerLeft,
              child: ShimmerLine(width: 100, height: 20),
            ),
            const SizedBox(height: AppTokens.spacingMd),
            Row(
              children: [
                ShimmerContainer(
                  width: 80,
                  height: 32,
                  borderRadius: AppTokens.radiusMd,
                ),
                const SizedBox(width: AppTokens.spacingSm),
                ShimmerContainer(
                  width: 70,
                  height: 32,
                  borderRadius: AppTokens.radiusMd,
                ),
                const SizedBox(width: AppTokens.spacingSm),
                ShimmerContainer(
                  width: 90,
                  height: 32,
                  borderRadius: AppTokens.radiusMd,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// List shimmer for generic list loading
class ListShimmer extends StatelessWidget {
  final int itemCount;
  final double itemHeight;

  const ListShimmer({
    super.key,
    this.itemCount = 5,
    this.itemHeight = 80,
  });

  @override
  Widget build(BuildContext context) {
    return ShimmerWidget(
      child: ListView.builder(
        padding: const EdgeInsets.all(AppTokens.spacingMd),
        itemCount: itemCount,
        itemBuilder: (context, index) {
          return Container(
            height: itemHeight,
            margin: const EdgeInsets.only(bottom: AppTokens.spacingMd),
            decoration: BoxDecoration(
              color: AppColors.divider,
              borderRadius: BorderRadius.circular(AppTokens.radiusMd),
            ),
          );
        },
      ),
    );
  }
}
