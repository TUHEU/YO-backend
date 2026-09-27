# -*- coding: utf-8 -*-
"""
LL(1) predictive parser. Given an LL(1) table (built by grammar_utils) and a
list of input terminals, simulates the standard stack-based algorithm and
returns a step-by-step trace plus an accept/reject verdict.
"""

EPS = "EPS"
END = "$"


def parse(grammar, table, terminals):
    start = grammar["start"]
    stack = [END, start]
    input_symbols = list(terminals) + [END]
    pos = 0
    trace = []
    accepted = False
    error = None

    max_steps = 500
    steps = 0
    while stack and steps < max_steps:
        steps += 1
        top = stack[-1]
        current = input_symbols[pos] if pos < len(input_symbols) else END

        row = {
            "stack": " ".join(reversed(stack)),
            "remaining_input": " ".join(input_symbols[pos:]),
        }

        if top == END and current == END:
            row["action"] = "ACCEPT"
            trace.append(row)
            accepted = True
            break

        if top not in grammar["productions"]:
            # top is a terminal (or END) — must match current input symbol
            if top == current:
                row["action"] = "MATCH {}".format(top)
                trace.append(row)
                stack.pop()
                pos += 1
                continue
            else:
                row["action"] = "ERROR: expected '{}' but found '{}'".format(top, current)
                trace.append(row)
                error = row["action"]
                break

        # top is a non-terminal: consult the LL(1) table
        production = table.get(top, {}).get(current)
        if production is None:
            row["action"] = (
                "ERROR: no rule for {} on input '{}' "
                "(sentence does not fit the grammar)".format(top, current)
            )
            trace.append(row)
            error = row["action"]
            break

        row["action"] = "{} -> {}".format(top, " ".join(production))
        trace.append(row)
        stack.pop()
        if production != [EPS]:
            for symbol in reversed(production):
                stack.append(symbol)

    return {
        "accepted": accepted,
        "error": error,
        "trace": trace,
    }
