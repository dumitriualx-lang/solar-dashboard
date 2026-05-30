#!/usr/bin/env python3
import os, io, base64
from PIL import Image

# ── Auto version management ───────────────────────────────────────────────────
# VERSION_CODE uses GITHUB_RUN_NUMBER (auto-incremented by GitHub Actions on
# every run — no files, no manual editing, never resets).
# BASE_VERSION_CODE is set so run #1 produces code 10 (above Play Store v9).
# Every subsequent run produces 11, 12, 13 ... automatically.
BASE_VERSION_CODE = 9   # offset: run N → version code (BASE + N)
VERSION_NAME      = "1.2.0"
_run = int(os.environ.get("GITHUB_RUN_NUMBER", "1"))
VERSION_CODE = BASE_VERSION_CODE + _run
print(f"Build: versionCode={VERSION_CODE}  versionName={VERSION_NAME}  (run #{_run})")

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "twa")
APP  = os.path.join(ROOT, "app")
MAIN = os.path.join(APP, "src", "main")
RES  = os.path.join(MAIN, "res")
WRAP = os.path.join(ROOT, "gradle", "wrapper")

PKG       = "com.dumitriualxlang.solardasboard"
HOST      = "dumitriualx-lang.github.io"
START_URL = "https://dumitriualx-lang.github.io/solar-dashboard/"
APP_NAME  = "Solar Dashboard"
COLOR_HEX = "FF1D9E75"
KEYSTORE  = os.path.join(HOME, "solar.keystore")

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
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
    id 'com.android.application' version '8.3.2' apply true
}
android {
    namespace "%s"
    compileSdk 35
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 35
        versionCode 4
        versionName "1.2.0"
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
    implementation "androidx.work:work-runtime:2.9.0"
}
""" % (PKG, PKG, KEYSTORE))

write(os.path.join(MAIN, "AndroidManifest.xml"), """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"/>
    <uses-permission android:name="android.permission.WAKE_LOCK"/>
    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC"/>
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
        <receiver
            android:name=".BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED"/>
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED"/>
            </intent-filter>
        </receiver>
        <receiver
            android:name=".SolarAlarmReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="com.dumitriualxlang.solardasboard.SOLAR_CHECK"/>
                <action android:name="com.dumitriualxlang.solardasboard.RESTART_FGS"/>
            </intent-filter>
        </receiver>
        <service
            android:name=".SolarForegroundService"
            android:foregroundServiceType="dataSync"
            android:exported="false"/>
    </application>
</manifest>
""")
_bgpath = os.path.join(APP, "build.gradle")
with open(_bgpath) as _f: _bg = _f.read()
import re as _re
_bg = _re.sub(r'versionCode \d+',    f'versionCode {VERSION_CODE}',       _bg)
_bg = _re.sub(r'versionName "[^"]*"', f'versionName "{VERSION_NAME}"',     _bg)
with open(_bgpath, "w") as _f: _f.write(_bg)
print(f"  patched build.gradle → versionCode={VERSION_CODE} versionName={VERSION_NAME}")


# Ownership verification file for Google Play package registration
assets_dir = os.path.join(APP, "src", "main", "assets")
os.makedirs(assets_dir, exist_ok=True)
with open(os.path.join(assets_dir, "adi-registration.properties"), "w") as f:
    f.write("DXQBJOK6FSERIAAAAAAAAAAAAA\n")

write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "MainActivity.java"), """package com.dumitriualxlang.solardasboard;

import android.app.Activity;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
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
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import java.util.concurrent.TimeUnit;
import android.app.AlarmManager;
import android.net.Uri;
import android.os.PowerManager;
import android.provider.Settings;

public class MainActivity extends Activity {
    private WebView webView;
    private Handler mainHandler;
    private static final String APP_URL = "https://dumitriualx-lang.github.io/solar-dashboard/";
    private static final String CHANNEL_ID = "solar_alerts";
    private int notifId = 1;

    private String httpGet(String urlStr) {
        try {
            URL url = new URL(urlStr);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(20000);
            conn.setReadTimeout(20000);
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14)");
            conn.setRequestProperty("Accept", "application/json");
            conn.setInstanceFollowRedirects(true);
            int code = conn.getResponseCode();
            if (code == 200) {
                BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();
                conn.disconnect();
                return sb.toString();
            }
            conn.disconnect();
            return "HTTP_ERROR_" + code;
        } catch (Exception e) {
            return "JAVA_ERROR_" + e.getClass().getSimpleName() + "_" + e.getMessage();
        }
    }

    public class AppBridge {
        // Called from JS to fetch weather - runs HTTP in background, injects result back
        @JavascriptInterface
        public void fetchWeather(String urlStr) {
            new Thread(() -> {
                String result = httpGet(urlStr);
                if (result == null) result = "NULL_RESULT";
                final String escaped = android.util.Base64.encodeToString(
                    result.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    android.util.Base64.NO_WRAP);
                mainHandler.post(() ->
                    webView.evaluateJavascript(
                        "window.__nativeWeatherResult('" + escaped + "');", null));
            }).start();
        }

        @JavascriptInterface
        public void showNotif(String title, String body) {
            showNotifTagged(title, body, title);  // tag = title (stable)
        }

        @JavascriptInterface
        public void showNotifTagged(String title, String body, String tag) {
            mainHandler.post(() -> {
                NotificationCompat.Builder b = new NotificationCompat.Builder(
                    MainActivity.this, CHANNEL_ID)
                    .setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(title).setContentText(body)
                    .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setAutoCancel(true)
                    .setColor(Color.parseColor("#1D9E75"));
                Intent i = new Intent(MainActivity.this, MainActivity.class);
                i.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
                b.setContentIntent(PendingIntent.getActivity(MainActivity.this, 0, i,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
                try {
                    // Stable ID derived from tag hash - same tag replaces previous notification
                    int stableId = 4000 + (Math.abs((tag != null ? tag : title).hashCode()) % 1000);
                    NotificationManagerCompat.from(MainActivity.this).notify(stableId, b.build());
                } catch (Exception ignored) {}
            });
        }

        @JavascriptInterface
        public boolean notifGranted() {
            return NotificationManagerCompat.from(MainActivity.this).areNotificationsEnabled();
        }

        @JavascriptInterface
        public void requestNotif() {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
                requestPermissions(
                    new String[]{android.Manifest.permission.POST_NOTIFICATIONS}, 1);
        }

        // saveSoc — persists all system state to SharedPreferences.
        // Called from JS every 5s (evolveSoc) and on any config change.
        // soc_saved_at_ms is used by injectLocation() to catch-up SOC evolution
        // when the app reopens and the background service hasn't fired yet.
        @JavascriptInterface
        public void saveSoc(float soc, float panelKw, float battGross, float battRes, float consKw, float battMaxC, float battMaxD, float panelAzimuth) {
            getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE)
                .edit()
                .putFloat("soc",            soc)
                .putFloat("panel_kw",       panelKw)
                .putFloat("batt_gross",     battGross)
                .putFloat("batt_res",       battRes)
                .putFloat("cons_kw",        consKw)
                .putFloat("batt_max_c",     battMaxC)
                .putFloat("batt_max_d",     battMaxD)
                .putFloat("panel_azimuth",   panelAzimuth)
                .putLong ("soc_saved_at_ms", System.currentTimeMillis())
                .putBoolean("soc_confirmed",  true)
                .apply();
        }

        // savePvCalibFactor — pushes the JS-side production calibration multiplier
        // to Java so background SOC updates use the same calibrated kW as the
        // dashboard. Without this, the notification reading would be 5-15% below
        // the dashboard for the same instant.
        @JavascriptInterface
        public void savePvCalibFactor(float factor) {
            // Clamp to the same range JS uses (getLearnedFactor returns 0.25..4.0)
            float clamped = Math.max(0.25f, Math.min(4.0f, factor));
            // CRITICAL: write to "solar_prefs" - the SAME SharedPreferences file
            // that FGS / AlarmReceiver / Worker read from. Previously this method
            // wrote to "SolarDashboard" (a different file), so background
            // services never saw the calibration and notifications showed the
            // uncalibrated raw model value.
            getSharedPreferences("solar_prefs", android.content.Context.MODE_PRIVATE)
                .edit()
                .putFloat("pv_calib_factor", clamped)
                .apply();
            android.util.Log.d("AppBridge", "Calibration factor saved: " + clamped);
        }

        @JavascriptInterface
        public String getBackgroundLog() {
            // Returns the JSON array of log entries written by FGS on every
            // background check (~once per 30 min). JS calls this at startup to
            // merge background entries into its rolling rlog buffer, so the
            // Reading Log page shows continuous coverage of the entire day
            // instead of only the periods when the app was foreground.
            try {
                return getSharedPreferences("solar_prefs", MODE_PRIVATE)
                    .getString("bg_log_v1", "[]");
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "getBackgroundLog: " + e.getMessage());
                return "[]";
            }
        }

        @JavascriptInterface
        public void clearBackgroundLog() {
            // Called by JS after merging entries into rlog and persisting to
            // localStorage. Prevents re-merging the same entries on every
            // launch. Safe because the JS-side localStorage is the durable
            // store once entries cross the bridge.
            try {
                getSharedPreferences("solar_prefs", MODE_PRIVATE)
                    .edit()
                    .putString("bg_log_v1", "[]")
                    .apply();
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "clearBackgroundLog: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public int getVersionCode() {
            try {
                return getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
            } catch (Exception e) { return 0; }
        }

        @JavascriptInterface
        public String getVersionName() {
            try {
                return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
            } catch (Exception e) { return ""; }
        }

        @JavascriptInterface
        public void openUrl(String url) {
            // Open URL using Android Intent — works for Play Store and https URLs
            try {
                android.content.Intent intent = new android.content.Intent(
                    android.content.Intent.ACTION_VIEW,
                    android.net.Uri.parse(url)
                );
                intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                getApplicationContext().startActivity(intent);
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "openUrl failed: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public String loadSoc() {
            android.content.SharedPreferences p =
                getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);
            float soc      = p.getFloat("soc",        -1f);
            float panelKw  = p.getFloat("panel_kw",    0f);
            float battGross= p.getFloat("batt_gross",  0f);
            float battRes  = p.getFloat("batt_res",    0f);
            float consKw    = p.getFloat("cons_kw",        0f);
            float gridExp   = p.getFloat("grid_export_kwh", 0f);
            float gridImp   = p.getFloat("grid_import_kwh", 0f);
            float pvKwh     = p.getFloat("pv_kwh",           0f);
            String gridDate = p.getString("grid_date",       "");
            String socStr   = soc >= 0 ? String.valueOf(soc) : "-1";
            return socStr + "," + panelKw + "," + battGross + "," + battRes + "," + consKw
                 + "," + gridExp + "," + gridImp + "," + gridDate + "," + pvKwh;
        }

        @JavascriptInterface
        public void saveGps(double lat, double lon, String name) {
            android.content.SharedPreferences prefs =
                getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);
            prefs.edit()
                .putFloat("gps_lat", (float) lat)
                .putFloat("gps_lon", (float) lon)
                .putString("gps_name", name)
                .apply();
        }

        @JavascriptInterface
        public String loadGps() {
            android.content.SharedPreferences prefs =
                getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);
            float lat = prefs.getFloat("gps_lat", 0f);
            float lon = prefs.getFloat("gps_lon", 0f);
            String name = prefs.getString("gps_name", "");
            if (lat == 0f && lon == 0f) return "";
            return lat + "," + lon + "," + name;
        }

        @JavascriptInterface
        public boolean locationPermissionGranted() {
            return checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                == android.content.pm.PackageManager.PERMISSION_GRANTED;
        }

        @JavascriptInterface
        public void openLocationSettings() {
            startActivity(new android.content.Intent(
                android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS));
        }

        @JavascriptInterface
        public void requestLocationPermission() {
            requestPermissions(new String[]{
                android.Manifest.permission.ACCESS_FINE_LOCATION,
                android.Manifest.permission.ACCESS_COARSE_LOCATION}, 2);
        }

        @JavascriptInterface
        public void saveConsProfile(String jsonArr) {
            // 24-hour consumption profile array (kW per hour 0..23)
            // Used by SOC catch-up in onResume() to integrate consumption correctly
            // across long sleeps (instead of applying a single consKw for all hours).
            try {
                if (jsonArr == null) return;
                org.json.JSONArray arr = new org.json.JSONArray(jsonArr);
                if (arr.length() != 24) return;
                android.content.SharedPreferences.Editor ed =
                    getSharedPreferences("solar_prefs", MODE_PRIVATE).edit();
                StringBuilder sb = new StringBuilder();
                for (int h = 0; h < 24; h++) {
                    if (h > 0) sb.append(",");
                    sb.append(arr.getDouble(h));
                }
                ed.putString("cons_profile_hourly", sb.toString()).apply();
                android.util.Log.d("AppBridge", "Saved 24h consumption profile");
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "saveConsProfile: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public void saveForecast(float peakKw, int peakHour, float todayKwh) {
            // Pushed by JS after weather fetch. Used by FGS morning notification.
            try {
                getSharedPreferences("solar_prefs", MODE_PRIVATE).edit()
                    .putFloat("peak_kw", peakKw)
                    .putInt("peak_hour", peakHour)
                    .putFloat("forecast_today_kwh", todayKwh)
                    .apply();
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "saveForecast: " + e.getMessage());
            }
        }

        
        @JavascriptInterface
        public void savePanelLocation(double lat, double lon, String name) {
            // Store the locked panel location. Used by all background services
            // (FGS, AlarmReceiver, Worker) and the SOC catch-up. This is what
            // makes the app independent of where the phone physically is - so
            // when the user travels, the forecast stays for the panel location.
            try {
                android.content.SharedPreferences.Editor ed =
                    getSharedPreferences("solar_prefs", MODE_PRIVATE).edit();
                ed.putFloat("panel_lat", (float) lat)
                  .putFloat("panel_lon", (float) lon);
                if (name != null) ed.putString("panel_loc_name", name);
                ed.apply();
                android.util.Log.d("AppBridge", "Panel location locked: " + lat + "," + lon + " (" + name + ")");
            } catch (Exception e) {
                android.util.Log.e("AppBridge", "savePanelLocation: " + e.getMessage());
            }
        }

