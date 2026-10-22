// Desenmascara · Identificador de llamadas. GitHub Actions builds it (.github/workflows/android.yml): no Android
// SDK is needed on your computer.
plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
