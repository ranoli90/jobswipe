import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'core/theme/app_theme.dart';
import 'core/di/service_locator.dart';
import 'presentation/screens/auth/login_screen.dart';
import 'presentation/screens/auth/register_screen.dart';
import 'presentation/screens/jobs/job_feed_screen.dart';
import 'presentation/screens/profile/profile_screen.dart';
import 'presentation/screens/applications/applications_screen.dart';
import 'presentation/bloc/auth/auth_bloc.dart';
import 'presentation/bloc/jobs/jobs_bloc.dart';
import 'presentation/bloc/profile/profile_bloc.dart';
import 'presentation/bloc/applications/applications_bloc.dart';
import 'config/app_config.dart';

/// Lightweight splash screen widget with timeout protection
class SplashScreen extends StatefulWidget {
  final Widget child;
  final Duration timeout;

  const SplashScreen({
    super.key,
    required this.child,
    this.timeout = const Duration(seconds: 10),
  });

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // Auto-navigate after timeout to prevent indefinite white screen
    Future.delayed(widget.timeout, () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => widget.child),
        );
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
  ErrorWidget.builder = (FlutterErrorDetails details) {
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
    WidgetsFlutterBinding.ensureInitialized();
    FlutterError.onError = (details) {
      FlutterError.presentError(details);
      debugPrint('FlutterError: ${details.exceptionAsString()}');
    };

    Widget appContent;
    try {
      // Load environment variables (gracefully handle missing .env)
      try {
        // Try to load .env from the current directory (for web/dev builds)
        await dotenv.load(fileName: '.env');
        debugPrint('Loaded .env file successfully');
      } catch (e) {
        // .env file not found - use default config values
        // This is expected behavior for production builds without bundled .env
        debugPrint('Note: .env file not found, using default configuration');
      }

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

    // Run the app with proper widget tree structure
    runApp(
      MaterialApp(
        title: 'JobSwipe',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: SplashScreen(
          child: appContent,
          timeout: const Duration(seconds: 10),
        ),
        onGenerateRoute: (settings) {
          switch (settings.name) {
            case '/login':
              return MaterialPageRoute(
                builder: (_) => const LoginScreen(),
              );
            case '/register':
              return MaterialPageRoute(
                builder: (_) => BlocProvider.value(
                  value: getIt<AuthBloc>(),
                  child: const RegisterScreen(),
                ),
              );
            case '/jobs':
              return MaterialPageRoute(
                builder: (_) => BlocProvider.value(
                  value: getIt<AuthBloc>(),
                  child: const JobFeedScreen(),
                ),
              );
            case '/profile':
              return MaterialPageRoute(
                builder: (_) => BlocProvider.value(
                  value: getIt<AuthBloc>(),
                  child: const ProfileScreen(),
                ),
              );
            case '/applications':
              return MaterialPageRoute(
                builder: (_) => BlocProvider.value(
                  value: getIt<AuthBloc>(),
                  child: const ApplicationsScreen(),
                ),
              );
            default:
              return MaterialPageRoute(
                builder: (_) => const LoginScreen(),
              );
          }
        },
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
    // No longer create a new MaterialApp here - use the root one
    return const LoginScreen();
  }
}