// ── FusionSolar integration ────────────────────────────────────────


        // Fetches the CAPTCHA image as base64 so JS can display it in an <img> tag


        // Retries login with the user-supplied CAPTCHA code
    }

    private void requestBatteryOptimizationExemption() {
        // Samsung (and other OEMs) aggressively kill background tasks.
        // This prompts the user once to whitelist the app from battery optimization.
        // Without this, WorkManager periodic tasks may never fire on Samsung S24.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            try {
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                if (pm != null && !pm.isIgnoringBatteryOptimizations(getPackageName())) {
                    Intent intent = new Intent(
                        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                    intent.setData(Uri.parse("package:" + getPackageName()));
                    startActivity(intent);
                }
            } catch (Exception e) {
                android.util.Log.w("MainActivity", "Battery opt exemption request failed: " + e.getMessage());
            }
        }
    }

    private void scheduleBackgroundWork() {
        // No network constraint — worker handles offline gracefully.
        // CONNECTED was causing complete overnight failure on Samsung (WiFi off during sleep).
        PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(
            SolarWorker.class, 30, TimeUnit.MINUTES)
            .build();
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "solar_background",
            ExistingPeriodicWorkPolicy.UPDATE,
            work);
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
            ch.setLightColor(Color.parseColor("#1D9E75"));
            ((NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE))
                .createNotificationChannel(ch);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());
        createNotificationChannel();
        scheduleBackgroundWork();              // WorkManager — tertiary backup
        SolarAlarmReceiver.schedule(this);    // AlarmManager — secondary backup
        try { SolarForegroundService.start(this); } catch (Exception e) {
            android.util.Log.w("MainActivity", "FGS start failed: " + e.getMessage());
        } // Foreground Service - PRIMARY (Samsung-safe)
        requestBatteryOptimizationExemption();

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#1D9E75"));
        setContentView(webView);

        // Clear cache on every launch so the latest GitHub Pages index.html
        // is always fetched. Without this, stale JS with old bugs persists
        // across installs and updates, causing stuck values and wrong behaviour.
        // Only clear cache when app version changes - prevents spurious update prompts
        try {
            android.content.SharedPreferences bp =
                getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);
            int lastVer = bp.getInt("last_cached_version", 0);
            int curVer  = getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
            if (lastVer != curVer) {
                webView.clearCache(true);
                bp.edit().putInt("last_cached_version", curVer).apply();
            }
        } catch (Exception e) { webView.clearCache(true); }

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(true);
        // NOTE: Do NOT call webView.setLayerType(LAYER_TYPE_HARDWARE) -
        // it causes ANR on complex pages by double-compositing the renderer.
        // Hardware acceleration is enabled at manifest level (android:hardwareAccelerated="true").
        s.setAllowContentAccess(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.addJavascriptInterface(new AppBridge(), "AppBridge");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin,
                    GeolocationPermissions.Callback cb) { cb.invoke(origin, true, true); }
            @Override
            public void onPermissionRequest(android.webkit.PermissionRequest r) {
                r.grant(r.getResources());
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return false;
            }
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                // Inject GPS and state AFTER page has fully loaded
                // This guarantees JS functions exist when we call them
                mainHandler.postDelayed(() -> injectLocation(), 200);
            }
        });

        // Request location permission if not already granted
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                    != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{
                    android.Manifest.permission.ACCESS_FINE_LOCATION,
                    android.Manifest.permission.ACCESS_COARSE_LOCATION
                }, 2);
            }
        }

        if (savedInstanceState != null) webView.restoreState(savedInstanceState);
        else webView.loadUrl(APP_URL);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    public void onResume() {
        super.onResume();
        // On resume: try to get last known location from Android LocationManager
        // This is instant (no GPS fix needed) and works even without network
        mainHandler.postDelayed(() -> injectLocation(), 300);
        scheduleMorningAlarm();
    }

    private void scheduleMorningAlarm() {
        try {
            android.app.AlarmManager am =
                (android.app.AlarmManager) getSystemService(ALARM_SERVICE);
            if (am == null) return;
            android.content.Intent intent =
                new android.content.Intent(this, SolarAlarmReceiver.class);
            java.util.Calendar cal = java.util.Calendar.getInstance();
            if (cal.get(java.util.Calendar.HOUR_OF_DAY) >= 8)
                cal.add(java.util.Calendar.DAY_OF_YEAR, 1);
            cal.set(java.util.Calendar.HOUR_OF_DAY, 8);
            cal.set(java.util.Calendar.MINUTE, 0);
            cal.set(java.util.Calendar.SECOND, 0);
            cal.set(java.util.Calendar.MILLISECOND, 0);
            android.app.PendingIntent pi = android.app.PendingIntent.getBroadcast(
                this, 9999, intent,
                android.app.PendingIntent.FLAG_UPDATE_CURRENT |
                android.app.PendingIntent.FLAG_IMMUTABLE);
            am.setExactAndAllowWhileIdle(
                android.app.AlarmManager.RTC_WAKEUP, cal.getTimeInMillis(), pi);
        } catch (Exception ex) {
            android.util.Log.w("SolarMain", "scheduleMorningAlarm failed: " + ex);
        }
    }

    private void injectLocation() {
        android.content.SharedPreferences prefs =
            getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);

        // ── GPS ──────────────────────────────────────────────────────────────
        double gpsLat = 0, gpsLon = 0;
        String gpsName = "";
        try {
            android.location.LocationManager lm =
                (android.location.LocationManager) getSystemService(android.content.Context.LOCATION_SERVICE);
            android.location.Location loc = null;
            if (lm != null && checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                    == android.content.pm.PackageManager.PERMISSION_GRANTED) {

                // Step 1: Use last known immediately for fast UI response
                loc = lm.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
                if (loc == null)
                    loc = lm.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER);
                if (loc == null)
                    loc = lm.getLastKnownLocation(android.location.LocationManager.PASSIVE_PROVIDER);

                // Step 2: Also request a FRESH fix in parallel — fires async when ready
                // Uses NETWORK provider (fast, battery-friendly) then upgrades to GPS if needed
                try {
                    android.location.LocationListener freshListener = location -> {
                        double fLat = location.getLatitude();
                        double fLon = location.getLongitude();
                        prefs.edit()
                            .putFloat("gps_lat", (float) fLat)
                            .putFloat("gps_lon", (float) fLon)
                            .apply();
                        mainHandler.post(() -> webView.evaluateJavascript(
                            "if(typeof applyGpsFromNative==='function')" +
                            "applyGpsFromNative(" + fLat + "," + fLon + ",'');", null));
                    };
                    if (lm.isProviderEnabled(android.location.LocationManager.NETWORK_PROVIDER)) {
                        lm.requestSingleUpdate(android.location.LocationManager.NETWORK_PROVIDER,
                            freshListener, android.os.Looper.getMainLooper());
                    }
                    if (lm.isProviderEnabled(android.location.LocationManager.GPS_PROVIDER)) {
                        lm.requestSingleUpdate(android.location.LocationManager.GPS_PROVIDER,
                            freshListener, android.os.Looper.getMainLooper());
                    }
                } catch (Exception ignored) {}
            }
            if (loc != null) {
                gpsLat = loc.getLatitude();
                gpsLon = loc.getLongitude();
                prefs.edit().putFloat("gps_lat", (float)gpsLat)
                            .putFloat("gps_lon", (float)gpsLon).apply();
            }
        } catch (Exception e) { /* fall through */ }

        // Fall back to SharedPreferences if LocationManager had no fix
        if (gpsLat == 0 && gpsLon == 0) {
            gpsLat  = prefs.getFloat("gps_lat", 0f);
            gpsLon  = prefs.getFloat("gps_lon", 0f);
            gpsName = prefs.getString("gps_name", "");
        } else {
            // Fresh GPS fix — reuse cached city name only if within 1km
            float storedLat   = prefs.getFloat("gps_lat", 0f);
            float storedLon   = prefs.getFloat("gps_lon", 0f);
            String storedName = prefs.getString("gps_name", "");
            if (!storedName.isEmpty()
                    && Math.abs(gpsLat - storedLat) < 0.01f
                    && Math.abs(gpsLon - storedLon) < 0.01f) {
                gpsName = storedName;
            }
            // If we moved more than 1km, clear the saved name so JS re-geocodes
        }

        if (gpsLat != 0 && gpsLon != 0) {
            String safeN = gpsName.replace("'", "\\'");
            webView.evaluateJavascript(
                "if(typeof applyGpsFromNative==='function')" +
                "applyGpsFromNative(" + gpsLat + "," + gpsLon + ",'" + safeN + "');", null);
        }

        // Start FusionSolar live data injection loop (if FS credentials are configured)

        // ── SOC & CONFIG ─────────────────────────────────────────────────────
        // Always inject — not conditional on GPS success
        float soc       = prefs.getFloat("soc",        -1f);
        float panelKw   = prefs.getFloat("panel_kw",    0f);
        float battGross = prefs.getFloat("batt_gross",  0f);
        float battRes   = prefs.getFloat("batt_res",    0f);
        float consKw    = prefs.getFloat("cons_kw",     0f);
        float bgPvKwRaw = prefs.getFloat("pv_kw",      -1f);
        long  bgAge     = System.currentTimeMillis() - prefs.getLong("soc_saved_at_ms", 0L);
        // Only inject last-known pvKw if it's less than 15 min old.
        // 90 min was too long — stale production data locked the display on app open.
        float bgPvKw    = (bgAge > 0 && bgAge < 15L * 60 * 1000) ? bgPvKwRaw : -1f;

        // ── SOC CATCH-UP ─────────────────────────────────────────────────────
        // The alarm fires every 30 min. If the app was closed for only 5 minutes,
        // the alarm hasn't fired and SharedPreferences SOC is stale.
        // We catch-up here using elapsed time + last known pvKw/consKw,
        // so the battery panel shows the correct value immediately on reopen.
        if (soc >= 0 && battGross > 0 && panelKw > 0) {
            long socSavedAt = prefs.getLong("soc_saved_at_ms", -1L);
            if (socSavedAt > 0) {
                double elapsedH = (System.currentTimeMillis() - socSavedAt) / 3600000.0;
                // Only apply catch-up if gap is meaningful (>2 min) and not absurd (>12h)
                // A >12h gap means the alarm should have fired; trust its value instead.
                if (elapsedH > (2.0 / 60.0) && elapsedH <= 12.0) {
                    float battMaxC = prefs.getFloat("batt_max_c", 2.5f);
                    float battMaxD = prefs.getFloat("batt_max_d", 2.5f);
                    float pvKwLast = bgPvKw >= 0 ? bgPvKw : 0f;  // 0 if alarm never ran

                    double battUse = battGross * (1.0 - battRes);
                    if (battUse <= 0) battUse = 4.5;
                    double hardFlr = 0.0;
                    double rampTop = 2.0;
                    double battEff = 0.95;

                    // Try to load hourly consumption profile (24 values comma-separated)
                    String prof = prefs.getString("cons_profile_hourly", "");
                    double[] profHourly = null;
                    if (!prof.isEmpty()) {
                        try {
                            String[] parts = prof.split(",");
                            if (parts.length == 24) {
                                profHourly = new double[24];
                                for (int h = 0; h < 24; h++) profHourly[h] = Double.parseDouble(parts[h]);
                            }
                        } catch (Exception ignored) {}
                    }

                    double curSoc = soc;
                    double totalFlow = 0.0;
                    if (profHourly != null) {
                        // Walk elapsed time in 1-hour chunks, applying the correct cons for each hour
                        long startMs = socSavedAt;
                        long endMs = System.currentTimeMillis();
                        long step = 15L * 60L * 1000L;  // 15-min steps for granularity
                        // PV during the gap: estimate using the forecast bell curve.
                        // JS pushes peak_kw and peak_hour via AppBridge.saveForecast() after every weather fetch.
                        // The bell-curve model is far more accurate than the old linear-decay-to-zero approach,
                        // especially when the gap crosses sunrise/sunset.
                        float catchPeakKw = prefs.getFloat("peak_kw", 0f);
                        int   catchPeakHr = prefs.getInt("peak_hour", 12);
                        for (long t = startMs; t < endMs; t += step) {
                            long chunkEnd = Math.min(t + step, endMs);
                            double dtH = (chunkEnd - t) / 3600000.0;
                            java.util.Calendar c = java.util.Calendar.getInstance();
                            c.setTimeInMillis(t);
                            int hr = c.get(java.util.Calendar.HOUR_OF_DAY);
                            int mn = c.get(java.util.Calendar.MINUTE);
                            double hOfDay = hr + mn / 60.0;
                            double consH = profHourly[hr];
                            // Bell-curve PV: peakKw * cos(deltaH * π/12)²  (clamped >= 0, dies at ±6h from peak)
                            double pvH;
                            if (catchPeakKw > 0) {
                                double normDist = (hOfDay - catchPeakHr) / 6.0;
                                pvH = (Math.abs(normDist) >= 1.0)
                                    ? 0.0
                                    : catchPeakKw * Math.pow(Math.cos(normDist * Math.PI / 2.0), 2);
                            } else {
                                // No forecast saved yet — fall back to linear decay (legacy behaviour)
                                double frac = (t - startMs) / (double)(endMs - startMs);
                                pvH = pvKwLast * Math.max(0.0, 1.0 - frac);
                            }

                            double s2hH = Math.min(pvH, consH);
                            double pvSH = pvH - s2hH;
                            double hDH  = consH - s2hH;
                            double bCH  = curSoc < 100 ? Math.min(pvSH, battMaxC) : 0;
                            double bDH;
                            if      (curSoc <= hardFlr) bDH = 0;
                            else if (curSoc <= rampTop) { double f=(curSoc-hardFlr)/rampTop; bDH=Math.min(hDH*f, battMaxD); }
                            else                        bDH = Math.min(hDH, battMaxD);

                            double bf = bCH - bDH;
                            double eff = bf > 0 ? bf * battEff : bf;
                            curSoc += (eff / battUse) * dtH * 100.0;
                            curSoc = Math.max(hardFlr, Math.min(100.0, curSoc));
                            totalFlow += bf * dtH;
                        }
                        android.util.Log.d("MainActivity", String.format(
                            "SOC catch-up (bell curve, peak=%.2fkW@%dh): %.1f min, total battFlow=%.2fkWh, soc %.1f->%.1f",
                            catchPeakKw, catchPeakHr, elapsedH * 60, totalFlow, (double) soc, curSoc));
                    } else {
                        // Legacy fallback: single consKw value
                        double s2h = Math.min(pvKwLast, consKw);
                        double pvS = pvKwLast - s2h;
                        double hD  = consKw - s2h;
                        double bC  = soc < 100 ? Math.min(pvS, battMaxC) : 0;
                        double bD;
                        if      (soc <= hardFlr) bD = 0;
                        else if (soc <= rampTop) { double f=(soc-hardFlr)/rampTop; bD=Math.min(hD*f, (double)battMaxD); }
                        else                     bD = Math.min(hD, (double) battMaxD);
                        double battFlow = bC - bD;
                        double effFlow  = battFlow > 0 ? battFlow * battEff : battFlow;
                        curSoc = soc + (effFlow / battUse) * elapsedH * 100.0;
                        curSoc = Math.max(hardFlr, Math.min(100.0, curSoc));
                        android.util.Log.d("MainActivity", String.format(
                            "SOC catch-up (legacy): %.1f min, pv=%.2fkW cons=%.2fkW flow=%.2fkW soc %.1f->%.1f",
                            elapsedH * 60, pvKwLast, (double) consKw, battFlow, (double) soc, curSoc));
                    }

                    prefs.edit()
                         .putFloat("soc", (float) curSoc)
                         .putLong("soc_saved_at_ms", System.currentTimeMillis())
                         .apply();
                    soc = (float) curSoc;
                }
            }
        }

        if (soc >= 0 && panelKw > 0 && battGross > 0) {
            webView.evaluateJavascript(
                "if(typeof applyStateFromNative==='function')" +
                "applyStateFromNative(" + soc + "," + panelKw + "," +
                battGross + "," + battRes + "," + consKw + "," + bgPvKw + ");", null);
        }
    }


    // ── FusionSolar live data injection ───────────────────────────────────────
    private android.os.Handler fsHandler;
    private Runnable           fsRunnable;

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 2) {
            // Location permission result — trigger JS to retry GPS
            mainHandler.postDelayed(() ->
                webView.evaluateJavascript("if(typeof requestLocation==='function')requestLocation();", null),
            500);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
""")





write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarForegroundService.java"), """package com.dumitriualxlang.solardasboard;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import androidx.core.app.NotificationCompat;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Calendar;
import java.util.GregorianCalendar;

/**
 * SolarForegroundService — the PRIMARY background engine.
 *
 * A Foreground Service is the ONLY mechanism that cannot be killed by Samsung's
 * Device Care, even with battery optimization enabled. It runs permanently until
 * the user explicitly stops it or the app is uninstalled.
 *
 * Every 30 minutes it:
 *   1. Fetches weather from Open-Meteo
 *   2. Calculates solar production using the same physics model as the JS app
 *   3. Runs the energy flow model (Solar → Home → Battery → Grid)
 *   4. Evolves battery SOC over elapsed time
 *   5. Persists soc + pv_kw + soc_saved_at_ms to SharedPreferences
 *   6. Fires a notification if any alert rule matches
 *
 * The persistent "Solar monitoring active" notification is required by Android
 * for foreground services — it cannot be dismissed but can be minimised.
 */
public class SolarForegroundService extends Service {

    private static final String CHANNEL_ID    = "solar_alerts";
    private static final String CHANNEL_FG_ID = "solar_fg";
    private static final String PREFS         = "SolarDashboard";
    private static final int    FG_NOTIF_ID   = 999;
    private static final long   INTERVAL_MS   = 30 * 60 * 1000L;  // 30 minutes
    private static int          alertNotifId  = 3000;
    private volatile boolean    isWorking     = false;

    private Handler  handler;
    private Runnable checker;

    // ── Public API ────────────────────────────────────────────────────────────
    public static void start(Context ctx) {
        Intent intent = new Intent(ctx, SolarForegroundService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ctx.startForegroundService(intent);
        } else {
            ctx.startService(intent);
        }
    }

    public static void stop(Context ctx) {
        ctx.stopService(new Intent(ctx, SolarForegroundService.class));
    }

    // ── Service lifecycle ─────────────────────────────────────────────────────
    @Override
    public void onCreate() {
        super.onCreate();
        handler = new Handler(Looper.getMainLooper());
        createChannels();
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            startForeground(FG_NOTIF_ID, buildFgNotification("Solar monitoring active"),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        } else {
            startForeground(FG_NOTIF_ID, buildFgNotification("Solar monitoring active"));
        }
        android.util.Log.d("SolarFGS", "Service created — starting 30-min check loop");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // ANDROID 14+ FIX: dataSync FGS has a 6-hour cumulative-per-day limit.
        // Previously we ran continuously via handler.postDelayed and were killed
        // by ForegroundServiceDidNotStopInTimeException after 6 hours.
        // New architecture: do ONE check, then stop. AlarmReceiver wakes us up
        // every 30 min for the next check, keeping cumulative FGS time minimal.
        if (isWorking) {
            android.util.Log.d("SolarFGS", "Already working - ignoring duplicate start");
            return START_NOT_STICKY;
        }
        isWorking = true;
        new Thread(() -> {
            try {
                doSolarCheck();
            } catch (Exception e) {
                android.util.Log.e("SolarFGS", "Check error: " + e.getMessage());
            } finally {
                // Always stop the FGS after one check so we stay well under the
                // 6-hour cumulative-runtime limit for dataSync foreground services.
                isWorking = false;
                handler.post(() -> {
                    try {
                        stopForeground(true);
                        stopSelf();
                        android.util.Log.d("SolarFGS", "Check complete - service stopped");
                    } catch (Exception ignored) {}
                });
            }
        }).start();
        // Make sure AlarmReceiver is scheduled so we wake up again in 30 min
        SolarAlarmReceiver.schedule(getApplicationContext());
        // START_NOT_STICKY: do not auto-restart - SAR will restart us at the next alarm
        return START_NOT_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (handler != null && checker != null) {
            handler.removeCallbacks(checker);
        }
        // NOTE: We no longer schedule a 1-minute restart alarm on destroy.
        // Under the new one-shot architecture, every onDestroy is expected
        // (we stopped ourselves intentionally). AlarmReceiver handles the
        // next periodic wake-up in 30 min.
        android.util.Log.d("SolarFGS", "Service destroyed (expected after one-shot check)");
    }

    private void scheduleRestartAlarm() {
        try {
            android.app.AlarmManager am =
                (android.app.AlarmManager) getSystemService(ALARM_SERVICE);
            if (am == null) return;
            Intent ri = new Intent(this, SolarAlarmReceiver.class)
                .setAction("com.dumitriualxlang.solardasboard.RESTART_FGS");
            android.app.PendingIntent pi = android.app.PendingIntent.getBroadcast(
                this, 9001, ri,
                android.app.PendingIntent.FLAG_UPDATE_CURRENT |
                android.app.PendingIntent.FLAG_IMMUTABLE);
            long at = System.currentTimeMillis() + 60_000L; // 1 minute
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && am.canScheduleExactAlarms()) {
                am.setExactAndAllowWhileIdle(android.app.AlarmManager.RTC_WAKEUP, at, pi);
            } else {
                am.setAndAllowWhileIdle(android.app.AlarmManager.RTC_WAKEUP, at, pi);
            }
        } catch (Exception e) {
            android.util.Log.e("SolarFGS", "Restart alarm failed: " + e.getMessage());
        }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    // ── Core physics check ────────────────────────────────────────────────────
    private void doSolarCheck() {
        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long nowMs = System.currentTimeMillis();

        // Elapsed time since last run
        long lastMs = prefs.getLong("fgs_last_run_ms", nowMs);
        double dtH  = (nowMs - lastMs) / 3600000.0;
        if (dtH <= 0 || dtH > 1.5) dtH = 0.5;  // cap: service restarts can cause gaps
        prefs.edit().putLong("fgs_last_run_ms", nowMs).apply();

        // Read config
        float soc      = prefs.getFloat("soc",       -1f);
        float panelKw  = prefs.getFloat("panel_kw",   0f);
        float battGross= prefs.getFloat("batt_gross", 0f);
        float battRes  = prefs.getFloat("batt_res",   0.1f);
        float consKw   = prefs.getFloat("cons_kw",    0f);
        float battMaxC = prefs.getFloat("batt_max_c", 2.5f);
        float battMaxD = prefs.getFloat("batt_max_d", 2.5f);
        // PANEL LOCATION LOCK: prefer the user-set panel coords over phone GPS.
        // This way the forecast stays for the panels even when the user travels.
        float lat      = prefs.getFloat("panel_lat", 0f);
        float lon      = prefs.getFloat("panel_lon", 0f);
        if (lat == 0f || lon == 0f) {
            // No panel lock yet (first run before user sets it) - fall back to phone GPS
            lat = prefs.getFloat("gps_lat", 0f);
            lon = prefs.getFloat("gps_lon", 0f);
        }
        // Skip if system not configured - prevents fake data on fresh install
        if (panelKw <= 0 || battGross <= 0) {
            android.util.Log.d("SolarFGS", "System not configured - skipping");
            return;
        }
        if (soc < 0) soc = 50f; // default only after system is configured

        // GPS fallback via LocationManager
        if (lat == 0f || lon == 0f) {
            try {
                android.location.LocationManager lm =
                    (android.location.LocationManager) getSystemService(LOCATION_SERVICE);
                if (lm != null) {
                    android.location.Location loc =
                        lm.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
                    if (loc == null)
                        loc = lm.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER);
                    if (loc == null)
                        loc = lm.getLastKnownLocation(android.location.LocationManager.PASSIVE_PROVIDER);
                    if (loc != null) {
                        lat = (float) loc.getLatitude();
                        lon = (float) loc.getLongitude();
                        prefs.edit().putFloat("gps_lat", lat).putFloat("gps_lon", lon).apply();
                    }
                }
            } catch (Exception e) { android.util.Log.w("SolarFGS", "GPS fallback: " + e.getMessage()); }
        }
        if (lat == 0f || lon == 0f) {
            android.util.Log.w("SolarFGS", "No GPS available — skipping");
            return;
        }

        // ── Try FusionSolar first if credentials are configured ────────────
        // If successful, real inverter data overrides all satellite estimates.

        // Fetch weather — skip gracefully if offline, still evolve SOC
        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude=" + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = httpGet(url);
        boolean hasWeather = raw != null && !raw.startsWith("ERR");
        if (!hasWeather) android.util.Log.w("SolarFGS", "Weather unavailable — SOC evolves with last pvKw");

        // Use last known pvKw when offline; weather fetch overwrites if successful
        double pvKw = prefs.getFloat("pv_kw", 0f);
        double gridImport = 0, battFlow = 0;
        // Hoisted from inside the hasWeather block so the background-log entry
        // below (after the prefs commit) can read them even when weather fetch
        // was successful. Without this, the log append failed to compile because
        // poa_in/gridExport were out of scope.
        double poa_in    = 0;
        double gridExport = 0;
        double newSoc = soc;
        double battUse = battGross > 0 ? battGross * (1.0 - battRes) : 4.5;

        // Calendar declared here so hourNow is available in notifications section
        // regardless of whether weather fetch succeeded
        final Calendar nowCal = Calendar.getInstance();

        try {
            if (hasWeather) {
            JSONObject cur = new JSONObject(raw).getJSONObject("current");
            double directRad  = cur.optDouble("direct_radiation",  0);
            double diffuseRad = cur.optDouble("diffuse_radiation", 0);
            double tempC      = cur.optDouble("temperature_2m", 25);

            // ── Solar position (same algorithm as JS solarPosition()) ──────────
            Calendar cal = Calendar.getInstance();
            long dayOfYear = (nowMs - new GregorianCalendar(
                cal.get(Calendar.YEAR), 0, 1).getTimeInMillis()) / 86400000L;
            double utcH  = cal.get(Calendar.HOUR_OF_DAY)
                         + cal.get(Calendar.MINUTE) / 60.0
                         + cal.get(Calendar.SECOND) / 3600.0
                         - cal.getTimeZone().getOffset(nowMs) / 3600000.0;
            double decl  = 23.45 * Math.sin((360.0/365.0*(dayOfYear-81)) * Math.PI/180.0);
            double ha    = (utcH - 12) * 15 + lon;
            double latR  = lat * Math.PI/180.0, decR = decl * Math.PI/180.0;
            double sinAlt= Math.sin(latR)*Math.sin(decR)
                         + Math.cos(latR)*Math.cos(decR)*Math.cos(ha*Math.PI/180.0);
            double alt   = Math.asin(Math.max(-1,Math.min(1,sinAlt)))*180.0/Math.PI;

            double solAzDeg = 180.0;
            if (alt > 0) {
                double sinAz = Math.cos(decR) * Math.sin(ha * Math.PI/180.0)
                    / Math.max(0.001, Math.cos(alt * Math.PI/180.0));
                solAzDeg = Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, sinAz))));
                if (ha > 0) solAzDeg = 180.0 - solAzDeg;
                else        solAzDeg = 180.0 + solAzDeg;
            }

            if (alt > 2.0) {
                float  panelAz  = prefs.getFloat("panel_azimuth", 180f);
                double tiltR    = 30.0 * Math.PI / 180.0;
                double altR     = alt      * Math.PI / 180.0;
                double solAzR   = solAzDeg * Math.PI / 180.0;
                double pnlAzR   = panelAz  * Math.PI / 180.0;
                double cosAOI   = Math.sin(altR)*Math.cos(tiltR)
                                + Math.cos(altR)*Math.sin(tiltR)*Math.cos(solAzR - pnlAzR);
                double poaBeam  = Math.max(0, cosAOI) * Math.max(0, directRad);
                double poaSky   = Math.max(0, diffuseRad) * (1 + Math.cos(tiltR)) / 2.0;
                double poaGnd   = (directRad + diffuseRad) * 0.20 * (1 - Math.cos(tiltR)) / 2.0;
                poa_in          = poaBeam + poaSky + poaGnd;
                double cellT    = tempC + (45.0 - 20.0) * (poa_in / 800.0);
                double tFac     = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
                // Apply user PV calibration multiplier so background SOC tracks
                // the same calibrated production value as the JS dashboard.
                float calib = prefs.getFloat("pv_calib_factor", 1.0f);
                pvKw = Math.max(0, Math.min(panelKw * 0.984,
                    (poa_in / 1000.0) * panelKw * 0.984 * tFac)) * calib;
            } else {
                pvKw = 0; // sun below horizon
            }
            } // end if(hasWeather)

            // ── Energy flow (same model as JS calcFlow()) ─────────────────────
            double hardFlr = 0.0;
            double rampTop = 2.0;
            double s2h = Math.min(pvKw, consKw);
            double pvS = pvKw - s2h, hD = consKw - s2h;
            double bC  = soc < 100 ? Math.min(pvS, battMaxC) : 0;
            double bD;
            if      (soc <= hardFlr) bD = 0;
            else if (soc <= rampTop) { double frac=(soc-hardFlr)/rampTop; bD=Math.min(hD*frac,battMaxD); }
            else                     bD = Math.min(hD, battMaxD);
            battFlow   = bC - bD;
            gridImport = Math.max(0, hD - bD);
            gridExport = Math.max(0, pvS - bC);

            // ── Evolve SOC ────────────────────────────────────────────────────
            // Huawei Luna 2000 round-trip efficiency = 0.92
            double battEff = 0.95;
            double effFlow = battFlow > 0 ? battFlow * battEff : battFlow; // discharge: no penalty
            newSoc = soc + (effFlow / battUse) * dtH * 100.0;
            newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

            // ── Persist all state ─────────────────────────────────────────────
            int nm = nowCal.get(Calendar.MONTH)+1, nd = nowCal.get(Calendar.DAY_OF_MONTH);
            String todayStr = nowCal.get(Calendar.YEAR)
                + "-" + (nm<10?"0":"") + nm + "-" + (nd<10?"0":"") + nd;
            String lastGridDate = prefs.getString("grid_date", "");
            float prevExp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
            float prevImp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
            float prevPv  = lastGridDate.equals(todayStr) ? prefs.getFloat("pv_kwh",          0f) : 0f;
            float newExp  = prevExp + (float) gridExport * (float) dtH;
            float newImp  = prevImp + (float) gridImport * (float) dtH;
            float newPv   = prevPv  + (float) pvKw       * (float) dtH;
            prefs.edit()
                 .putFloat("soc",            (float) newSoc)
                 .putFloat("pv_kw",          (float) pvKw)
                 .putFloat("grid_export_kwh", newExp)
                 .putFloat("grid_import_kwh", newImp)
                 .putFloat("pv_kwh",          newPv)
                 .putString("grid_date",      todayStr)
                 .putLong ("soc_saved_at_ms", nowMs)
                 .apply();

            // ── Append a structured log entry for the JS-side reading log ────
            // The JS rlog only captures while the app is foreground (every 30 sec).
            // Without this Java-side log, the energy summary only reflected the
            // time the user was actively looking at the app. By writing one
            // entry per FGS run (~every 30 min in background) the log can show
            // continuous coverage of the whole day when JS merges these at
            // startup via AppBridge.getBackgroundLog().
            try {
                String existing = prefs.getString("bg_log_v1", "[]");
                org.json.JSONArray arr = new org.json.JSONArray(existing);
                org.json.JSONObject entry = new org.json.JSONObject();
                java.text.SimpleDateFormat iso = new java.text.SimpleDateFormat(
                    "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", java.util.Locale.US);
                iso.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                entry.put("t",     iso.format(new java.util.Date(nowMs)));
                entry.put("pvKw",  +String.format(java.util.Locale.US, "%.3f", pvKw));
                entry.put("batt",  +String.format(java.util.Locale.US, "%.3f", battFlow));
                entry.put("soc",   (float) newSoc);
                entry.put("irr",   (float) poa_in);
                // grd: positive = export to grid, negative = import (matches JS sign convention)
                double gridFlow = gridExport - gridImport;
                entry.put("grd",   +String.format(java.util.Locale.US, "%.3f", gridFlow));
                entry.put("lat",   (float) lat);
                entry.put("lon",   (float) lon);
                entry.put("src",   "bg");   // mark so JS can distinguish foreground vs background
                arr.put(entry);
                // Keep last 500 entries (~10 days at 48/day) to prevent unbounded growth
                while (arr.length() > 500) arr.remove(0);
                prefs.edit().putString("bg_log_v1", arr.toString()).apply();
            } catch (Exception logE) {
                android.util.Log.e("SolarFGS", "bg log append failed: " + logE.getMessage());
            }

            // Update the foreground notification with live values
            String status = String.format("☀️ %.2fkW · 🏠 %.2fkW · 🔋 %.0f%%",
                pvKw, (double) consKw, newSoc);
            updateFgNotification(status);

            android.util.Log.d("SolarFGS", String.format(
                "dtH=%.2fh pv=%.2f cons=%.2f flow=%.3f soc %.1f→%.1f grid=%.2f",
                dtH, pvKw, (double)consKw, battFlow, (double)soc, newSoc, gridImport));

            
            // ── Quiet hours: no notifications 22:00–08:00 ────────────────────
            int hourNow = nowCal.get(Calendar.HOUR_OF_DAY);
            int minuteNow = nowCal.get(Calendar.MINUTE);
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US);
            String todayKey = sdf.format(new java.util.Date(nowMs));
            String morningSentDate = prefs.getString("morning_sent_date", "");
            String eveningSentDate = prefs.getString("evening_sent_date", "");

            // NIGHT-TIME: no proactive notifications between 21:00 and 07:00
            if (hourNow >= 7 && hourNow < 21) {
                double surplus   = pvKw - (double) consKw;
                double storedKwh = battUse * (newSoc / 100.0);
                double dispSoc   = 10.0 + (newSoc / 100.0) * 90.0;
                long now2H       = 2L * 60 * 60 * 1000;

                // RULE A: MORNING "Production started" (once per day, 7-12h)
                if (hourNow >= 7 && hourNow < 12 && pvKw > 0.3
                        && !todayKey.equals(morningSentDate)) {
                    float  peakKw   = prefs.getFloat("peak_kw", (float) pvKw);
                    int    peakHr   = prefs.getInt("peak_hour", 12);
                    float  todayKwh = prefs.getFloat("forecast_today_kwh", 0f);
                    String body;
                    if (peakKw > 0 && peakHr > 0) {
                        body = String.format(
                            "Now: %.2f kW. Peak ~%.1f kW at %02d:00. Battery %d%%. Forecast: %.1f kWh today.",
                            pvKw, peakKw, peakHr, (int) dispSoc, todayKwh);
                    } else {
                        body = String.format("Production started \u2014 %.2f kW. Battery %d%%.", pvKw, (int) dispSoc);
                    }
                    sendAlert(ALERT_ID_MORNING, "Production started", body);
                    prefs.edit().putString("morning_sent_date", todayKey).apply();
                }

                // RULE B: HOURLY status (every full hour, 08-20h)
                long lastHourly = prefs.getLong("notif_last_hourly", 0);
                // NOTE: removed the "minuteNow < 10" gate. Alarms fire at drifting
                // times (e.g. :17, :47) and Android 14+ Doze throttles them, so a
                // first-10-minutes-of-the-hour window almost never matched. The
                // 55-minute cooldown alone produces ~hourly notifications whenever
                // the background check happens to run.
                if (hourNow >= 8 && hourNow < 20 && pvKw > 0.3
                        && (nowMs - lastHourly) > 55L * 60 * 1000) {
                    String body = String.format(
                        "Current %.2f kW. Battery %d%% (%.1f kWh stored).",
                        pvKw, (int) dispSoc, storedKwh);
                    sendAlert(ALERT_ID_HOURLY, "Solar update", body);
                    prefs.edit().putLong("notif_last_hourly", nowMs).apply();
                }

                // RULE C: EVENING "Production ended" (once per day, 16-21h)
                if (hourNow >= 16 && hourNow < 21
                        && pvKw < (double) consKw - 0.1
                        && battFlow < -0.1
                        && !todayKey.equals(eveningSentDate)) {
                    double backupHrs = storedKwh / Math.max(0.1, (double) consKw);
                    String body = String.format(
                        "Production %.2f kW < load %.2f kW. Battery %d%% \u2014 ~%.1fh backup remaining.",
                        pvKw, (double) consKw, (int) dispSoc, backupHrs);
                    sendAlert(ALERT_ID_SUN_END, "Production ended", body);
                    prefs.edit().putString("evening_sent_date", todayKey).apply();
                }

                // RULE D: BATTERY LOW (critical, daytime, 8h cooldown)
                long lBattLo = prefs.getLong("notif_last_batt_low", 0);
                if (storedKwh < battUse * 0.10 && dispSoc < 15.0
                        && (nowMs - lBattLo) > 4 * now2H) {
                    String body = String.format(
                        "Battery %d%% (%.1f kWh). Grid backup active. Solar: %.2f kW.",
                        (int) dispSoc, storedKwh, pvKw);
                    sendAlert(ALERT_ID_BATT_LOW, "Battery very low", body);
                    prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
                }

                // RULE E: PRODUCTION DROP (daytime, fires when pv was high but
                // dropped sharply — e.g. unexpected rain shower that the forecast
                // missed). Useful to remind the user to stop large appliances
                // before they drain the battery / pull from grid.
                //
                // Logic: track the rolling peak observed today (high water mark).
                // If current pvKw is below 1.0 kW AND below 30% of today's
                // observed peak AND it was previously high in the last 2 hours
                // (so we don't fire all morning on a cloudy day from sunrise),
                // emit the alert. 60-min cooldown to avoid spam.
                float observedPeakToday = prefs.getFloat("observed_peak_today", 0f);
                long  observedPeakDate  = prefs.getLong("observed_peak_date", 0);
                long  todayMs = nowMs - (nowMs % (24L * 60 * 60 * 1000));
                if (observedPeakDate != todayMs) {
                    // New day - reset the high-water mark
                    observedPeakToday = 0f;
                    prefs.edit()
                        .putFloat("observed_peak_today", 0f)
                        .putLong("observed_peak_date", todayMs)
                        .apply();
                }
                if (pvKw > observedPeakToday) {
                    observedPeakToday = (float) pvKw;
                    prefs.edit().putFloat("observed_peak_today", observedPeakToday).apply();
                    prefs.edit().putLong("last_high_pv_ms", nowMs).apply();
                } else if (pvKw > observedPeakToday * 0.5) {
                    // Still reasonably high — refresh the "was high" marker
                    prefs.edit().putLong("last_high_pv_ms", nowMs).apply();
                }
                long  lastHighMs   = prefs.getLong("last_high_pv_ms", 0);
                long  lastDropNotif= prefs.getLong("notif_last_pv_drop", 0);
                if (hourNow >= 8 && hourNow < 20
                        && pvKw < 1.0
                        && observedPeakToday >= 1.5
                        && pvKw < observedPeakToday * 0.30
                        && (nowMs - lastHighMs)    < 2L * 60 * 60 * 1000
                        && (nowMs - lastDropNotif) > 60L * 60 * 1000) {
                    String body = String.format(
                        "Production dropped to %.2f kW (peak today %.1f kW). " +
                        "Battery %d%% — consider postponing large appliances.",
                        pvKw, observedPeakToday, (int) dispSoc);
                    sendAlert(ALERT_ID_PV_DROP, "Production dropped", body);
                    prefs.edit().putLong("notif_last_pv_drop", nowMs).apply();
                }
            }  // end night-time gate

            prefs.edit().putFloat("last_notif_pv_kw", (float) pvKw).commit();


                    } catch (Exception e) {
            android.util.Log.e("SolarFGS", "doSolarCheck exception: " + e.getMessage());
        }
    }

    // ── Notifications ─────────────────────────────────────────────────────────
    private Notification buildFgNotification(String text) {
        Intent open = new Intent(this, MainActivity.class)
            .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        return new NotificationCompat.Builder(this, CHANNEL_FG_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Solar Dashboard")
            .setContentText(text)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setColor(Color.parseColor("#1D9E75"))
            .setContentIntent(pi)
            .build();
    }

    private void updateFgNotification(String text) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (nm != null) nm.notify(FG_NOTIF_ID, buildFgNotification(text));
    }

    // Stable notification IDs per alert type - same type replaces previous,
    // preventing stacking of multiple notifications with different SOC values.
    static final int ALERT_ID_SURPLUS    = 3001;
    static final int ALERT_ID_SUN_END    = 3002;
    static final int ALERT_ID_GOOD_DAY   = 3003;
    static final int ALERT_ID_BATT_LOW   = 3004;
    static final int ALERT_ID_MORNING    = 3005;
    static final int ALERT_ID_HIGH_CONS  = 3006;
    static final int ALERT_ID_PV_DROP    = 3007;
    static final int ALERT_ID_HOURLY     = 3008;

    private void sendAlert(int alertId, String title, String body) {
        try {
            Intent open = new Intent(this, MainActivity.class)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pi = PendingIntent.getActivity(this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            NotificationCompat.Builder nb = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title).setContentText(body)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setColor(Color.parseColor("#1D9E75"))
                .setContentIntent(pi);
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (nm != null) nm.notify(alertId, nb.build());
            android.util.Log.d("SolarFGS", "Alert sent (id=" + alertId + "): " + title);
        } catch (Exception e) {
            android.util.Log.e("SolarFGS", "sendAlert: " + e.getMessage());
        }
    }

    private void createChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (nm == null) return;
            // Foreground service channel — low priority, no sound
            if (nm.getNotificationChannel(CHANNEL_FG_ID) == null) {
                NotificationChannel fg = new NotificationChannel(
                    CHANNEL_FG_ID, "Solar background monitor", NotificationManager.IMPORTANCE_LOW);
                fg.setDescription("Keeps solar physics running in background");
                fg.setShowBadge(false);
                nm.createNotificationChannel(fg);
            }
            // Alert channel — high priority, for solar/battery alerts
            if (nm.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel al = new NotificationChannel(
                    CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
                al.setDescription("Solar production and battery alerts");
                al.setLightColor(Color.parseColor("#1D9E75"));
                al.enableLights(true);
                al.enableVibration(true);
                nm.createNotificationChannel(al);
            }
        }
    }

    private String httpGet(String urlStr) {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(15000);
            c.setRequestProperty("User-Agent","SolarDashboard/1.0");
            if (c.getResponseCode() == 200) {
                BufferedReader br = new BufferedReader(new InputStreamReader(c.getInputStream(),"UTF-8"));
                StringBuilder sb = new StringBuilder(); String ln;
                while ((ln=br.readLine())!=null) sb.append(ln);
                br.close(); c.disconnect(); return sb.toString();
            }
            c.disconnect(); return "ERR_HTTP_"+c.getResponseCode();
        } catch (Exception e) { return "ERR_"+e.getMessage(); }
    }
}
""")


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarAlarmReceiver.java"), """package com.dumitriualxlang.solardasboard;

