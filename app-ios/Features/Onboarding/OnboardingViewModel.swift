import Foundation
import PhotosUI
import Combine

@MainActor
class OnboardingViewModel: ObservableObject {
    // Step tracking
    @Published var currentStep: Int = 1
    let totalSteps: Int = 4
    
    // Profile information
    @Published var fullName: String = ""
    @Published var phone: String = ""
    @Published var location: String = ""
    @Published var headline: String = ""
    
    // Resume information
    @Published var resumeUrl: URL?
    @Published var isUploading: Bool = false
    
    // Job preferences
    let availableJobTypes = ["Full-time", "Part-time", "Contract", "Temporary"]
    @Published var selectedJobTypes: Set<String> = ["Full-time"]
    
    enum RemotePreference: String, CaseIterable {
        case any = "Any"
        case remote = "Remote Only"
        case onsite = "On-site Only"
    }
    @Published var remotePreference: RemotePreference = .any
    
    enum ExperienceLevel: String, CaseIterable {
        case entry = "Entry Level"
        case mid = "Mid Level"
        case senior = "Senior Level"
        case executive = "Executive"
    }
    @Published var experienceLevel: ExperienceLevel = .mid
    
    // Errors and completion
    @Published var errorMessage: String?
    @Published var isOnboardingComplete: Bool = false
    
    private let apiClient: APIClient
    private var cancellables = Set<AnyCancellable>()
    
    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }
    
    // MARK: - Profile Validation
    
    var isProfileValid: Bool {
        !fullName.isEmpty && !phone.isEmpty && !location.isEmpty && !headline.isEmpty
    }
    
    func validateProfile() -> Bool {
        guard isProfileValid else {
            errorMessage = "Please fill in all required fields"
            return false
        }
        
        guard isValidPhoneNumber(phone) else {
            errorMessage = "Please enter a valid phone number"
            return false
        }
        
        return true
    }
    
    private func isValidPhoneNumber(_ phone: String) -> Bool {
        let phoneRegex = "^[+]?[0-9]{10,15}$"
        let cleanedPhone = phone.replacingOccurrences(of: "[^0-9+]", with: "", options: .regularExpression)
        return NSPredicate(format: "SELF MATCHES %@", phoneRegex).evaluate(with: cleanedPhone)
    }
    
    // MARK: - Resume Upload
    
    var isResumeUploaded: Bool {
        resumeUrl != nil
    }
    
    func uploadResume(from item: PhotosPickerItem) async {
        isUploading = true
        errorMessage = nil
        
        do {
            if let data = try await item.loadTransferable(type: Data.self) {
                let temporaryFileURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(UUID().uuidString)
                    .appendingPathExtension("pdf")
                
                try data.write(to: temporaryFileURL)
                
                let profile = try await apiClient.uploadResume(temporaryFileURL)
                resumeUrl = temporaryFileURL
                updateProfileFromAPI(profile)
            } else {
                throw NSError(domain: "JobSweep", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to load image data"])
            }
        } catch let error as APIError {
            errorMessage = error.localizedDescription
        } catch {
            errorMessage = "Failed to upload resume. Please try again."
        }
        
        isUploading = false
    }
    
    func uploadResume(_ fileURL: URL) throws {
        isUploading = true
        errorMessage = nil
        
        Task {
            do {
                let profile = try await apiClient.uploadResume(fileURL)
                resumeUrl = fileURL
                updateProfileFromAPI(profile)
            } catch let error as APIError {
                errorMessage = error.localizedDescription
            } catch {
                errorMessage = "Failed to upload resume. Please try again."
            }
            
            isUploading = false
        }
    }
    
    private func updateProfileFromAPI(_ profile: ProfileResponse) {
        if fullName.isEmpty, let name = profile.full_name {
            fullName = name
        }
        if phone.isEmpty, let phoneNumber = profile.phone {
            phone = phoneNumber
        }
        if location.isEmpty, let loc = profile.location {
            location = loc
        }
        if headline.isEmpty, let title = profile.headline {
            headline = title
        }
    }
    
    // MARK: - Complete Onboarding
    
    func completeOnboarding() {
        Task {
            do {
                // Update profile with collected information
                let profileUpdate = CandidateProfileUpdate(
                    full_name: fullName,
                    phone: phone,
                    location: location,
                    headline: headline,
                    skills: nil,
                    experience: nil,
                    education: nil,
                    preferences: CandidateProfileUpdate.Preferences(
                        job_types: Array(selectedJobTypes),
                        remote_preference: remotePreference.rawValue,
                        experience_level: experienceLevel.rawValue
                    )
                )
                
                let updatedProfile = try await apiClient.updateProfile(profileUpdate)
                isOnboardingComplete = true
                
                // Post notification to update app state
                NotificationCenter.default.post(name: .onboardingComplete, object: nil)
                
                // Track onboarding completion
                AnalyticsService.shared.track(event: .onboardingComplete)
            } catch let error as APIError {
                errorMessage = error.localizedDescription
            } catch {
                errorMessage = "Failed to complete onboarding. Please try again."
            }
        }
    }
    
    // MARK: - Navigation
    
    func canNavigateToNextStep() -> Bool {
        switch currentStep {
        case 1:
            return true
        case 2:
            return isProfileValid
        case 3:
            return isResumeUploaded
        case 4:
            return true
        default:
            return false
        }
    }
}

// MARK: - Analytics Service

class AnalyticsService {
    static let shared = AnalyticsService()
    
    private init() {}
    
    func track(event: AnalyticsEvent) {
        // In a real app, send this to a analytics service like Firebase or Amplitude
        print("Tracking event: \(event.rawValue)")
        
        // Example implementation using UserDefaults to track first app launch
        if event == .appLaunch {
            UserDefaults.standard.set(true, forKey: "hasLaunchedBefore")
        }
    }
}

enum AnalyticsEvent: String {
    case appLaunch = "app_launch"
    case onboardingStart = "onboarding_start"
    case onboardingComplete = "onboarding_complete"
    case profileSetup = "profile_setup"
    case resumeUpload = "resume_upload"
    case jobView = "job_view"
    case jobSwipe = "job_swipe"
    case applicationSubmit = "application_submit"
    case applicationSuccess = "application_success"
    case applicationFailure = "application_failure"
    case searchPerformed = "search_performed"
}
