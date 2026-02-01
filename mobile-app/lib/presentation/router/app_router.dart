import 'package:flutter/material.dart';
import '../screens/auth/onboarding_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/auth/reset_password_screen.dart';
import '../screens/jobs/job_feed_screen.dart';
import '../screens/jobs/job_detail_screen.dart';
import '../screens/applications/applications_screen.dart';
import '../screens/profile/profile_screen.dart';

class AppRouter {
  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/forgot-password':
        return MaterialPageRoute(
          builder: (_) => const ForgotPasswordScreen(),
        );
      case '/reset-password':
        final token = settings.arguments as String;
        return MaterialPageRoute(
          builder: (_) => ResetPasswordScreen(token: token),
        );
      case '/feed':
        return MaterialPageRoute(
          builder: (_) => const JobFeedScreen(),
        );
      case '/jobs/detail':
        final jobId = settings.arguments as String;
        return MaterialPageRoute(
          builder: (_) => JobDetailScreen(jobId: jobId),
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
