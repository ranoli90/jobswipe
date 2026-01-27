import Foundation

struct MatchMetadata: Codable {
    let bm25_score: Double
    let has_skill_match: Bool
    let has_location_match: Bool
}

struct JobCard: Codable, Identifiable {
    let id: String
    let title: String
    let company: String
    let location: String?
    let snippet: String?
    let score: Double
    let metadata: MatchMetadata?
    let apply_url: String?
}
