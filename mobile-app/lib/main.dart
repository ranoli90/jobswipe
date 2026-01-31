import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'core/theme/app_theme.dart';
import 'core/di/service_locator.dart';
import 'screens/login_screen.dart';
import 'screens/job_swipe_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/applications_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize service locator
  await setupLocator();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  runApp(
    const ProviderScope(
      child: JobSwipeApp(),
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
              builder: (_) => const JobSwipeScreen(),
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
      errorBuilder: (context, error, stackTrace) {
        return Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.error_outline,
                  size: 64,
                  color: Colors.red,
                ),
                const SizedBox(height: 16),
                const Text(
                  'An error occurred',
                  style: TextStyle(fontSize: 20),
                ),
                const SizedBox(height: 8),
                Text(
                  error.toString(),
                  style: const TextStyle(color: Colors.grey),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).pushNamedAndRemoveUntil(
                      '/login',
                      (route) => false,
                    );
                  },
                  child: const Text('Go to Login'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
