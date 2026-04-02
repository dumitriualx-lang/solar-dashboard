#!/usr/bin/env python3
import os, urllib.request

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "twa")
APP  = os.path.join(ROOT, "app")
MAIN = os.path.join(APP, "src", "main")
RES  = os.path.join(MAIN, "res")
WRAP = os.path.join(ROOT, "gradle", "wrapper")

PKG       = "com.dumitriualxlang.solardashboard"
HOST      = "dumitriualx-lang.github.io"
START_URL = "https://dumitriualx-lang.github.io/solar-dashboard/"
APP_NAME  = "Solar Dashboard"
COLOR_HEX = "FF1D9E75"
KEYSTORE  = os.path.join(HOME, "solar.keystore")
ICON_BASE = "https://dumitriualx-lang.github.io/solar-dashboard/icons"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {path}")

# settings.gradle
write(os.path.join(ROOT, "settings.gradle"), """pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "SolarDashboard"
include ":app"
""")

# root build.gradle
write(os.path.join(ROOT, "build.gradle"), "// Top-level build file\n")

# app/build.gradle
write(os.path.join(APP, "build.gradle"), """plugins {
    id 'com.android.application' version '8.3.0' apply true
}
android {
    namespace "%s"
    compileSdk 34
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
        manifestPlaceholders = [
            hostName:        "%s",
            defaultUrl:      "%s",
            launcherName:    "%s",
            assetStatements: '[{ \\"relation\\": [\\"delegate_permission/common.handle_all_urls\\"], \\"target\\": { \\"namespace\\": \\"web\\", \\"site\\": \\"https://%s\\" }}]'
        ]
    }
    signingConfigs {
        release {
            storeFile     file("%s")
            storePassword "solar2024"
            keyAlias      "solar-key"
            keyPassword   "solar2024"
        }
    }
    buildTypes {
        release {
            minifyEnabled false
            signingConfig signingConfigs.release
        }
    }
}
dependencies {
    implementation "androidx.browser:browser:1.8.0"
    implementation "com.google.androidbrowserhelper:androidbrowserhelper:2.5.0"
}
""" % (PKG, PKG, HOST, START_URL, APP_NAME, HOST, KEYSTORE))

# AndroidManifest.xml
write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <application
        android:label="${launcherName}"
        android:icon="@mipmap/ic_launcher"
        android:theme="@android:style/Theme.NoTitleBar"
        android:allowBackup="true"
        android:supportsRtl="true">
        <meta-data
            android:name="asset_statements"
            android:value="${assetStatements}"/>
        <activity
            android:name="com.google.androidbrowserhelper.trusted.LauncherActivity"
            android:exported="true">
            <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL"
                android:value="${defaultUrl}"/>
            <meta-data android:name="android.support.customtabs.trusted.THEME_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data android:name="android.support.customtabs.trusted.NAVIGATION_BAR_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data android:name="android.support.customtabs.trusted.STATUS_BAR_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data android:name="android.support.customtabs.trusted.SPLASH_SCREEN_BACKGROUND_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data android:name="android.support.customtabs.trusted.FALLBACK_STRATEGY"
                android:value="customtabs"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/>
                <category android:name="android.intent.category.DEFAULT"/>
                <category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https" android:host="${hostName}"
                      android:pathPrefix="/solar-dashboard"/>
            </intent-filter>
        </activity>
        <service android:name="com.google.androidbrowserhelper.trusted.DelegationService"
            android:exported="true" android:enabled="true">
            <intent-filter>
                <action android:name="android.support.customtabs.trusted.TRUSTED_WEB_ACTIVITY_SERVICE"/>
                <category android:name="android.intent.category.DEFAULT"/>
            </intent-filter>
        </service>
    </application>
</manifest>
""")

# strings.xml
write(os.path.join(RES, "values", "strings.xml"), """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">%s</string>
    <color name="colorPrimary">#%s</color>
</resources>
""" % (APP_NAME, COLOR_HEX))

# gradle-wrapper.properties
write(os.path.join(WRAP, "gradle-wrapper.properties"), """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

print("All project files written OK")

# Download icons
densities = {
    "mipmap-mdpi":    ["icon-48.png", "icon-72.png"],
    "mipmap-hdpi":    ["icon-72.png", "icon-any-72.png"],
    "mipmap-xhdpi":   ["icon-96.png", "icon-any-96.png"],
    "mipmap-xxhdpi":  ["icon-144.png", "icon-any-144.png"],
    "mipmap-xxxhdpi": ["icon-192.png", "icon-any-192.png"],
}
for density, candidates in densities.items():
    dst = os.path.join(RES, density, "ic_launcher.png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for name in candidates:
        try:
            urllib.request.urlretrieve(f"{ICON_BASE}/{name}", dst)
            print(f"  icon {density}: {name} OK")
            break
        except Exception:
            continue

print("Build script complete")
