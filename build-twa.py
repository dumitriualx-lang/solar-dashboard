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
COLOR_HEX = "1D9E75" 
KEYSTORE  = os.path.join(HOME, "solar.keystore")
ICON_BASE = "https://dumitriualx-lang.github.io/solar-dashboard/icons"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# 1. Settings
write(os.path.join(ROOT, "settings.gradle"), """
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "SolarDashboard"
include ":app"
""")

# 2. Build Script
write(os.path.join(APP, "build.gradle"), """
plugins { id 'com.android.application' }
android {
    namespace "%s"
    compileSdk 34
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 34
        versionCode 10
        versionName "1.1.0"
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
            signingConfig signingConfigs.release
            minifyEnabled false
        }
    }
}
dependencies {
    implementation "com.google.androidbrowserhelper:androidbrowserhelper:2.5.0"
}
""" % (PKG, PKG, HOST, START_URL, APP_NAME, HOST, KEYSTORE))

# 3. Manifest (The Crash Fix)
write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    
    <queries>
        <intent>
            <action android:name="android.support.customtabs.action.CustomTabsService" />
        </intent>
    </queries>

    <uses-permission android:name="android.permission.INTERNET"/>

    <application
        android:label="${launcherName}"
        android:icon="@mipmap/ic_launcher"
        android:theme="@android:style/Theme.Translucent.NoTitleBar">
        
        <meta-data android:name="asset_statements" android:value="${assetStatements}"/>

        <activity android:name="com.google.androidbrowserhelper.trusted.LauncherActivity"
            android:exported="true">
            <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL" android:value="${defaultUrl}"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/>
                <category android:name="android.intent.category.DEFAULT"/>
                <category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https" android:host="${hostName}" android:pathPrefix="/solar-dashboard" />
            </intent-filter>
        </activity>

        <service android:name="com.google.androidbrowserhelper.trusted.DelegationService"
            android:enabled="true"
            android:exported="true"
            tools:node="replace">
            <intent-filter>
                <action android:name="android.support.customtabs.trusted.TRUSTED_WEB_ACTIVITY_SERVICE"/>
                <category android:name="android.intent.category.DEFAULT"/>
            </intent-filter>
        </service>
    </application>
</manifest>
""")

write(os.path.join(ROOT, "gradle.properties"), "android.useAndroidX=true\\nandroid.enableJetifier=true")
write(os.path.join(WRAP, "gradle-wrapper.properties"), "distributionUrl=https\\\\://services.gradle.org/distributions/gradle-8.7-bin.zip")
write(os.path.join(RES, "values", "colors.xml"), """<?xml version="1.0" encoding="utf-8"?><resources><color name="colorPrimary">#1D9E75</color></resources>""")

# Minimal Icon Download
for size in ["48", "72", "96", "144", "192"]:
    try: urllib.request.urlretrieve(f"{ICON_BASE}/icon-{size}.png", os.path.join(RES, f"mipmap-mdpi", "ic_launcher.png"))
    except: pass

print("Files generated.")
