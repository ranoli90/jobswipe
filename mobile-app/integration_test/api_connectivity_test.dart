import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:jobswipe/main.dart' as app;
import 'package:jobswipe/core/di/service_locator.dart' as di;
import 'package:jobswipe/core/datasources/remote/api_client.dart';
import 'package:jobswipe/core/datasources/remote/api_endpoints.dart';
import 'package:jobswipe/repositories/auth_repository.dart';
import 'package:get_it/get_it.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('API Connectivity Integration Test', () {
    setUpAll(() async {
      // Initialize service locator
      await di.setupLocator();
    });

    testWidgets('App launches successfully', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Verify app launches without crashing
      expect(find.text('JobSwipe'), findsOneWidget);
    });

    test('API client can make health check request', () async {
      final apiClient = GetIt.instance<ApiClient>();

      // Test health endpoint
      final response = await apiClient.get(ApiEndpoints.health);

      expect(response.statusCode, 200);
      expect(response.data, isNotNull);
      expect(response.data['status'], 'healthy');
    });

    test('Auth repository can attempt login (expect failure without valid credentials)', () async {
      final authRepository = GetIt.instance<AuthRepository>();

      // This should fail with invalid credentials, but test that API is reachable
      expect(
        () async => await authRepository.login('invalid@email.com', 'wrongpassword'),
        throwsA(isA<Exception>()),
      );
    });
  });
}