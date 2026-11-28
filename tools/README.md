# Build scripts

Kept here so the generated pages can be rebuilt.

- `build_v5.py`: builds `v5/index.html` from the live flyer (`index.html`).
- `make_v6.py`: derives `build_v6.py` (shape picker) from `build_v5.py`; run it, then `build_v6.py`.
- `mobile.py`: builds the phone-format PDFs from the canvas page sources.

Paths inside point at the working folders used when they were written; adjust before running.
- `aumbry/`: renders the Aumbry 2.0 previews from `aumbry 2.0 clean.3dm` (Drive, projects/aumbry 2.0) and swaps them into the portfolio PDFs.
  1. `python3 export.py "aumbry 2.0 clean.3dm" model` writes `model.bin`/`model.json` from the render meshes cached in the file (needs `rhino3dm`).
  2. Put `oak.jpg` (the "Oak light" texture) and three.js 0.170 (`npm pack three@0.170.0`, unpacked to `npm/package`) next to `render.html`, serve the folder on port 8765, then `python3 run.py 1.25` renders every shot in `shots.json` to `out/*.png` (transparent, so each can be laid on white or birch).
  3. `python3 swap.py out <dir with the current PDFs> <out dir>` replaces the render images in `aumbry-2.0.pdf` and `aumbry-2.0-mobile.pdf`, keeping layout and text. Grounds follow the design system: white on white pages, birch (#F1E9DC) on birch pages.
