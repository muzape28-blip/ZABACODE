"""
ZABACODE Core — Multi-Provider AI Chat Handlers
Supports: OpenRouter, Gemini, Groq, Mistral, DeepSeek, Ollama (local)
"""

import json
import urllib.request
import urllib.error

ALLOWED_PROVIDERS = {"openrouter", "gemini", "groq", "mistral", "deepseek", "ollama"}

# Default system prompt
SYSTEM_PROMPT = (
    "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
    "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android. "
    "Jawab dengan singkat, padat, dan langsung ke solusi."
)


def _handle_url_error(e: Exception, provider_name: str) -> dict:
    """Handle URL errors from AI providers, returning error dict."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
            err_json = json.loads(err_body)
            if isinstance(err_json.get("error"), dict):
                msg = err_json["error"].get("message", str(e))
            else:
                msg = err_json.get("error") or str(e)
            return {"ok": False, "message": f"{provider_name} error ({e.code}): {msg}"}
        except Exception:
            return {"ok": False, "message": f"{provider_name} error ({e.code})"}
    return {"ok": False, "message": f"{provider_name} error: {e}"}


def call_openrouter(api_key: str, message: str, code_context: str = "") -> dict:
    """Call OpenRouter API (supports multiple models)."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "model": "qwen/qwen-2.5-coder-32b-instruct:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/muzape28-blip/ZABACODE",
            "X-Title": "Zabacode Mobile IDE"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        return {"ok": True, "reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return _handle_url_error(e, "OpenRouter")


def call_gemini(api_key: str, message: str, code_context: str = "") -> dict:
    """Call Google Gemini API."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_content}]}]
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"ok": True, "reply": reply}
    except Exception as e:
        return _handle_url_error(e, "Gemini")


def call_groq(api_key: str, message: str, code_context: str = "") -> dict:
    """Call Groq API (ultra-fast inference)."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        return {"ok": True, "reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return _handle_url_error(e, "Groq")


def call_mistral(api_key: str, message: str, code_context: str = "") -> dict:
    """Call Mistral API (Codestral model)."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        return {"ok": True, "reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return _handle_url_error(e, "Mistral")


def call_deepseek(api_key: str, message: str, code_context: str = "") -> dict:
    """Call DeepSeek API (coding-specialized model)."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "model": "deepseek-coder",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return {"ok": True, "reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return _handle_url_error(e, "DeepSeek")


def call_ollama(api_key: str, message: str, code_context: str = "") -> dict:
    """Call Ollama local API (offline-capable, runs on localhost)."""
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}" if code_context else message
    body = json.dumps({
        "model": "codellama",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return {"ok": True, "reply": data.get("message", {}).get("content", "")}
    except Exception as e:
        return _handle_url_error(e, "Ollama")


# Provider registry
PROVIDER_HANDLERS = {
    "openrouter": call_openrouter,
    "gemini": call_gemini,
    "groq": call_groq,
    "mistral": call_mistral,
    "deepseek": call_deepseek,
    "ollama": call_ollama,
}

# Provider display info
PROVIDER_INFO = {
    "openrouter": {"name": "OpenRouter", "mode": "online", "icon": "🌐", "models": "Multi-model (free & paid)"},
    "gemini": {"name": "Google Gemini", "mode": "online", "icon": "✨", "models": "Gemini 1.5 Flash"},
    "groq": {"name": "Groq", "mode": "online", "icon": "⚡", "models": "Llama 3.1 8B (ultra-fast)"},
    "mistral": {"name": "Mistral", "mode": "online", "icon": "🌀", "models": "Codestral"},
    "deepseek": {"name": "DeepSeek", "mode": "online", "icon": "🔍", "models": "DeepSeek Coder"},
    "ollama": {"name": "Ollama (Local)", "mode": "offline", "icon": "🖥️", "models": "CodeLlama / Local models"},
}
