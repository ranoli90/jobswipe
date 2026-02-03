/// Custom exceptions for the JobSwipe app

class AppException implements Exception {
  final String message;
  final String? code;
  final dynamic originalError;

  AppException(this.message, {this.code, this.originalError});

  @override
  String toString() => 'AppException: $message${code != null ? ' (code: $code)' : ''}';
}

/// Authentication exceptions
class AuthException extends AppException {
  AuthException(super.message, {super.code, super.originalError});
}

class UnauthorizedException extends AuthException {
  UnauthorizedException([String message = 'Unauthorized access'])
      : super(message, code: 'UNAUTHORIZED');
}

class TokenExpiredException extends AuthException {
  TokenExpiredException([String message = 'Authentication token has expired'])
      : super(message, code: 'TOKEN_EXPIRED');
}

/// Network exceptions
class NetworkException extends AppException {
  NetworkException(super.message, {super.code, super.originalError});
}

class NoInternetException extends NetworkException {
  NoInternetException([String message = 'No internet connection'])
      : super(message, code: 'NO_INTERNET');
}

class TimeoutException extends NetworkException {
  TimeoutException([String message = 'Request timeout'])
      : super(message, code: 'TIMEOUT');
}

/// API exceptions
class ApiException extends AppException {
  final int? statusCode;

  ApiException(super.message, {this.statusCode, super.code, super.originalError});
}

class BadRequestException extends ApiException {
  BadRequestException(super.message, {super.originalError})
      : super(statusCode: 400, code: 'BAD_REQUEST');
}

class ForbiddenException extends ApiException {
  ForbiddenException(super.message, {super.originalError})
      : super(statusCode: 403, code: 'FORBIDDEN');
}

class NotFoundException extends ApiException {
  NotFoundException(super.message, {super.originalError})
      : super(statusCode: 404, code: 'NOT_FOUND');
}

class RateLimitException extends ApiException {
  RateLimitException(super.message, {super.originalError})
      : super(statusCode: 429, code: 'RATE_LIMIT');
}

class ServerException extends ApiException {
  ServerException(super.message, {super.originalError})
      : super(statusCode: 500, code: 'SERVER_ERROR');
}

/// Validation exceptions
class ValidationException extends AppException {
  final Map<String, List<String>>? errors;

  ValidationException(super.message, {this.errors, super.originalError})
      : super(code: 'VALIDATION_ERROR');
}

/// Data exceptions
class DataException extends AppException {
  DataException(super.message, {super.code, super.originalError});
}

class ParsingException extends DataException {
  ParsingException(super.message, {super.originalError})
      : super(code: 'PARSING_ERROR');
}

/// File exceptions
class FileException extends AppException {
  FileException(super.message, {super.code, super.originalError});
}

class FileUploadException extends FileException {
  FileUploadException(super.message, {super.originalError})
      : super(code: 'UPLOAD_ERROR');
}