import SwiftUI
import LocalAuthentication

@main
struct JobSweepApp: App {
    @StateObject private var appState = AppState()
    @Environment(\.scenePhase) private var scenePhase
    
    var body: some Scene {
        WindowGroup {
            if appState.isAuthenticated {
                if appState.isOnboardingComplete {
                    MainAppView()
                        .environmentObject(appState)
                } else {
                    OnboardingView(apiClient: appState.apiClient)
                        .environmentObject(appState)
                }
            } else {
                LoginView(apiClient: appState.apiClient)
                    .environmentObject(appState)
            }
        }
        .onChange(of: scenePhase) { _, newPhase in
            if newPhase == .active {
                appState.checkAuthentication()
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .authSuccess)) { notification in
            if let userInfo = notification.userInfo, userInfo["logout"] as? Bool == true {
                appState.logout()
            } else {
                appState.isAuthenticated = true
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .onboardingComplete)) { _ in
            appState.isOnboardingComplete = true
        }
    }
}

class AppState: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var isOnboardingComplete: Bool = false
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    let apiClient: APIClient
    
    private let keychainService = KeychainService()
    private let userDefaults = UserDefaults.standard
    
    init() {
        let baseURL = URL(string: "http://localhost:8000/api")!
        self.apiClient = APIClient(baseURL: baseURL) { [weak self] in
            self?.keychainService.token
        }
        
        // Check onboarding status
        self.isOnboardingComplete = userDefaults.bool(forKey: "onboardingComplete")
    }
    
    func checkAuthentication() {
        if let token = keychainService.token {
            Task {
                isLoading = true
                do {
                    // Validate token with backend
                    _ = try await apiClient.getCurrentUser()
                    isAuthenticated = true
                } catch {
                    // Token is invalid or expired, remove it
                    try? keychainService.removeToken()
                    isAuthenticated = false
                }
                isLoading = false
            }
        } else {
            isAuthenticated = false
        }
    }
    
    func logout() throws {
        try keychainService.removeToken()
        userDefaults.set(false, forKey: "onboardingComplete")
        isAuthenticated = false
        isOnboardingComplete = false
        errorMessage = nil
    }
    
    func markOnboardingComplete() {
        userDefaults.set(true, forKey: "onboardingComplete")
        isOnboardingComplete = true
    }
}

struct MainAppView: View {
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        TabView {
            JobFeedView(apiClient: appState.apiClient)
                .tabItem {
                    Label("Feed", systemImage: "list.bullet")
                }
            
            ApplicationsView(apiClient: appState.apiClient)
                .tabItem {
                    Label("Applications", systemImage: "briefcase.fill")
                }
            
            ProfileView(apiClient: appState.apiClient)
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
        }
        .navigationViewStyle(.stack)
    }
}

