# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import app as app_module


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_index_serves_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Yo-B" in res.data


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_get_statements_returns_all_14(client):
    res = client.get("/api/statements")
    assert res.status_code == 200
    assert len(res.get_json()["statements"]) == 14


def test_lexer_tokenize_endpoint(client):
    res = client.post("/api/lexer/tokenize", json={"text": "Taxi drop me"})
    assert res.status_code == 200
    tokens = res.get_json()["tokens"]
    assert [t["category"] for t in tokens] == ["NOUN", "VERB", "PRON"]


def test_grammar_analysis_endpoint_reports_ll1(client):
    res = client.get("/api/grammar/analysis")
    assert res.status_code == 200
    assert res.get_json()["is_ll1"] is True


def test_parser_parse_endpoint_accepted(client):
    res = client.post("/api/parser/parse", json={"text": "Taxi drop me for quartier"})
    assert res.status_code == 200
    assert res.get_json()["accepted"] is True


def test_parser_test_suite_endpoint(client):
    res = client.get("/api/parser/test-suite")
    body = res.get_json()
    assert body["total"] == 14
    assert body["accepted"] == 8


def test_translate_endpoint_forward(client):
    res = client.post("/api/translate", json={"text": "Bendskin hala me", "direction": "to_french"})
    assert res.status_code == 200
    assert "moto-taxi" in res.get_json()["translated_text"]


def test_translate_endpoint_rejects_bad_direction(client):
    res = client.post("/api/translate", json={"text": "hello", "direction": "sideways"})
    assert res.status_code == 400


def test_translate_endpoint_rejects_empty_text(client):
    res = client.post("/api/translate", json={"text": "", "direction": "to_french"})
    assert res.status_code == 400
