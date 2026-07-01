"""
Apply: realistic Book-view page turn in recipe_management.html.

Replaces the blank rotating overlay with a content-carrying two-faced leaf
(outgoing page on the front, incoming page on the back), plus a cast shadow
that sweeps across the revealed page, cylinder shading on the leaf, and
weighted easing. Uses the recipes already in BOOK_RECIPES + renderBookRecipeGrid,
so there is no server round-trip. The spine, rings and punch holes are untouched.

Two edits, both fail-loud (each anchor must appear exactly once or NOTHING is
written):
  1. CSS: the .book-flip-overlay block + @keyframes flipForward/flipBack
     -> .book-flip-leaf / .book-flip-face / .book-flip-curl / .book-flip-cast
        + @keyframes bookGlare/bookCast.
  2. JS: the whole bookNavigate() function
     -> bookPageWrap() + buildBookLeaf() helpers + a rewritten bookNavigate()
        (grid mode = content leaf; detail mode = blank paper turn, same async
        content swap as before).

Run from the repo root:  python apply_book_pageturn.py
"""
import os
import sys

PATH = os.path.join("pages", "templates", "recipe_management.html")

# ---------------------------------------------------------------- CSS --------
OLD_CSS = """.book-flip-overlay {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 50%;
    z-index: 100;
    transform-origin: left center;
    transform-style: preserve-3d;
    pointer-events: none;
}

.book-flip-overlay.flip-forward {
    right: 0;
    transform-origin: left center;
    background: linear-gradient(to right, rgba(0,0,0,0.15), #fdf3e3, #f5e6cc);
    background-image: repeating-linear-gradient(transparent, transparent 31px, rgba(180,160,120,0.12) 31px, rgba(180,160,120,0.12) 32px);
    animation: flipForward 0.6s ease-in-out forwards;
}

.book-flip-overlay.flip-back {
    left: 0;
    transform-origin: right center;
    background: linear-gradient(to left, rgba(0,0,0,0.15), #fdf3e3, #f5e6cc);
    background-image: repeating-linear-gradient(transparent, transparent 31px, rgba(180,160,120,0.12) 31px, rgba(180,160,120,0.12) 32px);
    animation: flipBack 0.6s ease-in-out forwards;
}

@keyframes flipForward {
    0%   { transform: rotateY(0deg); box-shadow: -4px 0 12px rgba(0,0,0,0.2); }
    40%  { box-shadow: -20px 0 40px rgba(0,0,0,0.35); }
    100% { transform: rotateY(-180deg); box-shadow: none; }
}

@keyframes flipBack {
    0%   { transform: rotateY(0deg); box-shadow: 4px 0 12px rgba(0,0,0,0.2); }
    40%  { box-shadow: 20px 0 40px rgba(0,0,0,0.35); }
    100% { transform: rotateY(180deg); box-shadow: none; }
}"""

NEW_CSS = """/* Realistic page turn: content-carrying leaf + cast shadow + cylinder shading */
.book-flip-leaf {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 50%;
    z-index: 100;
    transform-style: preserve-3d;
    pointer-events: none;
    transition: transform 0.85s cubic-bezier(.34,.85,.3,1);
    will-change: transform;
}
.book-flip-leaf.flip-forward { right: 0; transform-origin: left center; }
.book-flip-leaf.flip-forward.turning { transform: rotateY(-180deg); }
.book-flip-leaf.flip-back { left: 0; transform-origin: right center; }
.book-flip-leaf.flip-back.turning { transform: rotateY(180deg); }

.book-flip-face {
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    overflow: hidden;
    background: #fdf8f0;
    background-image: repeating-linear-gradient(transparent, transparent 31px, rgba(180,160,120,0.12) 31px, rgba(180,160,120,0.12) 32px);
    box-shadow: inset 0 0 30px rgba(120,90,50,0.05);
}
.book-flip-front { transform: rotateY(0deg); }
.book-flip-back  { transform: rotateY(180deg); }

.book-flip-curl {
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0;
    background:
        linear-gradient(90deg, rgba(255,255,255,.4), rgba(255,255,255,0) 20%),
        linear-gradient(270deg, rgba(40,25,0,.20), rgba(40,25,0,0) 38%);
}
.book-flip-back .book-flip-curl { transform: scaleX(-1); }
.book-flip-leaf.turning .book-flip-curl { animation: bookGlare 0.85s cubic-bezier(.34,.85,.3,1) both; }
@keyframes bookGlare {
    0%   { opacity: 0; }
    25%  { opacity: 1; }
    75%  { opacity: .7; }
    100% { opacity: 0; }
}

.book-flip-cast {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 50%;
    z-index: 95;
    pointer-events: none;
    opacity: 0;
}
.book-flip-cast.cast-right { right: 0; background: linear-gradient(90deg, rgba(0,0,0,.42), rgba(0,0,0,0) 68%); }
.book-flip-cast.cast-left  { left: 0;  background: linear-gradient(270deg, rgba(0,0,0,.42), rgba(0,0,0,0) 68%); }
.book-flip-cast.animate { animation: bookCast 0.85s cubic-bezier(.34,.85,.3,1) both; }
@keyframes bookCast {
    0%   { opacity: 0; }
    35%  { opacity: .9; }
    70%  { opacity: .45; }
    100% { opacity: 0; }
}"""

