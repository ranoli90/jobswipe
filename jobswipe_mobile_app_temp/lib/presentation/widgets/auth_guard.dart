import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/auth/auth_bloc.dart';
import '../screens/auth/login_screen.dart';
import '../screens/splash_screen.dart';

/// AuthGuard widget that handles authentication state and redirects accordingly.
/// Wrap your main app content with this widget to ensure proper auth flow.
class AuthGuard extends StatelessWidget {
  final Widget child;

  const AuthGuard({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        // Initial state - check if authenticated
        if (state is AuthInitial) {
          // Trigger auth check
          WidgetsBinding.instance.addPostFrameCallback((_) {
            context.read<AuthBloc>().add(AuthCheckRequested());
          });
          return const SplashScreen();
        }

        // Loading state - show splash/loading
        if (state is AuthLoading) {
          return const SplashScreen();
        }

        // Authenticated - show the actual content
        if (state is AuthAuthenticated) {
          return child;
        }

        // Unauthenticated or error - show login
        if (state is AuthUnauthenticated || state is AuthError) {
          return const LoginScreen();
        }

        // Default fallback
        return const SplashScreen();
      },
    );
  }
}

/// A route wrapper that requires authentication.
/// Use this for individual screens that need auth protection.
class AuthRequiredRoute extends StatelessWidget {
  final Widget child;
  final String? redirectRoute;

  const AuthRequiredRoute({
    super.key,
    required this.child,
    this.redirectRoute,
  });

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is AuthUnauthenticated) {
          // Redirect to login when unauthenticated
          if (redirectRoute != null) {
            Navigator.of(context).pushReplacementNamed(redirectRoute!);
          } else {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            );
          }
        }
      },
      child: BlocBuilder<AuthBloc, AuthState>(
        builder: (context, state) {
          if (state is AuthAuthenticated) {
            return child;
          }

          // Show loading while checking auth
          return Scaffold(
            body: Center(
              child: CircularProgressIndicator(
                color: Theme.of(context).primaryColor,
              ),
            ),
          );
        },
      ),
    );
  }
}
