import Foundation
import GRDB

class CacheManager {
    static let shared = CacheManager()

    private var dbQueue: DatabaseQueue?
    private let maxCacheAge: TimeInterval = 3600 // 1 hour

    private init() {
        do {
            let databaseURL = try FileManager.default
                .url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("jobswipe.db")
            dbQueue = try DatabaseQueue(path: databaseURL.path)

            try dbQueue?.write { db in
                try db.create(table: "jobCard", ifNotExists: true) { t in
                    t.column("id", .text).primaryKey()
                    t.column("title", .text)
                    t.column("company", .text)
                    t.column("location", .text)
                    t.column("snippet", .text)
                    t.column("score", .double)
                    t.column("applyUrl", .text)
                    t.column("timestamp", .double)
                }

                try db.create(table: "pendingSwipe", ifNotExists: true) { t in
                    t.column("id", .integer).primaryKey(autoIncrement: true)
                    t.column("jobId", .text)
                    t.column("direction", .text)
                }
            }
        } catch {
            print("Error setting up database: \(error)")
        }
    }

    struct JobRecord: Codable, FetchableRecord, PersistableRecord {
        var id: String
        var title: String
        var company: String
        var location: String?
        var snippet: String?
        var score: Double
        var applyUrl: String?
        var timestamp: Double
    }

    struct PendingSwipeRecord: Codable, FetchableRecord, PersistableRecord {
        var id: Int64?
        var jobId: String
        var direction: String
    }
    
    func cacheJobs(_ jobs: [JobCard]) {
        do {
            try dbQueue?.write { db in
                try JobRecord.deleteAll(db)
                let timestamp = Date().timeIntervalSince1970
                for job in jobs {
                    let record = JobRecord(
                        id: job.id,
                        title: job.title,
                        company: job.company,
                        location: job.location,
                        snippet: job.snippet,
                        score: job.score,
                        applyUrl: job.applyUrl,
                        timestamp: timestamp
                    )
                    try record.insert(db)
                }
            }
        } catch {
            print("Error caching jobs: \(error)")
        }
    }
    
    func getCachedJobs() -> [JobCard]? {
        do {
            let records: [JobRecord] = try dbQueue?.read { db in
                try JobRecord.fetchAll(db)
            } ?? []

            if records.isEmpty {
                return nil
            }

            let cacheAge = Date().timeIntervalSince1970 - (records.first?.timestamp ?? 0)
            if cacheAge > maxCacheAge {
                clearCache()
                return nil
            }

            return records.map { record in
                JobCard(
                    id: record.id,
                    title: record.title,
                    company: record.company,
                    location: record.location,
                    snippet: record.snippet,
                    score: record.score,
                    applyUrl: record.applyUrl
                )
            }
        } catch {
            print("Error fetching cached jobs: \(error)")
            return nil
        }
    }
    
    func clearCache() {
        do {
            try dbQueue?.write { db in
                try JobRecord.deleteAll(db)
            }
        } catch {
            print("Error clearing cache: \(error)")
        }
    }
    
    func cachePendingSwipes(_ swipes: [(jobId: String, direction: SwipeDirection)]) {
        do {
            try dbQueue?.write { db in
                try PendingSwipeRecord.deleteAll(db)
                for swipe in swipes {
                    let record = PendingSwipeRecord(
                        id: nil,
                        jobId: swipe.jobId,
                        direction: swipe.direction.rawValue
                    )
                    try record.insert(db)
                }
            }
        } catch {
            print("Error caching pending swipes: \(error)")
        }
    }

    func getPendingSwipes() -> [(jobId: String, direction: SwipeDirection)] {
        do {
            let records: [PendingSwipeRecord] = try dbQueue?.read { db in
                try PendingSwipeRecord.fetchAll(db)
            } ?? []

            return records.compactMap { record in
                guard let direction = SwipeDirection(rawValue: record.direction) else { return nil }
                return (jobId: record.jobId, direction: direction)
            }
        } catch {
            print("Error fetching pending swipes: \(error)")
            return []
        }
    }

    func clearPendingSwipes() {
        do {
            try dbQueue?.write { db in
                try PendingSwipeRecord.deleteAll(db)
            }
        } catch {
            print("Error clearing pending swipes: \(error)")
        }
    }
}
