import SwiftUI

struct ApplicationsView: View {
    @StateObject private var viewModel: ApplicationsViewModel
    @State private var selectedApplication: ApplicationResponse?
    
    init(apiClient: APIClient) {
        _viewModel = StateObject(wrappedValue: ApplicationsViewModel(apiClient: apiClient))
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Header
                VStack(spacing: 8) {
                    Text("Applications")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    
                    HStack(spacing: 16) {
                        ApplicationStatusBadge(
                            status: "Applied",
                            count: viewModel.appliedCount,
                            color: .blue
                        )
                        ApplicationStatusBadge(
                            status: "In Progress",
                            count: viewModel.inProgressCount,
                            color: .orange
                        )
                        ApplicationStatusBadge(
                            status: "Completed",
                            count: viewModel.completedCount,
                            color: .green
                        )
                        ApplicationStatusBadge(
                            status: "Failed",
                            count: viewModel.failedCount,
                            color: .red
                        )
                    }
                    .padding(.horizontal)
                }
                .padding()
                .background(Color(.systemBackground))
                .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
                
                // Applications List
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(viewModel.applications) { application in
                            ApplicationCardView(application: application)
                                .onTapGesture {
                                    selectedApplication = application
                                }
                        }
                        
                        if viewModel.isLoading {
                            LoadingView()
                        }
                        
                        if viewModel.applications.isEmpty && !viewModel.isLoading {
                            EmptyStateView(
                                title: "No Applications Yet",
                                message: "Start applying to jobs to see your applications here"
                            )
                        }
                    }
                    .padding()
                }
                
                // Error View
                if let error = viewModel.errorMessage {
                    ErrorView(error: error)
                        .padding()
                }
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                Button("Refresh") {
                    viewModel.refreshApplications()
                }
                .foregroundColor(.blue)
            }
            .onAppear {
                viewModel.refreshApplications()
            }
            .sheet(item: $selectedApplication) { application in
                ApplicationDetailsView(
                    application: application,
                    auditLogs: viewModel.auditLogs(for: application.id)
                )
            }
        }
    }
}

// MARK: - Application Card View

