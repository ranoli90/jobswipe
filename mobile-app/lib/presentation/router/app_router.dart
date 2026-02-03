import 'package:flutter/material.dart';
import '../screens/splash_screen.dart';
import '../screens/auth/onboarding_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/auth/reset_password_screen.dart';
import '../screens/jobs/job_feed_screen.dart';
import '../screens/jobs/job_detail_screen.dart';
import '../screens/applications/applications_screen.dart';
import '../screens/applications/application_detail_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/notifications/notifications_screen.dart';

class AppRouter {
  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/splash':
        return MaterialPageRoute(
          builder: (_) => const SplashScreen(),
        );
      case '/onboarding':
        return MaterialPageRoute(
          builder: (_) => const OnboardingScreen(),
        );
      case '/login':
        return MaterialPageRoute(
          builder: (_) => const LoginScreen(),
        );
      case '/register':
        return MaterialPageRoute(
          builder: (_) => const RegisterScreen(),
        );
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
      case '/applications/detail':
        final applicationId = settings.arguments as String;
        return MaterialPageRoute(
          builder: (_) => ApplicationDetailScreen(applicationId: applicationId),
        );
      case '/profile':
        return MaterialPageRoute(
          builder: (_) => const ProfileScreen(),
        );
      case '/notifications':
        return MaterialPageRoute(
          builder: (_) => const NotificationsScreen(),
        );
      default:
        return MaterialPageRoute(
          builder: (_) => const SplashScreen(),
        );
    }
  }
}
