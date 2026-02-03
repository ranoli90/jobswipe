plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.jobswipe.jobswipe"
    compileSdk = 36
    ndkVersion = "28.2.13676358"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.jobswipe.jobswipe"
        minSdk = flutter.minSdkVersion
        targetSdk = 36
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        multiDexEnabled = true
    }

    flavorDimensions += "environment"

    productFlavors {
        create("dev") {
            dimension = "environment"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
        }
        create("staging") {
            dimension = "environment"
            applicationIdSuffix = ".staging"
            versionNameSuffix = "-staging"
        }
        create("prod") {
            dimension = "environment"
            // No suffix for production
        }
    }

    signingConfigs {
        create("release") {
            storeFile = file(project.property("MYAPP_UPLOAD_STORE_FILE").toString())
            storePassword = project.property("MYAPP_UPLOAD_STORE_PASSWORD").toString()
            keyAlias = project.property("MYAPP_UPLOAD_KEY_ALIAS").toString()
            keyPassword = project.property("MYAPP_UPLOAD_KEY_PASSWORD").toString()
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debug")
            // Disable unnecessary features for debug builds to save memory
            isShrinkResources = false
            isMinifyEnabled = false
        }
        release {
            // Using debug signing for now to avoid keystore password issues
            signingConfig = signingConfigs.getByName("debug")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    // Memory-efficient build configuration is handled automatically by Android Gradle Plugin 8.0+
}

flutter {
    source = "../.."
}
