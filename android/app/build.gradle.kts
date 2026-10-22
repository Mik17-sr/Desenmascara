plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "co.desenmascara.llamadas"
    compileSdk = 34

    defaultConfig {
        applicationId = "co.desenmascara.llamadas"
        // Android 10: the first with a call-screening role an app can ask for.
        minSdk = 29
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
        // The same public endpoint the Dashboard's Banco de números uses: it never sees who asks.
        buildConfigField("String", "API_URL", "\"https://desenmascara-api.onrender.com/api/v1\"")
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
