# ZMUX Coexistence Fix Package — Siap Timpa

Ini file fix siap timpa untuk repo ZABAWHEELS (Zmux).

## File & Lokasi Tujuan

1. **buildozer.spec**
   - Raw: https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/buildozer.spec
   - Timpa ke: https://github.com/muzape28-blip/ZABAWHEELS/blob/main/app/buildozer.spec
   - Edit link: https://github.com/muzape28-blip/ZABAWHEELS/edit/main/app/buildozer.spec

2. **server.py**
   - Raw: https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/server.py
   - Timpa ke: https://github.com/muzape28-blip/ZABAWHEELS/blob/main/app/zmux/server.py
   - Edit link: https://github.com/muzape28-blip/ZABAWHEELS/edit/main/app/zmux/server.py

3. **p4a_hook.py (BARU)**
   - Raw: https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/p4a_hook.py
   - Buat file baru di: https://github.com/muzape28-blip/ZABAWHEELS/new/main/app/tools
   - Path: `app/tools/p4a_hook.py` (buat folder tools kalau belum ada)

## Cara Timpa Cepat (2 menit)

Via web GitHub:
- Buka Edit link di atas → hapus semua → paste dari Raw link → Commit directly to main

Via local:
```bash
cd ZABAWHEELS
curl -sL https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/buildozer.spec > app/buildozer.spec
curl -sL https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/server.py > app/zmux/server.py
mkdir -p app/tools
curl -sL https://raw.githubusercontent.com/muzape28-blip/ZABACODE/arena/019fbd3f-zabacode/fix-packages/zmux/p4a_hook.py > app/tools/p4a_hook.py
git add app/buildozer.spec app/zmux/server.py app/tools/p4a_hook.py
git commit -m "fix(coexistence): Zmux 5000→6000 + taskAffinity hook (no more ketuker with Zabacode)"
git push
```

Setelah push, APK Zmux baru akan auto build (kalau ada workflow), dan akan coexist dengan Zabacode 5000.

