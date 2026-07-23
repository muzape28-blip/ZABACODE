"""
ZABACODE Core — Multi-Provider AI Chat Handlers
Supports: OpenRouter, Gemini, Groq, Mistral, DeepSeek, Ollama (local)
"""

import json
import urllib.request
import urllib.error

ALLOWED_PROVIDERS = {"openrouter", "gemini", "groq", "mistral", "deepseek", "ollama"}

# Default system prompt (Updated to English and Tsundere persona as requested)
SYSTEM_PROMPT = (
    "You are Zabacode AI, an adaptive, sharp-tongued/tsundere coding assistant. "
    "You like to tease Zaba, but are extremely expert at helping with Python coding on Android. "
    "Answer concisely, directly, and go straight to the solution in English."
)


def _handle_url_error(e: Exception, provider_name: str) -> dict:
    """Handle URL errors from AI providers, returning error dict with rate-limit flag."""
    is_rate_limit = False
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (429, 402):
            is_rate_limit = True
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
            err_json = json.loads(err_body)
            if isinstance(err_json.get("error"), dict):
                msg = err_json["error"].get("message", str(e))
            else:
                msg = err_json.get("error") or str(e)
            
            lower_msg = msg.lower()
            if any(w in lower_msg for w in ("rate limit", "quota", "credit", "billing", "balance", "insufficient", "exhausted")):
                is_rate_limit = True

            return {"ok": False, "message": f"{provider_name} error ({e.code}): {msg}", "is_rate_limit": is_rate_limit}
        except Exception:
            return {"ok": False, "message": f"{provider_name} error ({e.code})", "is_rate_limit": is_rate_limit}
            
    err_str = str(e)
    lower_err = err_str.lower()
    if any(w in lower_err for w in ("rate limit", "quota", "credit", "billing", "balance", "insufficient", "exhausted")):
        is_rate_limit = True
    return {"ok": False, "message": f"{provider_name} error: {e}", "is_rate_limit": is_rate_limit}


def call_openrouter(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call OpenRouter API (supports multiple models)."""
    actual_model = model if (model and model.strip()) else "qwen/qwen-2.5-coder-32b-instruct:free"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "model": actual_model,
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


def call_gemini(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call Google Gemini API."""
    actual_model = model if (model and model.strip()) else "gemini-1.5-flash"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_content}]}]
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={api_key}",
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


def call_groq(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call Groq API (ultra-fast inference)."""
    actual_model = model if (model and model.strip()) else "llama-3.1-8b-instant"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "model": actual_model,
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


def call_mistral(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call Mistral API (Codestral model)."""
    actual_model = model if (model and model.strip()) else "codestral-latest"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "model": actual_model,
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


def call_deepseek(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call DeepSeek API (coding-specialized model)."""
    actual_model = model if (model and model.strip()) else "deepseek-coder"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "model": actual_model,
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


def call_ollama(api_key: str, message: str, code_context: str = "", model: str = "") -> dict:
    """Call Ollama local API (offline-capable, runs on localhost)."""
    actual_model = model if (model and model.strip()) else "codellama"
    user_content = f"Active code editor content:\n```python\n{code_context}\n```\n\nQuestion: {message}" if code_context else message
    body = json.dumps({
        "model": actual_model,
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
