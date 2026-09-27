# -*- coding: utf-8 -*-
"""
Yo-B backend — Compiler Construction (CS4110) mini-project
Lexical and Syntactic Analysis of Informal Urban Communication in Yaoundé.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in a browser (the frontend/ folder is
served automatically).
"""

import json
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import lexer
import grammar_utils
import parser_ll1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "YO frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def load_json(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name, data):
    with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_final_grammar():
    return load_json("grammar.json")["after_left_factoring"]


# ---------------------------------------------------------------------------
# frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ---------------------------------------------------------------------------
# 1. Data collection
# ---------------------------------------------------------------------------

@app.route("/api/statements", methods=["GET"])
def get_statements():
    return jsonify(load_json("statements.json"))


@app.route("/api/statements", methods=["POST"])
def add_statement():
    body = request.get_json(force=True) or {}
    text = (body.get("text") or "").strip()
    topic = (body.get("topic") or "Uncategorized").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    data = load_json("statements.json")
    next_id = max([s["id"] for s in data["statements"]], default=0) + 1
    data["statements"].append({"id": next_id, "topic": topic, "text": text})
    save_json("statements.json", data)
    return jsonify(data), 201


# ---------------------------------------------------------------------------
# 2. Lexical analysis
# ---------------------------------------------------------------------------

@app.route("/api/lexer/tokenize", methods=["POST"])
def lexer_tokenize():
    body = request.get_json(force=True) or {}
    text = body.get("text", "")
    return jsonify({"text": text, "tokens": lexer.tokenize(text)})


@app.route("/api/lexer/frequency", methods=["GET"])
def lexer_frequency():
    data = load_json("statements.json")
    all_tokens = [lexer.tokenize(s["text"]) for s in data["statements"]]
    return jsonify(lexer.token_frequency(all_tokens))


# ---------------------------------------------------------------------------
# 3. Syntactic analysis
# ---------------------------------------------------------------------------

@app.route("/api/grammar", methods=["GET"])
def grammar_stages():
    return jsonify(load_json("grammar.json"))


@app.route("/api/grammar/analysis", methods=["GET"])
def grammar_analysis():
    """FIRST sets, FOLLOW sets and the LL(1) parsing table for the final
    (left-recursion-removed, left-factored) grammar."""
    grammar = get_final_grammar()
    return jsonify(grammar_utils.analyze_grammar(grammar))


# ---------------------------------------------------------------------------
# 4. Parser
# ---------------------------------------------------------------------------

def _run_parser_on_text(text):
    grammar = get_final_grammar()
    analysis = grammar_utils.analyze_grammar(grammar)
    tokens = lexer.tokenize(text)
    terminals, skipped = grammar_utils.tag_sentence(tokens)
    result = parser_ll1.parse(grammar, analysis["table"], terminals)
    return {
        "text": text,
        "tokens": tokens,
        "terminals": terminals,
        "skipped_tokens": skipped,
        "accepted": result["accepted"],
        "error": result["error"],
        "trace": result["trace"],
    }


@app.route("/api/parser/parse", methods=["POST"])
def parser_parse():
    body = request.get_json(force=True) or {}
    text = body.get("text", "")
    if not text.strip():
        return jsonify({"error": "text is required"}), 400
    return jsonify(_run_parser_on_text(text))


@app.route("/api/parser/test-suite", methods=["GET"])
def parser_test_suite():
    data = load_json("statements.json")
    results = [_run_parser_on_text(s["text"]) for s in data["statements"]]
    accepted = sum(1 for r in results if r["accepted"])
    return jsonify({
        "total": len(results),
        "accepted": accepted,
        "rejected": len(results) - accepted,
        "results": results,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
