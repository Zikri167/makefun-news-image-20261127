"""Entry point: render the 27 November 2026 front page to entry.png."""
import os

from draw import render_png

out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
    fh.write(render_png())
