# Contributing to ZABACODE

Terima kasih sudah tertarik berkontribusi! 🎉

## Cara Berkontribusi

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/ZABACODE.git
cd ZABACODE
```

### 2. Setup Environment
```bash
pip install -r requirements-dev.txt
python main.py
# Buka http://localhost:5000
```

### 3. Buat Branch
```bash
git checkout -b feature/nama-fitur-lo
# atau
git checkout -b fix/bug-yang-mau-diperbaiki
```

### 4. Code & Test
```bash
# Jalanin tests
pytest test_main.py -v

# Check format
black main.py
flake8 main.py
isort main.py
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
- Kasih deskripsi jelas apa yang lu ubah
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
- Tambah ke `KNOWN_LIBRARIES` di `main.py`
- Update tier (runtime vs buildtime)

### 2. **UI/UX Improvements** 🎨
- Monaco Editor improvements
- Theme customization
- Mobile responsiveness

### 3. **AI Providers** 🤖
- Implementasi provider baru
- Follow pola `_call_openrouter()` di `main.py`

### 4. **Security & Performance** 🔐
- Security audit suggestions
- Performance optimization
- Memory improvements

### 5. **Testing** ✅
- Hardware testing di ARMv7
- Integration tests
- Stress tests

### 6. **Documentation** 📖
- Troubleshooting guides
- API documentation
- Tutorial videos

## Code Style Guide

### Python
- Follow PEP 8 (black formatter)
- Type hints untuk functions
- Docstring untuk semua function/class

### JavaScript/HTML
- Use semicolons
- Const/let instead of var
- kebab-case untuk IDs/classes

## Testing Requirements

Before submitting PR:

✅ **Unit Tests Pass**
```bash
pytest test_main.py -v --cov=main
```

✅ **No Linting Errors**
```bash
flake8 main.py
black --check main.py
```

✅ **Code Works Locally**
```bash
python main.py
```

---

**Happy coding!** 🚀
