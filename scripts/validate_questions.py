#!/usr/bin/env python3
"""Validate a Jev question spec before running it.

Usage: python3 validate_questions.py spec.json
The spec is either {"questions": {...}} or a bare {key: question} map.
Exit 1 on any error. Warnings do not fail.
"""
import json, sys, re

ESCAPES = {"other", "unclear", "unknown", "not_stated", "none", "none_of_the_above", "cannot_tell"}

def main(path):
    data = json.load(open(path))
    qs = data.get("questions", data) if isinstance(data, dict) else None
    if not isinstance(qs, dict) or not qs:
        print("ERROR: spec must be an object of questions"); return 1
    errors, warns = [], []
    for key, q in qs.items():
        t = q.get("type"); ins = q.get("instructions"); crit = q.get("criteria")
        if t not in ("choice", "score", "noul"):
            errors.append(f"{key}: type must be choice, score, or noul (got {t!r})"); continue
        text = ins if isinstance(ins, str) else json.dumps(ins or "")
        if not text or len(text.split()) < 4:
            errors.append(f"{key}: instructions must hold the full question; the key name is not sent to the model")
        if t == "choice":
            if not isinstance(crit, dict) or not (2 <= len(crit) <= 255):
                errors.append(f"{key}: choice needs 2 to 255 options as a criteria object (got {len(crit) if isinstance(crit, dict) else 'none'})")
            else:
                for opt, desc in crit.items():
                    if not str(desc).strip(): errors.append(f"{key}: option {opt!r} has no criterion")
                    if re.search(r"\b(somewhat|fairly|quite|very|slightly|moderately)\b", str(desc), re.I):
                        warns.append(f"{key}.{opt}: criterion uses a degree word; describe the situation instead")
                if not (set(crit) & ESCAPES):
                    warns.append(f"{key}: no escape option (other/unclear/unknown/not_stated); empty or vague inputs will be forced into a real category")
                elif not any(re.search(rf"\b{re.escape(e)}\b", text, re.I) for e in set(crit) & ESCAPES):
                    warns.append(f"{key}: has an escape option but the instructions never say when to use it")
        elif t == "score":
            if not isinstance(crit, list) or not (2 <= len(crit) <= 10):
                errors.append(f"{key}: score needs an ordered list of 2 to 10 levels")
            elif all(re.fullmatch(r"\s*\d+(\.\d+)?\s*", str(c)) for c in crit):
                warns.append(f"{key}: score levels are bare numbers; use descriptive labels so the model has something to match")
        elif t == "noul":
            if isinstance(crit, dict) and set(crit) - {"true", "false"}:
                errors.append(f"{key}: noul criteria may only have 'true' and 'false' keys")
            if not re.search(r"\?$|\b(is|does|do|did|has|have|was|are|should|could|can|would|will|contains|matches)\b", text, re.I):
                warns.append(f"{key}: noul instructions should read as a statement or yes/no question")
        if " and " in text.lower() and t != "score" and len(text.split()) > 12 and text.lower().count(" and ") >= 3:
            warns.append(f"{key}: instructions join several judgments with 'and'; consider splitting into separate questions")
    if isinstance(data, dict):
        known = set(qs) | {f"{k}.{x}" for k in qs for x in ("confidence", "score", "noul")}
        for rule in data.get("buckets") or []:
            for cond in (rule.get("when") or []) + (rule.get("any") or []):
                if not isinstance(cond, list) or len(cond) != 3:
                    errors.append(f"bucket {rule.get('name')}: each condition is [path, op, value]")
                elif cond[1] not in ("==", "!=", ">=", ">", "<=", "<", "in", "not_in"):
                    errors.append(f"bucket {rule.get('name')}: unknown operator {cond[1]!r}")
                elif cond[0] not in known and "." in cond[0]:
                    errors.append(f"bucket {rule.get('name')}: {cond[0]!r} is not a question output")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print(f"{len(qs)} questions, {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1]))