# ----------------------------------------------------------------- JS --------
OLD_JS = """function bookNavigate(direction) {
    if (bookMode === 'detail') {
        const currentIndex = BOOK_RECIPES.findIndex(r => r.recipe_id === bookDetailRecipeId);
        const newIndex = currentIndex + direction;
        if (newIndex < 0 || newIndex >= BOOK_RECIPES.length) return;

        document.getElementById('bookPrevBtn').disabled = true;
        document.getElementById('bookNextBtn').disabled = true;

        const book = document.getElementById('recipeBook');
        const overlay = document.createElement('div');
        overlay.className = `book-flip-overlay ${direction > 0 ? 'flip-forward' : 'flip-back'}`;
        book.appendChild(overlay);

        setTimeout(() => { openBookDetail(BOOK_RECIPES[newIndex].recipe_id); }, 300);
        setTimeout(() => { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 620);
        return;
    }

    const perSpread = getRecipesPerSpread();
    const totalSpreads = Math.ceil(BOOK_RECIPES.length / perSpread);
    const newSpread = bookCurrentSpread + direction;
    if (newSpread < 0 || newSpread >= totalSpreads) return;

    document.getElementById('bookPrevBtn').disabled = true;
    document.getElementById('bookNextBtn').disabled = true;

    const book = document.getElementById('recipeBook');
    const overlay = document.createElement('div');
    overlay.className = `book-flip-overlay ${direction > 0 ? 'flip-forward' : 'flip-back'}`;
    book.appendChild(overlay);

    setTimeout(() => {
        bookCurrentSpread = newSpread;
        bookMode = 'grid';
        renderBookSpread();
    }, 300);

    setTimeout(() => {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        const totalSpreadsNow = Math.ceil(BOOK_RECIPES.length / getRecipesPerSpread());
        document.getElementById('bookPrevBtn').disabled = bookCurrentSpread === 0;
        document.getElementById('bookNextBtn').disabled = bookCurrentSpread >= totalSpreadsNow - 1;
    }, 620);
}"""

