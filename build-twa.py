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

# 1. Project settings
write(os.path.join(ROOT, "settings.gradle"), "include ':app'")

# 2. Build Script (Targeting Android 14 / API 34)
write(os.path.join(APP, "build.gradle"), """
plugins { id 'com.android.application' }
android {
    namespace "%s"
    compileSdk 34
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 34
        versionCode 25
        versionName "1.2.5"
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

# 3. Android Manifest with Security Fixes
write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">
    <queries><intent><action android:name="android.support.customtabs.action.CustomTabsService" /></intent></queries>
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="${launcherName}" android:icon="@mipmap/ic_launcher" android:theme="@android:style/Theme.Translucent.NoTitleBar">
        <meta-data android:name="asset_statements" android:value="${assetStatements}"/>
        <activity android:name="com.google.androidbrowserhelper.trusted.LauncherActivity" android:exported="true">
            <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL" android:value="${defaultUrl}"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW"/><category android:name="android.intent.category.DEFAULT"/><category android:name="android.intent.category.BROWSABLE"/>
                <data android:scheme="https" android:host="${hostName}" android:pathPrefix="/solar-dashboard" />
            </intent-filter>
        </activity>
        <service android:name="com.google.androidbrowserhelper.trusted.DelegationService" android:enabled="true" android:exported="true" tools:node="replace">
            <intent-filter><action android:name="android.support.customtabs.trusted.TRUSTED_WEB_ACTIVITY_SERVICE"/><category android:name="android.intent.category.DEFAULT"/></intent-filter>
        </service>
    </application>
</manifest>
""")

write(os.path.join(RES, "values", "colors.xml"), """<?xml version="1.0" encoding="utf-8"?><resources><color name="colorPrimary">#1D9E75</color></resources>""")

print("Project files generated.")
