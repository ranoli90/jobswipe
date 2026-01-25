import SwiftUI
import LocalAuthentication

struct LoginView: View {
    @StateObject private var viewModel: AuthViewModel
    @State private var showRegister = false
    @State private var showPassword = false
    
    init(apiClient: APIClient) {
        _viewModel = StateObject(wrappedValue: AuthViewModel(apiClient: apiClient))
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                // Logo and Title
                VStack(spacing: 8) {
                    Image(systemName: "briefcase.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    Text("JobSweep")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    Text("Swipe right to apply, swipe left to skip")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 40)
                
                // Email Field
                VStack(alignment: .leading, spacing: 8) {
                    Text("Email")
                        .font(.headline)
                        .foregroundColor(.blue)
                    HStack {
                        Image(systemName: "envelope")
                            .foregroundColor(.gray)
                        TextField("you@example.com", text: $viewModel.email)
                            .textInputAutocapitalization(.never)
                            .disableAutocorrection(true)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.blue, lineWidth: viewModel.email.isEmpty ? 0 : 2)
                    )
                }
                
                // Password Field
                VStack(alignment: .leading, spacing: 8) {
                    Text("Password")
                        .font(.headline)
                        .foregroundColor(.blue)
                    HStack {
                        Image(systemName: "lock")
                            .foregroundColor(.gray)
                        if showPassword {
                            TextField("Password", text: $viewModel.password)
                                .disableAutocorrection(true)
                        } else {
                            SecureField("Password", text: $viewModel.password)
                                .disableAutocorrection(true)
                        }
                        Button(action: { showPassword.toggle() }) {
                            Image(systemName: showPassword ? "eye.slash" : "eye")
                                .foregroundColor(.gray)
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.blue, lineWidth: viewModel.password.isEmpty ? 0 : 2)
                    )
                }
                
                // Error Message
                if let error = viewModel.errorMessage {
                    HStack {
                        Image(systemName: "exclamationmark.triangle")
                            .foregroundColor(.red)
                        Text(error)
                            .font(.subheadline)
                            .foregroundColor(.red)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                
                // Login Button
                Button(action: {
                    Task {
                        await viewModel.login()
                    }
                }) {
                    HStack {
                        if viewModel.isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        }
                        Text("Log In")
                            .font(.headline)
                            .fontWeight(.bold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        viewModel.isLoading 
                            ? Color.blue.opacity(0.7) 
                            : Color.blue
                    )
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                }
                .disabled(viewModel.isLoading || viewModel.email.isEmpty || viewModel.password.isEmpty)
                
                // Biometric Authentication
                if LAContext().canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil) {
                    Button(action: {
                        Task {
                            await viewModel.authenticateWithBiometrics()
                        }
                    }) {
                        HStack {
                            Image(systemName: LAContext().biometryType == .faceID ? "faceid" : "touchid")
                                .font(.title2)
                            Text("Use \(LAContext().biometryType == .faceID ? "Face ID" : "Touch ID")")
                                .font(.headline)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemGray6))
                        .foregroundColor(.blue)
                        .cornerRadius(10)
                    }
                    .padding(.top, 20)
                }
                
                // Register Link
                HStack {
                    Text("Don't have an account?")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Button("Sign Up") {
                        showRegister.toggle()
                    }
                    .font(.subheadline)
                    .foregroundColor(.blue)
                }
                .padding(.top, 20)
                
                Spacer()
            }
            .padding(.horizontal, 24)
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: $showRegister) {
                RegisterView(apiClient: viewModel.apiClient)
            }
            .onChange(of: viewModel.isAuthenticated) { isAuthenticated in
                if isAuthenticated {
                    // Navigate to main app
                    NotificationCenter.default.post(name: .authSuccess, object: nil)
                }
            }
        }
    }
}

extension Notification.Name {
    static let authSuccess = Notification.Name("authSuccess")
}
