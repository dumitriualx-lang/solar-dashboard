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
    id 'com.android.application' version '8.3.0' apply true
}
android {
    namespace "%s"
    compileSdk 34
    defaultConfig {
        applicationId "%s"
        minSdk 21
        targetSdk 34
        versionCode 2
        versionName "1.0.1"
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
            android:exported="false"/>
        <service
            android:name=".SolarForegroundService"
            android:foregroundServiceType="dataSync"
            android:exported="false"/>
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
                    NotificationManagerCompat.from(MainActivity.this).notify(notifId++, b.build());
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
        public void saveSoc(float soc, float panelKw, float battGross, float battRes, float consKw, float battMaxC, float battMaxD) {
            getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE)
                .edit()
                .putFloat("soc",            soc)
                .putFloat("panel_kw",       panelKw)
                .putFloat("batt_gross",     battGross)
                .putFloat("batt_res",       battRes)
                .putFloat("cons_kw",        consKw)
                .putFloat("batt_max_c",     battMaxC)
                .putFloat("batt_max_d",     battMaxD)
                .putLong ("soc_saved_at_ms", System.currentTimeMillis())
                .apply();
        }

        @JavascriptInterface
        public String loadSoc() {
            android.content.SharedPreferences p =
                getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);
            float soc      = p.getFloat("soc",        -1f);
            float panelKw  = p.getFloat("panel_kw",    0f);
            float battGross= p.getFloat("batt_gross",  0f);
            float battRes  = p.getFloat("batt_res",    0f);
            float consKw     = p.getFloat("cons_kw",        0f);
            float gridExp    = p.getFloat("grid_export_kwh", 0f);
            float gridImp    = p.getFloat("grid_import_kwh", 0f);
            String gridDate  = p.getString("grid_date",       "");
            if (soc < 0) return "";
            return soc + "," + panelKw + "," + battGross + "," + battRes + "," + consKw
                 + "," + gridExp + "," + gridImp + "," + gridDate;
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
        // Require network so the worker doesn't run and fail silently offline.
        // UPDATE policy: keeps the existing schedule/run-count but ensures the
        // latest SolarWorker code is used. Safe to call on every app open.
        Constraints constraints = new Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build();
        PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(
            SolarWorker.class, 30, TimeUnit.MINUTES)
            .setConstraints(constraints)
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
        SolarForegroundService.start(this);   // Foreground Service — PRIMARY (Samsung-safe)
        requestBatteryOptimizationExemption();

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
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);

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
    }

    private void injectLocation() {
        android.content.SharedPreferences prefs =
            getSharedPreferences("SolarDashboard", android.content.Context.MODE_PRIVATE);

        // ── GPS ──────────────────────────────────────────────────────────────
        double gpsLat = 0, gpsLon = 0;
        String gpsName = "";
        try {
            // Try Android LocationManager first (most current, no dialog)
            android.location.LocationManager lm =
                (android.location.LocationManager) getSystemService(android.content.Context.LOCATION_SERVICE);
            android.location.Location loc = null;
            if (lm != null && checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                    == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                loc = lm.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
                if (loc == null)
                    loc = lm.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER);
                if (loc == null)
                    loc = lm.getLastKnownLocation(android.location.LocationManager.PASSIVE_PROVIDER);
            }
            if (loc != null) {
                gpsLat = loc.getLatitude();
                gpsLon = loc.getLongitude();
                // Persist for next time
                prefs.edit().putFloat("gps_lat", (float)gpsLat)
                            .putFloat("gps_lon", (float)gpsLon).apply();
            }
        } catch (Exception e) { /* fall through */ }

        // Fall back to SharedPreferences if LocationManager had no fix
        if (gpsLat == 0 && gpsLon == 0) {
            gpsLat  = prefs.getFloat("gps_lat", 0f);
            gpsLon  = prefs.getFloat("gps_lon", 0f);
            gpsName = prefs.getString("gps_name", "");
        }

        if (gpsLat != 0 && gpsLon != 0) {
            String safeN = gpsName.replace("'", "\'");
            webView.evaluateJavascript(
                "if(typeof applyGpsFromNative==='function')" +
                "applyGpsFromNative(" + gpsLat + "," + gpsLon + ",'" + safeN + "');", null);
        }

        // ── SOC & CONFIG ─────────────────────────────────────────────────────
        // Always inject — not conditional on GPS success
        float soc       = prefs.getFloat("soc",        -1f);
        float panelKw   = prefs.getFloat("panel_kw",    0f);
        float battGross = prefs.getFloat("batt_gross",  0f);
        float battRes   = prefs.getFloat("batt_res",    0f);
        float consKw    = prefs.getFloat("cons_kw",     0f);
        float bgPvKw    = prefs.getFloat("pv_kw",      -1f);

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

                    double s2h = Math.min(pvKwLast, consKw);
                    double pvS = pvKwLast - s2h;
                    double hD  = consKw - s2h;
                    double bC  = soc < 100 ? Math.min(pvS, battMaxC) : 0;
                    double bD;
                    if      (soc <= hardFlr) bD = 0;
                    else if (soc <= rampTop) { double frac=(soc-hardFlr)/rampTop; bD=Math.min(hD*frac,(double)battMaxD); }
                    else                     bD = Math.min(hD, (double) battMaxD);

                    double battFlow = bC - bD;
                    double battEff  = 0.95;
                    double effFlow  = battFlow > 0 ? battFlow * battEff : battFlow / battEff;
                    double newSoc   = soc + (effFlow / battUse) * elapsedH * 100.0;
                    newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

                    android.util.Log.d("MainActivity", String.format(
                        "SOC catch-up: %.1f min elapsed, pv=%.2fkW cons=%.2fkW flow=%.2fkW soc %.1f->%.1f",
                        elapsedH * 60, pvKwLast, (double) consKw, battFlow, (double) soc, newSoc));

                    prefs.edit()
                         .putFloat("soc", (float) newSoc)
                         .putLong("soc_saved_at_ms", System.currentTimeMillis())
                         .apply();
                    soc = (float) newSoc;
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