struct ApplicationCardView: View {
    let application: ApplicationResponse
    
    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 16) {
                // Status Badge
                ApplicationStatusBadge(
                    status: application.status,
                    count: nil,
                    color: statusColor(application.status)
                )
                
                // Application Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(application.job_title)
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    Text(application.company_name)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    if let location = application.location {
                        HStack(spacing: 4) {
                            Image(systemName: "location.fill")
                                .font(.caption)
                            Text(location)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                
                // Actions
                if application.status == "queued" || application.status == "in_progress" {
                    Button(action: {}) {
                        Image(systemName: "pause.fill")
                            .foregroundColor(.orange)
                    }
                }
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            // Application Timeline
            HStack(spacing: 8) {
                Image(systemName: "clock.fill")
                    .font(.caption)
                    .foregroundColor(.blue)
                Text("Applied \(application.created_at, formatter: dateFormatter)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                if let completedAt = application.completed_at {
                    Spacer()
                    Image(systemName: "checkmark.circle.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                    Text("Completed \(completedAt, formatter: dateFormatter)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            // Progress Indicator
            if application.status == "in_progress" {
                ProgressView(value: application.progress ?? 0.5)
                    .progressViewStyle(LinearProgressViewStyle(tint: .blue))
                    .padding(.horizontal, 8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 10, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.systemGray3), lineWidth: 1)
        )
    }
    
    private func statusColor(_ status: String) -> Color {
        switch status {
        case "applied", "queued":
            return .blue
        case "in_progress":
            return .orange
        case "completed":
            return .green
        case "failed":
            return .red
        default:
            return .gray
        }
    }
}

// MARK: - Application Details View

struct ApplicationDetailsView: View {
    let application: ApplicationResponse
    let auditLogs: [ApplicationAuditLog]
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Job Information
                    VStack(spacing: 16) {
                        HStack {
                            Text("Job Information")
                                .font(.headline)
                                .fontWeight(.bold)
                                .foregroundColor(.blue)
                            Spacer()
                            ApplicationStatusBadge(
                                status: application.status,
                                count: nil,
                                color: statusColor(application.status)
                            )
                        }
                        
                        VStack(alignment: .leading, spacing: 12) {
                            Text(application.job_title)
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Text(application.company_name)
                                .font(.headline)
                                .foregroundColor(.blue)
                            
                            HStack(spacing: 8) {
                                if let location = application.location {
                                    HStack(spacing: 4) {
                                        Image(systemName: "location.fill")
                                        Text(location)
                                    }
                                }
                                
                                if let salary = application.salary {
                                    HStack(spacing: 4) {
                                        Image(systemName: "dollarsign.circle.fill")
                                        Text(salary)
                                    }
                                }
                            }
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            
                            if let description = application.job_description {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Description")
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                    Text(description)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                        .lineLimit(3)
                                        .truncationMode(.tail)
                                }
                            }
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(10)
                    }
                    
                    // Application Timeline
                    if !auditLogs.isEmpty {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Application Timeline")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
                                Spacer()
                                Text("\(auditLogs.count) events")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            VStack(spacing: 8) {
                                ForEach(auditLogs) { log in
                                    ApplicationAuditLogView(log: log)
                                }
                            }
                        }
                    }
                    
                    // Application Actions
                    if application.status == "failed" {
                        VStack(spacing: 16) {
                            HStack {
                                Text("Application Failed")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.red)
                                Spacer()
                            }
                            
                            VStack(spacing: 12) {
                                if let error = application.error_message {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Error Message")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        Text(error)
                                            .font(.caption)
                                            .foregroundColor(.red)
                                            .lineLimit(nil)
                                    }
                                    .padding()
                                    .background(Color(.systemRed).opacity(0.1))
                                    .cornerRadius(10)
                                }
                                
                                HStack(spacing: 12) {
                                    Button(action: {}) {
                                        HStack {
                                            Image(systemName: "arrow.clockwise")
                                            Text("Retry")
                                        }
                                        .padding()
                                        .background(Color.blue)
                                        .foregroundColor(.white)
                                        .cornerRadius(10)
                                    }
                                    
                                    Button(action: {}) {
                                        HStack {
                                            Image(systemName: "trash.fill")
                                            Text("Delete")
                                        }
                                        .padding()
                                        .background(Color.red)
                                        .foregroundColor(.white)
                                        .cornerRadius(10)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Application Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Back") {
                        // Dismiss sheet
                    }
                }
            }
        }
    }
    
    private func statusColor(_ status: String) -> Color {
        switch status {
        case "applied", "queued":
            return .blue
        case "in_progress":
            return .orange
        case "completed":
            return .green
        case "failed":
            return .red
        default:
            return .gray
        }
    }
}

// MARK: - Helper Views

struct ApplicationStatusBadge: View {
    let status: String
    let count: Int?
    let color: Color
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 0) {
                Text(status)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                if let count = count {
                    Text("\(count)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(20)
    }
}

struct ApplicationAuditLogView: View {
    let log: ApplicationAuditLog
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: log.iconName)
                    .font(.subheadline)
                    .foregroundColor(log.iconColor)
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Text(log.step)
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        if log.success {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.caption)
                                .foregroundColor(.green)
                        } else {
                            Image(systemName: "xmark.circle.fill")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                    
                    Text(log.timestamp, formatter: dateFormatter)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                
                Spacer()
            }
            
            if let details = log.details {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Details")
                        .font(.caption)
                        .fontWeight(.medium)
                    Text(details)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 8)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Formatters

private let dateFormatter: DateFormatter = {
    let formatter = DateFormatter()
    formatter.dateStyle = .medium
    formatter.timeStyle = .short
    return formatter
}()
