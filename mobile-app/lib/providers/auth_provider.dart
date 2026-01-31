import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/di/service_locator.dart';
import '../core/data/auth_repository.dart';
import '../models/user.dart';

enum AuthStatus {
  initial,
  loading,
  authenticated,
  unauthenticated,
  error,
}

class AuthState {
  final AuthStatus status;
  final User? user;
  final String? errorMessage;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.errorMessage,
  });

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? errorMessage,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _authRepository = getIt<AuthRepository>();

  AuthNotifier() : super(const AuthState());

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      final response = await _authRepository.login(
        email: email,
        password: password,
      );

      // Save tokens
      await _authRepository.saveTokens(
        accessToken: response['access_token'],
        refreshToken: response['refresh_token'],
      );

      // Create user from response
      final user = User(
        id: response['user']['id'],
        email: response['user']['email'],
        fullName: response['user']['full_name'] ?? 'User',
        phone: response['user']['phone'] ?? '',
        isEmailVerified: response['user']['is_email_verified'] ?? false,
        createdAt: DateTime.parse(response['user']['created_at']),
        updatedAt: DateTime.parse(response['user']['updated_at']),
      );

      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      );
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
  }) async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      final response = await _authRepository.register(
        email: email,
        password: password,
        fullName: fullName,
      );

      // Save tokens
      await _authRepository.saveTokens(
        accessToken: response['access_token'],
        refreshToken: response['refresh_token'],
      );

      // Create user from response
      final user = User(
        id: response['user']['id'],
        email: response['user']['email'],
        fullName: response['user']['full_name'] ?? fullName,
        phone: response['user']['phone'] ?? '',
        isEmailVerified: response['user']['is_email_verified'] ?? false,
        createdAt: DateTime.parse(response['user']['created_at']),
        updatedAt: DateTime.parse(response['user']['updated_at']),
      );

      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      );
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> logout() async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      await _authRepository.logout();
      state = const AuthState(
        status: AuthStatus.unauthenticated,
      );
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> checkAuthStatus() async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      final isAuthenticated = await _authRepository.isAuthenticated();
      if (isAuthenticated) {
        final userResponse = await _authRepository.getCurrentUser();
        final user = User(
          id: userResponse['user']['id'],
          email: userResponse['user']['email'],
          fullName: userResponse['user']['full_name'] ?? 'User',
          phone: userResponse['user']['phone'] ?? '',
          isEmailVerified: userResponse['user']['is_email_verified'] ?? false,
          createdAt: DateTime.parse(userResponse['user']['created_at']),
          updatedAt: DateTime.parse(userResponse['user']['updated_at']),
        );
        state = state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
        );
      } else {
        state = const AuthState(status: AuthStatus.unauthenticated);
      }
    } catch (e) {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  void clearError() {
    state = state.copyWith(errorMessage: null);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});

final authStatusProvider = Provider<AuthStatus>((ref) {
  return ref.watch(authProvider).status;
});

final currentUserProvider = Provider<User?>((ref) {
  return ref.watch(authProvider).user;
});

final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).status == AuthStatus.authenticated;
});
