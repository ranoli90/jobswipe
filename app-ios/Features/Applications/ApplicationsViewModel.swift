import Foundation
import Combine

@MainActor
class ApplicationsViewModel: ObservableObject {
    @Published private(set) var applications: [ApplicationResponse] = []
    @Published private(set) var auditLogs: [String: [ApplicationAuditLog]] = [:]
    @Published private(set) var isLoading: Bool = false
    @Published private(set) var errorMessage: String?
    
    private let apiClient: APIClient
    private var cancellables = Set<AnyCancellable>()
    
    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }
    
    // MARK: - Computed Properties
    
    var appliedCount: Int {
        applications.filter { $0.status == "applied" || $0.status == "queued" }.count
    }
    
    var inProgressCount: Int {
        applications.filter { $0.status == "in_progress" }.count
    }
    
    var completedCount: Int {
        applications.filter { $0.status == "completed" }.count
    }
    
    var failedCount: Int {
        applications.filter { $0.status == "failed" }.count
    }
    
    // MARK: - Public Methods
    
    func refreshApplications() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let applications = try await apiClient.getApplications()
                self.applications = applications.sorted(by: { $0.created_at > $1.created_at })
                
                // Load audit logs for each application
                await loadAuditLogs(for: applications)
            } catch let error as APIError {
                errorMessage = error.localizedDescription
            } catch {
                errorMessage = "Failed to load applications. Please try again."
            }
            
            isLoading = false
        }
    }
    
    func auditLogs(for applicationId: String) -> [ApplicationAuditLog] {
        return auditLogs[applicationId] ?? []
    }
    
    // MARK: - Private Methods
    
    private func loadAuditLogs(for applications: [ApplicationResponse]) async {
        var allLogs: [String: [ApplicationAuditLog]] = [:]
        
        for application in applications {
            do {
                let logs = try await apiClient.getApplicationAuditLogs(jobId: application.job_id)
                allLogs[application.id] = logs
            } catch {
                // Continue with other applications if one fails
                print("Failed to load audit logs for application \(application.id): \(error)")
            }
        }
        
        auditLogs = allLogs
    }
}

// MARK: - API Client Extensions

extension APIClient {
    func getApplicationAuditLogs(jobId: String) async throws -> [ApplicationAuditLog] {
        return try await get("/applications/\(jobId)/audit")
    }
}

// MARK: - Application Audit Log Model

struct ApplicationAuditLog: Codable, Identifiable {
    let id: String
    let step: String
    let payload: [String: Any]?
    let artifacts: [String: Any]?
    let timestamp: Date
    
    var application_id: String? {
        return payload?["application_id"] as? String
    }
    
    var success: Bool {
        return !step.lowercased().contains("error") && !step.lowercased().contains("failed")
    }
    
    var details: String? {
        if let error = payload?["error"] as? String {
            return error
        }
        return payload?["message"] as? String
    }
    
    var duration: Double? {
        return payload?["duration"] as? Double
    }
    
    var iconName: String {
        switch step.lowercased() {
        case "parsing job page":
            return "doc.text"
        case "filling form":
            return "text.bubble"
        case "uploading resume":
            return "arrow.up.doc"
        case "submitting":
            return "paperplane.fill"
        case "error", "failed":
            return "exclamationmark.triangle.fill"
        default:
            return "checkmark.circle"
        }
    }
    
    var iconColor: Color {
        return success ? .green : .red
    }
    
    enum CodingKeys: String, CodingKey {
        case id, step, payload, artifacts, timestamp
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        step = try container.decode(String.self, forKey: .step)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        
        // Decode payload and artifacts as dictionaries
        do {
            payload = try container.decodeIfPresent([String: Any].self, forKey: .payload)
        } catch {
            payload = nil
        }
        
        do {
            artifacts = try container.decodeIfPresent([String: Any].self, forKey: .artifacts)
        } catch {
            artifacts = nil
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(step, forKey: .step)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encodeIfPresent(payload, forKey: .payload)
        try container.encodeIfPresent(artifacts, forKey: .artifacts)
    }
}
