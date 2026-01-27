import Foundation

enum APIError: LocalizedError {
    case invalidEmail
    case invalidPassword
    case invalidToken
    case tokenStorageFailed
    case tokenRemovalFailed
    case invalidResponse
    case networkError
    case serverError
    case authenticationFailed
    case registrationFailed
    case resumeUploadFailed
    case jobSearchFailed
    case applicationFailed
    
    var errorDescription: String? {
        switch self {
        case .invalidEmail:
            return "Please enter a valid email address"
        case .invalidPassword:
            return "Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character"
        case .invalidToken:
            return "Invalid authentication token"
        case .tokenStorageFailed:
            return "Failed to store authentication token"
        case .tokenRemovalFailed:
            return "Failed to remove authentication token"
        case .invalidResponse:
            return "Received invalid response from server"
        case .networkError:
            return "Network connection failed. Please check your internet connection"
        case .serverError:
            return "Server error. Please try again later"
        case .authenticationFailed:
            return "Authentication failed. Please check your credentials"
        case .registrationFailed:
            return "Registration failed. Please try again"
        case .resumeUploadFailed:
            return "Resume upload failed. Please try again"
        case .jobSearchFailed:
            return "Job search failed. Please try again"
        case .applicationFailed:
            return "Application failed. Please try again"
        }
    }
    
    static func fromStatusCode(_ statusCode: Int) -> APIError {
        switch statusCode {
        case 400:
            return .invalidResponse
        case 401:
            return .authenticationFailed
        case 403:
            return .authenticationFailed
        case 404:
            return .invalidResponse
        case 409:
            return .registrationFailed
        case 500...599:
            return .serverError
        default:
            return .serverError
        }
    }
}
