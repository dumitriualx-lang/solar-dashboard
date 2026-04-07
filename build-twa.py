#!/usr/bin/env python3
import os, io, base64
from PIL import Image

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

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print("  wrote " + os.path.relpath(path, ROOT))

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

write(os.path.join(ROOT, "build.gradle"), "// Top-level build file\n")

write(os.path.join(ROOT, "gradle.properties"), """android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx2048m
""")

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
            hostName:     "dumitriualx-lang.github.io",
            defaultUrl:   "https://dumitriualx-lang.github.io/solar-dashboard/",
            launcherName: "Solar Dashboard"
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
configurations.all {
    exclude group: "org.jetbrains.kotlin", module: "kotlin-stdlib-jdk7"
    exclude group: "org.jetbrains.kotlin", module: "kotlin-stdlib-jdk8"
}
dependencies {
    implementation "androidx.appcompat:appcompat:1.6.1"
    implementation "androidx.webkit:webkit:1.8.0"
    implementation "androidx.core:core:1.10.1"
    implementation "org.jetbrains.kotlin:kotlin-stdlib:1.8.22"
}
""" % (PKG, PKG, KEYSTORE))

write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <application
        android:label="Solar Dashboard"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:theme="@android:style/Theme.NoTitleBar"
        android:allowBackup="true"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:networkSecurityConfig="@xml/network_security_config">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "MainActivity.java"), """package com.dumitriualxlang.solardashboard;

