import SwiftUI
import UniformTypeIdentifiers
import PhotosUI

struct OnboardingView: View {
    @StateObject private var viewModel: OnboardingViewModel
    @State private var selectedPhotoItem: PhotosPickerItem?
    @State private var showImagePicker = false
    @State private var showFilePicker = false
    
    init(apiClient: APIClient) {
        _viewModel = StateObject(wrappedValue: OnboardingViewModel(apiClient: apiClient))
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                // Progress Indicator
                OnboardingProgressView(currentStep: viewModel.currentStep, totalSteps: viewModel.totalSteps)
                
                // Step Content
                Group {
                    switch viewModel.currentStep {
                    case 1:
                        WelcomeStepView(
                            onContinue: { viewModel.currentStep = 2 }
                        )
                    case 2:
                        ProfileSetupStepView(
                            viewModel: viewModel,
                            onBack: { viewModel.currentStep = 1 },
                            onContinue: { viewModel.currentStep = 3 }
                        )
                    case 3:
                        ResumeUploadStepView(
                            viewModel: viewModel,
                            selectedPhotoItem: $selectedPhotoItem,
                            showImagePicker: $showImagePicker,
                            showFilePicker: $showFilePicker,
                            onBack: { viewModel.currentStep = 2 },
                            onContinue: { viewModel.currentStep = 4 }
                        )
                    case 4:
                        PreferencesStepView(
                            viewModel: viewModel,
                            onBack: { viewModel.currentStep = 3 },
                            onComplete: { viewModel.completeOnboarding() }
                        )
                    default:
                        EmptyView()
                    }
                }
                .animation(.spring(), value: viewModel.currentStep)
                
                Spacer()
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if viewModel.currentStep > 1 {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Back") {
                            viewModel.currentStep -= 1
                        }
                    }
                }
            }
            .photosPicker(
                isPresented: $showImagePicker,
                selection: $selectedPhotoItem,
                matching: [.images]
            ) {
                EmptyView()
            }
            .fileImporter(
                isPresented: $showFilePicker,
                allowedContentTypes: [.pdf],
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    if let url = urls.first {
                        do {
                            try viewModel.uploadResume(url)
                        } catch {
                            viewModel.errorMessage = "Failed to read file"
                        }
                    }
                case .failure(let error):
                    viewModel.errorMessage = error.localizedDescription
                }
            }
            .onChange(of: selectedPhotoItem) { _, newValue in
                if let item = newValue {
                    Task {
                        await viewModel.uploadResume(from: item)
                    }
                }
            }
            .alert(item: $viewModel.errorMessage) { error in
                Alert(title: Text("Error"), message: Text(error), dismissButton: .default(Text("OK")))
            }
            .onChange(of: viewModel.isOnboardingComplete) { _, isComplete in
                if isComplete {
                    NotificationCenter.default.post(name: .onboardingComplete, object: nil)
                }
            }
        }
    }
}

// MARK: - Welcome Step

struct WelcomeStepView: View {
    let onContinue: () -> Void
    
    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            
            Image(systemName: "hand.wave.fill")
                .font(.system(size: 80))
                .foregroundColor(.blue)
            
            VStack(spacing: 8) {
                Text("Welcome to JobSweep!")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                Text("Your smart job application assistant")
                    .font(.headline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button(action: onContinue) {
                HStack {
                    Text("Get Started")
                        .font(.headline)
                        .fontWeight(.bold)
                    Image(systemName: "arrow.right")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
                .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
            }
        }
        .padding(.horizontal, 24)
    }
}

// MARK: - Profile Setup Step

struct ProfileSetupStepView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    let onBack: () -> Void
    let onContinue: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Let's get to know you")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                TextField("Full Name", text: $viewModel.fullName)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
                
                TextField("Phone Number", text: $viewModel.phone)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.phonePad)
                
                TextField("Location", text: $viewModel.location)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
                
                TextField("Professional Headline", text: $viewModel.headline)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.sentences)
            }
            
            Spacer()
            
            HStack(spacing: 16) {
                Button(action: onBack) {
                    Text("Back")
                        .font(.headline)
                        .foregroundColor(.blue)
                        .frame(minWidth: 100)
                }
                
                Button(action: {
                    if viewModel.validateProfile() {
                        onContinue()
                    }
                }) {
                    HStack {
                        Text("Continue")
                            .font(.headline)
                            .fontWeight(.bold)
                        Image(systemName: "arrow.right")
                    }
                    .frame(minWidth: 100)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                }
                .disabled(!viewModel.isProfileValid)
            }
        }
        .padding(.horizontal, 24)
    }
}

// MARK: - Resume Upload Step

