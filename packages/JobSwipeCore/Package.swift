// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "JobSwipeCore",
    platforms: [
        .iOS(.v15),
        .macOS(.v12),
        .linux
    ],
    products: [
        .library(
            name: "JobSwipeCore",
            targets: ["Models", "Networking", "Storage"]
        ),
    ],
    dependencies: [],
    targets: [
        .target(
            name: "Models",
            dependencies: [],
            path: "Sources/Models"
        ),
        .target(
            name: "Networking",
            dependencies: [],
            path: "Sources/Networking"
        ),
        .target(
            name: "Storage",
            dependencies: [],
            path: "Sources/Storage"
        ),
        .testTarget(
            name: "JobSwipeCoreTests",
            dependencies: ["Models", "Networking", "Storage"]
        ),
    ]
)