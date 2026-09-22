#!/usr/bin/env python3
"""De-AI narration pass (v5) — tramstop four-layer model applied to episode copy.

The human-writing prose gate (check_prose.py) already bans surface AI markers
(vocabulary & syntax layers). This pass targets the deeper layers that gate
cannot see, per tramstop-skill's evidence-based model:

- STRUCTURE layer: every scene ending on a punchline / perfect echo closure;
  tour-guide signposting ("接下来我们看"); over-balanced parallel sections.
- EXPERIENCE layer: details that could be swapped for any other example;
  both-ways hedged judgments; narrator absent from the text.

This is a *report* tool: it prints per-scene findings ranked by weight
(experience >= structure > syntax > vocabulary) plus concrete rewrite hints.
The agent (or daily routine) applies rewrites in storyboard.json, then re-runs
the human prose gate + this report until findings clear. It never edits files.

Usage: python deai_narration.py <project_dir>
Exit code 0 always; findings list is the interface.
"""
import argparse
import json
import pathlib
import re
import sys

# structure layer (deeper than check_prose.py's vocabulary/syntax bans)
STRUCTURE_PATTERNS = [
    (re.compile(r"^(收束一下|收个尾|收尾。|最后我们|接下来我们|下面我们|让我们)", re.M), "导游式路标开头（tour-guide signpost）"),
    (re.compile(r"(这，就是|这便是|这正是)[^。]*。$", re.M), "金句收束（每节落 punchline）"),
    (re.compile(r"完美闭环|呼应了开头|回到我们(开头|最初)", re.M), "结尾回扣升华（perfect echo closure）"),
    (re.compile(r"一边…一边|一方面.*另一方面", re.M), "过度工整的对偶节"),
]
# experience layer proxies
EXPERIENCE_CHECKS = [
    (re.compile(r"可能|或许|在某些情况下|具体取决于", re.M), "两头堵限定（hedged judgment）"),
    (re.compile(r"许多|不少|大量|显著|一定程度", re.M), "不给数字的模糊量词（swappable detail）"),
]

TOPIC_WORD = re.compile(r"值得(一说|一提)的是|换句话说|归(believe|根结底)?")


def scan_scene(idx, sc):
    findings = []
    text = sc.get("narration", "")
    for pat, label in STRUCTURE_PATTERNS:
        for m in pat.finditer(text):
            ctx = text[max(0, m.start() - 12):m.end() + 12].replace("\n", " ")
            findings.append(("structure", f"scene {idx:02d} [{sc.get('topic','')}]", label, ctx))
    for pat, label in EXPERIENCE_CHECKS:
        hits = len(pat.findall(text))
        if hits:
            findings.append(("experience", f"scene {idx:02d} [{sc.get('topic','')}]", f"{label} ×{hits}", text[:44]))
    # swap-detail heuristic: abstract generic phrasing with no proper noun/number
    if not re.search(r"[A-Za-z]{3,}|\d", text):
        findings.append(("experience", f"scene {idx:02d} [{sc.get('topic','')}]", "全段无专名无数字（细节可替换嫌疑）", text[:44]))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    p = pathlib.Path(args.project).resolve()
    sb = json.loads((p / "storyboard.json").read_text(encoding="utf-8"))
    all_findings = []
    for i, sc in enumerate(sb["scenes"], 1):
        all_findings.extend(scan_scene(i, sc))
    # rank: experience >= structure
    rank = {"experience": 0, "structure": 1}
    all_findings.sort(key=lambda f: rank.get(f[0], 9))
    if not all_findings:
        print("DE-AI report: clean — no structure/experience layer findings.")
        return
    print(f"DE-AI report: {len(all_findings)} findings (experience layer first):")
    for layer, where, label, ctx in all_findings[:20]:
        print(f"  [{layer:9s}] {where} · {label} · …{ctx}…")
    print("Rewrite hints: replace hedged judgments with committable statements "
          "(numbers, named comparisons); cut tour-guide openers; let endings stop "
          "where thought stops; keep any real, oddly-specific detail even if it "
          "serves no argument.")


if __name__ == "__main__":
    sys.exit(main())
