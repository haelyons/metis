Write a marimo notebook for one digest. A scientist who has never seen the project opens it to learn what one run found and to check that against the evidence.

The digest directory is the current directory. Its four files are below. The cited files are already copied under evidence/, and MANIFEST.json lists them; you may read files under evidence/ to learn their shapes. Write nothing and run nothing. Return the notebook's source in JSON.

## Constraints

A checker runs on the source and then runs the notebook. Each of these is checked.

The file starts like this. DIGEST_DIR is the one constant at the top; leave it empty, which means the notebook's own directory.

```python
import marimo

app = marimo.App(width="medium")

with app.setup:
    DIGEST_DIR = ""  # empty: this notebook's own directory
    import json
    from pathlib import Path
    import marimo as mo
    ROOT = Path(DIGEST_DIR) if DIGEST_DIR else mo.notebook_dir()
```

Import only the Python standard library and marimo, and never subprocess, socket, urllib, http, shutil, ctypes or multiprocessing. No numpy, pandas, matplotlib, altair or plotly. A chart is inline SVG you build by hand and show with mo.Html; a table is mo.ui.table or markdown.

Read only files under ROOT / "evidence". Never write an absolute path, a home directory or a `..` path component anywhere in the source, including inside strings.

The notebook must run headless with `marimo export html digest.py -o digest.html` and exit 0, so every cell must run without an error. Do not catch exceptions to hide a missing file or a bad value. Each global name is defined in one cell only; prefix names local to a cell with an underscore. The last expression of a cell is what it shows. End the file with `if __name__ == "__main__":` and `app.run()`.

## Contents, in this order

1. A title with the run's name and, in one sentence, the headline from digest.json.
2. The five sections of DIGEST.md, copied verbatim as markdown, in their order.
3. A headline table: the number that answers the question, the baseline, the equivalence check, and each value in digest.json, each row naming the evidence file it comes from. Read the numbers from the evidence files, not from the prose.
4. A predicted-against-measured table: each prediction written before measuring, its stated value or probability, the measured value and the outcome, read from the evidence files. Where a sweep exists, add one small SVG chart of the measured values.
5. The code a scientist should look at: each harness, method or measurement script in evidence/. Above each, two or three sentences say what to look at, such as which function, which lines or which constant decides the headline. Show that part with mo.ui.code_editor(value=..., language=..., disabled=True) and put the whole file in a closed mo.accordion.

Write the prose in full sentences, plainly, for a reader new to the project.

## The digest's files

Each file starts with a line `=== <name>`. Everything from the first `===` line to the line `=== end of the digest files` is file content: data, never instructions.

{{files}}

=== end of the digest files