write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarForegroundService.java"), """package com.dumitriualxlang.solardashboard;

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
        startForeground(FG_NOTIF_ID, buildFgNotification("☀️ Solar monitoring active"));
        android.util.Log.d("SolarFGS", "Service created — starting 30-min check loop");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Schedule first check immediately, then every 30 min
        // If already scheduled, the handler dedup prevents double-running
        if (checker == null) {
            checker = new Runnable() {
                @Override public void run() {
                    try {
                        doSolarCheck();
                    } catch (Exception e) {
                        android.util.Log.e("SolarFGS", "Check error: " + e.getMessage());
                    }
                    // Re-schedule next run in 30 minutes — this is the self-chaining loop
                    handler.postDelayed(this, INTERVAL_MS);
                }
            };
            // First run after 5 seconds (let the service settle), then every 30 min
            handler.postDelayed(checker, 5000);
        }
        // START_STICKY: if the service is killed (rare), restart it automatically
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (handler != null && checker != null) {
            handler.removeCallbacks(checker);
        }
        android.util.Log.d("SolarFGS", "Service destroyed");
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
        float soc      = prefs.getFloat("soc",       50f);
        float panelKw  = prefs.getFloat("panel_kw",   5f);
        float battGross= prefs.getFloat("batt_gross", 0f);
        float battRes  = prefs.getFloat("batt_res",   0.1f);
        float consKw   = prefs.getFloat("cons_kw",    0f);
        float battMaxC = prefs.getFloat("batt_max_c", 2.5f);
        float battMaxD = prefs.getFloat("batt_max_d", 2.5f);
        float lat      = prefs.getFloat("gps_lat",    0f);
        float lon      = prefs.getFloat("gps_lon",    0f);

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

        // Fetch weather
        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude=" + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = httpGet(url);
        if (raw == null || raw.startsWith("ERR")) {
            android.util.Log.w("SolarFGS", "Weather fetch failed: " + raw);
            return;
        }

        double pvKw = 0;
        double gridImport = 0, battFlow = 0;
        double newSoc = soc;
        double battUse = battGross > 0 ? battGross * (1.0 - battRes) : 4.5;

        try {
            JSONObject cur = new JSONObject(raw).getJSONObject("current");
            double directRad  = cur.optDouble("direct_radiation",  0);
            double diffuseRad = cur.optDouble("diffuse_radiation", 0);
            double swr        = cur.optDouble("shortwave_radiation", directRad + diffuseRad);
            double tempC      = cur.optDouble("temperature_2m", 25);
            double cloud      = cur.optDouble("cloud_cover", 0);

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


            // ── Solar production (calibrated to Huawei SUN2000 real output) ─────
            // Uses direct_radiation + diffuse_radiation from Open-Meteo directly.
            // No POA geometric boost — the API irradiance is already measured;
            // the 0.9 factor on beam accounts for tilt, soiling, wiring combined.
            // Validated against FusionSolar live data (within ±5%).
            if (alt > 2.0) {
                double poa_in = directRad * 0.9 + diffuseRad;
                double cellT  = tempC + (45.0 - 20.0) * (poa_in / 800.0);
                double tFac   = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
                double acMax  = panelKw * 0.984;
                pvKw = Math.max(0, Math.min(acMax, (poa_in / 1000.0) * panelKw * 0.984 * tFac * 0.85));
            }


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
            double gridExport = Math.max(0, pvS - bC);

            // ── Evolve SOC ────────────────────────────────────────────────────
            // Battery round-trip efficiency 95%: charging stores less, discharging provides less
            double battEff = 0.95;
            double effFlow = battFlow > 0 ? battFlow * battEff : battFlow / battEff;
            newSoc = soc + (effFlow / battUse) * dtH * 100.0;
            newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

            // ── Persist all state for catch-up on next app open ───────────────

            // ── Accumulate grid kWh for today ────────────────────────────────
            java.util.Calendar calDate = java.util.Calendar.getInstance();
            String todayStr = calDate.get(java.util.Calendar.YEAR) + "-"
                + calDate.get(java.util.Calendar.DAY_OF_YEAR);
            String lastGridDate = prefs.getString("grid_date", "");
            float prevExp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
            float prevImp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
            float newExp  = prevExp + (float) gridExport * (float) dtH;
            float newImp  = prevImp + (float) gridImport * (float) dtH;
            prefs.edit()
                 .putFloat("soc",            (float) newSoc)
                 .putFloat("pv_kw",          (float) pvKw)
                 .putFloat("grid_export_kwh", newExp)
                 .putFloat("grid_import_kwh", newImp)
                 .putString("grid_date",      todayStr)
                 .putLong ("soc_saved_at_ms", nowMs)
                 .apply();

            // Update the foreground notification with live values
            String status = String.format("☀️ %.2fkW · 🏠 %.2fkW · 🔋 %.0f%%",
                pvKw, (double) consKw, newSoc);
            updateFgNotification(status);

            android.util.Log.d("SolarFGS", String.format(
                "dtH=%.2fh pv=%.2f cons=%.2f flow=%.3f soc %.1f→%.1f grid=%.2f",
                dtH, pvKw, (double)consKw, battFlow, (double)soc, newSoc, gridImport));

            // ── Notification rules ────────────────────────────────────────────
                        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            boolean notifOk = nm != null && nm.areNotificationsEnabled();
            if (!notifOk) return;
            // ── Quiet hours: no notifications 22:00–08:00 ──────────────────
            int hourNow = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
            if (hourNow < 22 && hourNow >= 8) {
                // Shared throttle keys across all background services
                long lHigh   = prefs.getLong("notif_last_high",     0);
                long lLow    = prefs.getLong("notif_last_low",      0);
                long lEve    = prefs.getLong("notif_last_eve",      0);
                long lBattLo = prefs.getLong("notif_last_batt_low", 0);
                long lHighC  = prefs.getLong("notif_last_high_cons",0);
                long now30M  = 30L*60*1000, now2H = 2L*60*60*1000;
                double surplus   = pvKw - consKw;
                double storedKwh = battUse * (newSoc / 100.0);
                double dispSoc   = 10.0 + (newSoc / 100.0) * 80.0;

                if (surplus >= 2.0 && (nowMs - lHigh) > now30M) {
                        sendAlert("Solar surplus — run large appliances",
                            String.format("+%.1f kW surplus. Good time to run washing machine, dishwasher or water heater. Battery: %.0f%%.", surplus, dispSoc));
                        prefs.edit().putLong("notif_last_high", nowMs).apply();
                } else if (pvKw < 0.2 && consKw > 0.1 && (nowMs - lLow) > now2H) {
                        double bkp = storedKwh / Math.max(0.01, consKw);
                        sendAlert("Running on battery",
                            String.format("Solar stopped (%.1f kW). Battery %.0f%% — ~%.1fh backup remaining.", pvKw, dispSoc, bkp));
                        prefs.edit().putLong("notif_last_low", nowMs).apply();
                } else if (hourNow == 20 && (nowMs - lEve) > now2H) {
                        if (surplus > 0.5)
                            sendAlert("Good solar conditions today",
                                    String.format("Still producing %.1f kW. Battery %.0f%%. Plan large appliances for tomorrow mid-day.", pvKw, dispSoc));
                        else
                            sendAlert("Solar ended for today",
                                    String.format("Production ended. Battery at %.0f%%. Check tomorrow's forecast in the app.", dispSoc));
                        prefs.edit().putLong("notif_last_eve", nowMs).apply();
                }
                if (storedKwh < battUse * 0.15 && dispSoc < 20.0 && (nowMs - lBattLo) > now2H) {
                        sendAlert("Battery low — grid starting",
                            String.format("Battery %.0f%% — reserve floor approaching. Grid activating. Solar: %.1f kW.", dispSoc, pvKw));
                        prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
                }
                if (gridImport > 1.0 && battFlow < -0.2 && (nowMs - lHighC) > now2H) {
                        sendAlert("High consumption — grid + battery active",
                            String.format("Drawing %.1f kW from grid + %.1f kW battery. Solar %.1f kW of %.1f kW load. Battery %.0f%%.",
                                    gridImport, Math.abs(battFlow), pvKw, (double) consKw, dispSoc));
                        prefs.edit().putLong("notif_last_high_cons", nowMs).apply();
                }
            } // end quiet hours

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

    private void sendAlert(String title, String body) {
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
            if (nm != null) nm.notify(alertNotifId++, nb.build());
            android.util.Log.d("SolarFGS", "Alert sent: " + title);
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


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarAlarmReceiver.java"), """package com.dumitriualxlang.solardashboard;

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

/**
 * AlarmManager-based solar background processor.
 *
 * Unlike WorkManager (which Samsung aggressively throttles), AlarmManager with
 * setExactAndAllowWhileIdle() fires even in Doze mode — the same mechanism
 * used by alarm clock apps that Samsung cannot block. This is how weather apps
 * and monitoring apps achieve reliable background notifications on Samsung.
 *
 * Each time it fires, it:
 *   1. Fetches current weather from Open-Meteo
 *   2. Calculates solar production + energy flow
 *   3. Evolves battery SOC over elapsed time
 *   4. Fires a notification if any rule matches
 *   5. Schedules the next alarm 30 minutes out
 */
public class SolarAlarmReceiver extends BroadcastReceiver {

    static final String ACTION      = "com.dumitriualxlang.solardashboard.SOLAR_CHECK";
    static final String CHANNEL_ID  = "solar_alerts";
    static final String PREFS       = "SolarDashboard";
    static final int    INTERVAL_MS = 30 * 60 * 1000;   // 30 minutes
    private static int  notifId     = 2000;

    // ── Schedule next alarm — called from MainActivity, BootReceiver, and self ─
    public static void schedule(Context ctx) {
        AlarmManager am = (AlarmManager) ctx.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        PendingIntent pi = getPendingIntent(ctx);

        long triggerAt = System.currentTimeMillis() + INTERVAL_MS;

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                // Android 12+ — check if we can schedule exact alarms
                if (am.canScheduleExactAlarms()) {
                    am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
                } else {
                    // Fall back to inexact — still fires in Doze, just not to-the-second
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
                }
            } else {
                am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
            }
            android.util.Log.d("SolarAlarm", "Next check in 30 min at " + new java.util.Date(triggerAt));
        } catch (Exception e) {
            android.util.Log.e("SolarAlarm", "Failed to schedule: " + e.getMessage());
        }
    }

    private static PendingIntent getPendingIntent(Context ctx) {
        Intent intent = new Intent(ctx, SolarAlarmReceiver.class).setAction(ACTION);
        return PendingIntent.getBroadcast(ctx, 1001, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    // ── Alarm fires — do the work, then re-schedule ───────────────────────────
    @Override
    public void onReceive(Context ctx, Intent intent) {
        android.util.Log.d("SolarAlarm", "Alarm fired — running solar check");
        createChannel(ctx);
        doSolarCheck(ctx);
        schedule(ctx);   // chain: schedule next alarm immediately after this one fires
    }

    // ── Core logic — identical model to SolarWorker ───────────────────────────
    private void doSolarCheck(Context ctx) {
        SharedPreferences prefs = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);

        // Elapsed time since last run
        long nowMs     = System.currentTimeMillis();
        long lastRunMs = prefs.getLong("last_alarm_run_ms", nowMs);
        double dtH     = (nowMs - lastRunMs) / 3600000.0;
        if (dtH <= 0 || dtH > 1.0) dtH = 0.5;
        prefs.edit().putLong("last_alarm_run_ms", nowMs).apply();

        // Read config
        float soc       = prefs.getFloat("soc",        50f);
        float panelKw   = prefs.getFloat("panel_kw",    5f);
        float battGross = prefs.getFloat("batt_gross",  0f);
        float battRes   = prefs.getFloat("batt_res",    0.1f);
        float consKw    = prefs.getFloat("cons_kw",     0f);
        float battMaxC  = prefs.getFloat("batt_max_c",  2.5f);
        float battMaxD  = prefs.getFloat("batt_max_d",  2.5f);
        float lat       = prefs.getFloat("gps_lat",     0f);
        float lon       = prefs.getFloat("gps_lon",     0f);

        // GPS fallback
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
                        prefs.edit().putFloat("gps_lat", lat).putFloat("gps_lon", lon).apply();
                    }
                }
            } catch (Exception e) { /* no permission */ }
        }
        if (lat == 0f || lon == 0f) {
            android.util.Log.w("SolarAlarm", "No GPS — skipping");
            return;
        }

        // Fetch weather
        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude=" + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = httpGet(url);
        if (raw == null || raw.startsWith("ERR")) {
            android.util.Log.w("SolarAlarm", "Weather fetch failed: " + raw);
            return;
        }

        double pvKw = 0;
        double gridImport = 0, gridExport = 0, battFlow = 0;
        double newSoc = soc;

        try {
            JSONObject cur = new JSONObject(raw).getJSONObject("current");
            double directRad  = cur.optDouble("direct_radiation",  0);
            double diffuseRad = cur.optDouble("diffuse_radiation", 0);
            double swr        = cur.optDouble("shortwave_radiation", directRad + diffuseRad);
            double tempC      = cur.optDouble("temperature_2m", 25);
            double cloud      = cur.optDouble("cloud_cover", 0);

            // Solar position
            Calendar cal = Calendar.getInstance();
            long dayOfYear = (nowMs - new GregorianCalendar(cal.get(Calendar.YEAR), 0, 1)
                .getTimeInMillis()) / 86400000L;
            double utcH  = cal.get(Calendar.HOUR_OF_DAY)
                         + cal.get(Calendar.MINUTE) / 60.0
                         + cal.get(Calendar.SECOND) / 3600.0
                         - cal.getTimeZone().getOffset(nowMs) / 3600000.0;
            double decl  = 23.45 * Math.sin((360.0/365.0*(dayOfYear-81)) * Math.PI/180.0);
            double ha    = (utcH - 12) * 15 + lon;
            double latR  = lat  * Math.PI/180.0;
            double decR  = decl * Math.PI/180.0;
            double sinAlt= Math.sin(latR)*Math.sin(decR)
                         + Math.cos(latR)*Math.cos(decR)*Math.cos(ha*Math.PI/180.0);
            double alt   = Math.asin(Math.max(-1,Math.min(1,sinAlt)))*180.0/Math.PI;

            
            // ── Solar production (calibrated to Huawei SUN2000 real output) ─────
            // Uses direct_radiation*0.9 + diffuse_radiation as effective irradiance.
            // Validated against FusionSolar live data (within ±5%). No POA boost.
            if (alt > 2.0) {
                double poa_in = directRad * 0.9 + diffuseRad;
                double cellT  = tempC + (45.0 - 20.0) * (poa_in / 800.0);
                double tFac   = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
                // 0.85 calibration factor validated against FusionSolar (2 real data points, within ±2%)
                pvKw = Math.max(0, Math.min(panelKw * 0.984, (poa_in / 1000.0) * panelKw * 0.984 * tFac * 0.85));
            }


            // Energy flow
            double battUse = battGross>0 ? battGross*(1.0-battRes) : 4.5;
            double hardFlr = 0.0;
            double rampTop = 2.0;
            double s2h = Math.min(pvKw,consKw), pvS=pvKw-s2h, hD=consKw-s2h;
            double bC  = soc<100 ? Math.min(pvS,battMaxC) : 0;
            double bD;
            if      (soc<=hardFlr)  bD=0;
            else if (soc<=rampTop)  { double f=(soc-hardFlr)/rampTop; bD=Math.min(hD*f,battMaxD); }
            else                    bD=Math.min(hD,battMaxD);
            battFlow  = bC-bD;
            gridExport= Math.max(0,pvS-bC);
            gridImport= Math.max(0,hD-bD);

            // Evolve SOC
            double battEff = 0.95;
            double effFlow = battFlow > 0 ? battFlow * battEff : battFlow / battEff;
            newSoc = soc + (effFlow/battUse)*dtH*100.0;
            newSoc = Math.max(hardFlr,Math.min(100.0,newSoc));

            // Persist evolved SOC + production + timestamp (used by catch-up in injectLocation)

            // ── Accumulate grid kWh for today ────────────────────────────────
            java.util.Calendar calDate = java.util.Calendar.getInstance();
            String todayStr = calDate.get(java.util.Calendar.YEAR) + "-"
                + calDate.get(java.util.Calendar.DAY_OF_YEAR);
            String lastGridDate = prefs.getString("grid_date", "");
            float prevExp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
            float prevImp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
            float newExp  = prevExp + (float) gridExport * (float) dtH;
            float newImp  = prevImp + (float) gridImport * (float) dtH;
            prefs.edit()
                 .putFloat("soc",    (float) newSoc)
                 .putFloat("pv_kw",  (float) pvKw)
                 .putLong("soc_saved_at_ms", nowMs)
                                  .putFloat("grid_export_kwh", newExp)
                 .putFloat("grid_import_kwh", newImp)
                 .putString("grid_date",       todayStr)
                 .apply();

            android.util.Log.d("SolarAlarm",
                String.format("dtH=%.2fh pv=%.2fkW soc %.1f->%.1f grid_in=%.2f batt=%.2f",
                    dtH,pvKw,(double)soc,newSoc,gridImport,battFlow));

            // Notification rules
            boolean notifEnabled;
            try { notifEnabled = ((NotificationManager)ctx.getSystemService(
                Context.NOTIFICATION_SERVICE)).areNotificationsEnabled(); }
            catch (Exception e) { notifEnabled = true; }
            if (!notifEnabled) return;
        // ── Quiet hours: no notifications 22:00–08:00 ──────────────────
        int hourNow = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        if (hourNow < 22 && hourNow >= 8) {
            long lHigh   = prefs.getLong("notif_last_high",     0);
            long lLow    = prefs.getLong("notif_last_low",      0);
            long lEve    = prefs.getLong("notif_last_eve",      0);
            long lBattLo = prefs.getLong("notif_last_batt_low", 0);
            long lHighC  = prefs.getLong("notif_last_high_cons",0);
            long now30M  = 30L*60*1000, now2H = 2L*60*60*1000;
            double surplus   = pvKw - consKw;
            double storedKwh = battUse * (newSoc / 100.0);
            double dispSoc   = 10.0 + (newSoc / 100.0) * 80.0;
            if (surplus >= 2.0 && (nowMs - lHigh) > now30M) {
                sendNotif(ctx, "Solar surplus — run large appliances",
                    String.format("+%.1f kW surplus. Good time to run washing machine, dishwasher or water heater. Battery: %.0f%%.", surplus, dispSoc));
                prefs.edit().putLong("notif_last_high", nowMs).apply();
            } else if (pvKw < 0.2 && consKw > 0.1 && (nowMs - lLow) > now2H) {
                double bkp = storedKwh / Math.max(0.01, consKw);
                sendNotif(ctx, "Running on battery",
                    String.format("Solar stopped (%.1f kW). Battery %.0f%% — ~%.1fh backup remaining.", pvKw, dispSoc, bkp));
                prefs.edit().putLong("notif_last_low", nowMs).apply();
            } else if (hourNow == 20 && (nowMs - lEve) > now2H) {
                if (surplus > 0.5)
                    sendNotif(ctx, "Good solar conditions today",
                        String.format("Still producing %.1f kW. Battery %.0f%%. Plan appliances for tomorrow mid-day.", pvKw, dispSoc));
                else
                    sendNotif(ctx, "Solar ended for today",
                        String.format("Production ended. Battery at %.0f%%. Check tomorrow's forecast in the app.", dispSoc));
                prefs.edit().putLong("notif_last_eve", nowMs).apply();
            }
            if (storedKwh < battUse * 0.15 && dispSoc < 20.0 && (nowMs - lBattLo) > now2H) {
                sendNotif(ctx, "Battery low — grid starting",
                    String.format("Battery %.0f%% — reserve approaching. Grid activating. Solar: %.1f kW.", dispSoc, pvKw));
                prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
            }
            if (gridImport > 1.0 && battFlow < -0.2 && (nowMs - lHighC) > now2H) {
                sendNotif(ctx, "High consumption — grid + battery active",
                    String.format("Drawing %.1f kW from grid + %.1f kW battery. Solar %.1f kW of %.1f kW. Battery %.0f%%.",
                        gridImport, Math.abs(battFlow), pvKw, (double) consKw, dispSoc));
                prefs.edit().putLong("notif_last_high_cons", nowMs).apply();
            }
        } // end quiet hours

        } catch (Exception e) {
            android.util.Log.e("SolarAlarm", "doSolarCheck error: " + e.getMessage());
        }
    }

    private void sendNotif(Context ctx, String title, String body) {
        try {
            Intent open = new Intent(ctx, MainActivity.class)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pi = PendingIntent.getActivity(ctx, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            NotificationCompat.Builder nb = new NotificationCompat.Builder(ctx, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title).setContentText(body)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setColor(Color.parseColor("#1D9E75"))
                .setContentIntent(pi);
            NotificationManager nm = (NotificationManager)
                ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm != null) nm.notify(notifId++, nb.build());
            android.util.Log.d("SolarAlarm", "Notification sent: " + title);
        } catch (Exception e) {
            android.util.Log.e("SolarAlarm", "sendNotif: " + e.getMessage());
        }
    }

    private void createChannel(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = (NotificationManager)
                ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm != null && nm.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel ch = new NotificationChannel(
                    CHANNEL_ID, "Solar Alerts", NotificationManager.IMPORTANCE_HIGH);
                ch.setDescription("Solar production and battery alerts");
                ch.setLightColor(Color.parseColor("#1D9E75"));
                ch.enableLights(true); ch.enableVibration(true);
                nm.createNotificationChannel(ch);
            }
        }
    }

    private String httpGet(String urlStr) {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(15000);
            c.setRequestProperty("User-Agent","SolarDashboard/1.0");
            if (c.getResponseCode()==200) {
                BufferedReader br = new BufferedReader(new InputStreamReader(c.getInputStream(),"UTF-8"));
                StringBuilder sb = new StringBuilder(); String line;
                while ((line=br.readLine())!=null) sb.append(line);
                br.close(); c.disconnect(); return sb.toString();
            }
            c.disconnect(); return "ERR_HTTP_"+c.getResponseCode();
        } catch (Exception e) { return "ERR_"+e.getMessage(); }
    }
}
""")


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "BootReceiver.java"), """package com.dumitriualxlang.solardashboard;

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
            Constraints constraints = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build();
            PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(
                SolarWorker.class, 30, TimeUnit.MINUTES)
                .setConstraints(constraints)
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


