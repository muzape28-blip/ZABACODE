# 🔍 ZABACODE — Deep Audit Report

**Tanggal:** 2026-07-28
**Branch:** `arena/019fa792-zabacode` (base: `7b54955`, merge PR #35)
**Metode:** static analysis (ruff/mypy) + runtime reproduction (venv Python 3.11, Flask test client) + end-to-end trace UI → API → core

> **✅ SEMUA TEMUAN DI LAPORAN INI SUDAH DIPERBAIKI.**
> Lihat bagian [STATUS PERBAIKAN](#-status-perbaikan) di bawah. Test: **144 → 159 PASS**.
>
> Laporan ini sengaja dipertahankan apa adanya sebagai catatan diagnosis —
> supaya jejak "kenapa bug ini bisa lolos" tetap terdokumentasi.

---

## 🎯 RINGKASAN EKSEKUTIF

| # | Temuan | Severity | Status |
|---|--------|----------|--------|
| **F-01** | `fetch()` tanpa header `Content-Type` → Flask buang body → Oracle terima `code=""` | 🔴 **CRITICAL** | **Ini penyebab kendala #2 lu** |
| **F-02** | Auto-Fix "memperbaiki" runtime error dengan cara **merusak kode** (`print(prices[9])` → `print("prices[9]")`) | 🔴 **CRITICAL** | Bug desain, muncul setelah F-01 dibenerin |
| **F-03** | Auto-Fix return `ok: True` walaupun hasil patch masih syntax error | 🟠 HIGH | `is_success` dihitung lalu dibuang |
| **F-04** | Regex `=` → `==` merusak keyword argument (`if f(a=1):` → `if f(a==1):`) | 🟠 HIGH | Korupsi kode valid |
| **F-05** | Test suite tidak pernah menguji jalur HTTP yang sebenarnya dipakai browser | 🟠 HIGH | Sebab kenapa F-01 lolos CI |
| **F-06** | CI tidak menjalankan `test_hardening_regressions.py` (6 test mati) | 🟡 MEDIUM | Gap CI |
| **F-07** | `check_code()` salah nomor baris (off-by-9 karena prelude) | 🟡 MEDIUM | Endpoint `/api/check` |
| **F-08** | Traceback interaktif membocorkan `_active_run.py` | 🟢 LOW | Inkonsistensi |
| **F-09** | Dead code + versi tidak konsisten (`v1.0.0` vs `v1.2.0`) | 🟢 LOW | Kosmetik |

---

# 🔴 KENDALA #1 & #2 — AKAR MASALAH SEBENARNYA

## Yang lu lakukan

```python
prices = [1, 2]
print(prices[9])     # ← sengaja dibikin salah → IndexError
```

Lu tekan **RUN** → error muncul → lu tap **"⚙️ Auto-Fix with Oracle"** → keluar toast:

> *"Oracle could not automatically fix this error safely."*

## Kesimpulan penting

**Oracle-nya TIDAK rusak. Oracle bahkan tidak pernah menerima kode lu.**

Yang rusak adalah **satu baris di frontend** — request-nya sampai ke server, tapi **body JSON-nya dibuang diam-diam oleh Flask**.

---

## 🧬 Root Cause — F-01: `fetch()` tanpa `Content-Type`

### Kode bermasalah

`templates/index.html` **baris 894** — helper global:

```javascript
function fetchApi(url, options = {}) {
  options.headers = options.headers || {};
  options.headers['X-Zabacode-Token'] = ZABACODE_TOKEN;
  return fetch(url, options);          // ⚠️ hanya inject token, TIDAK inject Content-Type
}
```

`templates/index.html` **baris 2928** — pemanggil Auto-Fix:

```javascript
const res = await fetchApi('/api/oracle/fix', {
  method: 'POST',
  // ❌ TIDAK ADA headers: { 'Content-Type': 'application/json' }
  body: JSON.stringify({ code: getEditorValue(), stderr: stderrText })
});
```

### Rantai kegagalan

1. `body` berupa **string** dan tidak ada header → browser otomatis pasang
   `Content-Type: text/plain;charset=UTF-8`
2. Flask `request.get_json(silent=True)` **hanya mem-parse kalau mimetype `application/json`**.
   Mimetype `text/plain` → return `None`.
3. `_get_json_payload()` (`web_app.py:81`) memperlakukan `None` sebagai **`{}` kosong**:
   ```python
   data = request.get_json(silent=True)
   if data is None:
       return {}, None          # ⚠️ body hilang tanpa error, tanpa log
   ```
4. `oracle_fix()` (`web_app.py:625`) → `code = payload.get("code", "")` → **`""`**
5. `auto_fix_code("")` (`oracle.py:806`) langsung kena guard:
   ```python
   if not code or not code.strip():
       return {"ok": False, "message": "The editor is empty. Write some code first, dummy!"}
   ```
6. Frontend baris 2936–2938 melihat `data.ok === false` → tampilkan toast generik:
   ```javascript
   } else {
     showToast('Oracle could not automatically fix this error safely.', 'info');
   ```

### 🧪 Bukti reproduksi (dijalankan beneran, bukan teori)

```
=== A) PERSIS seperti yang dikirim browser (TANPA Content-Type) ===
200 {'ok': False, 'message': 'The editor is empty. Write some code first, dummy!'}

=== B) DENGAN Content-Type: application/json ===
200 {'ok': True,
     'fixed_code': 'prices = [1, 2]\nprint("prices[9]")',
     'applied_fixes': ['Wrapped missing quotes in print() on line 2']}

=== C) /api/oracle/explain tanpa Content-Type (bug yang SAMA) ===
200 {'ok': False}
```

> **Server bilang "editor lu kosong", padahal editor lu ada isinya.** Pesan toast di UI menyesatkan karena menelan `data.message` yang asli dan menggantinya dengan kalimat generik.

### 💥 Blast radius — bukan cuma Auto-Fix

Saya scan **semua 18 pemanggilan `fetchApi` POST**. Hasilnya **3 rusak**:

| Baris | Endpoint | Dampak nyata |
|---|---|---|
| **2904** | `/api/oracle/explain` | 🔴 **Kartu penjelasan Oracle di terminal MATI.** Selalu jatuh ke kartu abu-abu generik *"could not auto-diagnose it precisely"* — padahal Oracle sebenarnya **bisa** mengenali `IndexError` lu dengan sempurna |
| **2928** | `/api/oracle/fix` | 🔴 **Ini kendala #2 lu** |
| **2155** | `/api/run/interactive/stop` | 🟡 Tidak berdampak (endpoint tidak baca body) |

**15 pemanggilan lain aman** karena sudah menulis `Content-Type` secara manual — inilah kenapa AI chat, save file, install library, dan plugin **jalan normal**, sementara **fitur Oracle di terminal justru mati**. Inkonsistensi inilah biang keroknya.

### ✅ Bukti perbaikan

Saya patch 2 baris tersebut → tes ulang → **`ok: True`, kode ter-parse, 144/144 test tetap hijau.**
*(patch sudah saya revert — repo lu masih bersih, ini murni diagnosis.)*

### 🩹 Perbaikan yang benar (fix di **satu tempat**, bukan tambal per-pemanggil)

```javascript
function fetchApi(url, options = {}) {
  options.headers = options.headers || {};
  options.headers['X-Zabacode-Token'] = ZABACODE_TOKEN;
  // Body string = selalu JSON di app ini → set default, tapi jangan timpa yang eksplisit
  if (options.body && !options.headers['Content-Type']) {
    options.headers['Content-Type'] = 'application/json';
  }
  return fetch(url, options);
}
```

**Plus hardening di backend** — jangan pernah buang body diam-diam:

```python
def _get_json_payload():
    data = request.get_json(silent=True)
    if data is None:
        # Body ada tapi gagal di-parse → kasih tahu, jangan pura-pura kosong
        if request.get_data(as_text=True).strip():
            return None, (jsonify({
                "ok": False,
                "message": "Body tidak bisa diparse sebagai JSON. Pastikan header Content-Type: application/json terkirim.",
                "code": "invalid_json",
            }), 400)
        return {}, None
    ...
```

> Tanpa hardening ini, bug kelas yang sama **pasti terulang** di endpoint berikutnya yang lu tambah.

---

# 🔴 F-02 — Bug KEDUA yang nunggu di belakang (WAJIB baca)

Ini bagian paling krusial dari laporan ini. **Kalau lu cuma benerin F-01, lu justru dapat masalah yang lebih buruk.**

Setelah `Content-Type` dibenerin, Auto-Fix untuk kode lu menghasilkan:

```diff
  prices = [1, 2]
- print(prices[9])
+ print("prices[9]")
```

Lalu Oracle dengan bangga bilang: *"Wrapped missing quotes in print() on line 2"* dan `ok: True`.

### Kenapa ini berbahaya

- `IndexError` adalah **runtime error**, **bukan** syntax error. Kodenya **sudah 100% valid secara sintaks**.
- Auto-Fix membungkus ekspresi jadi string → program **berhenti crash**, tapi sekarang **mencetak teks harfiah `prices[9]`** alih-alih mengakses list.
- Error yang **kelihatan** berubah jadi bug yang **diam-diam salah**. Ini regresi paling mahal di dunia debugging.
- Toast "cannot fix safely" yang lu keluhkan itu, ironisnya, **justru sedang melindungi lu** dari korupsi ini.

### Penyebab teknis

`oracle.py:825` — regex terlalu rakus:

```python
print_match = re.search(r"print\s*\(\s*([^\"'\s][^\"')]*[^\"'\s]|[a-zA-Z_][a-zA-Z0-9_]*)\s*\)", line_content)
```

Regex ini menangkap **ekspresi Python valid apa pun** di dalam `print()`, lalu mengubahnya jadi string literal. Tidak ada validasi AST sama sekali sebelum membungkus.

### 🧪 Bukti — 5 dari 8 kode VALID ikut dirusak

```
CASE                                ok  RESULT
----------------------------------------------------------------------------
IndexError case (gambar 1)        True  print("prices[9]")        <-- ⚠️ MANGLED
valid arithmetic                  True  print("x + 1")            <-- ⚠️ MANGLED
valid attribute access            True  print("math.pi")          <-- ⚠️ MANGLED
function call                     True  print("f()")              <-- ⚠️ MANGLED
ZeroDivisionError                 True  print("a/b")              <-- ⚠️ MANGLED
nested call                       True  print("len([1,2,3])")     <-- ⚠️ MANGLED
dict lookup -> KeyError          False  (unchanged)
f-string                         False  (unchanged)
```

> `print(math.pi)` — kode yang **sempurna benar** — akan dirusak jadi `print("math.pi")`.
> Dan tombol **"✔️ Apply Fix"** (baris 3000) langsung `setEditorValue()` + `saveActiveTab()` — **menimpa file lu dan auto-save, tanpa undo.**

### 🩹 Perbaikan

1. **Gerbang utama:** Auto-Fix **hanya boleh jalan kalau `ast.parse(code)` GAGAL.** Kalau kode sudah valid secara sintaks, error-nya runtime → serahkan ke `humanize_traceback()`, jangan pernah sentuh sumber.
2. Perketat rule `print()`: hanya bungkus kalau isinya **bukan** ekspresi Python valid (`ast.parse(inner, mode="eval")` gagal) **dan** ada spasi antar bare word.
3. Tolak semua patch yang tidak menaikkan validitas: `ast.parse(before)` gagal **dan** `ast.parse(after)` sukses — kalau tidak, buang patch-nya.

---

# 🟠 F-03 — `ok: True` padahal patch masih rusak

`oracle.py:945` menghitung `is_success`, lalu **tidak pernah memakainya** (terkonfirmasi ruff `F841`). Return statement di baris 995 hanya melihat jumlah patch:

```python
is_success = False
try:
    ast.parse(fixed_code)
    is_success = True     # ⚠️ dihitung, lalu dibuang
except SyntaxError:
    pass
...
return {
    "ok": len(applied_fixes) > 0,   # ⚠️ "ada perubahan" ≠ "berhasil diperbaiki"
    ...
}
```

### 🧪 Bukti

```python
input:  'def f(:\n    print("a"\n'
output: 'def f(:):\n    print("a"\n'    ok = True   ← klaim sukses
ast.parse(output) -> SyntaxError: invalid syntax
```

Oracle bilang "PATCH READY" dan menawarkan Apply Fix, padahal hasilnya **masih tidak bisa dijalankan** dan malah lebih berantakan (`def f(:):`).

**Fix:** `"ok": is_success and len(applied_fixes) > 0`

---

# 🟠 F-04 — Regex `=` → `==` merusak keyword argument

`oracle.py:848`:

```python
if re.match(r"^\s*(if|elif|while)\b", non_comment):
    fixed_nc, count = re.subn(r"(?<![!=<>+\-*/%])=(?![=])", "==", non_comment)
```

Regex ini tidak sadar konteks kurung — **semua** `=` di baris kena, termasuk kwarg.

### 🧪 Bukti

```
if d.get('k', default=1):     →  if d.get('k', default==1):    ❌ rusak
while retry(timeout=5):       →  while retry(timeout==5):      ❌ rusak
if x != 5:                    →  (unchanged)                   ✅ aman
```

**Fix:** lacak kedalaman kurung saat scanning; hanya ganti `=` yang berada di **depth 0**.

---

# 🟠 F-05 — Kenapa 144 test hijau tapi fitur mati di HP

Ini gap paling struktural. Test yang ada memanggil endpoint pakai `json=` (Flask test client **otomatis** pasang `Content-Type: application/json`):

```python
# test_main.py:1044
r = c.post("/api/oracle/fix",
           json={"code": "print(hello world)"},        # ⚠️ auto Content-Type
           headers={"X-Zabacode-Token": AUTH_TOKEN})
assert body["ok"] is True     # LULUS di CI, GAGAL di browser
```

Test memvalidasi **jalur yang tidak pernah dipakai user**, sementara jalur nyata browser (`text/plain`) **nol coverage**. Grep konfirmasi: tidak ada satu pun test yang menyentuh varian content-type.

Test UI pun cuma cek string ada atau tidak:

```python
assert "renderAutoFixButton" in html    # cek fungsi ADA, bukan fungsi BENAR
```

**Fix:** tambahkan regression test yang mengirim body **tanpa** `Content-Type` dan memastikan server merespons 400 eksplisit (bukan diam-diam `{}`), plus test kontrak yang menolak `fetchApi` POST tanpa Content-Type.

---

# 🟡 F-06 — CI tidak menjalankan seluruh test

`.github/workflows/build_apk.yml:112` dan `tools/check.sh:32`:

```bash
python3 -m pytest test_main.py -v      # ⚠️ hanya 1 file
```

`test_hardening_regressions.py` (**6 test**, termasuk proteksi TLS `--trusted-host` dan penolakan source oversize) **tidak pernah dieksekusi di CI**. Proteksi keamanan bisa diam-diam regresi tanpa ketahuan.

**Fix:** ganti jadi `python3 -m pytest -v` (auto-discovery).

---

# 🟡 F-07 — `check_code()` salah nomor baris (off-by-9)

`checker.py:95` memanggil `normalize_code(code)` yang **menyuntik prelude 9 baris** (`SAFE_INPUT_PATCH`), lalu menghitung nomor baris di atas kode yang sudah disuntik.

### 🧪 Bukti

```
Kode user (masalah asli di baris 2):
  1: if True:
  2: print('x')

check_code() bilang -> ["Line 11: missing indentation after ':' on line 10"]
```

Melenceng **tepat 9 baris** = `PRELUDE_LINE_COUNT`. `/api/run` sudah benar karena mengoper `line_offset=PRELUDE_LINE_COUNT` ke `humanize_traceback`, tapi `check_code` tidak punya kompensasi itu.

Mitigasi saat ini: endpoint `/api/check` **tidak dipanggil UI sama sekali** (grep: 0 hasil) — jadi dampaknya nol *hari ini*, tapi ini ranjau untuk fitur "validate before run" berikutnya.

**Fix:** validasi pakai kode mentah, atau kurangi `PRELUDE_LINE_COUNT` dari nomor baris yang dilaporkan.

---

# 🟢 F-08 — Traceback interaktif bocorkan nama file internal

`executor.py:142,162` membersihkan `_active_run.py` → `main.py`, tapi **hanya di `execute_code_isolated`**. Jalur interaktif (`_read_stream_char`) melakukan streaming karakter mentah tanpa sanitasi.

Akibatnya user melihat path internal `_active_run.py` di mode interaktif, tapi `main.py` di mode isolated — membingungkan dan tidak konsisten.

---

# 🟢 F-09 — Dead code, dan versi tidak konsisten

Dikonfirmasi ruff:

| Lokasi | Masalah |
|---|---|
| `oracle.py:972` | `import random` — diimpor, tidak pernah dipakai (opener pakai modulo) |
| `oracle.py:945` | `is_success` — F841, lihat F-03 |
| `oracle.py:983-984` | f-string tanpa placeholder (F541) |
| `checker.py:6` | `import re` tidak terpakai |
| `security.py:6,7` | `base64`, `json` tidak terpakai |
| `security.py:159` | `import os, stat` di dalam fungsi (E401) |
| `executor.py:15`, `file_manager.py:7`, `lib_manager.py:21` | `Path` tidak terpakai |
| `main.py:1` | docstring bilang **v1.0.0**, aslinya **v1.2.0** |
| `requirements-dev.txt:1` | header bilang **v1.0.0** |
| `lib_manager.py:398,414` | User-Agent hardcode `Zabacode/1.0.0` |

Total ruff non-blocking: **530** (347 `E501` line-too-long, 129 `W293` whitespace) — kosmetik, tapi bikin sinyal review tenggelam.

---

## ✅ Yang SUDAH BAGUS (jangan diutak-atik)

Audit ini juga mengkonfirmasi bagian yang solid — kredit di tempatnya:

- **Keystore** (`keystore.py`) — encrypt-then-MAC, PBKDF2 200k rounds, nonce acak per-write, `hmac.compare_digest` konstan-waktu, verifikasi tag **sebelum** dekripsi. Ini benar secara kriptografis.
- **TLS** (`net.py`) — tidak ada jalur fallback unverified sama sekali. Bersih.
- **Wheel install** (`lib_manager.py:419-431`) — verifikasi SHA-256 terhadap digest PyPI **dan** pengecekan path traversal sebelum `extractall`. Dua-duanya benar.
- **Path traversal** (`file_manager.py`) — blokir `..`, `/`, `\`, null byte, dotfile, underscore-prefix, plus allowlist regex.
- **Subprocess isolation** — `start_new_session` + `os.killpg` (PGID cleanup), timeout, bounded output/queue, `RLock` untuk waitress 4-thread. Concurrency-nya dipikirkan.
- **Security headers** — CSP, `nosniff`, `Referrer-Policy`, `frame-ancestors 'none'`.
- **Auth** — konstan-waktu `verify_token`, token per-install.
- **CI** — GitHub Actions di-pin ke commit SHA (supply-chain). Bagus.
- `requirements.lock` resolve bersih (diverifikasi via `pip install --dry-run`).

---

# 🗺️ ROADMAP PERBAIKAN

## 🔥 FASE 1 — Bikin Auto-Fix beneran jalan & aman *(prioritas tertinggi)*

| Langkah | Aksi | File | Effort |
|---|---|---|---|
| **1.1** | Inject `Content-Type: application/json` di helper `fetchApi` | `templates/index.html:894` | 2 menit |
| **1.2** | Backend balas **400 eksplisit** kalau body ada tapi gagal parse (jangan diam-diam `{}`) | `web_app.py:81` | 10 menit |
| **1.3** | Toast tampilkan `data.message` asli, bukan kalimat generik | `index.html:2937` | 5 menit |

> Setelah 1.1 saja, kartu Oracle + Auto-Fix langsung hidup. Tapi **JANGAN berhenti di sini** — lanjut Fase 2, kalau tidak lu buka F-02.

## 🔥 FASE 2 — Hentikan Auto-Fix merusak kode *(lakukan bareng Fase 1)*

| Langkah | Aksi | File | Effort |
|---|---|---|---|
| **2.1** | **Gerbang:** kalau `ast.parse(code)` SUKSES → jangan patch apa pun, arahkan ke penjelasan runtime | `oracle.py:800` | 20 menit |
| **2.2** | `"ok": is_success and len(applied_fixes) > 0` | `oracle.py:995` | 1 menit |
| **2.3** | Perketat regex `print()` — validasi `inner` pakai `ast.parse(mode="eval")` dulu | `oracle.py:825` | 30 menit |
| **2.4** | `=` → `==` hanya pada depth kurung 0 | `oracle.py:848` | 20 menit |
| **2.5** | Tolak patch yang tidak menaikkan validitas (`before` gagal → `after` harus sukses) | `oracle.py` | 15 menit |

**Perilaku target untuk kode lu:**

```
prices = [1, 2]
print(prices[9])
```
→ Auto-Fix **tidak menyentuh kode** (sintaks valid),
→ Oracle tampilkan kartu: *"🔮 Reached Past the End of a List — index 9, list cuma punya 2 item (0,1). Fix: `if i < len(prices):` — Line 2"*
→ Tombol berubah jadi **"Runtime error — butuh perbaikan logika"**, bukan toast menyesatkan.

## ⚡ FASE 3 — Tutup gap testing *(supaya tidak terulang)*

| Langkah | Aksi | File |
|---|---|---|
| **3.1** | Test: POST tanpa `Content-Type` → harus 400 eksplisit | `test_main.py` |
| **3.2** | Test kontrak: **semua** `fetchApi` POST di HTML wajib punya Content-Type (regex scan) | `test_main.py` |
| **3.3** | Test: Auto-Fix **tidak boleh** mengubah kode yang sintaksnya sudah valid | `test_main.py` |
| **3.4** | Test: `auto_fix_code` `ok=True` ⟹ `ast.parse(fixed_code)` sukses | `test_main.py` |
| **3.5** | CI: `pytest test_main.py` → `pytest` (semua file) | `build_apk.yml:112`, `check.sh:32` |

## 🧹 FASE 4 — Kebersihan

| Langkah | Aksi |
|---|---|
| **4.1** | Perbaiki off-by-9 di `check_code()` (F-07) |
| **4.2** | Sanitasi `_active_run.py` di jalur interaktif (F-08) |
| **4.3** | `ruff check . --fix` → bereskan 169 auto-fixable |
| **4.4** | Samakan versi ke `1.2.0` di `main.py`, `requirements-dev.txt`, User-Agent `lib_manager.py` |
| **4.5** | Tambah `[tool.ruff]` di `pyproject.toml` (`line-length = 120`) agar 347 E501 jadi sinyal berguna |

---

## 📌 Satu kalimat kesimpulan

> Kendala #2 lu **bukan** karena Oracle bodoh — Oracle **tidak pernah menerima kode lu** gara-gara satu header HTTP yang hilang di `templates/index.html:894`. Dan begitu header itu dibenerin, lu akan langsung ketemu bug kedua yang lebih berbahaya: Auto-Fix mengubah `print(prices[9])` jadi `print("prices[9]")` — mengubah error yang kelihatan jadi bug yang diam-diam salah. **Perbaiki Fase 1 dan Fase 2 sekaligus, jangan salah satu saja.**

---

---

# ✅ STATUS PERBAIKAN

Semua 9 temuan sudah diperbaiki dan diverifikasi runtime.

| # | Temuan | Status | Perbaikan |
|---|--------|--------|-----------|
| F-01 | Content-Type hilang | ✅ FIXED | `fetchApi` inject otomatis + backend balas 400 eksplisit |
| F-02 | Auto-Fix merusak kode valid | ✅ FIXED | Safety gate: kode yang lolos `ast.parse` tidak pernah disentuh |
| F-03 | `ok:True` padahal rusak | ✅ FIXED | `ok = is_success and len(applied_fixes) > 0` |
| F-04 | Kwarg dirusak `=`→`==` | ✅ FIXED | `_replace_bare_equals()` sadar kedalaman kurung + string |
| F-05 | Test tidak uji jalur browser | ✅ FIXED | +15 regression test |
| F-06 | CI cuma 1 file test | ✅ FIXED | `pytest -v` (auto-discovery) |
| F-07 | Line number off-by-9 | ✅ FIXED | `check_code` tidak lagi inject prelude |
| F-08 | Bocor `_active_run.py` | ✅ FIXED | `_mask_runner_filename()` di jalur interaktif |
| F-09 | Dead code + versi | ✅ FIXED | ruff --fix, versi seragam 1.2.0, `pyproject.toml` |

### Verifikasi akhir

```
pytest                 -> 159 passed  (dari 144)
ruff E9,F821           -> All checks passed
mypy core (6 modul)    -> Success: no issues found
security gates         -> no unverified SSL / ace bundled / CSP / certifi / no CDN
ruff total             -> 516 -> 99 (E501 350->87 setelah line-length=120)
```

### Perilaku baru untuk kode di gambar 1

```
prices = [1, 2]
print(prices[9])
```

| Sebelum | Sesudah |
|---|---|
| Toast: *"cannot fix this error safely"* | Kartu: **"🔮 Reached Past the End of a List — Line 2"** |
| Kartu Oracle mati (generic abu-abu) | Badge **RUNTIME ERROR** + penjelasan kenapa tidak dipatch |
| Kalau header dibenerin: kode dirusak jadi `print("prices[9]")` | Kode **tidak disentuh sama sekali** |

---

*Semua temuan direproduksi secara runtime di venv Python 3.11 dengan Flask test client, lalu diperbaiki dan diverifikasi ulang.*
