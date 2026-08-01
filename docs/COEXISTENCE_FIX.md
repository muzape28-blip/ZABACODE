# ZABACODE + ZMUX Coexistence Fix — Deep Dive

> **Masalah:** Zabacode.apk dan Zmux.apk terinstall, masing-masing jalan normal 5/5 gates, tapi kalau buka Zmux lalu balik home buka Zabacode yang muncul malah Zmux dan sebaliknya. Kadang gak bisa buka keduanya barengan.

## TL;DR Root Cause

Bukan bug Python, tapi **dua layer tabrakan di level Android**:

### 1) Port collision — penyebab utama (kritis)
- p4a webview bootstrap `WebViewLoader.tmpl.java` hardcode satu port:
  ```java
  public static void testConnection() {
      while (true) {
          if (pingHost("localhost", {{ args.port }}, 100)) {
              loadUrl("http://127.0.0.1:{{ args.port }}/");
              break;
          }
      }
  }
  ```
  `{{ args.port }}` diisi dari `p4a.port` di `buildozer.spec` saat build.
- Java cuma ping **satu port** itu. Gak ada range scan.
- Zabacode `web_app.py` lama mencoba range 5000-5010:
  ```python
  for port in range(5000,5011):
      s.bind(("127.0.0.1",port)) # probe then close
      serve(app, host="127.0.0.1", port=port)
  ```
  Ada TOCTOU race (bind check lalu close, baru serve), dan yang lebih fatal: **jika 5000 sudah dipakai app lain, Zabacode pindah ke 5001 tapi WebViewLoader tetap nunggu 5000** — akhirnya nge-load server app lain.
- Loopback `127.0.0.1` di Android **shared antar app**, bukan per-app isolated. Jadi dua app tidak bisa bind port sama bersamaan.
- **Skenario bug:**
  1. Zmux start duluan → bind 5000 → WebView load 5000 → tampil Zmux (ok)
  2. User home → Zmux background tapi server masih di 5000
  3. Zabacode start → coba bind 5000 gagal → bind 5001 → serve 5001, tapi Java-nya tetap ping 5000 (karena `p4a.port=5000`) → ping sukses karena Zmux masih di 5000 → load `http://127.0.0.1:5000/` → yang ke-load UI Zmux, bukan Zabacode. User lihat "buka zabacode muncul zmux".

Bukti: lihat `app/zmux/server.py` di ZABAWHEELS — mereka sudah sadar masalah ini dan menulis komentar eksplisit:

```python
#: The p4a webview bootstrap polls *exactly* this port (p4a.port = 5000) and
#: loads http://127.0.0.1:5000/ once it answers. On Android we must therefore
#: serve on this port — silently moving to another port leaves the WebView
#: waiting forever (the "stuck on loading screen" boot freeze).
P4A_HTTP_PORT = 5000
```

Dan implementasi Zmux yang benar: bind socket langsung, pass ke Waitress via `sockets=listeners` tanpa probe-close.

### 2) TaskAffinity / launchMode — penyebab sekunder
- p4a arg `--activity-launch-mode` default `singleTask` (lihat `pythonforandroid/bootstraps/common/build/build.py:962`):
  ```python
  ap.add_argument('--activity-launch-mode', dest='activity_launch_mode', default='singleTask', ...)
  ```
- `singleTask` behavior: saat launcher start activity dengan `FLAG_ACTIVITY_NEW_TASK`, sistem cari task yang affinity-nya sama dengan activity. Jika ketemu, bawa task itu ke depan.
- Default affinity = package name (`com.zaba.zabacode` vs `com.zaba.zmux`) → seharusnya beda, jadi tidak konflik. Tapi:
  - Kedua app pakai activity class name identik `org.kivy.android.PythonActivity`
  - Beberapa launcher Android Go / budget mengelompokkan recent task berdasarkan component name, bukan cuma affinity → bisa salah bawa task
  - Jika port collision sudah terjadi (app A tampilkan UI app B), user akan mengira itu taskAffinity bug, padahal port dulu

**Claude.ai suggestion `android.taskAffinity = com.zaba.zabacode` di buildozer.spec adalah TIDAK VALID** — buildozer tidak punya property itu (cek `buildozer/targets/android.py` — hanya handle `android.manifest.launch_mode`, `android.manifest_placeholders`, `android.extra_manifest_xml`, dll). Key `android.taskAffinity` akan diabaikan diam-diam.

