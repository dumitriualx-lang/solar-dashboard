# Solar Dashboard — Deployment Guide

## Files in this package
```
solar-app/
├── index.html      ← Main app (full dashboard)
├── manifest.json   ← PWA metadata (name, icons, theme)
├── sw.js           ← Service worker (offline caching)
└── icons/
    ├── icon-72.png
    ├── icon-96.png
    ├── icon-128.png
    ├── icon-144.png
    ├── icon-152.png
    ├── icon-192.png
    ├── icon-384.png
    └── icon-512.png
```

---

## OPTION A — Install on your phone in 5 minutes (free, no app store)

### Step 1 — Host on Netlify (free)
1. Go to **https://netlify.com/drop** (no account needed)
2. Drag the entire `solar-app` folder onto the page
3. Netlify gives you a live HTTPS URL like `https://amazing-name-123.netlify.app`

### Step 2 — Install on Android
1. Open the URL in **Chrome** on your Android phone
2. Chrome shows a banner: **"Add Solar Dashboard to Home Screen"** — tap it
3. OR tap the 3-dot menu → "Add to Home screen"
4. The app installs with your green icon, launches full-screen, works offline ✅

### Step 3 — Install on iPhone (iOS)
1. Open the URL in **Safari** (must be Safari, not Chrome)
2. Tap the Share button (box with arrow) → "Add to Home Screen"
3. Tap "Add" — the app appears on your home screen ✅

---

## OPTION B — Submit to Google Play Store

### Requirements
- Google Play Developer account ($25 one-time fee): https://play.google.com/console
- Your app must be hosted at an HTTPS URL (Netlify from Option A works)

### Step 1 — Build the APK with PWABuilder (free, no coding)
1. Go to **https://pwabuilder.com**
2. Enter your Netlify URL and click "Start"
3. PWABuilder checks your PWA — all should be green ✅
4. Click **"Package for Stores"** → **"Google Play"**
5. Fill in: App name, Package ID (e.g. `com.yourname.solardashboard`), Version
6. Click "Download Package" — you get a `.zip` with the signed APK + AAB

### Step 2 — Upload to Google Play
1. Go to https://play.google.com/console
2. Create a new app → Internal Testing → Upload the `.aab` file
3. Fill in store listing (description, screenshots)
4. Submit for review (usually approved in 1–3 days)

---

## OPTION C — Self-host on your home network (LAN only)

If you don't want to use a cloud host, run a local server:

```bash
# Python (if installed on any computer on your network)
cd solar-app
python3 -m http.server 8080

# Then on your phone, open:
# http://YOUR-PC-IP:8080
# e.g. http://192.168.1.100:8080
```

Note: PWA install requires HTTPS — local HTTP works for testing but won't show the install prompt.

---

## Updating the app

To update readings automatically in the future, the app saves all logged readings to `localStorage` on your phone — they persist across sessions. You can also connect it to the Huawei FusionSolar API in the future for fully automatic updates.

---

## Support
System: Huawei SUN2000-5KTL-M1 · 5 kW south-facing panels  
Battery: Huawei Luna 2000 CO · 5 kWh gross · 4.5 kWh usable  
Location: Pantelimon, Ilfov, Romania  
