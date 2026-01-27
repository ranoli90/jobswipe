import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_card_swiper/flutter_card_swiper.dart';
import '../../../core/di/service_locator.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../bloc/jobs/jobs_bloc.dart';
import '../../widgets/job_card_widget.dart';

class JobFeedScreen extends StatefulWidget {
  const JobFeedScreen({super.key});

  @override
  State<JobFeedScreen> createState() => _JobFeedScreenState();
}

class _JobFeedScreenState extends State<JobFeedScreen> {
  final CardSwiperController _cardController = CardSwiperController();
  final ScrollController _scrollController = ScrollController();
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    context.read<JobsBloc>().add(JobsFeedRequested());
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _cardController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      // Load more jobs when near bottom
      final state = context.read<JobsBloc>().state;
      if (state is JobsLoaded && state.hasMore) {
        context.read<JobsBloc>().add(
          JobsFeedRequested(
            cursor: state.nextCursor,
          ),
        );
      }
    }
  }

  void _onSwipeLeft(int index) {
    if (index < _getJobCount()) {
      final job = _getJobAt(index);
      context.read<JobsBloc>().add(
        JobsSwipeRequested(
          jobId: job.id,
          action: 'dislike',
        ),
      );
    }
  }

  void _onSwipeRight(int index) {
    if (index < _getJobCount()) {
      final job = _getJobAt(index);
      context.read<JobsBloc>().add(
        JobsSwipeRequested(
          jobId: job.id,
          action: 'like',
        ),
      );
    }
  }

  void _onSwipe(int previousIndex, int? currentIndex, CardSwiperDirection direction) {
    setState(() {
      _currentIndex = currentIndex ?? 0;
    });

    // Handle swipe actions
    if (direction == CardSwiperDirection.left) {
      _onSwipeLeft(previousIndex);
    } else if (direction == CardSwiperDirection.right) {
      _onSwipeRight(previousIndex);
    }

    // Load more jobs if near the end
    final jobCount = _getJobCount();
    if (currentIndex != null && currentIndex >= jobCount - 3) {
      final state = context.read<JobsBloc>().state;
      if (state is JobsLoaded && state.hasMore) {
        context.read<JobsBloc>().add(
          JobsFeedRequested(
            cursor: state.nextCursor,
          ),
        );
      }
    }
  }

  int _getJobCount() {
    final state = context.read<JobsBloc>().state;
    if (state is JobsLoaded) {
      return state.jobs.length;
    }
    return 0;
  }

  dynamic _getJobAt(int index) {
    final state = context.read<JobsBloc>().state;
    if (state is JobsLoaded && index < state.jobs.length) {
      return state.jobs[index];
    }
    return null;
  }

  void _onRefresh() {
    context.read<JobsBloc>().add(JobsRefreshRequested());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'JobSwipe',
          style: AppTypography.titleLarge.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: true,
        elevation: 0,
        backgroundColor: AppColors.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_outlined),
            onPressed: _onRefresh,
          ),
        ],
      ),
      body: BlocBuilder<JobsBloc, JobsState>(
        builder: (context, state) {
          if (state is JobsLoading && _getJobCount() == 0) {
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
                    'Failed to load jobs',
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

          if (state is JobsLoaded && state.jobs.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.inbox_outlined,
                    size: 64,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(height: AppTokens.spacingMd),
                  Text(
                    'No jobs available',
                    style: AppTypography.bodyLarge.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: AppTokens.spacingMd),
                  ElevatedButton(
                    onPressed: _onRefresh,
                    child: const Text('Refresh'),
                  ),
                ],
              ),
            );
          }

          if (state is JobsLoaded) {
            return CardSwiper(
              controller: _cardController,
              cardsCount: state.jobs.length,
              onSwipe: _onSwipe,
              numberOfCardsDisplayed: 2,
              backCardOffset: const Offset(40, 40),
              padding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 16,
              ),
              cardBuilder: (context, index, percentThresholdX, percentThresholdY) {
                final job = state.jobs[index];
                return JobCardWidget(
                  job: job,
                  onLike: () => _cardController.swipeRight(),
                  onDislike: () => _cardController.swipeLeft(),
                  onTap: () {
                    // TODO: Navigate to job detail
                  },
                );
              },
            );
          }

          return const SizedBox.shrink();
        },
      ),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  Widget _buildBottomNavigationBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: AppTokens.shadowLg,
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppTokens.spacingLg,
            vertical: AppTokens.spacingMd,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(
                icon: Icons.home_outlined,
                label: 'Feed',
                isSelected: true,
                onTap: () {
                  // Already on feed
                },
              ),
              _buildNavItem(
                icon: Icons.work_outline,
                label: 'Applications',
                isSelected: false,
                onTap: () {
                  Navigator.of(context).pushNamed('/applications');
                },
              ),
              _buildNavItem(
                icon: Icons.person_outline,
                label: 'Profile',
                isSelected: false,
                onTap: () {
                  Navigator.of(context).pushNamed('/profile');
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppTokens.spacingMd,
          vertical: AppTokens.spacingSm,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? AppColors.primary : AppColors.textSecondary,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTypography.labelSmall.copyWith(
                color: isSelected ? AppColors.primary : AppColors.textSecondary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