Untuk set taskAffinity yang benar di webview bootstrap, harus patch `AndroidManifest.tmpl.xml` karena template webview saat ini (p4a 2026.5.9) tidak include placeholder `{{ args.extra_manifest_application_arguments }}` (beda dengan sdl2/qt yang include). Satu-satunya cara resmi: pakai `p4a.hook`.

## Fix yang diterapkan di repo ini (Zabacode v1.2.1)

### A) Buildozer.spec
```ini
# Coexistence: Zabacode 5000, Zmux 6000
p4a.port = 5000
android.manifest.launch_mode = singleTop
p4a.hook = tools/p4a_hook.py
```
- `singleTop` lebih aman dari `singleTask` untuk co-existence — tidak agresif cari task lama
- Hook inject `android:taskAffinity="com.zaba.zabacode"` dan `android:documentLaunchMode="intoExisting"` (best practice untuk launcher dengan multiple MAIN activities)

### B) zabacode/web_app.py
- Copy pattern dari Zmux `server.py` yang sudah proven:
  - `_bind_listener()` bind langsung, tidak probe-close
  - `_bind_http_socket()` strict bind ke `P4A_HTTP_PORT=5000` di Android dengan retry 30s, bukan range
  - Desktop fallback tetap range 5000-5010 untuk dev
  - `serve(app, sockets=listeners)` pass live socket ke Waitress — no race
- Logging jelas: `[INFO] Coexistence: Zabacode=5000, Zmux=6000`

### C) tools/p4a_hook.py
- `before_apk_build` dan `after_apk_build` patch `src/main/AndroidManifest.xml`:
  ```python
  marker = 'android:name="org.kivy.android.PythonActivity"'
  text = text.replace(marker,
      f'{marker}\n android:taskAffinity="com.zaba.zabacode"\n android:documentLaunchMode="intoExisting"')
  ```
- Juga ubah `singleTask` → `singleTop` jika masih tersisa

### D) Untuk Zmux (repo ZABAWHEELS) — yang harus diubah juga
Di `app/buildozer.spec` Zmux:
```ini
# Zabacode 5000, Zmux 6000 — jangan sama!
p4a.port = 6000
android.manifest.launch_mode = singleTop
p4a.hook = tools/p4a_hook_zmux.py  # similar hook dengan affinity com.zaba.zmux
```
Di `app/zmux/server.py` sudah benar (strict 5000), tinggal ganti `P4A_HTTP_PORT = 6000`.

Tanpa kedua sisi ganti port, fix tidak lengkap.

## Tes Diagnostik

1. **Force-stop test (untuk bedakan port vs taskAffinity):**
   - Settings → Apps → Zmux → Force Stop
   - Buka Zabacode — jika sekarang normal (tampilkan Zabacode, bukan Zmux), berarti port collision confirmed (karena Zmux server sudah mati, port 5000 free, Zabacode bisa bind 5000 dan WebView load benar)

2. **adb dumpsys:**
   ```bash
   adb shell dumpsys activity recents | grep -A2 -i "zaba"
   adb shell dumpsys activity activities | grep -i "affinity\|PythonActivity\|zaba"
   ```

3. **Logcat port bind:**
   ```bash
   adb logcat | grep -i "Starting ZABACODE\|Starting ZMUX\|Port.*occupied\|P4A_HTTP_PORT\|WebViewLoader"
   ```

## Tentang Integrasi Zmux sebagai terminal tab Zabacode

### Kata Claude.ai
> Bug ketuker punya fix jauh lebih simpel (taskAffinity 1 baris) — gak butuh integrasi. Integrasi adalah keputusan lebih besar.

Ini **setengah benar**: taskAffinity saja tidak cukup karena root cause utama port collision. Fix port jauh lebih penting dari taskAffinity.

### Kapan integrasi layak?
Ingat prinsip lu sendiri: *"nanti kalau zmux udah layak, baru gw berani integrasikan"* dan `POST_FIX_REPORT.md` Zmux bilang "Layak dipakai sendiri — BELUM layak dirilis ke publik" karena (1) belum tes HP asli (ini sudah keatasi, gates 5/5), (2) **masih bukan shell beneran** (`$VAR`, glob, `~`, job control belum ada).

