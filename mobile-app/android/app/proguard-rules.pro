# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.kts.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# ========================================
# Core ProGuard Configuration
# ========================================

# Preserve annotations
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes InnerClasses
-keepattributes EnclosingMethod
-dontwarn javax.annotation.**

# ========================================
# Gson Rules
# ========================================
-keep class com.google.gson.** { *; }
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
-keepclassmembers,allowobfuscation class * {
  @com.google.gson.annotations.SerializedName <fields>;
}

# ========================================
# Retrofit & OkHttp Rules
# ========================================
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}
-dontwarn retrofit2.**
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-dontwarn okhttp3.**
-keep class okio.** { *; }
-dontwarn okio.**

# ========================================
# Flutter Specific Rules
# ========================================
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }
-dontwarn io.flutter.embedding.**

# ========================================
# Dio (Common Flutter HTTP Client)
# ========================================
-keep class dio.** { *; }
-keep class okhttp3.** { *; }
-keep class okio.** { *; }
-dontwarn dio.**

# ========================================
# Hive (Flutter Local Database)
# ========================================
-keep class hive.** { *; }
-keep class org.hive_console.** { *; }
-keep class * extends hive.Model { *; }
-keepclassmembers class * extends hive.Model {
    <fields>;
}
-dontwarn hive.**

# ========================================
# JSON Serialization (json_serializable)
# ========================================
-keep class com.jobswipe.jobswipe.** { *; }
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
-keep,allowobfuscation class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# ========================================
# Resource Classes
# ========================================
-keep class **.R
-keep class **.R$* { *; }
-keepclassmembers class **.R$* {
    public static <fields>;
}

# ========================================
# Keep model classes with fromJson/toJson
# ========================================
-keep class com.jobswipe.jobswipe.models.** { *; }
-keepclassmembers class com.jobswipe.jobswipe.models.** {
    <init>(...);
    <fields>;
}

# ========================================
# Common Flutter Plugin Rules
# ========================================
# shared_preferences
-keep class shared_preferences.** { *; }
-dontwarn shared_preferences.**

# path_provider
-keep class path_provider.** { *; }
-dontwarn path_provider.**

# connectivity_plus
-keep class connectivity_plus.** { *; }
-dontwarn connectivity_plus.**

# firebase_messaging (if used)
-keep class firebase_messaging.** { *; }
-keep class com.google.firebase.** { *; }
-dontwarn firebase_messaging.**

# ========================================
# Security & Encryption
# ========================================
-keep class javax.crypto.** { *; }
-keep class java.security.** { *; }
-dontwarn javax.crypto.**

# ========================================
# Kotlin Specific
# ========================================
-keep class kotlin.** { *; }
-keep class kotlin.Metadata { *; }
-dontwarn kotlin.**
-keepclassmembers class **$WhenMappings {
    <fields>;
}
-keepclassmembers class kotlin.Metadata {
    public <methods>;
}

# ========================================
# Coroutines
# ========================================
-keep class kotlinx.coroutines.** { *; }
-dontwarn kotlinx.coroutines.**

# ========================================
# Performance Optimizations
# ========================================
-optimizations !code/simplification/arithmetic,!field/*,!class/merging/*
-optimizationpasses 5
-allowaccessmodification