import android.app.AlarmManager;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import androidx.core.app.NotificationCompat;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Calendar;
import java.util.GregorianCalendar;

public class SolarAlarmReceiver extends BroadcastReceiver {

    static final String ACTION      = "com.dumitriualxlang.solardasboard.SOLAR_CHECK";
    static final String CHANNEL_ID  = "solar_alerts";
    static final String PREFS       = "SolarDashboard";
    static final int    INTERVAL_MS = 30 * 60 * 1000;

    public static void schedule(Context ctx) {
        AlarmManager am = (AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        PendingIntent pi = getPendingIntent(ctx);
        long triggerAt = System.currentTimeMillis() + INTERVAL_MS;
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (am.canScheduleExactAlarms()) {
                    am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
                } else {
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
                }
            } else {
                am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
            }
            android.util.Log.d("SolarAlarm", "Next check in 30 min");
        } catch (Exception e) {
            android.util.Log.e("SolarAlarm", "Failed to schedule: " + e.getMessage());
        }
    }

    private static PendingIntent getPendingIntent(Context ctx) {
        Intent intent = new Intent(ctx, SolarAlarmReceiver.class).setAction(ACTION);
        return PendingIntent.getBroadcast(ctx, 1001, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    @Override
    public void onReceive(Context ctx, Intent intent) {
        android.util.Log.d("SolarAlarm", "Alarm fired: " + intent.getAction());
        // Always restart the foreground service — it may have been killed by Samsung
        // battery optimisation. Starting an already-running service is a no-op.
        try { SolarForegroundService.start(ctx); } catch (Exception e) {
            // On Android 12+, starting FGS from background may be restricted
            // Schedule via WorkManager as fallback
            android.util.Log.w("SolarAlarm", "FGS start restricted: " + e.getMessage());
            try {
                androidx.work.OneTimeWorkRequest wr =
                    new androidx.work.OneTimeWorkRequest.Builder(SolarWorker.class).build();
                androidx.work.WorkManager.getInstance(ctx).enqueue(wr);
            } catch (Exception ignored) {}
        }

        // RESTART_FGS action is only for reviving the service — no solar check needed
        if ("com.dumitriualxlang.solardasboard.RESTART_FGS".equals(intent.getAction())) {
            android.util.Log.d("SolarAlarm", "FGS restart triggered");
            return;
        }

        createChannel(ctx);
        // ARCHITECTURE: FGS is now the single source of truth for SOC computation.
        // Previously SAR ran its own doSolarCheck on a goAsync thread, racing with
        // the FGS check that we just kicked off. Both wrote to "soc" pref -
        // last write wins, sometimes overwriting the more accurate value.
        //
        // We only fall back to running our own check if FGS start failed AND
        // WorkManager fallback also failed.
        schedule(ctx);  // reschedule next 30-min alarm before we return
    }

    private void doSolarCheck(Context ctx) {
        SharedPreferences prefs = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long nowMs     = System.currentTimeMillis();
        long lastRunMs = prefs.getLong("last_alarm_run_ms", nowMs);
        double dtH     = (nowMs - lastRunMs) / 3600000.0;
        if (dtH <= 0 || dtH > 1.0) dtH = 0.5;
        prefs.edit().putLong("last_alarm_run_ms", nowMs).apply();

        float soc       = prefs.getFloat("soc",        -1f);
        float panelKw   = prefs.getFloat("panel_kw",    0f);
        float battGross = prefs.getFloat("batt_gross",  0f);
        float battRes   = prefs.getFloat("batt_res",    0.1f);
        float consKw    = prefs.getFloat("cons_kw",     0f);
        float battMaxC  = prefs.getFloat("batt_max_c",  2.5f);
        float battMaxD  = prefs.getFloat("batt_max_d",  2.5f);
        // PANEL LOCATION LOCK: prefer the user-set panel coords over phone GPS.
        float lat       = prefs.getFloat("panel_lat",  0f);
        float lon       = prefs.getFloat("panel_lon",  0f);
        if (lat == 0f || lon == 0f) {
            lat = prefs.getFloat("gps_lat", 0f);
            lon = prefs.getFloat("gps_lon", 0f);
        }
        if (panelKw <= 0 || battGross <= 0) return;
        if (soc < 0) soc = 50f;

        if (lat == 0f || lon == 0f) {
            try {
                android.location.LocationManager lm = (android.location.LocationManager)
                    ctx.getSystemService(Context.LOCATION_SERVICE);
                if (lm != null) {
                    android.location.Location loc =
                        lm.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
                    if (loc == null) loc = lm.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER);
                    if (loc == null) loc = lm.getLastKnownLocation(android.location.LocationManager.PASSIVE_PROVIDER);
                    if (loc != null) {
                        lat = (float) loc.getLatitude();
                        lon = (float) loc.getLongitude();
                        prefs.edit().putFloat("gps_lat", lat).putFloat("gps_lon", lon).apply();
                    }
                }
            } catch (Exception e) { /* no permission */ }
        }
        if (lat == 0f || lon == 0f) { android.util.Log.w("SolarAlarm", "No GPS"); return; }

        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude=" + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = httpGet(url);
        boolean hasWx = raw != null && !raw.startsWith("ERR");
        if (!hasWx) android.util.Log.w("SolarAlarm", "Weather unavailable — SOC evolves with last pvKw");

        double pvKw = prefs.getFloat("pv_kw", 0f); // use last known; overwritten if fetch succeeds
        double gridImport = 0, gridExport = 0, battFlow = 0;
        double newSoc = soc;

        try {
            if (hasWx) {
            JSONObject cur = new JSONObject(raw).getJSONObject("current");
            double directRad  = cur.optDouble("direct_radiation",  0);
            double diffuseRad = cur.optDouble("diffuse_radiation", 0);
            double tempC      = cur.optDouble("temperature_2m", 25);

            // Solar position
            Calendar cal = Calendar.getInstance();
            long dayOfYear = (nowMs - new GregorianCalendar(cal.get(Calendar.YEAR), 0, 1).getTimeInMillis()) / 86400000L;
            double utcH  = cal.get(Calendar.HOUR_OF_DAY) + cal.get(Calendar.MINUTE) / 60.0
                         + cal.get(Calendar.SECOND) / 3600.0 - cal.getTimeZone().getOffset(nowMs) / 3600000.0;
            double decl  = 23.45 * Math.sin((360.0 / 365.0 * (dayOfYear - 81)) * Math.PI / 180.0);
            double ha    = (utcH - 12) * 15 + lon;
            double latR  = lat * Math.PI / 180.0, decR = decl * Math.PI / 180.0;
            double sinAlt = Math.sin(latR) * Math.sin(decR) + Math.cos(latR) * Math.cos(decR) * Math.cos(ha * Math.PI / 180.0);
            double alt   = Math.asin(Math.max(-1, Math.min(1, sinAlt))) * 180.0 / Math.PI;

            double solAzDeg = 180.0;
            if (alt > 0) {
                double sinAz = Math.cos(decR) * Math.sin(ha * Math.PI/180.0)
                    / Math.max(0.001, Math.cos(alt * Math.PI/180.0));
                solAzDeg = Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, sinAz))));
                if (ha > 0) solAzDeg = 180.0 - solAzDeg;
                else        solAzDeg = 180.0 + solAzDeg;
            }

            // Calibrated solar model
            if (alt > 2.0) {
                float  panelAz  = prefs.getFloat("panel_azimuth", 180f);
                double tiltR    = 30.0 * Math.PI / 180.0;
                double altR     = alt      * Math.PI / 180.0;
                double solAzR   = solAzDeg * Math.PI / 180.0;
                double pnlAzR   = panelAz  * Math.PI / 180.0;
                double cosAOI   = Math.sin(altR) * Math.cos(tiltR)
                                + Math.cos(altR) * Math.sin(tiltR) * Math.cos(solAzR - pnlAzR);
                double poaBeam  = Math.max(0, cosAOI) * Math.max(0, directRad);
                double poaSky   = Math.max(0, diffuseRad) * (1 + Math.cos(tiltR)) / 2.0;
                double poaGnd   = (directRad + diffuseRad) * 0.20 * (1 - Math.cos(tiltR)) / 2.0;
                double poa_in   = poaBeam + poaSky + poaGnd;
                double cellT  = tempC + (45.0 - 20.0) * (poa_in / 800.0);
                double tFac   = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
                float calib = prefs.getFloat("pv_calib_factor", 1.0f);
                pvKw = Math.max(0, Math.min(panelKw * 0.984, (poa_in / 1000.0) * panelKw * 0.984 * tFac)) * calib;
            } else {
                pvKw = 0; // sun below horizon
            }
            } // end if(hasWx)

            // Energy flow
            double battUse = battGross > 0 ? battGross * (1.0 - battRes) : 4.5;
            double hardFlr = 0.0, rampTop = 2.0;
            double s2h = Math.min(pvKw, consKw), pvS = pvKw - s2h, hD = consKw - s2h;
            double bC  = soc < 100 ? Math.min(pvS, battMaxC) : 0;
            double bD;
            if      (soc <= hardFlr) bD = 0;
            else if (soc <= rampTop) { double f = (soc - hardFlr) / rampTop; bD = Math.min(hD * f, battMaxD); }
            else                     bD = Math.min(hD, battMaxD);
            battFlow   = bC - bD;
            gridExport = Math.max(0, pvS - bC);
            gridImport = Math.max(0, hD - bD);

            // Evolve SOC with Huawei Luna 2000 efficiency
            double battEff = 0.95;
            double effFlow = battFlow > 0 ? battFlow * battEff : battFlow; // discharge: no penalty
            newSoc = soc + (effFlow / battUse) * dtH * 100.0;
            newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

            // Persist
            Calendar nowCalAR = Calendar.getInstance();
            int arm = nowCalAR.get(Calendar.MONTH)+1, ard = nowCalAR.get(Calendar.DAY_OF_MONTH);
            String todayStr = nowCalAR.get(Calendar.YEAR)
                + "-" + (arm<10?"0":"") + arm + "-" + (ard<10?"0":"") + ard;
            String lastDate = prefs.getString("grid_date", "");
            float prevExp = lastDate.equals(todayStr) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
            float prevImp = lastDate.equals(todayStr) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
            float prevPv  = lastDate.equals(todayStr) ? prefs.getFloat("pv_kwh",          0f) : 0f;
            prefs.edit()
                 .putFloat("soc",            (float) newSoc)
                 .putFloat("pv_kw",          (float) pvKw)
                 .putFloat("grid_export_kwh", prevExp + (float) gridExport * (float) dtH)
                 .putFloat("grid_import_kwh", prevImp + (float) gridImport * (float) dtH)
                 .putFloat("pv_kwh",          prevPv  + (float) pvKw       * (float) dtH)
                 .putString("grid_date",      todayStr)
                 .putLong("soc_saved_at_ms",  nowMs)
                 .apply();

            android.util.Log.d("SolarAlarm", String.format(
                "dtH=%.2fh pv=%.2f soc %.1f->%.1f grid_in=%.2f batt=%.2f", dtH, pvKw, (double)soc, newSoc, gridImport, battFlow));

            // Notifications
            boolean notifEnabled;
            try { notifEnabled = ((NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE)).areNotificationsEnabled(); }
            catch (Exception e) { notifEnabled = true; }
            if (!notifEnabled) return;

            // Quiet hours: no notifications 22:00-08:00
            int hourNow = nowCalAR.get(Calendar.HOUR_OF_DAY);
            if (hourNow >= 8 && hourNow < 22) {
                long lHigh    = prefs.getLong("notif_last_high",     0);
                long lLow     = prefs.getLong("notif_last_low",      0);
                long lEve     = prefs.getLong("notif_last_eve",      0);
                long lBattLo  = prefs.getLong("notif_last_batt_low", 0);
                long lHighC   = prefs.getLong("notif_last_high_cons",0);
                long lMorning = prefs.getLong("notif_last_morning",  0);
                long now30M   = 30L * 60 * 1000, now1H = 60L * 60 * 1000, now2H = 2L * 60 * 60 * 1000, now12H = 12L * 60 * 60 * 1000;
                double surplus   = pvKw - (double) consKw;
                double storedKwh = battUse * (newSoc / 100.0);
                double dispSoc   = 10.0 + (newSoc / 100.0) * 90.0;
                if (surplus >= 2.0 && (nowMs - lHigh) > now1H) {
                    sendNotif(ctx, "Solar surplus — run large appliances",
                        String.format("+%.1f kW surplus. Battery: %.0f%%.", surplus, dispSoc));
                    prefs.edit().putLong("notif_last_high", nowMs).apply();
                } else if (pvKw <= 0.20 && consKw > 0.1 && hourNow >= 16 && (nowMs - lLow) > now2H) {
                    sendNotif(ctx, "Solar ended for today",
                        String.format("Production ended. Battery at %.0f%%. ~%.1fh backup remaining.", dispSoc, storedKwh / Math.max(0.01, consKw)));
                    prefs.edit().putLong("notif_last_low", nowMs).apply();
                } else if (hourNow == 20 && pvKw > 0.20 && (nowMs - lEve) > now2H) {
                    sendNotif(ctx, "Good solar today",
                        String.format("Still %.1f kW. Battery %.0f%%.", pvKw, dispSoc));
                    prefs.edit().putLong("notif_last_eve", nowMs).apply();
                }
                if (storedKwh < battUse * 0.15 && dispSoc < 20.0 && (nowMs - lBattLo) > now2H) {
                    sendNotif(ctx, "Battery low — grid activating",
                        String.format("Battery %.0f%% — reserve approaching.", dispSoc));
                    prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
                }
                if (hourNow >= 7 && hourNow <= 11 && pvKw > 0.5 && (nowMs - lMorning) > now12H) {
                    boolean socConfirmed = prefs.getBoolean("soc_confirmed", false);
                    String battStr = socConfirmed
                        ? String.format(" Battery at %.0f%%.", dispSoc) : "";
                    sendNotif(ctx, "Good morning — solar production started",
                        String.format("Panels producing %.1f kW.", pvKw) + battStr);
                    prefs.edit().putLong("notif_last_morning", nowMs).apply();
                }
                if (gridImport > 1.0 && battFlow < -0.2 && (nowMs - lHighC) > now2H) {
                    sendNotif(ctx, "High consumption — grid + battery active",
                        String.format("Grid %.1f kW + battery %.1f kW. Battery %.0f%%.", gridImport, Math.abs(battFlow), dispSoc));
                    prefs.edit().putLong("notif_last_high_cons", nowMs).apply();
                }
            }
                // Rule 7: Production drop — notify to pause large appliances
                float lastPvKw = prefs.getFloat("last_notif_pv_kw", -1f);
                prefs.edit().putFloat("last_notif_pv_kw", (float) pvKw).commit();
                if (lastPvKw >= 1.5f && pvKw < 1.5f && (lastPvKw - (float) pvKw) > 1.0f
                        && hourNow >= 8 && hourNow < 22
                        && (nowMs - prefs.getLong("notif_last_drop", 0L)) > 30L * 60 * 1000) {
                    prefs.edit().putLong("notif_last_drop", nowMs).apply();
                    sendNotif(ctx, "☁️ Solar dropped — pause large appliances",
                        String.format("Production fell from %.2f kW to %.2f kW. Pause high-load appliances.", lastPvKw, (float) pvKw));
                }


        } catch (Exception e) {
            android.util.Log.e("SolarAlarm", "doSolarCheck error: " + e.getMessage());
        }
    }

    private void sendNotif(Context ctx, String title, String body) {
        // No-op: SolarForegroundService is the single source of truth for notifications.
        // Previously this raced with the FGS to update the shared notification ID 999,
        // causing inconsistent SOC values in consecutive notifications.
        android.util.Log.d("SolarAlarm", "sendNotif suppressed (FGS handles it): " + title);
    }

    private void createChannel(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm != null && nm.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel ch = new NotificationChannel(CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
                ch.setLightColor(Color.parseColor("#1D9E75")); ch.enableLights(true); ch.enableVibration(true);
                nm.createNotificationChannel(ch);
            }
        }
    }

    private String httpGet(String urlStr) {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(15000);
            c.setRequestProperty("User-Agent", "SolarDashboard/1.0");
            if (c.getResponseCode() == 200) {
                BufferedReader br = new BufferedReader(new InputStreamReader(c.getInputStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder(); String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close(); c.disconnect(); return sb.toString();
            }
            c.disconnect(); return "ERR_HTTP_" + c.getResponseCode();
        } catch (Exception e) { return "ERR_" + e.getMessage(); }
    }
}""")


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "BootReceiver.java"), """package com.dumitriualxlang.solardasboard;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import java.util.concurrent.TimeUnit;

