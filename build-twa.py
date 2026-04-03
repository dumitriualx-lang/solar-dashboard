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

# ✅ settings.gradle
write(os.path.join(ROOT, "settings.gradle"), """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "twa"
include(":app")
""")

# ✅ root build.gradle (FIXED: Added repositories to buildscript)
write(os.path.join(ROOT, "build.gradle"), """
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath "com.android.tools.build:gradle:8.2.0"
    }
}
""")

# ✅ gradle.properties
write(os.path.join(ROOT, "gradle.properties"), """
org.gradle.jvmargs=-Xmx2g
android.useAndroidX=true
android.enableJetifier=true
""")

# ✅ app build.gradle
write(os.path.join(APP, "build.gradle"), f"""
plugins {{
    id 'com.android.application'
}}

android {{
    namespace "{PKG}"
    compileSdk 34

    defaultConfig {{
        applicationId "{PKG}"
        minSdk 21
        targetSdk 34
        versionCode 30
        versionName "1.3.0"

        manifestPlaceholders = [
            hostName: "{HOST}",
            defaultUrl: "{START_URL}",
            launcherName: "{APP_NAME}",
            assetStatements: '[{{ "relation": ["delegate_permission/common.handle_all_urls"], "target": {{ "namespace": "web", "site": "https://{HOST}" }} }}]'
        ]
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
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
    implementation "com.google.androidbrowserhelper:androidbrowserhelper:2.5.1"
}}
""")

# ✅ AndroidManifest (FIXED: Added <queries> for Android 14 compatibility)
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

        <meta-data
            android:name="asset_statements"
            android:value="${assetStatements}"/>

        <activity
            android:name="com.google.androidbrowserhelper.trusted.LauncherActivity"
            android:exported="true">

            <meta-data
                android:name="android.support.customtabs.trusted.DEFAULT_URL"
                android:value="${defaultUrl}"/>

            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
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

print("Project generated successfully.")
