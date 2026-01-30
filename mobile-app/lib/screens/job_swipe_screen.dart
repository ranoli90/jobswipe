import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_card_swiper/flutter_card_swiper.dart';
import '../providers/jobs_provider.dart';
import '../models/job.dart';

class JobSwipeScreen extends ConsumerStatefulWidget {
  const JobSwipeScreen({super.key});

  @override
  ConsumerState<JobSwipeScreen> createState() => _JobSwipeScreenState();
}

class _JobSwipeScreenState extends ConsumerState<JobSwipeScreen> {
  final CardSwiperController _swiperController = CardSwiperController();

  @override
  void initState() {
    super.initState();
    // Load jobs when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(jobsProvider.notifier).loadJobs();
    });
  }

  @override
  void dispose() {
    _swiperController.dispose();
    super.dispose();
  }

  void _handleSwipe(int index, CardSwiperDirection direction) {
    final jobsState = ref.read(jobsProvider);
    if (index < jobsState.jobs.length) {
      final job = jobsState.jobs[index];
      
      if (direction == CardSwiperDirection.right) {
        // Like/Apply
        ref.read(jobsProvider.notifier).likeJob(job.id);
      } else if (direction == CardSwiperDirection.left) {
        // Dislike/Pass
        ref.read(jobsProvider.notifier).dislikeJob(job.id);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final jobsState = ref.watch(jobsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('JobSwipe'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(jobsProvider.notifier).resetJobs();
              ref.read(jobsProvider.notifier).loadJobs();
            },
            tooltip: 'Refresh Jobs',
          ),
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: () {
              Navigator.of(context).pushNamed('/applications');
            },
            tooltip: 'My Applications',
          ),
        ],
      ),
      body: SafeArea(
        child: _buildBody(jobsState, theme),
      ),
      bottomNavigationBar: jobsState.status == JobsStatus.loaded &&
              jobsState.currentJob != null
          ? _buildActionButtons(jobsState.currentJob!, theme)
          : null,
    );
  }

  Widget _buildBody(JobsState jobsState, ThemeData theme) {
    switch (jobsState.status) {
      case JobsStatus.initial:
      case JobsStatus.loading:
        return const Center(
          child: CircularProgressIndicator(),
        );

      case JobsStatus.error:
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  size: 64,
                  color: theme.colorScheme.error,
                ),
                const SizedBox(height: 16),
                Text(
                  'Failed to load jobs',
                  style: theme.textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  jobsState.errorMessage ?? 'An unknown error occurred',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: () {
                    ref.read(jobsProvider.notifier).loadJobs();
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        );

      case JobsStatus.loaded:
        if (jobsState.jobs.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.work_outline,
                  size: 64,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                const SizedBox(height: 16),
                Text(
                  'No jobs available',
                  style: theme.textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Check back later for new opportunities',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          );
        }

        if (jobsState.currentJob == null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.check_circle_outline,
                  size: 64,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(height: 16),
                Text(
                  'All caught up!',
                  style: theme.textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'You\'ve reviewed all available jobs',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: () {
                    ref.read(jobsProvider.notifier).resetJobs();
                    ref.read(jobsProvider.notifier).loadJobs();
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Start Over'),
                ),
              ],
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: SizedBox.expand(
            child: CardSwiper(
              controller: _swiperController,
              cardsCount: jobsState.jobs.length - jobsState.currentIndex,
              onSwipe: _handleSwipe,
              cardBuilder: (context, index, percentThreshold, direction) {
                final jobIndex = jobsState.currentIndex + index;
                if (jobIndex >= jobsState.jobs.length) {
                  return const SizedBox.shrink();
                }
                return _buildJobCard(jobsState.jobs[jobIndex], theme);
              },
            ),
          ),
        );
    }
  }

  Widget _buildJobCard(Job job, ThemeData theme) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header with gradient
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    theme.colorScheme.primary,
                    theme.colorScheme.primaryContainer,
                  ],
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Match Score Badge
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surface,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.star,
                          size: 16,
                          color: Colors.amber[700],
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${(job.score * 100).toInt()}% Match',
                          style: TextStyle(
                            color: theme.colorScheme.onSurface,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Job Title
                  Text(
                    job.title,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      color: theme.colorScheme.onPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Company
                  if (job.company != null)
                    Row(
                      children: [
                        Icon(
                          Icons.business,
                          size: 16,
                          color: theme.colorScheme.onPrimary.withOpacity(0.8),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          job.company!,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onPrimary.withOpacity(0.9),
                          ),
                        ),
                      ],
                    ),
                  const SizedBox(height: 4),
                  // Location
                  if (job.location != null)
                    Row(
                      children: [
                        Icon(
                          Icons.location_on,
                          size: 16,
                          color: theme.colorScheme.onPrimary.withOpacity(0.8),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          job.location!,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onPrimary.withOpacity(0.9),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'About this role',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (job.snippet != null)
                        Text(
                          job.snippet!,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                            height: 1.5,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(Job job, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            // Dislike Button
            FloatingActionButton.extended(
              onPressed: () {
                _swiperController.swipe(CardSwiperDirection.left);
              },
              backgroundColor: theme.colorScheme.errorContainer,
              icon: Icon(
                Icons.close,
                color: theme.colorScheme.onErrorContainer,
              ),
              label: Text(
                'Pass',
                style: TextStyle(
                  color: theme.colorScheme.onErrorContainer,
                ),
              ),
            ),
            // Undo Button
            FloatingActionButton(
              heroTag: 'undo',
              onPressed: () {
                ref.read(jobsProvider.notifier).undoSwipe();
              },
              backgroundColor: theme.colorScheme.secondaryContainer,
              child: Icon(
                Icons.undo,
                color: theme.colorScheme.onSecondaryContainer,
              ),
            ),
            // Like Button
            FloatingActionButton.extended(
              onPressed: () {
                _swiperController.swipe(CardSwiperDirection.right);
              },
              backgroundColor: theme.colorScheme.primaryContainer,
              icon: Icon(
                Icons.favorite,
                color: theme.colorScheme.onPrimaryContainer,
              ),
              label: Text(
                'Apply',
                style: TextStyle(
                  color: theme.colorScheme.onPrimaryContainer,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
