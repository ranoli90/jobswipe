import 'dart:async';
import 'package:flutter/foundation.dart';
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

/// Lightweight splash screen widget with timeout protection
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // Auto-navigate after timeout to prevent indefinite white screen
    Future.delayed(const Duration(seconds: 10), () {
      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/login');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.work,
              size: 80,
              color: Theme.of(context).primaryColor,
            ),
            const SizedBox(height: 24),
            const Text(
              'JobSwipe',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Loading...',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  ErrorWidget.builder = (FlutterErrorDetails details) {
    debugPrint('ErrorWidget: ${details.exceptionAsString()}');
    debugPrint('Error occurred in ${details.library}');
    if (kIsWeb) debugPrint('Web context - ${details.context}');
    return Material(
      color: Colors.white,
      child: Center(
        child: Text(
          'Something went wrong.\nPlease restart the app.',
          textAlign: TextAlign.center,
        ),
      ),
    );
  };

  runZonedGuarded(() async {
    FlutterError.onError = (details) {
      FlutterError.presentError(details);
      debugPrint('FlutterError: ${details.exceptionAsString()}');
      debugPrint('Stack trace: ${details.stack}');
      if (kIsWeb) debugPrint('Web environment detected');
    };

    Widget appContent;
    try {
      // Load environment variables (gracefully handle missing .env in APK)
      if (!kIsWeb) {
        await dotenv.load(fileName: '.env');
      } else {
        debugPrint('Skipping .env load in web environment');
      }
    } catch (e) {
      // .env file not bundled in APK - use default config values
      // This is expected behavior for production builds
      debugPrint('Note: .env file not found, using default configuration');
    }

    try {
      // Initialize service locator
      await setupLocator();

      // Create the app content widget after successful initialization
      appContent = MultiBlocProvider(
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
        child: const JobSwipeAppContent(),
      );
    } catch (e, st) {
      debugPrint('Init error: $e\n$st');
      // Show error UI on initialization failure
      appContent = const Scaffold(
        body: Center(
          child: Text(
            'Initialization failed.\nPlease restart the app.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    // Run the app
    runApp(
      MaterialApp(
        title: 'JobSwipe',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: appContent,
        navigatorObservers: [
          LoggingNavigatorObserver(),
        ],
      ),
    );
  }, (error, stack) {
    debugPrint('Uncaught zone error: $error');
  });
}

/// Main app content with routing
class JobSwipeAppContent extends StatelessWidget {
  const JobSwipeAppContent({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'JobSwipe',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: '/',
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case '/':
            return MaterialPageRoute(builder: (_) => const SplashScreen());
          case '/login':
            return MaterialPageRoute(builder: (_) => const LoginScreen());
          case '/jobs':
            return MaterialPageRoute(builder: (_) => const JobFeedScreen());
          case '/profile':
            return MaterialPageRoute(builder: (_) => const ProfileScreen());
          case '/applications':
            return MaterialPageRoute(builder: (_) => const ApplicationsScreen());
          default:
            return MaterialPageRoute(builder: (_) => const SplashScreen());
        }
      },
    );
  }
}

class LoggingNavigatorObserver extends NavigatorObserver {
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    debugPrint('Navigator pushed: ${route.settings.name}');
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    debugPrint('Navigator popped: ${route.settings.name}');
  }
}
