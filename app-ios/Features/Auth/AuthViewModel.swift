import Foundation
import LocalAuthentication
import SecureStorage

@MainActor
class AuthViewModel: ObservableObject {
    @Published var email: String = ""
    @Published var password: String = ""
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var isAuthenticated: Bool = false
    @Published var showBiometricPrompt: Bool = false
    @Published var biometricError: String?
    
    private let apiClient: APIClient
    private let keychainService = KeychainService()
    
    init(apiClient: APIClient) {
        self.apiClient = apiClient
        self.isAuthenticated = keychainService.token != nil
    }
    
    func login() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await apiClient.login(email: email, password: password)
            
            // Store token securely
            try keychainService.storeToken(response.access_token)
            
            isAuthenticated = true
            email = ""
            password = ""
        } catch let error as APIError {
            errorMessage = error.localizedDescription
        } catch {
            errorMessage = "An unexpected error occurred"
        }
        
        isLoading = false
    }
    
    func register() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await apiClient.register(email: email, password: password)
            
            // Store token securely
            try keychainService.storeToken(response.access_token)
            
            isAuthenticated = true
            email = ""
            password = ""
        } catch let error as APIError {
            errorMessage = error.localizedDescription
        } catch {
            errorMessage = "An unexpected error occurred"
        }
        
        isLoading = false
    }
    
    func logout() throws {
        try keychainService.removeToken()
        isAuthenticated = false
    }
    
    func authenticateWithBiometrics() async {
        let context = LAContext()
        var error: NSError?
        
        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            do {
                try await context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: "Authenticate to access your job matches")
                isAuthenticated = true
                biometricError = nil
            } catch let authError as NSError {
                biometricError = formatBiometricError(authError)
            }
        } else {
            biometricError = "Biometric authentication not available"
        }
    }
    
    private func formatBiometricError(_ error: NSError) -> String {
        switch error.code {
        case LAError.authenticationFailed.rawValue:
            return "Authentication failed. Please try again."
        case LAError.userCancel.rawValue:
            return "Authentication cancelled by user"
        case LAError.userFallback.rawValue:
            return "User chose fallback method"
        case LAError.systemCancel.rawValue:
            return "Authentication cancelled by system"
        case LAError.passcodeNotSet.rawValue:
            return "Passcode not set on device"
        case LAError.biometryNotAvailable.rawValue:
            return "Biometric authentication not available"
        case LAError.biometryNotEnrolled.rawValue:
            return "No biometric data enrolled"
        case LAError.biometryLockout.rawValue:
            return "Biometric authentication locked out"
        default:
            return "An unexpected error occurred"
        }
    }
}


class KeychainService {
    private let tokenKey = "com.jobsweep.access_token"
    
    var token: String? {
        get {
            guard let data = try? KeychainSwift().getData(tokenKey),
                  let token = String(data: data, encoding: .utf8) else {
                return nil
            }
            return token
        }
    }
    
    func storeToken(_ token: String) throws {
        guard let data = token.data(using: .utf8) else {
            throw APIError.invalidToken
        }
        
        let keychain = KeychainSwift()
        keychain.accessGroup = "com.jobsweep"
        keychain.synchronizable = true
        
        guard keychain.set(data, forKey: tokenKey, withAccess: .accessibleWhenUnlockedThisDeviceOnly) else {
            throw APIError.tokenStorageFailed
        }
    }
    
    func removeToken() throws {
        let keychain = KeychainSwift()
        guard keychain.delete(tokenKey) else {
            throw APIError.tokenRemovalFailed
        }
    }
}