struct ResumeUploadStepView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    @Binding var selectedPhotoItem: PhotosPickerItem?
    @Binding var showImagePicker: Bool
    @Binding var showFilePicker: Bool
    let onBack: () -> Void
    let onContinue: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Upload your resume")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                Text("Help us understand your skills and experience")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                if let resumeUrl = viewModel.resumeUrl {
                    HStack {
                        Image(systemName: "doc.text.fill")
                            .font(.largeTitle)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading) {
                            Text(resumeUrl.lastPathComponent)
                                .font(.headline)
                            Text("Tap to replace")
                                .font(.subheadline)
                                .foregroundColor(.blue)
                        }
                        
                        Spacer()
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                    .onTapGesture {
                        showFilePicker = true
                    }
                } else {
                    VStack(spacing: 16) {
                        Button(action: {
                            showFilePicker = true
                        }) {
                            VStack(spacing: 12) {
                                Image(systemName: "plus.app.fill")
                                    .font(.system(size: 40))
                                    .foregroundColor(.blue)
                                Text("Choose from Files")
                                    .font(.headline)
                                    .foregroundColor(.blue)
                            }
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(10)
                        }
                        
                        Divider()
                        
                        Button(action: {
                            showImagePicker = true
                        }) {
                            VStack(spacing: 12) {
                                Image(systemName: "camera.fill")
                                    .font(.system(size: 40))
                                    .foregroundColor(.blue)
                                Text("Take Photo or Choose from Photos")
                                    .font(.headline)
                                    .foregroundColor(.blue)
                            }
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(10)
                        }
                    }
                }
            }
            
            if viewModel.isUploading {
                VStack(spacing: 8) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .blue))
                    Text("Uploading and analyzing resume...")
                        .font(.subheadline)
                        .foregroundColor(.blue)
                }
            }
            
            Spacer()
            
            HStack(spacing: 16) {
                Button(action: onBack) {
                    Text("Back")
                        .font(.headline)
                        .foregroundColor(.blue)
                        .frame(minWidth: 100)
                }
                
                Button(action: onContinue) {
                    HStack {
                        Text("Continue")
                            .font(.headline)
                            .fontWeight(.bold)
                        Image(systemName: "arrow.right")
                    }
                    .frame(minWidth: 100)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                }
                .disabled(!viewModel.isResumeUploaded)
            }
        }
        .padding(.horizontal, 24)
    }
}

// MARK: - Preferences Step

struct PreferencesStepView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    let onBack: () -> Void
    let onComplete: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Job Preferences")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                Text("Help us find the right jobs for you")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Job Types")
                        .font(.headline)
                    
                    ForEach(viewModel.availableJobTypes, id: \.self) { jobType in
                        Toggle(jobType, isOn: Binding(
                            get: { viewModel.selectedJobTypes.contains(jobType) },
                            set: { isSelected in
                                if isSelected {
                                    viewModel.selectedJobTypes.insert(jobType)
                                } else {
                                    viewModel.selectedJobTypes.remove(jobType)
                                }
                            }
                        ))
                        .toggleStyle(SwitchToggleStyle(tint: .blue))
                    }
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Remote Work")
                        .font(.headline)
                    
                    Picker("Remote Work", selection: $viewModel.remotePreference) {
                        Text("Any").tag(RemotePreference.any)
                        Text("Remote Only").tag(RemotePreference.remote)
                        Text("On-site Only").tag(RemotePreference.onsite)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Experience Level")
                        .font(.headline)
                    
                    Picker("Experience Level", selection: $viewModel.experienceLevel) {
                        Text("Entry Level").tag(ExperienceLevel.entry)
                        Text("Mid Level").tag(ExperienceLevel.mid)
                        Text("Senior Level").tag(ExperienceLevel.senior)
                        Text("Executive").tag(ExperienceLevel.executive)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
            }
            
            Spacer()
            
            HStack(spacing: 16) {
                Button(action: onBack) {
                    Text("Back")
                        .font(.headline)
                        .foregroundColor(.blue)
                        .frame(minWidth: 100)
                }
                
                Button(action: onComplete) {
                    HStack {
                        Text("Complete")
                            .font(.headline)
                            .fontWeight(.bold)
                        Image(systemName: "checkmark")
                    }
                    .frame(minWidth: 100)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                }
            }
        }
        .padding(.horizontal, 24)
    }
}

// MARK: - Progress View

struct OnboardingProgressView: View {
    let currentStep: Int
    let totalSteps: Int
    
    var body: some View {
        VStack(spacing: 8) {
            HStack(spacing: 4) {
                ForEach(1...totalSteps, id: \.self) { step in
                    Capsule()
                        .frame(height: 4)
                        .foregroundColor(step <= currentStep ? .blue : .gray)
                        .animation(.spring(), value: currentStep)
                }
            }
            Text("Step \(currentStep) of \(totalSteps)")
                .font(.subheadline)
                .foregroundColor(.blue)
        }
        .padding()
    }
}

// MARK: - Extensions

extension Notification.Name {
    static let onboardingComplete = Notification.Name("onboardingComplete")
}
