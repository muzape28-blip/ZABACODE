"""
ZABACODE Core — Security: Auth Token, Encryption, Key Storage
Handles local session auth tokens, XOR-Base64 encryption, and Android Keystore integration.
"""

import base64
import json
import secrets
import sys

from zabacode.core.paths import KEYS_FILE, TOKEN_FILE, USER_PACKAGES_DIR

# ---------------------------------------------------------------------------  
# Auth Token Management
# ---------------------------------------------------------------------------

def _load_or_create_token() -> str:
    """Load existing auth token or generate a new 128-bit hex token."""
    if TOKEN_FILE.exists():
        try:
            token = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if len(token) >= 16:
                return token
        except Exception:
            pass
    
    token = secrets.token_hex(16)
    try:
        TOKEN_FILE.write_text(token, encoding="utf-8")
    except Exception:
        pass
    return token


AUTH_TOKEN = _load_or_create_token()

# Ensure user_packages in sys.path
if str(USER_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(USER_PACKAGES_DIR))


# ---------------------------------------------------------------------------
# XOR-Base64 Encryption (Dev Mode Fallback)
# ---------------------------------------------------------------------------

def xor_cipher(data_str: str, key_str: str) -> str:
    """Encrypt/decrypt using XOR + Base64 encoding (symmetric)."""
    key_bytes = key_str.encode("utf-8")
    data_bytes = data_str.encode("utf-8")
    res = bytearray()
    for i, b in enumerate(data_bytes):
        res.append(b ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(bytes(res)).decode("utf-8")


def xor_decipher(b64_str: str, key_str: str) -> str:
    """Decrypt XOR-Base64 encoded string."""
    try:
        key_bytes = key_str.encode("utf-8")
        data_bytes = base64.b64decode(b64_str.encode("utf-8"))
        res = bytearray()
        for i, b in enumerate(data_bytes):
            res.append(b ^ key_bytes[i % len(key_bytes)])
        return res.decode("utf-8")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Android Keystore / Encrypted Preferences Integration
# ---------------------------------------------------------------------------

def _try_keystore_load() -> dict:
    """Attempt to load keys from Android EncryptedSharedPreferences."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        MasterKey = autoclass('androidx.security.crypto.MasterKey')
        EncryptedSharedPreferences = autoclass('androidx.security.crypto.EncryptedSharedPreferences')
        
        activity = PythonActivity.mActivity
        masterKey = MasterKey.Builder(activity).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
        prefs = EncryptedSharedPreferences.create(
            activity, "zabacode_secure_keys", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SKEY,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        keys = {}
        for p in ["openrouter", "gemini", "groq", "mistral", "deepseek", "ollama"]:
            val = prefs.getString(p, "")
            if val:
                keys[p] = val
        if keys:
            return keys
    except Exception:
        pass
    return {}


def _try_keystore_save(provider: str, api_key: str) -> bool:
    """Attempt to save a key to Android EncryptedSharedPreferences."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        MasterKey = autoclass('androidx.security.crypto.MasterKey')
        EncryptedSharedPreferences = autoclass('androidx.security.crypto.EncryptedSharedPreferences')
        
        activity = PythonActivity.mActivity
        masterKey = MasterKey.Builder(activity).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
        prefs = EncryptedSharedPreferences.create(
            activity, "zabacode_secure_keys", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SKEY,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        editor = prefs.edit()
        editor.putString(provider, api_key)
        editor.apply()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public Key Storage API
# ---------------------------------------------------------------------------

def load_keys() -> dict:
    """Load API keys from Android Keystore (Production) or XOR file (Dev)."""
    # 1. Try Android Keystore
    keystore_keys = _try_keystore_load()
    if keystore_keys:
        return keystore_keys
    
    # 2. Fallback to XOR encrypted file
    if KEYS_FILE.exists():
        try:
            raw_text = KEYS_FILE.read_text(encoding="utf-8")
            decrypted = xor_decipher(raw_text, AUTH_TOKEN)
            return json.loads(decrypted) if decrypted else {}
        except Exception:
            return {}
    return {}


def save_key(provider: str, api_key: str) -> None:
    """Save an API key securely (Keystore + XOR file backup)."""
    provider = provider.strip()
    api_key = api_key.strip()
    
    # 1. Try Android Keystore
    _try_keystore_save(provider, api_key)
    
    # 2. XOR encrypted file backup
    keys = load_keys()
    keys[provider] = api_key
    try:
        encrypted_text = xor_cipher(json.dumps(keys), AUTH_TOKEN)
        KEYS_FILE.write_text(encrypted_text, encoding="utf-8")
    except Exception as e:
        print(f"[SECURITY] Failed to save encrypted key: {e}")


def verify_token(token: str) -> bool:
    """Verify an auth token using constant-time comparison."""
    import hmac
    if not token:
        return False
    return hmac.compare_digest(token, AUTH_TOKEN)
