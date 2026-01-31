#!/bin/bash

# Flutter Run Script with Memory Optimizations
# This script runs Flutter with reduced memory usage to prevent CLI crashes

# Set memory limits for the Dart VM (used by Flutter)
export DART_VM_OPTIONS="--old_gen_heap_size=2048 --max_gen_heap_size=2048"

# Reduce Gradle memory usage
export GRADLE_OPTS="-Xmx2G -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError"

# Set Flutter tool options for low-memory environments
export FLUTTER_TOOL_ARGS="--track-widget-creation --enable-software-rendering"

# Disable analytics to reduce overhead
export FLUTTER_ANALYTICS_OPT_OUT=1

# Clean build cache to free memory
flutter clean

# Get dependencies with reduced parallelism
flutter pub get

# Build with optimizations for debug mode
flutter build apk --debug --target-platform android-arm64 --split-debug-info=build/debug_info

echo "Build complete. To run on device, use:"
echo "flutter run --debug --enable-software-rendering --cache-sksl"