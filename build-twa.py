#!/usr/bin/env python3
import os

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "twa")
APP  = os.path.join(ROOT, "app")
MAIN = os.path.join(APP, "src", "main")
RES  = os.path.join(MAIN, "res")

PKG       = "com.dumitriualxlang.solardashboard"
HOST      = "dumitriualx-lang.github.io"
START_URL = "https://dumitriualx-lang.github.io/solar-dashboard/"
APP_NAME  = "Solar Dashboard"
KEYSTORE  = os.path.join(HOME, "solar.keystore")

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# 1. Project Configuration Files
write(os.path.join(ROOT, "settings.gradle"), "include ':app'")
write(os.path.join(ROOT, "gradle.properties"), "android.useAndroidX=true\nandroid.enableJetifier=true")

# 2. Root build.gradle (Fixes the repository error)
write(os.path.join(ROOT, "build.gradle"), """
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath "com.android.tools.build:gradle:8.2.0" }
}
allprojects {
    repositories { google(); mavenCentral() }
}
""")

# 3. App build.gradle
write(os.path.join(APP, "build.gradle"), f"""
plugins {{ id 'com.android.application' }}
android {{
    namespace "{PKG}"
    compileSdk 34
    defaultConfig {{
        applicationId "{PKG}"
        minSdk 21
        targetSdk 34
        versionCode 50
        versionName "1.5.0"
        manifestPlaceholders = [
            hostName: "{HOST}",
            defaultUrl: "{START_URL}",
            launcherName: "{APP_NAME}",
            assetStatements: '[{{ "relation": ["delegate_permission/common.handle_all_urls"], "target": {{ "namespace": "web", "site": "https://{HOST}" }} }}]'
        ]
    }}
    signingConfigs {{
        release {{
            storeFile file("{KEYSTORE}")
            storePassword "solar2024"
            keyAlias "solar-key"
            keyPassword "solar2024"
        }}
    }}
    buildTypes {{
        release {{
            signingConfig signingConfigs.release
            minifyEnabled false
        }}
    }}
}}
dependencies {{
    implementation "com.google.androidbrowserhelper:androidbrowserhelper:2.5.0"
}}
""")

# 4. AndroidManifest.xml (Android 14 Ready)
write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">
    <queries><intent><action android:name="android.support.customtabs.action.CustomTabsService" /></intent></queries>
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="${launcherName}" android:icon="@mipmap/ic_launcher" android:theme="@android:style/Theme.Translucent.NoTitleBar">
        <meta-data android:name="asset_statements" android:value="${assetStatements}"/>
        <activity android:name="com.google.androidbrowserhelper.trusted.LauncherActivity" android:exported="true">
            <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL" android:value="${defaultUrl}"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/><category android:name="android.intent.category.DEFAULT"/><category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https" android:host="${hostName}" android:pathPrefix="/solar-dashboard" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

# 5. GENERATE AUTOMATIC ICON (Fixes the 404/Missing Resource error)
# This creates a green placeholder adaptive icon so the build always passes
write(os.path.join(RES, "values", "colors.xml"), """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#1D9E75</color>
</resources>""")

write(os.path.join(RES, "mipmap-anydpi-v26", "ic_launcher.xml"), """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground>
        <inset android:inset="25%">
            <path android:fillColor="#FFFFFF" android:pathData="M12,2L4.5,20.29L5.21,21L12,18L18.79,21L19.5,20.29L12,2Z"/>
        </inset>
    </foreground>
</adaptive-icon>""")

print("Project generated successfully with built-in resources.")
