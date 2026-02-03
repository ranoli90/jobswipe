import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import '../../config/app_config.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/local/cache_service.dart';
import '../datasources/local/secure_storage_service.dart';
import '../datasources/local/offline_service.dart';
import '../datasources/local/database_service.dart';
import '../datasources/local/hive_service.dart';
import '../repositories/auth_repository.dart';
import '../repositories/job_repository.dart';
import '../repositories/application_repository.dart';
import '../repositories/profile_repository.dart';
import '../repositories/notification_repository.dart';
import '../../presentation/bloc/auth/auth_bloc.dart';
import '../../presentation/bloc/jobs/jobs_bloc.dart';
import '../../presentation/bloc/applications/applications_bloc.dart';
import '../../presentation/bloc/profile/profile_bloc.dart';
import '../../presentation/bloc/notifications/notifications_bloc.dart';

final getIt = GetIt.instance;

Future<void> setupLocator() async {
  // Initialize Hive
  await HiveService.init();

  // Services
  final sharedPreferences = await SharedPreferences.getInstance();
  // Register SharedPreferences so it can be injected elsewhere
  getIt.registerSingleton<SharedPreferences>(sharedPreferences);
  
  // Web vs Native secure storage
  if (kIsWeb) {
    getIt.registerLazySingleton<FlutterSecureStorage>(() => FlutterSecureStorage());
  } else {
    getIt.registerLazySingleton<FlutterSecureStorage>(() => const FlutterSecureStorage());
  }
  
  // API Client
  getIt.registerLazySingleton<Dio>(() => Dio(
    BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      sendTimeout: AppConfig.sendTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    ),
  ));
  getIt.registerLazySingleton<ApiClient>(() => ApiClient(getIt<Dio>(), getIt<SecureStorageService>()));
  
  // Local Services
  getIt.registerLazySingleton<CacheService>(() => CacheService(getIt<SharedPreferences>()));
  getIt.registerLazySingleton<SecureStorageService>(
    () => SecureStorageService(getIt<FlutterSecureStorage>()),
  );
  
  // Database service - web uses Hive fallback
  getIt.registerLazySingleton<DatabaseService>(() => DatabaseService());
  
  // Connectivity & Offline Service (must be before JobRepository)
  getIt.registerLazySingleton<Connectivity>(() => Connectivity());
  getIt.registerLazySingleton<OfflineService>(
    () => kIsWeb 
      ? OfflineService(getIt<SharedPreferences>())
      : OfflineService(getIt<SharedPreferences>(), getIt<Connectivity>()),
  );
  
  // Repositories
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepository(
      getIt<ApiClient>(),
      getIt<SecureStorageService>(),
    ),
  );

  getIt.registerLazySingleton<JobRepository>(
    () => JobRepository(
      getIt<ApiClient>(),
      getIt<DatabaseService>(),
      getIt<OfflineService>(),
    ),
  );

  getIt.registerLazySingleton<ApplicationRepository>(
    () => ApplicationRepository(getIt<ApiClient>()),
  );

  getIt.registerLazySingleton<ProfileRepository>(
    () => ProfileRepository(getIt<ApiClient>()),
  );

  getIt.registerLazySingleton<NotificationRepository>(
    () => NotificationRepository(getIt<ApiClient>()),
  );
  
  // BLoCs
  getIt.registerFactory<AuthBloc>(
    () => AuthBloc(getIt<AuthRepository>()),
  );
  
  getIt.registerFactory<JobsBloc>(
    () => JobsBloc(getIt<JobRepository>()),
  );
  
  getIt.registerFactory<ApplicationsBloc>(
    () => ApplicationsBloc(getIt<ApplicationRepository>()),
  );
  
  getIt.registerFactory<ProfileBloc>(
    () => ProfileBloc(getIt<ProfileRepository>()),
  );

  getIt.registerFactory<NotificationsBloc>(
    () => NotificationsBloc(getIt<NotificationRepository>()),
  );
}
