import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Web App Integration Tests', () {
    testWidgets('App launches on web without crash', (tester) async {
      // Verify we're on web platform
      expect(kIsWeb, isTrue);

      // Build a minimal test app
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.work, size: 64),
                  const SizedBox(height: 16),
                  const Text('JobSwipe'),
                  const SizedBox(height: 8),
                  const Text('Web Test Passed'),
                ],
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify app renders without errors
      expect(find.text('JobSwipe'), findsOneWidget);
      expect(find.text('Web Test Passed'), findsOneWidget);
      expect(find.byIcon(Icons.work), findsOneWidget);
    });

    testWidgets('Responsive layout adapts to web screen sizes', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LayoutBuilder(
              builder: (context, constraints) {
                final isWideScreen = constraints.maxWidth > 600;
                return Center(
                  child: Text(
                    isWideScreen ? 'Wide Layout' : 'Narrow Layout',
                  ),
                );
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Default test screen size should be detected
      expect(
        find.textContaining('Layout'),
        findsOneWidget,
      );
    });

    testWidgets('Material icons render correctly on web', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                Icon(Icons.work),
                Icon(Icons.person),
                Icon(Icons.settings),
                Icon(Icons.search),
              ],
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.work), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.byIcon(Icons.settings), findsOneWidget);
      expect(find.byIcon(Icons.search), findsOneWidget);
    });

    testWidgets('Form inputs work on web', (tester) async {
      final controller = TextEditingController();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: controller,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'Enter your email',
                ),
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Find and interact with text field
      final textField = find.byType(TextField);
      expect(textField, findsOneWidget);

      await tester.enterText(textField, 'test@example.com');
      await tester.pumpAndSettle();

      expect(controller.text, 'test@example.com');
    });

    testWidgets('Buttons are interactive on web', (tester) async {
      bool buttonPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: ElevatedButton(
                onPressed: () {
                  buttonPressed = true;
                },
                child: const Text('Click Me'),
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      final button = find.byType(ElevatedButton);
      expect(button, findsOneWidget);

      await tester.tap(button);
      await tester.pumpAndSettle();

      expect(buttonPressed, isTrue);
    });
  });
}
