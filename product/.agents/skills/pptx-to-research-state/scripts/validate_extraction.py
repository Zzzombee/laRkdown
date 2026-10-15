#!/usr/bin/env python3
"""Cross-check structural extraction, slide renders, media assets and explicit visual-review coverage."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def slide_number(path: Path) -> int | None:
    match = re.search(r"(\d+)(?=\D*$)", path.stem)
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--media-manifest", type=Path)
    parser.add_argument("--visual-review", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    structure = json.loads(args.structure.read_text(encoding="utf-8"))
    expected = int(structure["slide_count"])
    render_paths = [
        path for path in args.renders.iterdir() if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    render_numbers = {number for path in render_paths if (number := slide_number(path)) is not None}
    issues = []
    if len(render_paths) != expected:
        issues.append({"code": "render-count", "expected": expected, "actual": len(render_paths)})
    missing = sorted(set(range(1, expected + 1)) - render_numbers)
    if missing:
        issues.append({"code": "missing-render-numbers", "slides": missing})
    structure_errors = [item for item in structure.get("warnings", []) if item.get("severity", "error") == "error"]
    if structure_errors:
        issues.append({"code": "structure-errors", "count": len(structure_errors)})

    media_summary = None
    if args.media_manifest:
        media = json.loads(args.media_manifest.read_text(encoding="utf-8"))
        if media.get("source", {}).get("sha256") != structure["source"]["sha256"]:
            issues.append({"code": "media-source-mismatch"})
        media_summary = {
            "assets": media.get("asset_count", 0),
            "occurrences": media.get("occurrence_count", 0),
            "warnings": len(media.get("warnings", [])),
        }
        for asset in media.get("assets", []):
            original = args.media_manifest.parent / asset["original"]
            if not original.is_file():
                issues.append({"code": "missing-original-image", "path": str(original)})
            elif hashlib.sha256(original.read_bytes()).hexdigest() != asset["sha256"]:
                issues.append({"code": "original-image-hash-mismatch", "path": str(original)})
            for frame in asset.get("frames", []):
                preview = args.media_manifest.parent / frame["preview"]
                if not preview.is_file():
                    issues.append({"code": "missing-image-preview", "path": str(preview)})
        media_errors = [item for item in media.get("warnings", []) if item.get("severity", "error") == "error"]
        if media_errors:
            issues.append({"code": "media-errors", "count": len(media_errors)})

    visual = json.loads(args.visual_review.read_text(encoding="utf-8"))
    if visual.get("source_sha256") != structure["source"]["sha256"]:
        issues.append({"code": "visual-source-mismatch"})
    reviews = visual.get("reviews", [])
    reviewed_numbers = [item.get("slide") for item in reviews]
    if sorted(reviewed_numbers) != list(range(1, expected + 1)):
        issues.append({"code": "visual-review-coverage"})
    for item in reviews:
        if item.get("evidence_bearing", True):
            if item.get("completed") is not True or not item.get("reader") or not item.get("inspected_files") or item.get("unreadable"):
                issues.append({"code": "visual-review-incomplete", "slide": item.get("slide")})
            render = (args.visual_review.parent / item.get("render", "")).resolve()
            if render.parent != args.renders.resolve() or slide_number(render) != item.get("slide") or not render.is_file():
                issues.append({"code": "visual-render-mismatch", "slide": item.get("slide")})
            inspected = [args.visual_review.parent / name for name in item.get("inspected_files", [])]
            if not inspected or any(not path.is_file() or not path.resolve().is_relative_to(args.visual_review.parent.resolve()) for path in inspected):
                issues.append({"code": "missing-inspected-image", "slide": item.get("slide")})
            if render not in [path.resolve() for path in inspected]:
                issues.append({"code": "full-slide-not-inspected", "slide": item.get("slide")})

    report = {
        "ok": not issues,
        "slide_count": expected,
        "render_count": len(render_paths),
        "media": media_summary,
        "visual_review_count": len(reviews),
        "visual_limit": "Ledger coverage is validated; actual vision accuracy and tool use require independent review",
        "issues": issues,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
