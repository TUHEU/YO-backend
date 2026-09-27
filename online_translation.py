# -*- coding: utf-8 -*-
"""
Optional online fallback for words the glossary doesn't cover, used only for the
Pidgin/Franc-anglais -> French/English direction (there's no public API that knows
Yaoundé Pidgin, so it can't help the reverse direction).

Off by default. Turn on with the environment variable YO_B_ONLINE_TRANSLATION=true.
Every call is wrapped in a short timeout and a broad except: a slow or unreachable
network must never hang a translation request or crash the app.
"""

import logging

try:
    import requests
except ImportError:  # pragma: no cover - requests is in requirements.txt
    requests = None

logger = logging.getLogger(__name__)

_MYMEMORY_URL = "https://api.mymemory.translated.net/get"
_TARGET_CODE = {"french": "fr", "english": "en"}


def lookup_online(word, target, timeout_seconds=4.0):
    """Best-effort translation of a single word. Returns None on any failure —
    callers must treat that exactly like 'the dictionary has no entry either'."""
    if requests is None or not word or not word.strip():
        return None
    try:
        response = requests.get(
            _MYMEMORY_URL,
            params={"q": word, "langpair": "auto|" + _TARGET_CODE[target]},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        translated = body.get("responseData", {}).get("translatedText")
        if not translated or not translated.strip():
            return None
        if translated.strip().lower() == word.strip().lower():
            return None  # MyMemory echoed the input back: treat as "no answer"
        return translated.strip()
    except Exception:
        logger.warning("online translation lookup failed for %r -> %s", word, target, exc_info=True)
        return None
