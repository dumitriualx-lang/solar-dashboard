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
    print(f"  wrote {path}")

# 1. Settings
write(os.path.join(ROOT, "settings.gradle"), """
rootProject.name = "SolarDashboard"
include ":app"
""")

# 2. App Build Script (Updated for Gradle 8.x + Android 14)
write(os.path.join(APP, "build.gradle"), """
plugins {
    id 'com.android.application'
}
android {
    namespace "%s"
    compileSdk 34
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 34
        versionCode 5
        versionName "1.0.5"
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
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt')
        }
    }
}
dependencies {
    implementation "com.google.androidbrowserhelper:androidbrowserhelper:2.5.0"
    implementation "androidx.browser:browser:1.8.0"
}
""" % (PKG, PKG, HOST, START_URL, APP_NAME, HOST, KEYSTORE))

# 3. AndroidManifest.xml (THE CRASH FIXER)
write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    
    <queries>
        <intent>
            <action android:name="android.support.customtabs.action.CustomTabsService" />
        </intent>
    </queries>

    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>

    <application
        android:label="${launcherName}"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true"
        android:theme="@android:style/Theme.Translucent.NoTitleBar">
        
        <meta-data android:name="asset_statements" android:value="${assetStatements}"/>

        <activity android:name="com.google.androidbrowserhelper.trusted.LauncherActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|screenLayout|keyboardHidden">
            
            <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL" android:value="${defaultUrl}"/>
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/>
                <category android:name="android.intent.category.DEFAULT"/>
                <category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https" android:host="${hostName}"/>
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

# 4. Support Files
write(os.path.join(ROOT, "gradle.properties"), "android.useAndroidX=true\nandroid.enableJetifier=true")
write(os.path.join(RES, "values", "colors.xml"), """<?xml version="1.0" encoding="utf-8"?>
<resources><color name="colorPrimary">#%s</color></resources>""" % COLOR_HEX)

# 5. Icons
densities = {"mdpi": "48", "hdpi": "72", "xhdpi": "96", "xxhdpi": "144", "xxxhdpi": "192"}
for dName, size in densities.items():
    dst = os.path.join(RES, f"mipmap-{dName}", "ic_launcher.png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        urllib.request.urlretrieve(f"{ICON_BASE}/icon-{size}.png", dst)
    except:
        pass

print("Build script V5 generated successfully.")
