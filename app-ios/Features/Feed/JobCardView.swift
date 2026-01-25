import SwiftUI
import UIKit

enum SwipeDirection: String, Codable {
    case left = "left"
    case right = "right"
}

struct JobCardView: View {
    @State private var offset: CGSize = .zero
    let job: JobCard
    let onSwipe: (SwipeDirection) -> Void
    
    init(job: JobCard, onSwipe: @escaping (SwipeDirection) -> Void) {
        self.job = job
        self.onSwipe = onSwipe
    }
    
    var body: some View {
        ZStack {
            VStack(alignment: .leading, spacing: 8) {
                // Job Title and Company
                Text(job.title).font(.title2).bold()
                Text(job.company).font(.headline)
                if let loc = job.location { Text(loc).font(.subheadline).foregroundColor(.secondary) }
                
                // Match Score
                if let metadata = job.metadata {
                    HStack(spacing: 8) {
                        // BM25 Score
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Match Score").font(.caption).foregroundColor(.secondary)
                            HStack(spacing: 4) {
                                Image(systemName: "star.fill")
                                    .foregroundColor(.yellow)
                                Text(String(format: "%.0f%%", metadata.bm25_score * 100))
                                    .font(.headline)
                            }
                        }
                        
                        Spacer()
                        
                        // Skill Match
                        HStack(spacing: 4) {
                            Image(systemName: "checkmark.circle")
                                .foregroundColor(metadata.has_skill_match ? .green : .gray)
                            Text("Skills")
                                .font(.caption)
                                .foregroundColor(metadata.has_skill_match ? .green : .gray)
                        }
                        
                        // Location Match
                        HStack(spacing: 4) {
                            Image(systemName: "location.circle")
                                .foregroundColor(metadata.has_location_match ? .blue : .gray)
                            Text("Location")
                                .font(.caption)
                                .foregroundColor(metadata.has_location_match ? .blue : .gray)
                        }
                    }
                    .padding(.top, 8)
                }
                
                // Snippet
                if let snippet = job.snippet {
                    Text(snippet)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .lineLimit(3)
                        .padding(.top, 8)
                }
                
                Spacer()
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(Color(.systemBackground))
                    .shadow(color: Color.black.opacity(0.1), radius: 8, x: 0, y: 4)
                    .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
            )
            .overlay(
                // Left swipe indicator
                Group {
                    if offset.width < -50 {
                        VStack {
                            Spacer()
                            HStack {
                                Text("SKIP")
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                                    .foregroundColor(.red)
                                    .padding()
                                    .background(Color.red.opacity(0.2))
                                    .cornerRadius(12)
                                Spacer()
                            }
                            Spacer()
                        }
                    }
                }
            )
            .overlay(
                // Right swipe indicator
                Group {
                    if offset.width > 50 {
                        VStack {
                            Spacer()
                            HStack {
                                Spacer()
                                Text("APPLY")
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                                    .foregroundColor(.green)
                                    .padding()
                                    .background(Color.green.opacity(0.2))
                                    .cornerRadius(12)
                            }
                            Spacer()
                        }
                    }
                }
            )
        }
        .offset(x: offset.width)
        .rotationEffect(.degrees(Double(offset.width / 20)))
        .gesture(DragGesture()
            .onChanged { value in
                offset = value.translation
                // Add haptic feedback during drag
                if abs(value.translation.width) > 50 {
                    let generator = UIImpactFeedbackGenerator(style: .light)
                    generator.impactOccurred()
                }
            }
            .onEnded { value in
                defer { offset = .zero }
                if value.translation.width > 120 {
                    // Right swipe - apply
                    let generator = UIImpactFeedbackGenerator(style: .medium)
                    generator.impactOccurred()
                    onSwipe(.right)
                } else if value.translation.width < -120 {
                    // Left swipe - skip
                    let generator = UIImpactFeedbackGenerator(style: .medium)
                    generator.impactOccurred()
                    onSwipe(.left)
                }
            }
        )
    }
}
