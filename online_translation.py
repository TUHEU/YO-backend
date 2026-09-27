# -*- coding: utf-8 -*-
"""
Optional online fallback for words the glossary doesn't cover, used only for the
Pidgin/Franc-anglais -> French/English direction (there's no public API that knows
Yaoundé Pidgin, so it can't help the reverse direction).

On by default (YO_B_ONLINE_TRANSLATION=false to disable). Every call is wrapped in a
short timeout and a broad except: a slow or unreachable network must never hang a
translation request or crash the app.
"""

import logging

try:
    import requests
except ImportError:  # pragma: no cover - requests is in requirements.txt
    requests = None

logger = logging.getLogger(__name__)

_MYMEMORY_URL = "https://api.mymemory.translated.net/get"
_TARGET_CODE = {"french": "fr", "english": "en"}
# MyMemory has no "auto-detect" source language (a langpair like "auto|fr" is invalid
# and — critically — the API answers that with HTTP 200 and an *error explanation*
# sitting in responseData.translatedText, which looks exactly like a real translation
# unless it's specifically checked for). Since we don't know a lone word's source
# language, we guess it as the *other* language from the target: a word Yo-B's own
# lexicon can't place is most likely a borrowing from English or French rather than
# from Pidgin (which MyMemory doesn't know regardless).
_GUESSED_SOURCE = {"french": "en", "english": "fr"}

# Substrings MyMemory's own error/help text is known to contain — never treated as a
# real translation even if the HTTP call otherwise "succeeds".
_ERROR_MARKERS = (
    "invalid source language", "invalid target language", "langpair=",
    "iso 639", "rfc3066", "must specify", "no translation found",
)


def _looks_like_api_error(text):
    lowered = text.lower()
    return any(marker in lowered for marker in _ERROR_MARKERS)


def lookup_online(word, target, timeout_seconds=4.0):
    """Best-effort translation of a single word. Returns None on any failure or any
    response that isn't confidently a real translation — callers must treat that
    exactly like 'the dictionary has no entry either'."""
    if requests is None or not word or not word.strip():
        return None
    try:
        response = requests.get(
            _MYMEMORY_URL,
            params={"q": word, "langpair": _GUESSED_SOURCE[target] + "|" + _TARGET_CODE[target]},
            timeout=(2.0, timeout_seconds),  # (connect timeout, read timeout) — a slow
                                              # or blocked network must fail fast, not hang
        )
        response.raise_for_status()
        body = response.json()
        if body.get("responseStatus") not in (200, "200"):
            return None
        translated = body.get("responseData", {}).get("translatedText")
        if not translated or not translated.strip():
            return None
        translated = translated.strip()
        if _looks_like_api_error(translated):
            logger.warning("online translation returned an API error string for %r -> %s: %s",
                            word, target, translated)
            return None
        if translated.lower() == word.strip().lower():
            return None  # MyMemory echoed the input back: treat as "no answer"
        if len(translated) > 80:
            return None  # a one-word query answered with a paragraph is not a translation
        return translated
    except Exception:
        logger.warning("online translation lookup failed for %r -> %s", word, target, exc_info=True)
        return None

