import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../config/app_config.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/remote/api_endpoints.dart';
import '../datasources/local/cache_service.dart';
import '../datasources/local/secure_storage_service.dart';
import '../datasources/local/offline_service.dart';
import '../datasources/local/database_service.dart';
import '../datasources/local/hive_service.dart';
import '../data/auth_repository.dart';
import '../data/job_repository.dart';
import '../data/application_repository.dart';
import '../data/profile_repository.dart';
import '../data/notification_repository.dart';
import '../../presentation/bloc/auth/auth_bloc.dart';
import '../../presentation/bloc/jobs/jobs_bloc.dart';
import '../../presentation/bloc/applications/applications_bloc.dart';
import '../../presentation/bloc/profile/profile_bloc.dart';

final getIt = GetIt.instance;

Future<void> setupLocator() async {
  // Initialize Hive
  await HiveService.init();

  // Services
  final sharedPreferences = await SharedPreferences.getInstance();
  final secureStorage = FlutterSecureStorage();

  getIt.registerLazySingleton<SharedPreferences>(() => sharedPreferences);
  getIt.registerLazySingleton<FlutterSecureStorage>(() => secureStorage);
  
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
  getIt.registerLazySingleton<DatabaseService>(() => DatabaseService());
  getIt.registerLazySingleton<HiveService>(() => HiveService());
  
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
  
  // Offline Service
  getIt.registerLazySingleton<Connectivity>(() => Connectivity());
  getIt.registerLazySingleton<OfflineService>(
    () => OfflineService(getIt<SharedPreferences>(), getIt<Connectivity>()),
  );
  
  // BLoCs
  getIt.registerFactory<AuthBloc>(
    () => AuthBloc(
      authRepository: getIt<AuthRepository>(),
    ),
  );
  
  getIt.registerFactory<JobsBloc>(
    () => JobsBloc(
      jobRepository: getIt<JobRepository>(),
    ),
  );
  
  getIt.registerFactory<ApplicationsBloc>(
    () => ApplicationsBloc(
      applicationRepository: getIt<ApplicationRepository>(),
    ),
  );
  
  getIt.registerFactory<ProfileBloc>(
    () => ProfileBloc(
      profileRepository: getIt<ProfileRepository>(),
    ),
  );
}