import android.app.Activity;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.Window;
import android.view.WindowManager;
import android.graphics.Color;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {
    private WebView webView;
    private Handler mainHandler;
    private static final String APP_URL = "https://dumitriualx-lang.github.io/solar-dashboard/";
    private static final String CHANNEL_ID = "solar_alerts";
    private int notifId = 1;

    // Fetch URL in background thread, return result to JS callback
    private void fetchUrl(String urlStr, String jsCallback) {
        new Thread(() -> {
            String result = null;
            String errorMsg = "unknown";
            try {
                java.net.URL url = new java.net.URL(urlStr);
                java.net.URLConnection rawConn = url.openConnection();
                rawConn.setConnectTimeout(20000);
                rawConn.setReadTimeout(25000);
                rawConn.setRequestProperty("Accept", "application/json");
                rawConn.setRequestProperty("User-Agent", "Mozilla/5.0");
                rawConn.setRequestProperty("Accept-Encoding", "identity");
                rawConn.connect();
                java.io.InputStream is;
                if (rawConn instanceof java.net.HttpURLConnection) {
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) rawConn;
                    int code = conn.getResponseCode();
                    errorMsg = "HTTP " + code;
                    if (code == 200) {
                        is = conn.getInputStream();
                    } else {
                        is = null;
                    }
                } else {
                    is = rawConn.getInputStream();
                }
                if (is != null) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) sb.append(line);
                    br.close();
                    result = sb.toString();
                }
            } catch (Exception e) {
                errorMsg = e.getClass().getSimpleName() + ": " + e.getMessage();
            }
            final String b64 = result != null ?
                android.util.Base64.encodeToString(
                    result.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    android.util.Base64.NO_WRAP) : null;
            final String errFinal = errorMsg;
            mainHandler.post(() -> {
                String js = b64 != null
                    ? jsCallback + "('" + b64 + "', null);"
                    : jsCallback + "(null, 'ERR:" + errFinal.replace("'","") + "');";
                webView.evaluateJavascript(js, null);
            });
        }).start();
    }

    // JavaScript bridge
    public class SolarBridge {
        @JavascriptInterface
        public void fetchData(String urlStr, String callbackFn) {
            fetchUrl(urlStr, callbackFn);
        }

        @JavascriptInterface
        public void showNotification(String title, String body, String tag) {
            mainHandler.post(() -> {
                NotificationCompat.Builder builder = new NotificationCompat.Builder(MainActivity.this, CHANNEL_ID)
                    .setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(title)
                    .setContentText(body)
                    .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setAutoCancel(true)
                    .setColor(Color.parseColor("#1D9E75"));
                Intent intent = new Intent(MainActivity.this, MainActivity.class);
                intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
                PendingIntent pi = PendingIntent.getActivity(MainActivity.this, 0, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
                builder.setContentIntent(pi);
                try {
                    NotificationManagerCompat.from(MainActivity.this).notify(notifId++, builder.build());
                } catch (Exception ignored) {}
            });
        }

        @JavascriptInterface
        public boolean notificationsGranted() {
            return NotificationManagerCompat.from(MainActivity.this).areNotificationsEnabled();
        }

        @JavascriptInterface
        public void requestNotifications() {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS}, 1);
            }
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("Solar production alerts");
            ch.enableLights(true);
            ch.setLightColor(Color.parseColor("#1D9E75"));
            ((NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE)).createNotificationChannel(ch);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());
        createNotificationChannel();

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#1D9E75"));
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setJavaScriptCanOpenWindowsAutomatically(false);

        // Register bridge BEFORE loading URL
        SolarBridge bridge = new SolarBridge();
        webView.addJavascriptInterface(bridge, "AndroidBridge");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                cb.invoke(origin, true, false);
            }
            @Override
            public void onPermissionRequest(android.webkit.PermissionRequest request) {
                request.grant(request.getResources());
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false; // allow all URLs to load in WebView
            }
        });

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState);
        } else {
            webView.loadUrl(APP_URL);
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
""")



write(os.path.join(RES, "xml", "network_security_config.xml"), """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system"/>
            <certificates src="user"/>
        </trust-anchors>
    </base-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">api.forecast.solar</domain>
        <domain includeSubdomains="true">api.open-meteo.com</domain>
        <domain includeSubdomains="true">dumitriualx-lang.github.io</domain>
    </domain-config>
</network-security-config>
""")

write(os.path.join(RES, "values", "strings.xml"), """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">%s</string>
    <color name="colorPrimary">#%s</color>
    <string name="asset_statements">[{"relation":["delegate_permission/common.handle_all_urls"],"target":{"namespace":"web","site":"https://dumitriualx-lang.github.io"}}]</string>
</resources>
""" % (APP_NAME, COLOR_HEX))

write(os.path.join(WRAP, "gradle-wrapper.properties"), """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

print("All project files written OK")

# Icons embedded as base64
ICON_MASKABLE_B64 = "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"
ICON_ANY_B64      = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAYAAABS3GwHAAAFg0lEQVR42u3d23EUSxBFUTrjugG+gQ9gBPgAvoEh8HFDEQpJ82r1I6vOOp98aKar9s7MGqZ7lg+ySz7+/Pp3y7/358uPxapuH4vaCHJyEADspCAA4AlBANCTgQCgJwMBQE8GAgCfCAQAPhEIAHoyEAD4RNgkBX5JXuPFpkhyN1iAL8kiLMCXZBEK/JK8N4vFleRuUOCX5D0rCynJe7dYPEkeiQr8krynZaEkeW8XiyPJI1GBX5L3vCyEJO99gV+SGVjAf2x+f/7+5r9/+vXNmSClA6j80oWJAr8kS1Dgl2QJCvySLEGBX5IlKPBLsgQFfkmWoMAvyRKU5ZXk1GjGii7QWgDwy0gSFPglWQJnAHEGUP0ltQsU+CVZggK/JEvgDCDOAKq/pHaBGh3+S7cYCgmmH4Ge4CeBwnOoAB2q/8sNIEF24VnLZI28AcYhhefwDtCh+l97hAgJcgvPGjaHPQOQoM/MP/IzjWpvw0gA/s5doEaFnwTg34LVKf4nmATgX5tla6NsGPi75J7njU71XSCdAPy7HoJJAP7ZclOAEb/wRgLw38vutF+HJoHK/+4OMPrXnUkA/lsMT39DDAlU/lUCzHSzCwmy4b/GcswtkSRQ+aMFIAH47xZg5nt90yVIhf8S05FPhbi00bNXP5WfABc3PAGAVPEfEiDpUSdPG58EQKL419iOfzBWYvVLFP9S/vsgLWbwo6UE//9ZUsefTsCD9dg8v09AB2gM/su/RwQjUBT4RCAA8Imwa8r8Pxb8XV575Dxn3e8DDA4gCTbqADIueCQgQDxwJCBAPGgkWCmAA/A8gJHgsYOwDjAhWCQwAsUDRQICiBAguZLqAgQQIUByBdUFbgjgI1BJzcefX//qAAGVUxcwAokQQIQAIgTIm5mdAwgg8iqH3RN8dAVyv6y0EkCMUB0LmBFInAFECCBCABGH4KEPNSItBZCxM2sBMwKFbLYOTAARAogQQIQAOTOz+f+KAM9/L0kkKX++/Fh0gMkrp+pvBBIhQGIFVf0JIEKAxEqq+hMgFijwPyiAj0LnAQv89+WJeR1gIsDAbwSKBQ38BIgFDvwEiAUP/BsJ4CA8HoDgf98BWAcYFMRPv76Bf6O4J5hoBBDgp+bV3O83w9Zny+dngn7/+d8ZYAdwZawU+L+3k+Co6k/8NwRI+jj0JQBJQHQU/+jxJ7oDXNr4BCCSxSfAjQ0/+/C59+sni3+3ADOPQZ3hP1uwmSW4xHRUB0iHP12CaAFGgP/I90GCGwLMNAap/NkSXGN5+g4AfhKsHoFG7wLgJ8EthqftAKPB3/nj15k7Qb3XIPDrBKNW/yk7wJnwz/4w3Rk7QYHf+JMswd3jTff7BLrAfzQge17byKPkvaP7FB0gdeY/c6SbpRPU1kaBf66xaUQJHmG19vrD4J/nzDCSBI8yOuwI5KNOB+NDD8EdD8RvLfwo8K+F5uzr61x41kwoQx+CXy747JW/86MYR137Osq0vTcE/NmFZy2TBQ7Xl1x46mjjZB65u7y397BYZ72w6Gxnwz/NCCRymgC6gOo/avXfrAOQAPwjwr/pCEQC8I8GvzOAOAN0NXPmeCpzH8aq+xsU2ZOtGuWNqv7gbz8CiUSfAXQB1X80lmrUNy7gH2IEIsHr6u+z/j7s1CwXMkrA34uZmu2CzP7gbymATqD6d2SkZr/ALtUf/D3ZqJQLVfnB/1ZOBbH780Zl/oJYqRcu4D9dABKA/+z3UBZCkve8HXjOBcCP6wC6AfgJQALwG4GMRMDXAXQD8BOABOA3AhmJgK8D6Ab2RgfQDYBPACIAnwBEAH7yGcD5wBrrALoB8AlABtATgAjAJwARgE8AMoCeAGQAPQHIAHoCpAsBeALESAF2AkwvB8j3yT89FHaODGWaIQAAAABJRU5ErkJggg=="

def write_icon(b64_data, path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.open(io.BytesIO(base64.b64decode(b64_data)))
    img = img.resize((size, size), Image.LANCZOS)
    img.save(path, "PNG")
    print("  icon " + os.path.basename(os.path.dirname(path)) + " " + str(size) + "x" + str(size) + " OK")

density_sizes = {
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}
for density, size in density_sizes.items():
    write_icon(ICON_MASKABLE_B64, os.path.join(RES, density, "ic_launcher.png"), size)
    write_icon(ICON_ANY_B64,      os.path.join(RES, density, "ic_launcher_round.png"), size)

print("Icons written OK")
print("Build script complete")
