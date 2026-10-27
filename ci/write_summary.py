"""Publish actual evidence values to the GitHub Actions run summary."""
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
reports = root / "reports"
lines = ["## Track E pipeline evidence", "", "| Measure | Result |", "|---|---|"]
for level in ["unit", "integration", "bdd"]:
    path = reports / f"{level}.xml"
    if not path.exists():
        lines.append(f"| {level} | Not completed |")
        continue
    cases = list(ET.parse(path).getroot().iter("testcase"))
    failed = sum(any(c.find(t) is not None for t in ["failure", "error", "skipped"]) for c in cases)
    lines.append(f"| {level} | {len(cases)-failed}/{len(cases)} passed |")
for kind in ["coverage", "mutation"]:
    path = reports / f"{kind}_gate.json"
    value = path.read_text().replace("\n", " ") if path.exists() else "Not passed or not reached; see step logs"
    lines.append(f"| {kind} gate | {value} |")
lines += ["", "BDD scope: filter compiler component. Integration scope: filter compiler and real local LanceDB table.",
          "Gate demonstration mode: " + os.environ.get("DEMO", "none"), ""]
text = "\n".join(lines)
print(text)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle:
        handle.write(text)