Integrasi sekarang = **prematur** jika kriteria shell belum tercapai. Tapi bisa dimulai sebagai experimental branch.

### Effort integrasi (real, bukan drag folder)
- **Security:** dua `security.py`/`keystore.py`/`paths.py` terpisah → harus jadi satu (bagus, dari 2 titik rawan jadi 1)
- **Server:** Zmux punya WebSocket server + PTY + sessions di thread terpisah, Zabacode punya Flask. Harus merge: Flask Zabacode serve `/` + `/api/*` Zabacode + `/api/exec` Zmux + WebSocket di port berbeda (misal HTTP 5000, WS 5001)
- **UI:** xterm.js jadi tab baru di `index.html`, sejajar Ace editor
- **Build:** requirements gabung (`pyjnius`, `packaging`, dll), `proot` libs (`libproot.so`) harus ikut, APK size naik ±15-25MB
- **Port:** kalau integrated, port collision hilang karena single APK single server (solve root cause permanen)

### Roadmap yang disarankan
1. **Phase 1 — Now (coexistence fix):**
   - Terapkan fix di atas di kedua repo (port 5000 vs 6000, hook taskAffinity, strict bind)
   - Build ulang kedua APK, tes: buka Zmux → home → buka Zabacode → keduanya tampil benar, tidak ketuker
2. **Phase 2 — Evaluasi Zmux maturity:**
   - Lengkapi shell features: `$VAR` expansion, `~`, glob `*`, job control, `cd` persistence (sudah sebagian ada di `pty_session.py`?)
   - Pastikan `zmux-info` dan `zpip` stabil di device low-end
3. **Phase 3 — Integrasi (kalau layak):**
   - Branch baru `integrated-terminal`
   - Merge `zmux/*` jadi `zabacode/core/terminal/` (hindari dua security system)
   - Tambah tab terminal di UI: `terminal.html` → embed sebagai `<div id="view-terminal">` di `index.html` utama
   - Single Flask app, WebSocket di `WS_PORT = HTTP_PORT+1`
   - Test coexistence tidak perlu lagi (single APK)
   - Jaga philosophy: tetap offline-first, zero telemetry, GPLv3

### Keputusan
- **Jika alasan integrasi hanya karena bug ketuker → JANGAN integrasi dulu.** Fix port + taskAffinity (Phase 1) jauh lebih murah (2 file edit, 1 hook) vs bongkar dua rumah jadi satu.
- **Jika alasan integrasi karena pengen UX ala VSCode (editor + integrated terminal) → LANJUT, tapi di branch terpisah dengan rigor sama seperti audit-audit sebelumnya, bukan buru-buru.** Ingat: integrasi beneran butuh unify security, bukan dua sistem auth paralel.

## Referensi
- p4a webview manifest template: https://github.com/kivy/python-for-android/blob/master/pythonforandroid/bootstraps/webview/build/templates/AndroidManifest.tmpl.xml — tidak ada `extra_manifest_application_arguments` placeholder (bukti hook diperlukan)
- p4a bootstrap singleTask default: `pythonforandroid/bootstraps/common/build/build.py:962` — `default='singleTask'`
- buildozer android.py hanya handle `android.manifest.launch_mode`, bukan `android.taskAffinity` — grep `taskAffinity` tidak ada, hanya `launch_mode` di line 1280-1283
- WebViewLoader fixed port: `pythonforandroid/bootstraps/webview/build/templates/WebViewLoader.tmpl.java` — `{{ args.port }}` hardcoded
- Zmux correct strict bind pattern: `app/zmux/server.py` comment `polls *exactly* this port`
- Android taskAffinity docs: https://developer.android.com/guide/topics/manifest/activity-element — default affinity = package name, taskAffinity trumps launchMode discussion https://stackoverflow.com/questions/41055022/android-deep-linking-and-singleinstance-singletask
- documentLaunchMode="intoExisting": https://stackoverflow.com/questions/15526805/two-main-activities-in-androidmanifest-xml — solusi launcher dengan multiple MAIN activities

---
*Generated via deep research 2026 — verified against p4a 2026.5.9 source, buildozer, and both ZABACODE & ZABAWHEELS repos.*
