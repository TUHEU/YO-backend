# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import translation
import online_translation


def test_forward_translation_to_french_uses_dictionary():
    result = translation.translate("Bendskin hala me small money", "to_french")
    words = {w["source"]: w for w in result["words"]}
    assert words["Bendskin"]["translation"] == "moto-taxi"
    assert words["Bendskin"]["status"] == "dictionary"
    assert result["used_online_fallback"] is False


def test_forward_translation_to_english_uses_dictionary():
    result = translation.translate("Taxi drop me for quartier", "to_english")
    assert "taxi" in result["translated_text"].lower()
    assert "neighborhood" in result["translated_text"].lower()


def test_unresolved_word_is_flagged_not_invented():
    result = translation.translate("blahblah quartier", "to_french")
    assert "blahblah" in result["unresolved_words"]
    words = {w["source"]: w for w in result["words"]}
    assert words["blahblah"]["status"] == "unresolved"
    assert words["blahblah"]["translation"] == "blahblah"


def test_reverse_translation_english_to_pidgin():
    result = translation.translate("the money for the road", "from_english")
    words = {w["source"]: w for w in result["words"]}
    assert words["money"]["translation"] == "argent"
    assert words["road"]["translation"] == "route"


def test_reverse_translation_french_to_pidgin():
    result = translation.translate("argent pour la route", "from_french")
    words = {w["source"]: w for w in result["words"]}
    assert words["argent"]["status"] == "dictionary"


def test_reverse_direction_never_uses_online_fallback():
    # Even if an online_lookup callable is supplied, the reverse direction must
    # never call it — no public API is trained on Yaoundé Pidgin as a target.
    calls = []
    def fake_lookup(word, target):
        calls.append(word)
        return "SHOULD-NOT-BE-USED"
    translation.translate("some unresolved word here", "from_english", online_lookup=fake_lookup)
    assert calls == []


def test_invalid_direction_raises():
    import pytest
    with pytest.raises(ValueError):
        translation.translate("hello", "sideways")


# --- online_translation.py: the bug fixed in this revision ----------------------

def test_online_lookup_rejects_known_api_error_text():
    error_text = (
        "'AUTO' IS AN INVALID SOURCE LANGUAGE . EXAMPLE: LANGPAIR=EN|IT USING 2 "
        "LETTER ISO OR RFC3066 LIKE ZH-CN. ALMOST ALL LANGUAGES SUPPORTED BUT SOME "
        "MAY HAVE NO CONTENT"
    )
    assert online_translation._looks_like_api_error(error_text) is True


def test_online_lookup_does_not_flag_a_plausible_translation():
    assert online_translation._looks_like_api_error("réclamer de l'argent") is False


def test_online_lookup_never_sends_auto_as_source_language():
    # The bug: langpair="auto|fr" is invalid and MyMemory answers with HTTP 200 and
    # its own error text embedded as the "translation". The fix guesses a real
    # source-language code instead of ever sending "auto".
    assert "auto" not in online_translation._GUESSED_SOURCE.values()
    assert online_translation._GUESSED_SOURCE["french"] in ("en", "fr")
    assert online_translation._GUESSED_SOURCE["english"] in ("en", "fr")