// Reschedules SolarWorker after device reboot or app update.
// Samsung and other OEMs may kill WorkManager state on reboot —
// this ensures the background solar monitoring always restarts.
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (action == null) return;
        if (!action.equals(Intent.ACTION_BOOT_COMPLETED)
            && !action.equals(Intent.ACTION_MY_PACKAGE_REPLACED)) return;

        android.util.Log.d("BootReceiver", "Received: " + action + " — restarting solar background");
        // Start the foreground service first — most reliable on Samsung
        SolarForegroundService.start(context);
        try {
            // NO network constraint — worker handles offline gracefully (SOC evolution
            // still works without internet; weather fetch skipped if no connection).
            // CONNECTED constraint caused complete overnight failure when Samsung
            // turns off WiFi to save battery during sleep.
            PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(
                SolarWorker.class, 30, TimeUnit.MINUTES)
                .build();
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                "solar_background",
                ExistingPeriodicWorkPolicy.UPDATE,
                work);
            // Also reschedule AlarmManager chain — most reliable on Samsung
            SolarAlarmReceiver.schedule(context);
        } catch (Exception e) {
            android.util.Log.e("BootReceiver", "Failed to schedule worker: " + e.getMessage());
        }
    }
}
""")


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarWorker.java"), """package com.dumitriualxlang.solardasboard;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Calendar;
import java.util.GregorianCalendar;

