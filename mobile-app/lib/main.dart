import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'core/theme/app_theme.dart';
import 'core/di/service_locator.dart';
import 'presentation/screens/auth/login_screen.dart';
import 'presentation/screens/jobs/job_feed_screen.dart';
import 'presentation/screens/profile/profile_screen.dart';
import 'presentation/screens/applications/applications_screen.dart';
import 'presentation/bloc/auth/auth_bloc.dart';
import 'presentation/bloc/jobs/jobs_bloc.dart';
import 'presentation/bloc/profile/profile_bloc.dart';
import 'presentation/bloc/applications/applications_bloc.dart';
import 'config/app_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Load environment variables (gracefully handle missing .env in APK)
  try {
    await dotenv.load(fileName: '.env');
  } catch (e) {
    // .env file not bundled in APK - use default config values
    // This is expected behavior for production builds
    debugPrint('Note: .env file not found, using default configuration');
  }
  
  // Initialize service locator
  await setupLocator();
  
  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider<AuthBloc>(
          create: (_) => getIt<AuthBloc>(),
        ),
        BlocProvider<JobsBloc>(
          create: (_) => getIt<JobsBloc>(),
        ),
        BlocProvider<ProfileBloc>(
          create: (_) => getIt<ProfileBloc>(),
        ),
        BlocProvider<ApplicationsBloc>(
          create: (_) => getIt<ApplicationsBloc>(),
        ),
      ],
      child: const JobSwipeApp(),
    ),
  );
}

class JobSwipeApp extends StatelessWidget {
  const JobSwipeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'JobSwipe',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: '/login',
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case '/login':
            return MaterialPageRoute(
              builder: (_) => const LoginScreen(),
            );
          case '/jobs':
            return MaterialPageRoute(
              builder: (_) => const JobFeedScreen(),
            );
          case '/profile':
            return MaterialPageRoute(
              builder: (_) => const ProfileScreen(),
            );
          case '/applications':
            return MaterialPageRoute(
              builder: (_) => const ApplicationsScreen(),
            );
          default:
            return MaterialPageRoute(
              builder: (_) => const LoginScreen(),
            );
        }
      },
    );
  }
}
