"""
Apply: replace the spiral spine + punch holes with a centre gutter (Book view
of recipe_management.html).

Removes the .book-spine (rings) element and the two .book-punch-holes blocks,
puts a soft centre-fold gutter between the two pages, and rounds the book's
outer corners. Purely cosmetic; no JS touched. The page-turn added earlier is
unaffected -- in fact it now pivots exactly on the true page centre.

Two edits, both fail-loud (each anchor must match exactly once or NOTHING is
written). Line endings are normalised for matching and the file's original
endings (CRLF on Windows) are restored on write, so the git diff stays clean.

Note: this leaves the now-unused .book-spine / .spine-ring / .book-punch-holes
/ .punch-hole CSS rules in place (harmless dead code). Say the word and I'll
give you a tiny follow-up to strip them.

Run from the repo root:  python apply_book_gutter.py
"""
import os
import sys

PATH = os.path.join("pages", "templates", "recipe_management.html")

# ---- Edit 1: HTML -- swap spine + punch-hole blocks for a gutter ------------
OLD_HTML = """                <div class="book-punch-holes book-punch-holes-right">
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                </div>
            </div>

            <div class="book-spine">
                <div class="spine-ring"></div><div class="spine-ring"></div><div class="spine-ring"></div>
                <div class="spine-ring"></div><div class="spine-ring"></div><div class="spine-ring"></div>
                <div class="spine-ring"></div><div class="spine-ring"></div><div class="spine-ring"></div>
            </div>

            <div class="book-page book-page-right" id="bookPageRight">
                <div class="book-punch-holes book-punch-holes-left">
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                    <div class="punch-hole"></div><div class="punch-hole"></div><div class="punch-hole"></div>
                </div>"""

NEW_HTML = """            </div>

            <div class="book-gutter"></div>

            <div class="book-page book-page-right" id="bookPageRight">"""

# ---- Edit 2: CSS -- append gutter + rounded outer corners -------------------
OLD_CSS = (".book-page-right::after { content: ''; position: absolute; bottom: 0; "
           "right: 0; width: 40px; height: 40px; background: linear-gradient(225deg, "
           "#e8d9c0 45%, transparent 45%); box-shadow: -2px -2px 4px rgba(0,0,0,0.15); "
           "z-index: 5; }")

NEW_CSS = OLD_CSS + """

/* Centre gutter -- replaces the spiral spine. Soft fold where the pages meet. */
.book-gutter {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 64px;
    transform: translateX(-50%);
    z-index: 7;
    pointer-events: none;
    background: linear-gradient(90deg,
        rgba(60,45,20,0)    0%,
        rgba(60,45,20,0.05) 30%,
        rgba(60,45,20,0.16) 46%,
        rgba(60,45,20,0.28) 50%,
        rgba(60,45,20,0.16) 54%,
        rgba(60,45,20,0.05) 70%,
        rgba(60,45,20,0)    100%);
}
/* Rounded outer corners now that the spine no longer caps the left edge */
.book-page-left  { border-radius: 6px 0 0 6px; }
.book-page-right { border-radius: 0 6px 6px 0; }"""

EDITS = [(OLD_HTML, NEW_HTML), (OLD_CSS, NEW_CSS)]


def main():
    if not os.path.isfile(PATH):
        sys.exit(f"ABORT: {PATH} not found (run from repo root).")

    with open(PATH, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    crlf = "\r\n" in raw
    norm = raw.replace("\r\n", "\n")

    problems = []
    for old, new in EDITS:
        c = norm.count(old)
        if c != 1:
            problems.append(f"anchor found {c}x (expected 1): {old[:55]!r}...")
        if new in norm:
            problems.append(f"replacement already present: {new[:55]!r}...")
    if problems:
        print("ABORT -- nothing written:")
        for p in problems:
            print("  -", p)
        print("Diagnostics (after newline-normalisation):")
        for probe, label in [('<div class="book-spine">', "spine element"),
                             (".book-page-right::after", "CSS anchor line")]:
            print(f"  {label!r}: {norm.count(probe)} match(es)")
        sys.exit(1)

    out = norm
    for old, new in EDITS:
        out = out.replace(old, new)
    if crlf:
        out = out.replace("\n", "\r\n")

    with open(PATH + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(raw)
    with open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print(f"OK: {PATH} updated (spine -> centre gutter).  Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py check ; hard-refresh Recipe Management > Book view.")


if __name__ == "__main__":
    main()