public class SolarWorker extends Worker {
    private static final String CHANNEL_ID = "solar_alerts";
    private static final String PREFS      = "SolarDashboard";

    public SolarWorker(@NonNull Context ctx, @NonNull WorkerParameters p) {
        super(ctx, p);
    }

    @NonNull @Override
    public Result doWork() {
        Context ctx = getApplicationContext();
        createChannel(ctx);
        // Failover: revive FGS if killed by Samsung battery optimizer
        try { SolarForegroundService.start(ctx); } catch (Exception e) {}

        SharedPreferences prefs = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);

        // ── Elapsed time since last worker run ───────────────────────────────
        // This is the key: we know exactly how many hours passed and can evolve
        // SOC accordingly even while the app is fully closed.
        long nowMs     = System.currentTimeMillis();
        long lastRunMs = prefs.getLong("last_worker_run_ms", nowMs);
        double dtH     = (nowMs - lastRunMs) / 3600000.0;
        // Cap elapsed time at 1 hour to avoid huge SOC jumps after long gaps,
        // phone restarts, or first run. WorkManager fires every 30 min so
        // normally dtH will be 0.4–0.6h.
        if (dtH <= 0 || dtH > 1.0) dtH = 0.5;
        prefs.edit().putLong("last_worker_run_ms", nowMs).apply();

