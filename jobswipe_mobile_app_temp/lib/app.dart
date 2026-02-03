import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'core/theme/app_theme.dart';
import 'core/di/service_locator.dart';
import 'presentation/bloc/auth/auth_bloc.dart';
import 'presentation/bloc/jobs/jobs_bloc.dart';
import 'presentation/bloc/applications/applications_bloc.dart';
import 'presentation/bloc/profile/profile_bloc.dart';
import 'presentation/bloc/notifications/notifications_bloc.dart';
import 'presentation/router/app_router.dart';
import 'presentation/screens/splash_screen.dart';

class JobSwipeApp extends StatelessWidget {
  const JobSwipeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => getIt<AuthBloc>()),
        BlocProvider(create: (_) => getIt<JobsBloc>()),
        BlocProvider(create: (_) => getIt<ApplicationsBloc>()),
        BlocProvider(create: (_) => getIt<ProfileBloc>()),
        BlocProvider(create: (_) => getIt<NotificationsBloc>()),
      ],
      child: MaterialApp(
        title: 'JobSwipe',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: const SplashScreen(),
        onGenerateRoute: AppRouter.onGenerateRoute,
      ),
    );
  }
}
