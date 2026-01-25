import SwiftUI

struct JobFeedView: View {
    @State private var jobs: [JobCard] = []
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var isRefreshing: Bool = false
    @State private var currentCursor: String? = nil
    @State private var hasMorePages: Bool = true
    @State private var lastSwipedJob: JobCard? = nil
    @State private var showUndoSnackbar: Bool = false
    @State private var snackbarMessage: String = ""
    @State private var pendingSwipes: [(jobId: String, direction: SwipeDirection)] = []

    let apiClient: APIClient

    private let pendingSwipesKey = "pendingSwipes"
    
    var body: some View {
        NavigationStack {
            Group {
                if isLoading && jobs.isEmpty {
                    loadingView
                } else if let error = errorMessage {
                    errorView(error)
                } else if jobs.isEmpty {
                    emptyView
                } else {
                    cardStackView
                }
            }
            .navigationTitle("Job Matches")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                Button("Refresh") {
                    Task {
                        await fetchJobs()
                    }
                }
            }
            .onAppear {
                loadPendingSwipes()
                // Load from cache first
                if let cachedJobs = CacheManager.shared.getCachedJobs() {
                    jobs = cachedJobs
                }
                Task {
                    await fetchJobs()
                    await syncPendingSwipes()
                }
            }
        }
        .overlay(
            VStack {
                Spacer()
                if showUndoSnackbar {
                    HStack {
                        Text(snackbarMessage)
                            .foregroundColor(.white)
                            .font(.subheadline)
                        Spacer()
                        if lastSwipedJob != nil {
                            Button("Undo") {
                                undoLastSwipe()
                            }
                            .foregroundColor(.white)
                            .font(.subheadline.bold())
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .background(Color.black.opacity(0.8))
                    .cornerRadius(8)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 16)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        )
    }
    
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Finding your perfect job match...")
                .foregroundColor(.secondary)
        }
    }
    
    private func errorView(_ error: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.orange)
            Text("Oops!")
                .font(.title2)
                .fontWeight(.bold)
            Text(error)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            Button("Try Again") {
                Task {
                    await fetchJobs()
                }
            }
            .buttonStyle(.borderedProminent)
        }
    }
    
    private var emptyView: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            Text("No matches found")
                .font(.title2)
                .fontWeight(.bold)
            Text("Try adjusting your search criteria or check back later for new jobs")
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            Button("Refresh") {
                Task {
                    await fetchJobs()
                }
            }
            .buttonStyle(.borderedProminent)
        }
    }
    
    private var cardStackView: some View {
        ZStack {
            ForEach(Array(jobs.prefix(3).enumerated()), id: \.element.id) { index, job in
                JobCardView(job: job) { direction in
                    handleSwipe(job: job, direction: direction)
                }
                .scaleEffect(1.0 - Double(index) * 0.05)
                .offset(y: CGFloat(index) * 8)
                .zIndex(Double(3 - index))
                .shadow(radius: index == 0 ? 8 : 4)
                .opacity(index == 0 ? 1.0 : 0.8)
            }
        }
        .frame(maxHeight: 500)
        .padding(.horizontal, 16)
        .gesture(
            DragGesture()
                .onEnded { value in
                    // Handle global swipe gestures if needed
                }
        )
    }
    
    private func fetchJobs() async {
        isLoading = true
        errorMessage = nil
        currentCursor = nil
        hasMorePages = true

        do {
            jobs = try await apiClient.getJobFeed(cursor: nil, pageSize: 20)
            // If we got fewer than requested, we've reached the end
            hasMorePages = jobs.count >= 20
            // Cache the jobs
            CacheManager.shared.cacheJobs(jobs)
        } catch {
            errorMessage = error.localizedDescription
            // If fetch fails, try to use cached jobs
            if let cachedJobs = CacheManager.shared.getCachedJobs(), !cachedJobs.isEmpty {
                jobs = cachedJobs
                errorMessage = "Using cached jobs. Check your internet connection."
            }
        }

        isLoading = false
    }
    
    private func handleSwipe(job: JobCard, direction: SwipeDirection) {
        // Provide haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()

        // Store for undo functionality
        lastSwipedJob = job

        // Show snackbar notification
        snackbarMessage = direction == .right ? "Applied to \(job.title)" : "Skipped \(job.title)"
        withAnimation {
            showUndoSnackbar = true
        }

        // Auto-hide snackbar after 3 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
            withAnimation {
                showUndoSnackbar = false
            }
        }

        // Record swipe interaction with API (or queue if offline)
        Task {
            do {
                _ = try await apiClient.swipeJob(jobId: job.id, direction: direction)
                // Success - sync any pending swipes
                await syncPendingSwipes()
            } catch {
                // Offline or network error - queue for later
                queueSwipe(jobId: job.id, direction: direction)
                print("Failed to record swipe, queued for later: \(error)")
            }
        }

        // Handle swipe action
        if let index = jobs.firstIndex(where: { $0.id == job.id }) {
            withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
                jobs.remove(at: index)
            }

            // Load more jobs if running low
            if jobs.count < 10 {
                Task {
                    await loadMoreJobs()
                }
            }
        
            private func queueSwipe(jobId: String, direction: SwipeDirection) {
                pendingSwipes.append((jobId: jobId, direction: direction))
                CacheManager.shared.cachePendingSwipes(pendingSwipes)
            }
        
            private func syncPendingSwipes() async {
                guard !pendingSwipes.isEmpty else { return }
        
                var syncedIndices: [Int] = []
        
                for (index, swipe) in pendingSwipes.enumerated() {
                    do {
                        _ = try await apiClient.swipeJob(jobId: swipe.jobId, direction: swipe.direction)
                        syncedIndices.append(index)
                    } catch {
                        // Stop on first failure to preserve order
                        break
                    }
                }
        
                // Remove synced swipes
                for index in syncedIndices.reversed() {
                    pendingSwipes.remove(at: index)
                }
        
                if !syncedIndices.isEmpty {
                    CacheManager.shared.cachePendingSwipes(pendingSwipes)
                }
            }
        
            private func loadPendingSwipes() {
                pendingSwipes = CacheManager.shared.getPendingSwipes()
            }
        }
    }

    private func undoLastSwipe() {
        guard let job = lastSwipedJob else { return }

        // Add job back to the beginning of the array
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
            jobs.insert(job, at: 0)
        }

        // Hide snackbar
        withAnimation {
            showUndoSnackbar = false
        }

        lastSwipedJob = nil
        snackbarMessage = "Swipe undone"
        withAnimation {
            showUndoSnackbar = true
        }

        // Auto-hide after 2 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            withAnimation {
                showUndoSnackbar = false
            }
        }
    }

    private func loadMoreJobs() async {
        guard hasMorePages, !isLoading else { return }

        do {
            let newJobs = try await apiClient.getJobFeed(cursor: currentCursor, pageSize: 10)
            if newJobs.isEmpty {
                hasMorePages = false
            } else {
                jobs.append(contentsOf: newJobs)
                // Update cursor for next page (assuming last job ID as cursor)
                currentCursor = newJobs.last?.id
            }
        } catch {
            // Handle error silently or show minimal feedback
            print("Failed to load more jobs: \(error)")
        }
    }
}

struct JobFeedView_Previews: PreviewProvider {
    static var previews: some View {
        // Preview with mock data
        JobFeedView(apiClient: APIClient(baseURL: URL(string: "http://localhost:8000/api")!) { "mock-token" })
    }
}
