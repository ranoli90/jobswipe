import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';
import '../../core/theme/app_typography.dart';

/// Swipe direction enum
enum SwipeDirection { left, right, up }

/// Overlay widget that shows during card swiping
class SwipeOverlay extends StatelessWidget {
  final SwipeDirection direction;
  final double progress; // 0.0 to 1.0

  const SwipeOverlay({
    super.key,
    required this.direction,
    required this.progress,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      opacity: progress.clamp(0.0, 1.0),
      duration: const Duration(milliseconds: 50),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(AppTokens.radiusLg),
          gradient: _getGradient(),
        ),
        child: Center(
          child: Transform.rotate(
            angle: _getRotation(),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppTokens.spacingXl,
                vertical: AppTokens.spacingMd,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                border: Border.all(
                  color: _getBorderColor(),
                  width: 4,
                ),
                color: _getBackgroundColor(),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _getIcon(),
                    size: 48,
                    color: _getIconColor(),
                  ),
                  const SizedBox(height: AppTokens.spacingSm),
                  Text(
                    _getLabel(),
                    style: AppTypography.headlineSmall.copyWith(
                      color: _getTextColor(),
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  LinearGradient _getGradient() {
    switch (direction) {
      case SwipeDirection.left:
        return LinearGradient(
          colors: [
            AppColors.error.withOpacity(0.3 * progress),
            Colors.transparent,
          ],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        );
      case SwipeDirection.right:
        return LinearGradient(
          colors: [
            Colors.transparent,
            AppColors.success.withOpacity(0.3 * progress),
          ],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        );
      case SwipeDirection.up:
        return LinearGradient(
          colors: [
            Colors.transparent,
            AppColors.primary.withOpacity(0.3 * progress),
          ],
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
        );
    }
  }

  Color _getBorderColor() {
    switch (direction) {
      case SwipeDirection.left:
        return AppColors.error;
      case SwipeDirection.right:
        return AppColors.success;
      case SwipeDirection.up:
        return AppColors.primary;
    }
  }

  Color _getBackgroundColor() {
    switch (direction) {
      case SwipeDirection.left:
        return AppColors.error.withOpacity(0.2);
      case SwipeDirection.right:
        return AppColors.success.withOpacity(0.2);
      case SwipeDirection.up:
        return AppColors.primary.withOpacity(0.2);
    }
  }

  Color _getIconColor() {
    switch (direction) {
      case SwipeDirection.left:
        return AppColors.error;
      case SwipeDirection.right:
        return AppColors.success;
      case SwipeDirection.up:
        return AppColors.primary;
    }
  }

  Color _getTextColor() {
    switch (direction) {
      case SwipeDirection.left:
        return AppColors.error;
      case SwipeDirection.right:
        return AppColors.success;
      case SwipeDirection.up:
        return AppColors.primary;
    }
  }

  IconData _getIcon() {
    switch (direction) {
      case SwipeDirection.left:
        return Icons.close;
      case SwipeDirection.right:
        return Icons.favorite;
      case SwipeDirection.up:
        return Icons.star;
    }
  }

  String _getLabel() {
    switch (direction) {
      case SwipeDirection.left:
        return 'PASS';
      case SwipeDirection.right:
        return 'LIKE';
      case SwipeDirection.up:
        return 'SUPER LIKE';
    }
  }

  double _getRotation() {
    switch (direction) {
      case SwipeDirection.left:
        return -0.3;
      case SwipeDirection.right:
        return 0.3;
      case SwipeDirection.up:
        return 0;
    }
  }
}

/// A widget that wraps content and shows swipe overlays during swipe gestures
class SwipeableCard extends StatelessWidget {
  final Widget child;
  final double swipeProgressX; // -1.0 to 1.0 (negative = left, positive = right)
  final double swipeProgressY; // 0.0 to -1.0 (negative = up)

  const SwipeableCard({
    super.key,
    required this.child,
    this.swipeProgressX = 0.0,
    this.swipeProgressY = 0.0,
  });

  @override
  Widget build(BuildContext context) {
    // Determine which overlay to show based on swipe direction
    Widget? overlay;
    
    if (swipeProgressY < -0.2 && swipeProgressY.abs() > swipeProgressX.abs()) {
      // Swiping up (super like)
      overlay = SwipeOverlay(
        direction: SwipeDirection.up,
        progress: swipeProgressY.abs(),
      );
    } else if (swipeProgressX > 0.1) {
      // Swiping right (like)
      overlay = SwipeOverlay(
        direction: SwipeDirection.right,
        progress: swipeProgressX,
      );
    } else if (swipeProgressX < -0.1) {
      // Swiping left (pass)
      overlay = SwipeOverlay(
        direction: SwipeDirection.left,
        progress: swipeProgressX.abs(),
      );
    }

    return Stack(
      children: [
        child,
        if (overlay != null)
          Positioned.fill(
            child: overlay,
          ),
      ],
    );
  }
}

/// Action buttons for job card (Like, Pass, Super Like)
class SwipeActionButtons extends StatelessWidget {
  final VoidCallback onDislike;
  final VoidCallback onLike;
  final VoidCallback? onSuperLike;

  const SwipeActionButtons({
    super.key,
    required this.onDislike,
    required this.onLike,
    this.onSuperLike,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppTokens.spacingLg,
        vertical: AppTokens.spacingMd,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Pass button
          _buildActionButton(
            icon: Icons.close,
            color: AppColors.error,
            onTap: onDislike,
            size: 56,
          ),

          // Super like button (optional)
          if (onSuperLike != null)
            _buildActionButton(
              icon: Icons.star,
              color: AppColors.primary,
              onTap: onSuperLike!,
              size: 48,
            ),

          // Like button
          _buildActionButton(
            icon: Icons.favorite,
            color: AppColors.success,
            onTap: onLike,
            size: 56,
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
    required double size,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          boxShadow: AppTokens.shadowMd,
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 2,
          ),
        ),
        child: Icon(
          icon,
          color: color,
          size: size * 0.45,
        ),
      ),
    );
  }
}
