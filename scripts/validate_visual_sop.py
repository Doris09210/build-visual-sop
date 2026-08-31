from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated visual SOP HTML")
    parser.add_argument("html", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    text = args.html.read_text(encoding="utf-8")
    embedded = len(re.findall(r'<img[^>]+src="data:image/', text))
    external = len(re.findall(r'<img[^>]+src="(?!data:)', text))
    cards = text.count('class="step-card"')
    failures = []
    if embedded != cards:
        failures.append(f"embedded images ({embedded}) != step cards ({cards})")
    if external:
        failures.append(f"external image references found: {external}")
    for required in ("aria-current", "section-active", "setActive", "side.scrollTop", "data-section"):
        if required not in text:
            failures.append(f"missing scroll-spy marker: {required}")
    expected_sections = expected_steps = expected_redactions = None
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        expected_sections = len(manifest.get("sections", []))
        expected_steps = sum(len(section.get("steps", [])) for section in manifest.get("sections", []))
        expected_redactions = sum(len(step.get("redactions", [])) for section in manifest.get("sections", []) for step in section.get("steps", []))
        if cards != expected_steps:
            failures.append(f"step cards ({cards}) != manifest steps ({expected_steps})")
        if text.count('class="sop-head"') != expected_sections:
            failures.append("section count does not match manifest")
    result = {"file": str(args.html.resolve()), "bytes": args.html.stat().st_size, "sections": expected_sections, "steps": cards, "embedded_images": embedded, "external_images": external, "manifest_redactions": expected_redactions, "scroll_spy": not any("scroll-spy" in item for item in failures), "valid": not failures, "failures": failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
