import SwiftUI

struct ProfileView: View {
    @StateObject private var viewModel: ProfileViewModel
    
    init(apiClient: APIClient) {
        _viewModel = StateObject(wrappedValue: ProfileViewModel(apiClient: apiClient))
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 16) {
                        // Profile Image
                        ZStack {
                            Circle()
                                .frame(width: 120, height: 120)
                                .foregroundColor(.blue.opacity(0.1))
                            Image(systemName: "person.circle.fill")
                                .font(.system(size: 100))
                                .foregroundColor(.blue)
                        }
                        
                        // User Info
                        VStack(spacing: 8) {
                            Text(viewModel.profile?.full_name ?? "Loading...")
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Text(viewModel.profile?.headline ?? "Professional")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            HStack(spacing: 12) {
                                if let location = viewModel.profile?.location {
                                    HStack(spacing: 4) {
                                        Image(systemName: "location.fill")
                                            .font(.caption)
                                        Text(location)
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                
                                if let phone = viewModel.profile?.phone {
                                    HStack(spacing: 4) {
                                        Image(systemName: "phone.fill")
                                            .font(.caption)
                                        Text(phone)
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(20)
                    .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
                    
                    // Skills
                    if let skills = viewModel.profile?.skills, !skills.isEmpty {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Skills")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                            }
                            
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
                                    ForEach(skills, id: \.self) { skill in
                                        SkillTag(skill: skill)
                                    }
                                }
                                .padding(.horizontal, 8)
                            }
                        }
                    }
                    
                    // Experience
                    if let experience = viewModel.profile?.work_experience, !experience.isEmpty {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Work Experience")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                            }
                            
                            VStack(spacing: 12) {
                                ForEach(experience) { exp in
                                    ExperienceCard(experience: exp)
                                }
                            }
                        }
                    }
                    
                    // Education
                    if let education = viewModel.profile?.education, !education.isEmpty {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Education")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                            }
                            
                            VStack(spacing: 12) {
                                ForEach(education) { edu in
                                    EducationCard(education: edu)
                                }
                            }
                        }
                    }
                    
                    // Preferences
                    if let preferences = viewModel.profile?.preferences {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Job Preferences")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                            }
                            
                            VStack(spacing: 12) {
                                // Job Types
                                if let jobTypes = preferences.job_types, !jobTypes.isEmpty {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Job Types")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        HStack(spacing: 8) {
                                            ForEach(jobTypes, id: \.self) { jobType in
                                                Text(jobType)
                                                    .font(.caption)
                                                    .padding(.horizontal, 12)
                                                    .padding(.vertical, 6)
                                                    .background(Color.blue.opacity(0.1))
                                                    .foregroundColor(.blue)
                                                    .cornerRadius(12)
                                            }
                                        }
                                    }
                                }
                                
                                // Remote Preference
                                if let remotePreference = preferences.remote_preference {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Remote Preference")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        Text(remotePreference)
                                            .font(.caption)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(Color.blue.opacity(0.1))
                                            .foregroundColor(.blue)
                                            .cornerRadius(12)
                                    }
                                }
                                
                                // Experience Level
                                if let experienceLevel = preferences.experience_level {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Experience Level")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        Text(experienceLevel)
                                            .font(.caption)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(Color.blue.opacity(0.1))
                                            .foregroundColor(.blue)
                                            .cornerRadius(12)
                                    }
                                }
                            }
                        }
                    }
                    
                    // Resume
                    if let resumeUrl = viewModel.profile?.resume_file_url {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Resume")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                            }
                            
                            VStack(spacing: 8) {
                                HStack(spacing: 12) {
                                    Image(systemName: "doc.text.fill")
                                        .font(.title2)
                                        .foregroundColor(.blue)
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Resume.pdf")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        Text("Tap to download")
                                            .font(.caption)
                                            .foregroundColor(.blue)
                                    }
                                    Spacer()
                                    Image(systemName: "arrow.down.doc")
                                        .font(.headline)
                                        .foregroundColor(.blue)
                                }
                                .padding()
                                .background(Color(.systemGray6))
                                .cornerRadius(10)
                                .onTapGesture {
                                    // Handle resume download
                                    print("Downloading resume")
                                }
                            }
                        }
                    }
                    
                    // Actions
                    VStack(spacing: 16) {
                        Button(action: {
                            viewModel.refreshProfile()
                        }) {
                            HStack {
                                Image(systemName: "arrow.clockwise")
                                Text("Refresh Profile")
                                    .font(.headline)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                        
                        Button(action: {
                            // Handle edit profile
                        }) {
                            HStack {
                                Image(systemName: "pencil")
                                Text("Edit Profile")
                                    .font(.headline)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color(.systemGray6))
                            .foregroundColor(.blue)
                            .cornerRadius(10)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                Button("Logout") {
                    viewModel.logout()
                }
                .foregroundColor(.red)
            }
            .onAppear {
                viewModel.refreshProfile()
            }
            .alert(item: $viewModel.errorMessage) { error in
                Alert(title: Text("Error"), message: Text(error), dismissButton: .default(Text("OK")))
            }
        }
    }
}

// MARK: - Helper Views

struct SkillTag: View {
    let skill: String
    
    var body: some View {
        Text(skill)
            .font(.caption)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.blue.opacity(0.1))
            .foregroundColor(.blue)
            .cornerRadius(12)
    }
}

struct ExperienceCard: View {
    let experience: Experience
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(experience.position)
                        .font(.subheadline)
                        .fontWeight(.bold)
                    Text(experience.company)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                HStack(spacing: 4) {
                    Text(formatDate(experience.start_date))
                    Text("-")
                    if let endDate = experience.end_date {
                        Text(formatDate(endDate))
                    } else {
                        Text("Present")
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
            
            if let description = experience.description {
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
                    .truncationMode(.tail)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
    
    private func formatDate(_ dateString: String) -> String {
        // Simple date formatting - replace with proper date parsing
        return dateString.prefix(4).description
    }
}

struct EducationCard: View {
    let education: Education
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    if let degree = education.degree {
                        Text(degree)
                            .font(.subheadline)
                            .fontWeight(.bold)
                    }
                    if let field = education.field_of_study {
                        Text(field)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    Text(education.institution)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                HStack(spacing: 4) {
                    Text(formatDate(education.start_date))
                    Text("-")
                    if let endDate = education.end_date {
                        Text(formatDate(endDate))
                    } else {
                        Text("Present")
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
    
    private func formatDate(_ dateString: String) -> String {
        // Simple date formatting - replace with proper date parsing
        return dateString.prefix(4).description
    }
}