        // ── Read all system config from SharedPreferences ────────────────────
        float soc       = prefs.getFloat("soc",        50f);
        float panelKw   = prefs.getFloat("panel_kw",    5f);
        float battGross = prefs.getFloat("batt_gross",  0f);
        float battRes   = prefs.getFloat("batt_res",    0.1f);
        float consKw    = prefs.getFloat("cons_kw",     0f);
        float battMaxC  = prefs.getFloat("batt_max_c",  2.5f);
        float battMaxD  = prefs.getFloat("batt_max_d",  2.5f);
        // PANEL LOCATION LOCK: prefer the user-set panel coords over phone GPS.
        float lat       = prefs.getFloat("panel_lat",  0f);
        float lon       = prefs.getFloat("panel_lon",  0f);
        if (lat == 0f || lon == 0f) {
            lat = prefs.getFloat("gps_lat", 0f);
            lon = prefs.getFloat("gps_lon", 0f);
        }

        // ── GPS fallback via LocationManager ────────────────────────────────
        if (lat == 0f || lon == 0f) {
            try {
                android.location.LocationManager lm = (android.location.LocationManager)
                    ctx.getSystemService(Context.LOCATION_SERVICE);
                if (lm != null) {
                    android.location.Location loc =
                        lm.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
                    if (loc == null)
                        loc = lm.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER);
                    if (loc == null)
                        loc = lm.getLastKnownLocation(android.location.LocationManager.PASSIVE_PROVIDER);
                    if (loc != null) {
                        lat = (float) loc.getLatitude();
                        lon = (float) loc.getLongitude();
                        // Persist so next run has it immediately
                        prefs.edit().putFloat("gps_lat", lat).putFloat("gps_lon", lon).apply();
                    }
                }
            } catch (Exception e) { /* no location permission */ }
        }

        // Still no GPS — cannot calculate production, skip this run
        if (lat == 0f || lon == 0f) return Result.retry();

        // ── Fetch current weather from Open-Meteo (skip if offline) ──────────
        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude="  + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = null;
        try {
            android.net.ConnectivityManager cm = (android.net.ConnectivityManager)
                ctx.getSystemService(Context.CONNECTIVITY_SERVICE);
            android.net.NetworkInfo ni = cm != null ? cm.getActiveNetworkInfo() : null;
            if (ni != null && ni.isConnected()) {
                raw = httpGet(url);
            }
        } catch (Exception e) { /* ignore connectivity check errors */ }
        // If offline or fetch failed — still do SOC evolution below, just skip pvKw calc
        boolean hasWeather = raw != null && !raw.startsWith("ERR");

        double pvKw = hasWeather ? 0 : prefs.getFloat("pv_kw", 0f);
        if (hasWeather) try {
            JSONObject d   = new JSONObject(raw);
            JSONObject cur = d.getJSONObject("current");
            double directRad  = cur.optDouble("direct_radiation",  0);
            double diffuseRad = cur.optDouble("diffuse_radiation", 0);
            double swr        = cur.optDouble("shortwave_radiation", directRad + diffuseRad);
            double tempC      = cur.optDouble("temperature_2m", 25);
            double cloud      = cur.optDouble("cloud_cover", 0);

            // ── Solar position ────────────────────────────────────────────────
            // Uses the same algorithm as the JS solarPosition() function
            Calendar cal = Calendar.getInstance();
            long dayOfYear = (nowMs - new java.util.GregorianCalendar(
                cal.get(Calendar.YEAR), 0, 1).getTimeInMillis()) / 86400000L;
            double utcH   = cal.get(Calendar.HOUR_OF_DAY)
                          + cal.get(Calendar.MINUTE) / 60.0
                          + cal.get(Calendar.SECOND) / 3600.0
                          - cal.getTimeZone().getOffset(nowMs) / 3600000.0;
            double decl   = 23.45 * Math.sin((360.0 / 365.0 * (dayOfYear - 81)) * Math.PI / 180.0);
            double ha     = (utcH - 12) * 15 + lon;
            double latR   = lat  * Math.PI / 180.0;
            double decR   = decl * Math.PI / 180.0;
            double haR    = ha   * Math.PI / 180.0;
            double sinAlt = Math.sin(latR) * Math.sin(decR)
                          + Math.cos(latR) * Math.cos(decR) * Math.cos(haR);
            double alt    = Math.asin(Math.max(-1, Math.min(1, sinAlt))) * 180.0 / Math.PI;

                // Solar azimuth (degrees from North, clockwise)
            double solAzDeg = 180.0;
            if (alt > 0) {
                double sinAz = Math.cos(decR) * Math.sin(ha * Math.PI/180.0)
                    / Math.max(0.001, Math.cos(alt * Math.PI/180.0));
                solAzDeg = Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, sinAz))));
                if (ha > 0) solAzDeg = 180.0 - solAzDeg;
                else        solAzDeg = 180.0 + solAzDeg;
            }

            // Night or sun below horizon — production is zero
            if (alt > 2.0) {
            // Calibrated model: direct*0.9 + diffuse (validated vs FusionSolar ±5%)
            // Panel orientation-aware POA (matches JS calcPOA() exactly)
                float  panelAz  = prefs.getFloat("panel_azimuth", 180f);
                double tiltR    = 30.0 * Math.PI / 180.0;
                double altR     = alt       * Math.PI / 180.0;
                double solAzR   = solAzDeg  * Math.PI / 180.0;
                double pnlAzR   = panelAz   * Math.PI / 180.0;
                double cosAOI   = Math.sin(altR) * Math.cos(tiltR)
                                + Math.cos(altR) * Math.sin(tiltR) * Math.cos(solAzR - pnlAzR);
                double poaBeam  = Math.max(0, cosAOI) * Math.max(0, directRad);
                double poaSky   = Math.max(0, diffuseRad) * (1 + Math.cos(tiltR)) / 2.0;
                double poaGnd   = (directRad + diffuseRad) * 0.20 * (1 - Math.cos(tiltR)) / 2.0;
                double poa_in   = poaBeam + poaSky + poaGnd;
            double cellT  = tempC + (45.0 - 20.0) * (poa_in / 800.0);
            double tFac   = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
            float calib = prefs.getFloat("pv_calib_factor", 1.0f);
            pvKw = Math.max(0, Math.min(panelKw * 0.984,
                (poa_in / 1000.0) * panelKw * 0.984 * tFac)) * calib;
        }

        // ── Energy flow model (mirrors JS calcFlow) ──────────────────────────
        // Priority: Solar → Home → Battery → Grid
        // Internal SOC scale: 0% = display floor (10%), 100% = display ceiling (90%)
        // hardFlr=0 internal = display 10% reserve — discharge stops here
        // rampTop=2 internal = display ~11.6% — full discharge rate above this
        double hardFlr = 0.0;
        double rampTop = 2.0;
        double battUse = battGross > 0 ? battGross * (1.0 - battRes) : 4.5;

        double s2h  = Math.min(pvKw, consKw);
        double pvS  = pvKw  - s2h;
        double hD   = consKw - s2h;

        // Battery charge — from solar surplus only, never from grid
        double bC = soc < 100 ? Math.min(pvS, battMaxC) : 0;

        // Battery discharge — mirrors JS calcFlow()
        double bD;
        if      (soc <= hardFlr) bD = 0;
        else if (soc <= rampTop) { double frac=(soc-hardFlr)/rampTop; bD=Math.min(hD*frac,battMaxD); }
        else                     bD = Math.min(hD, battMaxD);

        double battFlow  = bC - bD;
        double gridExport = Math.max(0, pvS - bC);
        double gridImport = Math.max(0, hD - bD);

        // ── Evolve SOC over elapsed time ─────────────────────────────────────
        // Battery round-trip efficiency: Huawei Luna 2000 = 0.92
        double battEff = 0.95;
        double effFlow = battFlow > 0 ? battFlow * battEff : battFlow; // discharge: no penalty
        double newSoc = soc + (effFlow / battUse) * dtH * 100.0;
        newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

        // ── Persist evolved state back to SharedPreferences ──────────────────
        // JS reads these on resume via applyStateFromNative / injectLocation
        Calendar calSW = Calendar.getInstance();
        int swm = calSW.get(Calendar.MONTH)+1, swd = calSW.get(Calendar.DAY_OF_MONTH);
        String todaySW = calSW.get(Calendar.YEAR)
            + "-" + (swm<10?"0":"") + swm + "-" + (swd<10?"0":"") + swd;
        String lastDateSW = prefs.getString("grid_date", "");
        float prevExpSW = lastDateSW.equals(todaySW) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
        float prevImpSW = lastDateSW.equals(todaySW) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
        float prevPvSW  = lastDateSW.equals(todaySW) ? prefs.getFloat("pv_kwh",          0f) : 0f;
        prefs.edit()
            .putFloat("soc",            (float) newSoc)
            .putFloat("pv_kw",          (float) pvKw)
            .putFloat("grid_export_kwh", prevExpSW + (float) gridExport * (float) dtH)
            .putFloat("grid_import_kwh", prevImpSW + (float) gridImport * (float) dtH)
            .putFloat("pv_kwh",          prevPvSW  + (float) pvKw       * (float) dtH)
            .putString("grid_date",      todaySW)
            .putLong("soc_saved_at_ms",  nowMs)
            .apply();

        android.util.Log.d("SolarWorker",
            String.format("dtH=%.2fh pvKw=%.2f soc %.1f->%.1f battFlow=%.3f",
                dtH, pvKw, (double) soc, newSoc, battFlow));

        
            // ── Quiet hours: no notifications 22:00–08:00 ────────────────────
            int hourNow = calSW.get(Calendar.HOUR_OF_DAY);
            if (hourNow >= 8 && hourNow < 22) {
                // Shared throttle keys — all services read/write the same keys
                // so no duplicate or missed notifications across FGS/AR/Worker
                long lHigh    = prefs.getLong("notif_last_high",     0);
                long lLow     = prefs.getLong("notif_last_low",      0);
                long lEve     = prefs.getLong("notif_last_eve",      0);
                long lBattLo  = prefs.getLong("notif_last_batt_low", 0);
                long lHighC   = prefs.getLong("notif_last_high_cons",0);
                long lMorning = prefs.getLong("notif_last_morning",  0);
                long now30M   = 30L * 60 * 1000;
                long now1H    = 60L * 60 * 1000;
                long now2H    = 2L * 60 * 60 * 1000;
                long now12H   = 12L * 60 * 60 * 1000;
                double surplus   = pvKw - (double) consKw;
                double storedKwh = battUse * (newSoc / 100.0);
                double dispSoc   = 10.0 + (newSoc / 100.0) * 90.0;

                // Rule 1: Solar surplus ≥ 2kW — run appliances
                if (surplus >= 2.0 && (nowMs - lHigh) > now1H) {
                    sendNotif(ctx, "Solar surplus — run large appliances",
                        String.format("+%.1f kW surplus. Good time to run washing machine, dishwasher or water heater. Battery: %.0f%%.", surplus, dispSoc));
                    prefs.edit().putLong("notif_last_high", nowMs).apply();

                // Rule 2: Solar ended — pvKw dropped to ≤ 0.20 kW after 16:00
                } else if (pvKw <= 0.20 && consKw > 0.1 && hourNow >= 16 && (nowMs - lLow) > now2H) {
                    double bkp = storedKwh / Math.max(0.01, (double) consKw);
                    sendNotif(ctx, "Solar ended for today",
                        String.format("Production ended. Battery at %.0f%%. ~%.1fh backup remaining.", dispSoc, bkp));
                    prefs.edit().putLong("notif_last_low", nowMs).apply();

                // Rule 3: Evening summary at 20:00 if solar still running
                } else if (hourNow == 20 && pvKw > 0.20 && (nowMs - lEve) > now2H) {
                    sendNotif(ctx, "Good solar today",
                        String.format("Still producing %.1f kW. Battery %.0f%%. Plan appliances for tomorrow mid-day.", pvKw, dispSoc));
                    prefs.edit().putLong("notif_last_eve", nowMs).apply();
                }

                // Rule 4: Battery low
                if (storedKwh < battUse * 0.15 && dispSoc < 20.0 && (nowMs - lBattLo) > now2H) {
                    sendNotif(ctx, "Battery low — grid activating",
                        String.format("Battery %.0f%% — reserve approaching. Grid activating. Solar: %.1f kW.", dispSoc, pvKw));
                    prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
                }

                // Rule 5: Morning production started (fires at first solar > 0.5kW after sunrise)
                // Only between 07:00–11:00, once per 12h
                if (hourNow >= 7 && hourNow <= 11 && pvKw > 0.5 && (nowMs - lMorning) > now12H) {
                    boolean socConfirmed = prefs.getBoolean("soc_confirmed", false);
                    String battStr = socConfirmed
                        ? String.format(" Battery at %.0f%%.", dispSoc) : "";
                    sendNotif(ctx, "Good morning — solar production started",
                        String.format("Panels producing %.1f kW.", pvKw) + battStr);
                    prefs.edit().putLong("notif_last_morning", nowMs).apply();
                }

                // Rule 6: High consumption — grid + battery both active
                if (gridImport > 1.0 && battFlow < -0.2 && (nowMs - lHighC) > now2H) {
                    sendNotif(ctx, "High consumption — grid + battery active",
                        String.format("Drawing %.1f kW from grid + %.1f kW battery. Solar %.1f kW. Battery %.0f%%.",
                            gridImport, Math.abs(battFlow), pvKw, dispSoc));
                    prefs.edit().putLong("notif_last_high_cons", nowMs).apply();
                }
            } // end quiet hours
                // Rule 7: Production drop — notify to pause large appliances
                float lastPvKw = prefs.getFloat("last_notif_pv_kw", -1f);
                prefs.edit().putFloat("last_notif_pv_kw", (float) pvKw).commit();
                if (lastPvKw >= 1.5f && pvKw < 1.5f && (lastPvKw - (float) pvKw) > 1.0f
                        && hourNow >= 8 && hourNow < 22
                        && (nowMs - prefs.getLong("notif_last_drop", 0L)) > 30L * 60 * 1000) {
                    prefs.edit().putLong("notif_last_drop", nowMs).apply();
                    sendNotif(ctx, "☁️ Solar dropped — pause large appliances",
                        String.format("Production fell from %.2f kW to %.2f kW. Pause high-load appliances.", lastPvKw, (float) pvKw));
                }


        } catch (Exception e) {
            android.util.Log.e("SolarWorker", "Error: " + e.getMessage());
        }
        return Result.success();
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private void sendNotif(Context ctx, String title, String body) {
        // No-op: SolarForegroundService is the single source of truth for notifications.
        // Previously this raced with FGS to update notification ID 999, causing
        // inconsistent SOC values in consecutive notifications.
        android.util.Log.d("SolarWorker", "sendNotif suppressed (FGS handles it): " + title);
    }

    private void createChannel(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                NotificationManager nm = (NotificationManager)
                    ctx.getSystemService(Context.NOTIFICATION_SERVICE);
                if (nm != null && nm.getNotificationChannel(CHANNEL_ID) == null) {
                    NotificationChannel ch = new NotificationChannel(
                        CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
                    ch.setDescription("Solar production and battery alerts");
                    ch.setLightColor(Color.parseColor("#1D9E75"));
                    ch.enableLights(true);
                    ch.enableVibration(true);
                    nm.createNotificationChannel(ch);
                }
            } catch (Exception e) {
                android.util.Log.e("SolarWorker", "createChannel: " + e.getMessage());
            }
        }
    }

    private String httpGet(String urlStr) {
        try {
            HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);
            conn.setRequestProperty("User-Agent", "SolarDashboard/1.0");
            if (conn.getResponseCode() == 200) {
                BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();
                conn.disconnect();
                return sb.toString();
            }
            conn.disconnect();
            return "ERR_HTTP_" + conn.getResponseCode();
        } catch (Exception e) {
            return "ERR_" + e.getMessage();
        }
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
        <domain includeSubdomains="true">satellite-api.open-meteo.com</domain>
        <domain includeSubdomains="true">dumitriualx-lang.github.io</domain>\n        <domain includeSubdomains=\"true\">nominatim.openstreetmap.org</domain>
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
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-all.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

print("All project files written OK")

# Icons embedded as base64
ICON_MASKABLE_B64 = "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"
ICON_ANY_B64      = "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"

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