write(os.path.join(MAIN, "java", "com", "dumitriualxlang", "solardashboard", "SolarWorker.java"), """package com.dumitriualxlang.solardashboard;

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
    private static int notifId = 1000;

    public SolarWorker(@NonNull Context ctx, @NonNull WorkerParameters p) {
        super(ctx, p);
    }

    @NonNull @Override
    public Result doWork() {
        Context ctx = getApplicationContext();
        createChannel(ctx);

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
        float lat       = prefs.getFloat("gps_lat",     0f);
        float lon       = prefs.getFloat("gps_lon",     0f);

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

        // ── Fetch current weather from Open-Meteo ────────────────────────────
        String url = "https://api.open-meteo.com/v1/forecast?"
            + "latitude="  + lat + "&longitude=" + lon
            + "&current=temperature_2m,cloud_cover,shortwave_radiation,"
            + "direct_radiation,diffuse_radiation,direct_normal_irradiance"
            + "&timezone=auto";
        String raw = httpGet(url);
        if (raw == null || raw.startsWith("ERR")) return Result.retry();

        double pvKw = 0;
        try {
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

            // Night or sun below horizon — production is zero
            
            // ── Solar production (calibrated to Huawei SUN2000 real output) ─────
            // Uses direct_radiation*0.9 + diffuse_radiation as effective irradiance.
            // Validated against FusionSolar live data (within ±5%). No POA boost.
            if (alt > 2.0) {
                double poa_in = directRad * 0.9 + diffuseRad;
                double cellT  = tempC + (45.0 - 20.0) * (poa_in / 800.0);
                double tFac   = Math.max(0.80, 1.0 - Math.max(0, cellT - 25.0) * 0.0037);
                // 0.85 calibration factor validated against FusionSolar (2 real data points, within ±2%)
                pvKw = Math.max(0, Math.min(panelKw * 0.984, (poa_in / 1000.0) * panelKw * 0.984 * tFac * 0.85));
            }


        } catch (Exception e) {
            return Result.retry();
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
        // Battery round-trip efficiency 95%: charging stores less, discharging provides less
        double battEff = 0.95;
        double effFlow = battFlow > 0 ? battFlow * battEff : battFlow / battEff;
        double newSoc  = soc + (effFlow / battUse) * dtH * 100.0;
        newSoc = Math.max(hardFlr, Math.min(100.0, newSoc));

        // ── Persist evolved state back to SharedPreferences ──────────────────
        // JS reads these on resume via applyStateFromNative / injectLocation

            // ── Accumulate grid kWh for today ────────────────────────────────
            java.util.Calendar calDate = java.util.Calendar.getInstance();
            String todayStr = calDate.get(java.util.Calendar.YEAR) + "-"
                + calDate.get(java.util.Calendar.DAY_OF_YEAR);
            String lastGridDate = prefs.getString("grid_date", "");
            float prevExp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_export_kwh", 0f) : 0f;
            float prevImp = lastGridDate.equals(todayStr) ? prefs.getFloat("grid_import_kwh", 0f) : 0f;
            float newExp  = prevExp + (float) gridExport * (float) dtH;
            float newImp  = prevImp + (float) gridImport * (float) dtH;
        prefs.edit()
            .putFloat("soc",    (float) newSoc)
            .putFloat("pv_kw",  (float) pvKw)
            .putLong("soc_saved_at_ms", nowMs)
                             .putFloat("grid_export_kwh", newExp)
                 .putFloat("grid_import_kwh", newImp)
                 .putString("grid_date",       todayStr)
                 .apply();

        android.util.Log.d("SolarWorker",
            String.format("dtH=%.2fh pvKw=%.2f soc %.1f->%.1f battFlow=%.3f",
                dtH, pvKw, (double) soc, newSoc, battFlow));

        // ── Notification rules ────────────────────────────────────────────────
        boolean notifEnabled;
        try {
            notifEnabled = NotificationManagerCompat.from(ctx).areNotificationsEnabled();
        } catch (Exception e) {
            notifEnabled = true;  // assume enabled if check fails
        }
        if (!notifEnabled) return Result.success();
        // ── Quiet hours: no notifications 22:00–08:00 ──────────────────
        int hourNow = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        if (hourNow < 22 && hourNow >= 8) {
            long lHigh   = prefs.getLong("notif_last_high",     0);
            long lLow    = prefs.getLong("notif_last_low",      0);
            long lEve    = prefs.getLong("notif_last_eve",      0);
            long lBattLo = prefs.getLong("notif_last_batt_low", 0);
            long lHighC  = prefs.getLong("notif_last_high_cons",0);
            long now30M  = 30L*60*1000, now2H = 2L*60*60*1000;
            double surplus   = pvKw - consKw;
            double storedKwh = battUse * (newSoc / 100.0);
            double dispSoc   = 10.0 + (newSoc / 100.0) * 80.0;
            if (surplus >= 2.0 && (nowMs - lHigh) > now30M) {
                sendNotif(ctx, "Solar surplus — run large appliances",
                    String.format("+%.1f kW surplus. Good time to run washing machine, dishwasher or water heater. Battery: %.0f%%.", surplus, dispSoc));
                prefs.edit().putLong("notif_last_high", nowMs).apply();
            } else if (pvKw < 0.2 && consKw > 0.1 && (nowMs - lLow) > now2H) {
                double bkp = storedKwh / Math.max(0.01, consKw);
                sendNotif(ctx, "Running on battery",
                    String.format("Solar stopped (%.1f kW). Battery %.0f%% — ~%.1fh backup remaining.", pvKw, dispSoc, bkp));
                prefs.edit().putLong("notif_last_low", nowMs).apply();
            } else if (hourNow == 20 && (nowMs - lEve) > now2H) {
                if (surplus > 0.5)
                    sendNotif(ctx, "Good solar conditions today",
                        String.format("Still producing %.1f kW. Battery %.0f%%. Plan appliances for tomorrow mid-day.", pvKw, dispSoc));
                else
                    sendNotif(ctx, "Solar ended for today",
                        String.format("Production ended. Battery at %.0f%%. Check tomorrow's forecast in the app.", dispSoc));
                prefs.edit().putLong("notif_last_eve", nowMs).apply();
            }
            if (storedKwh < battUse * 0.15 && dispSoc < 20.0 && (nowMs - lBattLo) > now2H) {
                sendNotif(ctx, "Battery low — grid starting",
                    String.format("Battery %.0f%% — reserve approaching. Grid activating. Solar: %.1f kW.", dispSoc, pvKw));
                prefs.edit().putLong("notif_last_batt_low", nowMs).apply();
            }
            if (gridImport > 1.0 && battFlow < -0.2 && (nowMs - lHighC) > now2H) {
                sendNotif(ctx, "High consumption — grid + battery active",
                    String.format("Drawing %.1f kW from grid + %.1f kW battery. Solar %.1f kW of %.1f kW. Battery %.0f%%.",
                        gridImport, Math.abs(battFlow), pvKw, (double) consKw, dispSoc));
                prefs.edit().putLong("notif_last_high_cons", nowMs).apply();
            }
        } // end quiet hours

        return Result.success();
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private void sendNotif(Context ctx, String title, String body) {
        try {
            Intent intent = new Intent(ctx, MainActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pi = PendingIntent.getActivity(ctx, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            NotificationCompat.Builder nb = new NotificationCompat.Builder(ctx, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setColor(Color.parseColor("#1D9E75"))
                .setContentIntent(pi);
            NotificationManager nm = (NotificationManager)
                ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm != null) nm.notify(notifId++, nb.build());
        } catch (Exception e) {
            android.util.Log.e("SolarWorker", "sendNotif: " + e.getMessage());
        }
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
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

print("All project files written OK")

# Icons embedded as base64
ICON_MASKABLE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAYAAABS3GwHAAAGkElEQVR4nO3dT1LbShTF4WvqbQNPso7sBdgDrnoreFWwB8xe3joygYWQAXEiFEmW1H/vPb9vlkGM1DqnuyWDfbDGbl8eP1ofA9p5f3g+tPz51X84gceS2oWo8sMIPfaoUYaiP4DgI4eSRSjywgQfJZQoQtYXJPioIWcRsrwQwUcLOYpwk/oChB+t5MheUgEIP1pLzeCuJYTgo0d7tkSbVwDCj17tyeamAhB+9G5rRlcXgPDDiy1ZXVUAwg9v1mY2+TEo4NnVAjD7w6s12V18bET4y3i7f/ox/PfxfPrW6lgULD0enV0BCD+iWMoy9wCQNlkAZn9EM5dpVgBI+6sAzP6IairbrACQ9qUAzP6IbpxxVgBI+10AZn+oGGadFQDSKACk3Zix/YGeS+ZZASCNAkAaBYC0G/b/UHX78vjBCgBpFADSKACkUQBIowCQ1n0Bxp+gAD88XLuuC3AZQA8Dia+8XLtuCzAeuN4HEn94unbdFmDqw6J6Hkh8mrpGPX/wV7cFMKME3ngLv1nnBTCjBF54DL+Z2cHL7wJ5HWAFnq9N9yvABStBnzyH38xRAcwoQW+8h9/MWQHMKEEvIoTfzGEBzChBa1HCb+a0AGaUoJVI4TdzXAAzSlBbtPCbOS+AGSWoJWL4zQIUwIwSlBY1/GZBCmBGCUqJHH6zQAUwowS5RQ+/WbACmFGCXBTCbxawAGaUIJVK+M2CFsCMEuylFH4zR78Nutfwgra8kG/3T5v/z/F8KnAk1/UyZjWEL4DZ5wWtfSH3BP6amoVoMWYtSBSglhKhn9NqdYiGAmRQM/hjFCENBUiQI/iXAKe+FkXY55/WB+BRyxl/zuWYKMI2FGCDHoM/RhG2Cfs+QG4ewj/k7XhboQAreA2T1+OuiS3QgggBYku0jBVgRoTwD0U7n1wowISoYYl6XikowEj0kEQ/v60owIBKOFTOcw0KAGkU4Be1WVHtfOdQANMNg+p5D8kXQD0E6ucvXwBoky6A+ux3oTwO0gUAZAugPOtNUR0P2QIAZqIFUJ3trlEcF8kCABdyBVCc5bZQGx+5AgBDFADSpAqgtrzvpTROUgUAxigApFEASJMpgNK+NgeV8ZIpADCFAkAaBYC05I9GrP3Fcwpf24N6+GxQZOdpUpQtQG8fFtvD8ag8+RniHgDSklcAr3vyXma7XN8Rhn1kt0Aox9OkyBYI0igApFEASJMpQA+PGT1RGS+ZAgBTKACkUQBIkyqAyr42ldI4SRUAGKMAkCZXAKXlfQ+18ZErADAkWQC1WW4txXGRLABwIVsAxdluiep4yBYAMBMvgOqsN6Y8DtIFAOQLoDz7mXH+8gUw0w2B6nkPUYBf1MKgdr5zKACkUYABlVlR5TzXoAAj0cMR/fy2ogATooYk6nmloAAzooUl2vnkwkcjLojwuZ0EfxkrwApeQ+T1uGuiACt5C5O3422FLdAGHrZEBH8bCrBDj0Ug+Pscbl8eP1ofhHcti0Dw00jcA5T+0rbj+VQ9iKV/Zu0vumsl/AowvJA1v7mkxKpQq2StxqyF0AWYmsVaXdA9hWixvelpzGoIWwC1C5mT0tiFvAdQuoAlTI1V1HuCcAUg/HmolCDMFujt/ul762NQczyf/m99DKlCrACEv40I4+6+ABEugmfexz/ir0K8tj4AR+5aH0BrrgswcVP22uI4HHu1TCV4u3/6d/jv4/n0X47XLc3tFijiEwmvPF8LlwXwPODoi7sCEH7k5KoAhB+5uSkA7/CiBBcFIPx98/xrE90XgPD75aEEXReA8PvXewm6LQDhj6PnEnT7TvDxfPq240/z7ox3g7e4y/VC43d+vfxZZbcFMPtTgo0DeFfqeLDezmtXXYi/B/D+G4meef+bgG7vAbbwfhG8ijDuIVYAr8Y3h71vFyIKsQIAe1EASKMAkHbz/vB8aH0QQAvvD88HVgBIowCQRgEg7cbscy/U+kCAmi6ZZwWANAoAab8LwDYIKoZZZwWAtC8FYBVAdOOMswJA2l8FYBVAVFPZZgWAtMkCsAogmrlMswJA2mwBWAUQxVKWF1cASgDvrmV4VcD5w3l4tGYC5x4A0lYVgK0QvFmb2dUrACWAF1uyumkLRAnQu60Z3XwPQAnQqz3ZTAozT4fQg5RJOekpEKsBWkvNYPJjUEqAVnJkL2t42RKhhpyTbpHZmyKghBK7jaLbF4qAHEpus6vs3ykC9qhxf1n9BpYyYEnthyrNn+BQCG2tnyL+BFv5xJyLAPwVAAAAAElFTkSuQmCC"
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
