#!/usr/bin/env python3
"""
Generates a minimal Android TWA project for Solar Dashboard.
Run from the GitHub Actions workflow after Java and Android SDK are set up.
"""
import os, stat, urllib.request, shutil

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "twa")
APP  = os.path.join(ROOT, "app")
MAIN = os.path.join(APP, "src", "main")
RES  = os.path.join(MAIN, "res")
WRAP = os.path.join(ROOT, "gradle", "wrapper")

# App config
PKG         = "com.dumitriualxlang.solardashboard"
HOST        = "dumitriualx-lang.github.io"
START_URL   = "https://dumitriualx-lang.github.io/solar-dashboard/"
APP_NAME    = "Solar Dashboard"
COLOR       = "#1D9E75"
COLOR_HEX   = "FF1D9E75"
KEYSTORE    = os.path.join(HOME, "solar.keystore")
ICON_BASE   = "https://dumitriualx-lang.github.io/solar-dashboard/icons"

# Create directory structure
dirs = [
    APP,
    os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard"),
    os.path.join(RES, "values"),
    os.path.join(RES, "mipmap-mdpi"),
    os.path.join(RES, "mipmap-hdpi"),
    os.path.join(RES, "mipmap-xhdpi"),
    os.path.join(RES, "mipmap-xxhdpi"),
    os.path.join(RES, "mipmap-xxxhdpi"),
    WRAP,
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
print("Directories created")

# settings.gradle
with open(os.path.join(ROOT, "settings.gradle"), "w") as f:
    f.write('rootProject.name = "SolarDashboard"\ninclude ":app"\n')

# Root build.gradle
with open(os.path.join(ROOT, "build.gradle"), "w") as f:
    f.write("""buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath "com.android.tools.build:gradle:8.2.0" }
}
allprojects { repositories { google(); mavenCentral() } }
""")

# app/build.gradle
with open(os.path.join(APP, "build.gradle"), "w") as f:
    f.write("""plugins { id 'com.android.application' }
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
            hostName: "%s",
            defaultUrl: "%s",
            launcherName: "%s",
            assetStatements: '[{ \\"relation\\": [\\"delegate_permission/common.handle_all_urls\\"], \\"target\\": { \\"namespace\\": \\"web\\", \\"site\\": \\"https://%s\\" }}]'
        ]
    }
    signingConfigs {
        release {
            storeFile file("%s")
            storePassword "solar2024"
            keyAlias "solar-key"
            keyPassword "solar2024"
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
with open(os.path.join(MAIN, "AndroidManifest.xml"), "w") as f:
    f.write("""<?xml version="1.0" encoding="utf-8"?>
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
            <meta-data
                android:name="android.support.customtabs.trusted.DEFAULT_URL"
                android:value="${defaultUrl}"/>
            <meta-data
                android:name="android.support.customtabs.trusted.THEME_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data
                android:name="android.support.customtabs.trusted.NAVIGATION_BAR_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data
                android:name="android.support.customtabs.trusted.STATUS_BAR_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data
                android:name="android.support.customtabs.trusted.SPLASH_SCREEN_BACKGROUND_COLOR"
                android:value="@color/colorPrimary"/>
            <meta-data
                android:name="android.support.customtabs.trusted.FALLBACK_STRATEGY"
                android:value="customtabs"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/>
                <category android:name="android.intent.category.DEFAULT"/>
                <category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https"
                      android:host="${hostName}"
                      android:pathPrefix="/solar-dashboard"/>
            </intent-filter>
        </activity>
        <service
            android:name="com.google.androidbrowserhelper.trusted.DelegationService"
            android:exported="true"
            android:enabled="true">
            <intent-filter>
                <action android:name="android.support.customtabs.trusted.TRUSTED_WEB_ACTIVITY_SERVICE"/>
                <category android:name="android.intent.category.DEFAULT"/>
            </intent-filter>
        </service>
    </application>
</manifest>
""")

# res/values/strings.xml
with open(os.path.join(RES, "values", "strings.xml"), "w") as f:
    f.write("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">%s</string>
    <color name="colorPrimary">#%s</color>
</resources>
""" % (APP_NAME, COLOR_HEX))

# gradle-wrapper.properties
with open(os.path.join(WRAP, "gradle-wrapper.properties"), "w") as f:
    f.write("""distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.4-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

print("Project files written")

# Download launcher icons
icon_map = {
    "mdpi":    ("icon-48.png",  "icon-any-48.png",  "icon-72.png"),
    "hdpi":    ("icon-72.png",  "icon-any-72.png",  None),
    "xhdpi":   ("icon-96.png",  "icon-any-96.png",  None),
    "xxhdpi":  ("icon-144.png", "icon-any-144.png", None),
    "xxxhdpi": ("icon-192.png", "icon-any-192.png", None),
}

for density, candidates in icon_map.items():
    dst = os.path.join(RES, f"mipmap-{density}", "ic_launcher.png")
    fetched = False
    for candidate in candidates:
        if candidate is None:
            continue
        url = f"{ICON_BASE}/{candidate}"
        try:
            urllib.request.urlretrieve(url, dst)
            print(f"  {density}: {candidate} ✅")
            fetched = True
            break
        except Exception:
            continue
    if not fetched:
        # Copy any existing icon as fallback
        for src in [os.path.join(RES, "mipmap-xxxhdpi", "ic_launcher.png"),
                    os.path.join(RES, "mipmap-xxhdpi",  "ic_launcher.png")]:
            if os.path.exists(src):
                shutil.copy(src, dst)
                print(f"  {density}: copied from fallback")
                break

print("Icons done")
print("TWA project generation complete ✅")
