# Contributing to ZABACODE

Terima kasih sudah tertarik berkontribusi! 🎉

## Cara Berkontribusi

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/ZABACODE.git
cd ZABACODE
```

### 2. Setup Environment (Reproducible)
```bash
# Option A: Locked dependencies (reproducible, mirrors CI)
pip install -r requirements.lock

# Option B: Dev dependencies (floating, quick)
pip install -r requirements-dev.txt

# Verify
python main.py
# Buka http://127.0.0.1:5000
```

### 3. Buat Branch
```bash
git checkout -b feature/nama-fitur-lo
# atau
git checkout -b fix/bug-yang-mau-diperbaiki
```

### 4. Code & Test — One Local Check Command (Mirrors CI)
```bash
# Local check yang sama dengan CI gate (Fix #26):
./tools/check.sh
# atau:
bash tools/check.sh

# Isinya:
# - ruff check . --select=E9,F821 (blocking: syntax errors, undefined names)
# - ruff check . --select=E,F,W,I --exit-zero (non-blocking: style, import order)
# - mypy --ignore-missing-imports zabacode/core/security.py zabacode/core/executor.py zabacode/core/net.py zabacode/core/keystore.py zabacode/core/ai_provider.py zabacode/core/oracle.py (blocking)
# - mypy wider sweep non-blocking
# - pytest test_main.py -v
# - security checks: no unverified SSL, Ace bundled, CSP, certifi, no CDN, provider registry
```

**Catatan:** CONTRIBUTING lama nyaranin `black`, `flake8`, `isort` — sekarang CI pakai **Ruff** sebagai pengganti semua itu (Ruff sudah include Black + Flake8 + Isort). Jadi pakai Ruff aja, bukan Black/Flake8/Isort lagi. Ini diselaraskan biar kontributor bisa reproduce CI gate secara lokal (Fix #26).

Manual steps kalau mau run satu-satu:
```bash
# Lint critical (blocking — harus pass)
ruff check . --select=E9,F821

# Lint full (non-blocking — warning aja)
ruff check . --select=E,F,W,I --exit-zero

# Type checking (blocking on 5 core modules)
mypy --ignore-missing-imports zabacode/core/security.py zabacode/core/executor.py zabacode/core/net.py zabacode/core/keystore.py zabacode/core/ai_provider.py zabacode/core/oracle.py

# Tests
pytest test_main.py -v
```

### 5. Commit & Push
```bash
git add .
git commit -m "feat: deskripsi fitur" 
# atau "fix: deskripsi bug"
git push origin feature/nama-fitur-lo
```

### 6. Pull Request
- Buka GitHub repo lo
- Klik "New Pull Request"
- Kasih deskripsi jelas apa yang lu ubah + closes #nomor-issue kalau ada
- CI akan jalanin: Ruff + Mypy + Pytest + Security checks + Build APK (pinned Actions SHAs, lock file)
- Submit!

## Commit Message Format

Gunakan conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: Fitur baru
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Format code (tanpa logic change)
- `refactor`: Code reorganization
- `test`: Add/update tests
- `chore`: Dependencies, CI/CD, dll

## Areas Welcome untuk Kontribusi

### 1. **Library Recipes** 📦
- Check p4a official recipes
- Tambah ke `KNOWN_LIBRARIES` di `zabacode/lib_manager.py`
- Update tier (runtime vs buildtime) + mode (offline/online/hybrid)

### 2. **UI/UX Improvements** 🎨
- Ace Editor improvements (bundled offline)
- Theme customization (10 themes)
- Mobile responsiveness + privacy controls (localStorage drafts opt-in/out)

### 3. **AI Providers** 🤖
- Implementasi provider baru di `zabacode/core/ai_provider.py`
- Follow pola `call_openrouter()` / `call_custom_endpoint()` — must use `get_ssl_context()` verified TLS
- Jangan pakai `ssl._create_unverified_context()` — bakal di-block CI

### 4. **Security & Performance** 🔐
- Security audit suggestions (lihat SECURITY.md → checklist)
- Performance optimization (interactive bounds, output truncation, duration timeout)
- Memory improvements (bounded queue)

### 5. **Testing** ✅
- Hardware testing di ARMv7 / ARM64
- Integration tests (token exposure, JSON validation, path policy)
- Stress tests (interactive flooding, large source)

### 6. **Documentation** 📖
- Troubleshooting guides
- API documentation (JSON schema validation, 400/413 codes)
- Tutorial videos + privacy docs (localStorage behavior)

## Code Style Guide

### Python
- **Ruff** sebagai linter + formatter (pengganti Black + Flake8 + Isort) — blocking gate: `E9,F821` harus pass
- Type hints untuk functions (Mypy blocking on 5 core modules)
- Docstring untuk semua function/class
- No `ssl._create_unverified_context()` — use `get_ssl_context()` from `core/net.py`

### JavaScript/HTML
- Use semicolons
- Const/let instead of var
- kebab-case untuk IDs/classes
- No external CDN (breaks offline-first) — Ace bundled in `assets/vendor/ace/`

## Testing Requirements

Before submitting PR — run `./tools/check.sh` which mirrors CI:

✅ **Unit Tests Pass**
```bash
pytest test_main.py -v
```

✅ **No Critical Linting Errors** (blocking)
```bash
ruff check . --select=E9,F821
# Must be clean, otherwise CI fails
```

✅ **Mypy Core Modules Pass** (blocking)
```bash
mypy --ignore-missing-imports zabacode/core/security.py zabacode/core/executor.py zabacode/core/net.py zabacode/core/keystore.py zabacode/core/ai_provider.py zabacode/core/oracle.py
```

✅ **Security Checks**
```bash
# No unverified SSL
! grep -R "ssl._create_unverified_context" zabacode/

# Ace bundled
test -f assets/vendor/ace/ace.js

# CSP present
grep -q "Content-Security-Policy" zabacode/web_app.py

# No CDN
! grep -q "cdnjs.cloudflare.com\|unpkg.com\|jsdelivr.net" templates/index.html
```

✅ **Code Works Locally**
```bash
python main.py
# Open http://127.0.0.1:5000 — try 5000-5010 if 5000 occupied (port collision handling)
```

---

**Happy coding!** 🚀

P.S. Kalau kamu kasih task ke AI agent yang punya akses repo, tambahin kalimat eksplisit: *"cuma cek/fix bug, jangan nambahin fitur/branding/identitas baru tanpa nanya dulu."* Satu kalimat ini nutup celah scope creep (lesson learned dari Arena integration).
