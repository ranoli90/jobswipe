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
  AuthException(String message, {String? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
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
  NetworkException(String message, {String? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
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

  ApiException(String message, {this.statusCode, String? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
}

class BadRequestException extends ApiException {
  BadRequestException(String message, {dynamic originalError})
      : super(message, statusCode: 400, code: 'BAD_REQUEST', originalError: originalError);
}

class ForbiddenException extends ApiException {
  ForbiddenException(String message, {dynamic originalError})
      : super(message, statusCode: 403, code: 'FORBIDDEN', originalError: originalError);
}

class NotFoundException extends ApiException {
  NotFoundException(String message, {dynamic originalError})
      : super(message, statusCode: 404, code: 'NOT_FOUND', originalError: originalError);
}

class RateLimitException extends ApiException {
  RateLimitException(String message, {dynamic originalError})
      : super(message, statusCode: 429, code: 'RATE_LIMIT', originalError: originalError);
}

class ServerException extends ApiException {
  ServerException(String message, {dynamic originalError})
      : super(message, statusCode: 500, code: 'SERVER_ERROR', originalError: originalError);
}

/// Validation exceptions
class ValidationException extends AppException {
  final Map<String, List<String>>? errors;

  ValidationException(String message, {this.errors, dynamic originalError})
      : super(message, code: 'VALIDATION_ERROR', originalError: originalError);
}

/// Data exceptions
class DataException extends AppException {
  DataException(String message, {String? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
}

class ParsingException extends DataException {
  ParsingException(String message, {dynamic originalError})
      : super(message, code: 'PARSING_ERROR', originalError: originalError);
}

/// File exceptions
class FileException extends AppException {
  FileException(String message, {String? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
}

class FileUploadException extends FileException {
  FileUploadException(String message, {dynamic originalError})
      : super(message, code: 'UPLOAD_ERROR', originalError: originalError);
}