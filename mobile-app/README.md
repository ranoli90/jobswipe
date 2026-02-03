# JobSwipe Mobile App

A cross-platform Flutter application for the JobSwipe job search platform with Tinder-like swipe interface.

## Overview

JobSwipe is a job search and matching application with AI-powered job recommendations and automated application features. The mobile app provides a smooth user experience with:

- Tinder-like swipe interface for job cards
- AI-powered job matching
- Automated job applications
- User profile management
- Real-time notifications

## Current Status

✅ **Compilation Errors Resolved** - All 23 critical compilation errors fixed  
✅ **Type Safety** - Proper null handling and type conversion implemented  
✅ **BLoC Pattern** - State management using flutter_bloc library  
✅ **API Integration** - Dio HTTP client with proper error handling  

## Architecture

### Code Structure
```
mobile-app/lib/
├── main.dart              # Application entry point
├── app.dart              # App configuration
├── config/               # Environment configuration
├── core/                 # Core functionality
│   ├── datasources/     # Data sources (API, local storage)
│   ├── data/            # Repository implementations
│   ├── models/          # Data models
│   ├── di/              # Dependency injection
│   └── theme/           # App theming
└── presentation/        # UI Layer
    ├── bloc/           # BLoC state management
    ├── screens/        # Screen widgets
    ├── widgets/        # Reusable widgets
    └── router/         # Navigation routing
```

## Getting Started

### Prerequisites
- Flutter SDK 3.41.0-0.0.pre or later
- Dart SDK 3.10.7 or later
- Android Studio or VS Code with Flutter extension

### Installation

```bash
# Install dependencies
flutter pub get

# Run the app (development)
flutter run

# Build for production
flutter build apk --flavor prod --release
flutter build ios --flavor prod --release
```

## Build Configurations

The app supports multiple build flavors:

- **dev**: Development build with hot reload
- **staging**: Staging environment
- **prod**: Production build

For detailed configuration, see [BUILD_CONFIGURATIONS.md](BUILD_CONFIGURATIONS.md)

## Deployment

Automated deployment using GitHub Actions and Fastlane. For detailed deployment instructions, see [DEPLOYMENT_README.md](DEPLOYMENT_README.md)

## Bugs and Fixes

For a complete list of bugs and fixes, see [FLUTTER_BUGS_AND_FIX_PLAN.md](FLUTTER_BUGS_AND_FIX_PLAN.md)

## Codebase Analysis

Based on the [CODEBASE_ANALYSIS_REPORT.md](../CODEBASE_ANALYSIS_REPORT.md), the frontend codebase has several areas for improvement:

### Key Findings
- **Well-structured architecture** with clean separation of concerns
- **BLoC pattern** implementation for state management
- **Comprehensive error handling** using try/catch
- **Dependency injection** with get_it service locator

### Areas for Improvement
- Remove unused dependencies from pubspec.yaml
- Fix API mismatch with flutter_card_swiper package
- Add const constructors for better performance
- Simplify complex widget trees in job_feed_screen.dart

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Effective Dart](https://dart.dev/guides/language/effective-dart)
- [BLoC Pattern](https://bloclibrary.dev/)
