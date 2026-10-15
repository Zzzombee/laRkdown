#!/usr/bin/env python3
"""Create paginated contact sheets from full-slide PNG renders."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def natural_key(path: Path):
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", path.name)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--thumb-width", type=int, default=480)
    args = parser.parse_args()

    images = sorted(
        [path for path in args.image_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg"}],
        key=natural_key,
    )
    if not images:
        parser.error(f"No slide images found in {args.image_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    font = ImageFont.load_default()
    label_height = 28
    margin = 16
    per_page = args.columns * args.rows
    for page_index in range((len(images) + per_page - 1) // per_page):
        page_paths = images[page_index * per_page : (page_index + 1) * per_page]
        with Image.open(page_paths[0]) as sample:
            thumb_height = round(args.thumb_width * sample.height / sample.width)
        canvas_width = margin + args.columns * (args.thumb_width + margin)
        canvas_height = margin + args.rows * (thumb_height + label_height + margin)
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, path in enumerate(page_paths):
            row, column = divmod(slot, args.columns)
            x = margin + column * (args.thumb_width + margin)
            y = margin + row * (thumb_height + label_height + margin)
            with Image.open(path) as image:
                thumb = image.convert("RGB")
                thumb.thumbnail((args.thumb_width, thumb_height), Image.Resampling.LANCZOS)
                canvas.paste(thumb, (x, y))
            draw.text((x, y + thumb_height + 4), path.stem, fill="black", font=font)
        output = args.output_dir / f"contact-sheet-{page_index + 1:03d}.jpg"
        canvas.save(output, quality=90)
    print(f"Created {(len(images) + per_page - 1) // per_page} contact sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
