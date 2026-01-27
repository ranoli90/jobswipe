import Foundation

struct APIClient {
    let baseURL: URL
    var tokenProvider: () -> String?
    
    // MARK: - Authentication
    
    func login(email: String, password: String) async throws -> TokenResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/auth/login"))
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let body = "username=\(email.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!)&password=\(password.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!)"
        request.httpBody = body.data(using: .utf8)
        
        let (data, resp) = try await URLSession.shared.data(for: request)
        
        guard let http = resp as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        if !(200..<300 ~= http.statusCode) {
            throw APIError.fromStatusCode(http.statusCode)
        }
        
        do {
            return try JSONDecoder().decode(TokenResponse.self, from: data)
        } catch {
            throw APIError.invalidResponse
        }
    }
    
    func register(email: String, password: String) async throws -> TokenResponse {
        let body = RegisterRequest(email: email, password: password)
        return try await postJSON("/v1/auth/register", body: body)
    }
    
    func getCurrentUser() async throws -> MeResponse {
        return try await get("/v1/auth/me")
    }
    
    // MARK: - Core API Methods
    
    private func retry<T>(_ operation: @escaping () async throws -> T, maxRetries: Int = 3) async throws -> T {
        for attempt in 0..<maxRetries {
            do {
                return try await operation()
            } catch let error as APIError where (error == .networkError || error == .serverError) && attempt < maxRetries - 1 {
                // Wait for exponential backoff
                let delay = UInt64(1000 * pow(2.0, Double(attempt)))
                try await Task.sleep(nanoseconds: delay * 1_000_000)
                continue
            } catch {
                throw error
            }
        }
        throw APIError.networkError
    }
    
    func get<T: Decodable>(_ path: String, query: [URLQueryItem] = []) async throws -> T {
        return try await retry {
            var comps = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
            comps.queryItems = query
            var req = URLRequest(url: comps.url!)
            req.httpMethod = "GET"
            if let token = tokenProvider() {
                req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            let (data, resp) = try await URLSession.shared.data(for: req)
            
            guard let http = resp as? HTTPURLResponse else {
                throw APIError.networkError
            }
            
            if !(200..<300 ~= http.statusCode) {
                throw APIError.fromStatusCode(http.statusCode)
            }
            
            do {
                return try JSONDecoder().decode(T.self, from: data)
            } catch {
                throw APIError.invalidResponse
            }
        }
    }
    
    func postJSON<T: Encodable, U: Decodable>(_ path: String, body: T) async throws -> U {
        return try await retry {
            var req = URLRequest(url: baseURL.appendingPathComponent(path))
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if let token = tokenProvider() {
                req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            do {
                req.httpBody = try JSONEncoder().encode(body)
            } catch {
                throw APIError.invalidResponse
            }
            
            let (data, resp) = try await URLSession.shared.data(for: req)
            
            guard let http = resp as? HTTPURLResponse else {
                throw APIError.networkError
            }
            
            if !(200..<300 ~= http.statusCode) {
                throw APIError.fromStatusCode(http.statusCode)
            }
            
            do {
                return try JSONDecoder().decode(U.self, from: data)
            } catch {
                throw APIError.invalidResponse
            }
        }
    }
    
    // MARK: - File Upload
    
    func uploadResume(_ fileURL: URL) async throws -> ProfileResponse {
        return try await retry {
            var request = URLRequest(url: baseURL.appendingPathComponent("/v1/profile/resume"))
            request.httpMethod = "POST"
            if let token = tokenProvider() {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            let boundary = "Boundary-\(UUID().uuidString)"
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            
            let formData = try createMultipartFormData(boundary: boundary, fileURL: fileURL)
            request.httpBody = formData
            
            let (data, resp) = try await URLSession.shared.upload(for: request, from: formData)
            
            guard let http = resp as? HTTPURLResponse else {
                throw APIError.networkError
            }
            
            if !(200..<300 ~= http.statusCode) {
                throw APIError.fromStatusCode(http.statusCode)
            }
            
            do {
                return try JSONDecoder().decode(ProfileResponse.self, from: data)
            } catch {
                throw APIError.resumeUploadFailed
            }
        }
    }
    
    private func createMultipartFormData(boundary: String, fileURL: URL) throws -> Data {
        var formData = Data()
        
        formData.append("--\(boundary)\r\n".data(using: .utf8)!)
        formData.append("Content-Disposition: form-data; name=\"resume\"; filename=\"\(fileURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        formData.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
        
        let fileData = try Data(contentsOf: fileURL)
        formData.append(fileData)
        formData.append("\r\n".data(using: .utf8)!)
        formData.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        return formData
    }
    
    // MARK: - Job Matching

    func getJobFeed(cursor: String? = nil, pageSize: Int = 20) async throws -> [JobCard] {
        var query = [URLQueryItem(name: "page_size", value: "\(pageSize)")]
        if let cursor = cursor {
            query.append(URLQueryItem(name: "cursor", value: cursor))
        }
        return try await get("/v1/jobs/feed", query: query)
    }
    
    func swipeJob(jobId: String, direction: SwipeDirection) async throws -> JobInteractionResponse {
        let body = SwipeRequest(action: direction.rawValue)
        return try await postJSON("/v1/jobs/\(jobId)/swipe", body: body)
    }
    
    func getApplications() async throws -> [ApplicationResponse] {
        return try await get("/v1/applications")
    }
    
    func getApplicationStatus(jobId: String) async throws -> ApplicationResponse {
        return try await get("/v1/applications/\(jobId)/status")
    }
    
    func cancelApplication(jobId: String) async throws -> EmptyResponse {
        return try await postJSON("/v1/applications/\(jobId)/cancel", body: EmptyBody())
    }
    
    func getProfile() async throws -> ProfileResponse {
        return try await get("/v1/profile")
    }
    
    func updateProfile(_ profileUpdate: CandidateProfileUpdate) async throws -> ProfileResponse {
        var req = URLRequest(url: baseURL.appendingPathComponent("/v1/profile"))
        req.httpMethod = "PUT"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = tokenProvider() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        do {
            req.httpBody = try JSONEncoder().encode(profileUpdate)
        } catch {
            throw APIError.invalidResponse
        }
        
        let (data, resp) = try await URLSession.shared.data(for: req)
        
        guard let http = resp as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        if !(200..<300 ~= http.statusCode) {
            throw APIError.fromStatusCode(http.statusCode)
        }
        
        do {
            return try JSONDecoder().decode(ProfileResponse.self, from: data)
        } catch {
            throw APIError.invalidResponse
        }
    }
}

// MARK: - Request/Response Models

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct RegisterRequest: Codable {
    let email: String
    let password: String
}

struct TokenResponse: Codable {
    let access_token: String
    let token_type: String
    let user: UserResponse
}

struct UserResponse: Codable {
    let id: String
    let email: String
    let created_at: Date
}

struct MeResponse: Codable {
    let user: UserResponse
}

struct CandidateProfileUpdate: Codable {
    let full_name: String?
    let phone: String?
    let location: String?
    let headline: String?
    let skills: [String]?
    let experience: [Experience]?
    let education: [Education]?
    let preferences: Preferences?
    
    struct Preferences: Codable {
        let job_types: [String]?
        let remote_preference: String?
        let experience_level: String?
    }
}

struct ProfileResponse: Codable {
    let id: String
    let full_name: String?
    let phone: String?
    let location: String?
    let headline: String?
    let work_experience: [Experience]?
    let education: [Education]?
    let skills: [String]?
    let resume_file_url: String?
    let parsed_at: Date?
    let preferences: CandidateProfileUpdate.Preferences?
}

struct Experience: Codable {
    let company: String
    let position: String
    let start_date: String
    let end_date: String?
    let description: String?
}

struct Education: Codable {
    let institution: String
    let degree: String?
    let field_of_study: String?
    let start_date: String
    let end_date: String?
}

struct SwipeRequest: Codable {
    let action: String // "right" or "left"
}

enum SwipeDirection: String {
    case right = "right"
    case left = "left"
}

struct JobInteractionResponse: Codable {
    let success: Bool
    let message: String
    let job_id: String
}

struct ApplicationResponse: Codable {
    let id: String
    let job_id: String
    let status: String
    let attempt_count: Int
    let last_error: String?
    let assigned_worker: String?
    let created_at: Date
    let updated_at: Date
}

struct EmptyResponse: Codable {}

struct EmptyBody: Codable {}

