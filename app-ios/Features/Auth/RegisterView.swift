import SwiftUI

struct RegisterView: View {
    @StateObject private var viewModel: AuthViewModel
    @State private var confirmPassword: String = ""
    @State private var showPassword = false
    @State private var showConfirmPassword = false
    
    init(apiClient: APIClient) {
        _viewModel = StateObject(wrappedValue: AuthViewModel(apiClient: apiClient))
    }
    
    var body: some View {
        VStack(spacing: 24) {
            // Logo and Title
            VStack(spacing: 8) {
                Image(systemName: "briefcase.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                Text("Create Account")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                Text("Join JobSweep and start applying with a swipe")
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
                .alert("Weak Password", isPresented: $showWeakPasswordAlert) {
                    Button("OK", role: .cancel) { }
                } message: {
                    Text("Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character.")
                }
            }
            
            // Confirm Password Field
            VStack(alignment: .leading, spacing: 8) {
                Text("Confirm Password")
                    .font(.headline)
                    .foregroundColor(.blue)
                HStack {
                    Image(systemName: "lock.fill")
                        .foregroundColor(.gray)
                    if showConfirmPassword {
                        TextField("Confirm Password", text: $confirmPassword)
                            .disableAutocorrection(true)
                    } else {
                        SecureField("Confirm Password", text: $confirmPassword)
                            .disableAutocorrection(true)
                    }
                    Button(action: { showConfirmPassword.toggle() }) {
                        Image(systemName: showConfirmPassword ? "eye.slash" : "eye")
                            .foregroundColor(.gray)
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(10)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.blue, lineWidth: confirmPassword.isEmpty ? 0 : 2)
                )
                .alert("Password Mismatch", isPresented: $showMismatchAlert) {
                    Button("OK", role: .cancel) { }
                } message: {
                    Text("Passwords do not match. Please re-enter your password.")
                }
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
            
            // Register Button
            Button(action: {
                if validateFields() {
                    Task {
                        await viewModel.register()
                    }
                }
            }) {
                HStack {
                    if viewModel.isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    }
                    Text("Create Account")
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
            .disabled(viewModel.isLoading || viewModel.email.isEmpty || viewModel.password.isEmpty || confirmPassword.isEmpty)
            
            Spacer()
        }
        .padding(.horizontal, 24)
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: viewModel.isAuthenticated) { isAuthenticated in
            if isAuthenticated {
                NotificationCenter.default.post(name: .authSuccess, object: nil)
            }
        }
    }
    
    private var showWeakPasswordAlert: Binding<Bool> {
        Binding(
            get: { !isPasswordStrong(viewModel.password) && !viewModel.password.isEmpty },
            set: { _ in }
        )
    }
    
    private var showMismatchAlert: Binding<Bool> {
        Binding(
            get: { !viewModel.password.isEmpty && !confirmPassword.isEmpty && viewModel.password != confirmPassword },
            set: { _ in }
        )
    }
    
    private func isPasswordStrong(_ password: String) -> Bool {
        let passwordRegex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$"
        return NSPredicate(format: "SELF MATCHES %@", passwordRegex).evaluate(with: password)
    }
    
    private func validateFields() -> Bool {
        guard !viewModel.email.isEmpty, !viewModel.password.isEmpty, !confirmPassword.isEmpty else {
            return false
        }
        
        guard isValidEmail(viewModel.email) else {
            viewModel.errorMessage = "Please enter a valid email address"
            return false
        }
        
        guard isPasswordStrong(viewModel.password) else {
            return false
        }
        
        guard viewModel.password == confirmPassword else {
            return false
        }
        
        return true
    }
    
    private func isValidEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        return NSPredicate(format: "SELF MATCHES %@", emailRegex).evaluate(with: email)
    }
}
