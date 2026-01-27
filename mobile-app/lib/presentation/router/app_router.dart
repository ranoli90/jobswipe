import 'package:flutter/material.dart';
import '../screens/auth/onboarding_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/jobs/job_feed_screen.dart';
import '../screens/applications/applications_screen.dart';
import '../screens/profile/profile_screen.dart';

class AppRouter {
  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/feed':
        return MaterialPageRoute(
          builder: (_) => const JobFeedScreen(),
        );
      case '/applications':
        return MaterialPageRoute(
          builder: (_) => const ApplicationsScreen(),
        );
      case '/profile':
        return MaterialPageRoute(
          builder: (_) => const ProfileScreen(),
        );
      default:
        return MaterialPageRoute(
          builder: (_) => const OnboardingScreen(),
        );
    }
  }
}
