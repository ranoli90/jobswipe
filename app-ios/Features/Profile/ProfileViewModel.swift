import Foundation
import Combine

@MainActor
class ProfileViewModel: ObservableObject {
    @Published private(set) var profile: ProfileResponse?
    @Published private(set) var isLoading: Bool = false
    @Published var errorMessage: String?
    
    private let apiClient: APIClient
    private var cancellables = Set<AnyCancellable>()
    
    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }
    
    func refreshProfile() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let profile = try await apiClient.getProfile()
                self.profile = profile
            } catch let error as APIError {
                errorMessage = error.localizedDescription
            } catch {
                errorMessage = "Failed to load profile. Please try again."
            }
            
            isLoading = false
        }
    }
    
    func updateProfile(_ profileUpdate: CandidateProfileUpdate) async throws {
        isLoading = true
        errorMessage = nil
        
        do {
            let updatedProfile = try await apiClient.updateProfile(profileUpdate)
            self.profile = updatedProfile
        } catch let error as APIError {
            errorMessage = error.localizedDescription
            throw error
        } catch {
            errorMessage = "Failed to update profile. Please try again."
            throw error
        }
        
        isLoading = false
    }
    
    func logout() {
        Task {
            do {
                // Call backend logout endpoint if available
                // try await apiClient.logout()
            } catch {
                // Continue with local logout even if API call fails
            }
            
            // Remove token from secure storage
            let keychainService = KeychainService()
            do {
                try keychainService.removeToken()
            } catch {
                print("Failed to remove token from keychain: \(error)")
            }
            
            // Post notification to update app state
            NotificationCenter.default.post(name: .authSuccess, object: nil, userInfo: ["logout": true])
        }
    }
}

// MARK: - API Client Extensions

extension APIClient {
    func getProfile() async throws -> ProfileResponse {
        return try await get("/profile")
    }
}

// MARK: - Helper Extensions

extension ProfileResponse {
    var work_experience: [Experience] {
        return (work_experience as? [Experience]) ?? []
    }
    
    var education: [Education] {
        return (education as? [Education]) ?? []
    }
    
    var skills: [String] {
        return (skills as? [String]) ?? []
    }
}
