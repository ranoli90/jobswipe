import 'package:get_it/get_it.dart';
import 'package:dio/dio.dart';
import 'datasources/remote/api_client.dart';
import 'datasources/local/secure_storage_service.dart';
import '../repositories/auth_repository.dart';
import '../repositories/job_repository.dart';
import '../repositories/application_repository.dart';
import '../repositories/notification_repository.dart';

/// Service locator for dependency injection
final getIt = GetIt.instance;

/// Initialize all dependencies
Future<void> setupServiceLocator() async {
  // External dependencies
  getIt.registerLazySingleton<Dio>(() => Dio(BaseOptions(
    baseUrl: 'https://api.jobswipe.com', // This should come from config
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(seconds: 30),
  )));

  // Local services
  getIt.registerLazySingleton<SecureStorageService>(() => SecureStorageService());

  // API Client
  getIt.registerLazySingleton<ApiClient>(
    () => ApiClient(getIt<Dio>(), getIt<SecureStorageService>()),
  );

  // Repositories
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepository(getIt<ApiClient>(), getIt<SecureStorageService>()),
  );

  getIt.registerLazySingleton<JobRepository>(
    () => JobRepository(getIt<ApiClient>()),
  );

  getIt.registerLazySingleton<ApplicationRepository>(
    () => ApplicationRepository(getIt<ApiClient>()),
  );

  getIt.registerLazySingleton<NotificationRepository>(
    () => NotificationRepository(getIt<ApiClient>()),
  );
}