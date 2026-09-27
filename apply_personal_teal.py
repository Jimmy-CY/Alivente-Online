# -*- coding: utf-8 -*-
"""SECTION H, ROUND H2a - THE PERSONAL LANDING PAGE TAKES THE HOUSE TEAL

The Personal landing page is green: four green tiles, a green tab, a green
panel wash. It declares its own palette and uses ZERO house tokens.

    :root {
        --personal-dark:  #28a745;     <- white text on this is 3.13, a FAIL
        --personal-light: #d4edda;
        --future-dark:    #6c757d;
        --future-light:   #e9ecef;     <- already equals --alv-surface-deep
    }
    .btn-personal        { background-color: #28a745; }
    .btn-personal:hover  { background-color: #218838; }
    .admin-tab.personal-tab:not(.active):hover { background-color: #e8f5e9; }

THERE IS NOTHING TO INVENT HERE. admin_apms.html is the SAME COMPONENT -
the same .admin-tabs, .tab-panel and .admin-btn markup - and it is ALREADY
TEAL:

    --alivente-dark:  #0e7c8b;                       <- the house accent
    .btn-alivente        { background-color: #0e7c8b; }
    .btn-alivente:hover  { background-color: var(--alv-accent-ink); }

So Personal is the odd one out, and this round makes the twins match by
pointing BOTH at base's tokens.

MEASURED, white text on the tile fill:

    #28a745  the Personal green now      3.13   FAIL
    #218838  its hover                   4.52
    #0e7c8b  var(--alv-accent)           4.91   PASS
    #0a5e6a  var(--alv-accent-ink)       7.44

So this is a contrast repair, not only a repaint: the four tiles carry
white text and fail today.

WHAT IS DELIBERATELY LEFT ALONE
-------------------------------
The FUTURE side is GREY, not green, and recolouring it is not what was
asked. --future-dark (#6c757d), .btn-future, .btn-future:hover (#5a6268)
and the #adb5bd disabled fill are untouched on both pages. Only
--future-light is tokenised, and only because #e9ecef IS --alv-surface-deep
byte for byte, so nothing moves.

Backups: .bak_personalteal. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_personalteal'
CRLF = {}

# What base declares, read from base at run time rather than trusted here.
WANT = {
    '--alv-accent': '#0e7c8b',
    '--alv-accent-ink': '#0a5e6a',
    '--alv-accent-soft': '#e4f3f5',
    '--alv-surface-deep': '#e9ecef',
    '--alv-line-soft': '#f1f3f5',
}

# (file, exact old text, new text, does a pixel move?)
JOBS = [
    # ---- the Personal landing page: green -> teal ----------------------
    ('personal.html', '--personal-dark: #28a745;',
     '--personal-dark: var(--alv-accent);', True),
    ('personal.html', '--personal-light: #d4edda;',
     '--personal-light: var(--alv-accent-soft);', True),
    ('personal.html', '--future-light: #e9ecef;',
     '--future-light: var(--alv-surface-deep);', False),
    ('personal.html', 'background-color: #e8f5e9;',
     'background-color: var(--alv-accent-soft);', True),
    ('personal.html', 'background-color: #28a745;',
     'background-color: var(--alv-accent);', True),
    ('personal.html', 'background-color: #218838;',
     'background-color: var(--alv-accent-ink);', True),
    # ---- its twin, so the two pages really do match --------------------
    ('admin_apms.html', '--alivente-dark: #0e7c8b;',
     '--alivente-dark: var(--alv-accent);', False),
    ('admin_apms.html', '--alivente-light: #d1ecf1;',
     '--alivente-light: var(--alv-accent-soft);', True),
    ('admin_apms.html', '--future-light: #e9ecef;',
     '--future-light: var(--alv-surface-deep);', False),
    ('admin_apms.html', 'background-color: #e8f4f8;',
     'background-color: var(--alv-accent-soft);', True),
    ('admin_apms.html', 'background-color: #f1f3f5;',
     'background-color: var(--alv-line-soft);', False),
    ('admin_apms.html', 'background-color: #0e7c8b;',
     'background-color: var(--alv-accent);', False),
]

# A file that has never used var(--alv-*) may not be INSIDE base's scope,
# and a var() with no token in scope resolves to `unset` - worse than the
# literal it replaced (lesson 60). Both files are checked for {% extends %}.
EXTENDS = re.compile(r'\{%\s*extends\b')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def base_tokens():
    """What base really declares. Trusting the table above would be the
    round asserting its own assumption (lesson 20)."""
    css = read(os.path.join(ROOT, 'base.html'))
    got = {}
    for tok, want in WANT.items():
        m = re.search(re.escape(tok) + r'\s*:\s*(#[0-9a-fA-F]{3,6})\s*;', css)
        if not m:
            raise SystemExit('H2a: base declares no %s' % tok)
        got[tok] = m.group(1).lower()
        if got[tok] != want:
            raise SystemExit('H2a: base declares %s as %s, not %s - the '
                             'mapping in this file is out of date'
                             % (tok, got[tok], want))
    return got


def styles_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style\s*>', t,
                                re.S | re.I))


def expand(css, tokens):
    """Every var(--alv-x) replaced by base's declared value, so the two
    sides of the round trip are comparable."""
    def sub(m):
        return tokens.get(m.group(1), '<<%s>>' % m.group(1))
    return re.sub(r'var\(\s*(--alv-[\w-]+)\s*\)', sub, css)


def patch(rel, jobs, tokens):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('H2a: %s is not on disk' % rel)
    text = read(path)
    before = text

    if not EXTENDS.search(text):
        raise SystemExit('H2a: %s does not extend base - a var() with no '
                         'token in scope resolves to unset (lesson 60)'
                         % rel)

    done = 0
    for _f, old, new, _moves in jobs:
        if new in text and old not in text:
            continue                                  # already applied
        n = styles_of(text).count(old)
        if n != 1:
            raise SystemExit('H2a: %s - %r matched %d time(s) inside the '
                             'stylesheet' % (rel, old, n))
        # replace in the stylesheet only, by offset, so markup cannot move
        m = re.search(r'<style[^>]*>.*?</style\s*>', text, re.S | re.I)
        at = text.index(old, m.start())
        text = text[:at] + new + text[at + len(old):]
        done += 1

    if done == 0:
        return None

    # --- self-checks BEFORE anything is written --------------------------
    # 1. The markup did not move at all.
    strip = lambda s: re.sub(r'<style[^>]*>.*?</style\s*>', '', s,
                             flags=re.S | re.I)
    if strip(before) != strip(text):
        raise SystemExit('H2a: %s - something outside the stylesheet moved'
                         % rel)
    # 2. Every declaration that was NOT part of this round expands to what
    #    it was. The ones that were are listed, so a silent extra edit fails.
    moved = [old for _f, old, _n, mv in jobs if mv]
    # BOTH SIDES EXPAND. admin_apms already wrote
    # `.btn-alivente:hover { background-color: var(--alv-accent-ink) }`
    # before this round touched it, so expanding only the AFTER side made
    # that pre-existing token look like a change this round had made.
    a, b = (expand(styles_of(before), tokens),
            expand(styles_of(text), tokens))
    for _f, old, new, mv in jobs:
        if not mv:
            continue
        a = a.replace(old, '<<MOVED>>', 1)
        b = b.replace(expand(new, tokens), '<<MOVED>>', 1)
        b = b.replace(new, '<<MOVED>>', 1)
    for _f, old, new, mv in jobs:
        if mv:
            continue
        a = a.replace(old, '<<SAME>>', 1)
        b = b.replace(expand(new, tokens), '<<SAME>>', 1)
    if a != b:
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                 min(len(a), len(b)))
        raise SystemExit('H2a: %s - the stylesheet changed somewhere this '
                         'round did not ask for, near:\n   was %r\n   now %r'
                         % (rel, a[max(0, i - 60):i + 60],
                            b[max(0, i - 60):i + 60]))
    # 3. No green literal survives on the Personal page.
    if rel == 'personal.html':
        left = re.findall(r'#(?:28a745|218838|d4edda|e8f5e9)\b',
                          styles_of(text), re.I)
        if left:
            raise SystemExit('H2a: %s - a green literal survived: %s'
                             % (rel, left))

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return done


LATER = [
    ('alv_rounds.py',
     "    '.bak_reqmarker',\n]",
     "    '.bak_reqmarker',\n    '.bak_personalteal',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_req_marker.py'",
     "    'test_req_marker.py'\n    'test_personal_teal.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('H2a/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION H, ROUND H2a - THE PERSONAL LANDING PAGE TAKES THE HOUSE '
          'TEAL - %s' % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    tokens = base_tokens()
    print('  base declares: %s' % ', '.join('%s %s' % kv
                                            for kv in sorted(tokens.items())))
    print('-' * 74)
    total = 0
    for rel in ('personal.html', 'admin_apms.html'):
        jobs = [j for j in JOBS if j[0] == rel]
        n = patch(rel, jobs, tokens)
        if n is None:
            print('  %-24s already applied' % rel)
            continue
        moves = len([j for j in jobs if j[3]])
        print('  %-24s %d literal(s) -> token; %d move a pixel, %d do not'
              % (rel, n, moves, len(jobs) - moves))
        total += n
    later = patch_later()
    print('-' * 74)
    print('  %d literal(s) tokenised; %d LATER edit(s).' % (total, later))
    print()
    print('  LEFT ALONE, on purpose: the FUTURE side is grey, not green - '
          '--future-dark,\n  .btn-future, its hover and the #adb5bd '
          'disabled fill are untouched.')
    print('=' * 74)


if __name__ == '__main__':
    main()