NEW_JS = """function bookPageWrap(recipes) {
    return `<div class="book-page-content"><div class="book-page-scrollable">${renderBookRecipeGrid(recipes)}</div></div>`;
}

function buildBookLeaf(direction, frontHTML, backHTML) {
    const leaf = document.createElement('div');
    leaf.className = `book-flip-leaf ${direction > 0 ? 'flip-forward' : 'flip-back'}`;
    leaf.innerHTML =
        `<div class="book-flip-face book-flip-front">${frontHTML}<div class="book-flip-curl"></div></div>
         <div class="book-flip-face book-flip-back">${backHTML}<div class="book-flip-curl"></div></div>`;
    return leaf;
}

function bookNavigate(direction) {
    const prevBtn = document.getElementById('bookPrevBtn');
    const nextBtn = document.getElementById('bookNextBtn');
    const book = document.getElementById('recipeBook');

    // ---- Detail mode: blank paper turn; recipe content swaps in via async fetch ----
    if (bookMode === 'detail') {
        const currentIndex = BOOK_RECIPES.findIndex(r => r.recipe_id === bookDetailRecipeId);
        const newIndex = currentIndex + direction;
        if (newIndex < 0 || newIndex >= BOOK_RECIPES.length) return;

        prevBtn.disabled = true;
        nextBtn.disabled = true;

        const leaf = buildBookLeaf(direction, '', '');
        const cast = document.createElement('div');
        cast.className = `book-flip-cast ${direction > 0 ? 'cast-right' : 'cast-left'}`;
        book.appendChild(cast);
        book.appendChild(leaf);
        void leaf.offsetWidth;
        cast.classList.add('animate');
        leaf.classList.add('turning');

        setTimeout(() => { openBookDetail(BOOK_RECIPES[newIndex].recipe_id); }, 320);

        let done = false;
        const finish = () => {
            if (done) return;
            done = true;
            clearTimeout(safety);
            if (leaf.parentNode) leaf.remove();
            if (cast.parentNode) cast.remove();
        };
        const safety = setTimeout(finish, 1100);
        leaf.addEventListener('transitionend', e => {
            if (e.propertyName === 'transform' && e.target === leaf) finish();
        });
        return;
    }

    // ---- Grid mode: two-faced content leaf (outgoing front / incoming back) ----
    const perPage = bookRecipesPerPage;
    const perSpread = perPage * 2;
    const totalSpreads = Math.ceil(BOOK_RECIPES.length / perSpread);
    const newSpread = bookCurrentSpread + direction;
    if (newSpread < 0 || newSpread >= totalSpreads) return;

    prevBtn.disabled = true;
    nextBtn.disabled = true;

    const newStart = newSpread * perSpread;
    const newLeft = BOOK_RECIPES.slice(newStart, newStart + perPage);
    const newRight = BOOK_RECIPES.slice(newStart + perPage, newStart + perSpread);

    let leaf, cast;
    if (direction > 0) {
        // Right page turns to the left; reveal the new right page underneath.
        const oldRStart = bookCurrentSpread * perSpread + perPage;
        const oldRight = BOOK_RECIPES.slice(oldRStart, oldRStart + perPage);
        document.getElementById('bookPageRightContent').innerHTML = renderBookRecipeGrid(newRight);
        leaf = buildBookLeaf(1, bookPageWrap(oldRight), bookPageWrap(newLeft));
        cast = document.createElement('div');
        cast.className = 'book-flip-cast cast-right';
    } else {
        // Left page turns to the right; reveal the new left page underneath.
        const oldLStart = bookCurrentSpread * perSpread;
        const oldLeft = BOOK_RECIPES.slice(oldLStart, oldLStart + perPage);
        document.getElementById('bookPageLeftContent').innerHTML = renderBookRecipeGrid(newLeft);
        leaf = buildBookLeaf(-1, bookPageWrap(oldLeft), bookPageWrap(newRight));
        cast = document.createElement('div');
        cast.className = 'book-flip-cast cast-left';
    }
    book.appendChild(cast);
    book.appendChild(leaf);
    void leaf.offsetWidth;
    cast.classList.add('animate');
    leaf.classList.add('turning');

    let done = false;
    const finish = () => {
        if (done) return;
        done = true;
        clearTimeout(safety);
        bookCurrentSpread = newSpread;
        bookMode = 'grid';
        renderBookSpread();
        if (leaf.parentNode) leaf.remove();
        if (cast.parentNode) cast.remove();
    };
    const safety = setTimeout(finish, 1100);
    leaf.addEventListener('transitionend', e => {
        if (e.propertyName === 'transform' && e.target === leaf) finish();
    });
}"""

EDITS = [(OLD_CSS, NEW_CSS), (OLD_JS, NEW_JS)]


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
        # Diagnostics: are the blocks present at all (line-ending vs content drift)?
        print("Diagnostics (matches after newline-normalisation):")
        for probe, label in [(".book-flip-overlay {", "CSS block start"),
                             ("function bookNavigate(direction) {", "bookNavigate start")]:
            print(f"  {label!r}: {norm.count(probe)} match(es)")
        print("If the starts match but the full anchors don't, the block content has "
              "drifted from what I have -- paste me the current .book-flip-overlay CSS "
              "and the bookNavigate function and I'll re-cut the script.")
        sys.exit(1)

    out = norm
    for old, new in EDITS:
        out = out.replace(old, new)
    if crlf:
        out = out.replace("\n", "\r\n")   # restore the file's original CRLF endings

    with open(PATH + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(raw)                      # backup byte-for-byte (original endings)
    with open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print(f"OK: {PATH} updated (CSS + bookNavigate).  Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py check ; hard-refresh Recipe Management > Book view.")


if __name__ == "__main__":
    main()