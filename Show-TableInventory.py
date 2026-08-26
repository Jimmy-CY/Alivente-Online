"""Show-TableInventory - what the tables ACTUALLY look like, before we change them.

    python Show-TableInventory.py                  # the survey
    python Show-TableInventory.py --full suppliers.html
                                                   # verbatim dump of one file

READ-ONLY. This writes nothing, anywhere. It exists because every patcher
failure this month has had the same cause: an anchor written from memory of a
file rather than from the file. administration.py matched zero times because
the last line has no trailing newline. The middleware scrape found 192 tuples
where the map holds 176. home_original.html was an orphan nobody knew about.

So before the table standard goes anywhere near base.html or suppliers.html,
this reports what is there now:

  1. base.html anatomy - the <head> in order, so the component block goes in a
     place chosen rather than guessed, and so we find out whether a webfont is
     already loaded before adding a second one.
  2. The nine pilot pages in detail - table classes, the shape of the action
     cell, every btn-* class in use, the mobile block and its breakpoint, and
     any local rule that would collide with .data-table.
  3. Every OTHER template holding a <table>, one line each - because "nine list
     pages" is what we believe, and the belief should be checked.

The --full mode dumps one file's <style> block and its table markup verbatim.
That output is what the B2 anchors get written from.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run this from the project root')

# The agreed migration order. Names are checked, not assumed - anything that
# is not there is reported as missing rather than silently skipped.
PILOT = [
    'suppliers.html',
    'properties.html',
    'tenant.html',
    'petty_cash.html',
    'finance_valuations.html',
    'physical_invoice_list.html',
    'invoices.html',
    'act_expense.html',
    'issues.html',
]

FULL = None
if '--full' in sys.argv:
    i = sys.argv.index('--full')
    if i + 1 < len(sys.argv):
        FULL = sys.argv[i + 1]


def read(p):
    raw = open(p, 'rb').read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    return raw.decode(enc, errors='replace').replace('\r\n', '\n')


def find_file(name):
    """Templates live in subdirectories too (finance/, projects/)."""
    for dirpath, dirnames, filenames in os.walk(TPL):
        dirnames[:] = [d for d in dirnames if d != 'staticfiles']
        if name in filenames:
            return os.path.join(dirpath, name)
    return None


def rel(p):
    return os.path.relpath(p, ROOT)


# ===================================================================== 1. BASE
def base_anatomy():
    path = find_file('base.html')
    print('')
    print('=' * 74)
    print(' 1. base.html - where a component block would go')
    print('=' * 74)
    if not path:
        print('  ! base.html not found')
        return
    src = read(path)
    lines = src.split('\n')
    print('  %s  (%d lines)' % (rel(path), len(lines)))
    print('')

    # --- the head, in order. Order is the whole point: a rule that lands
    #     above Bootstrap loses, which is what we proved last round.
    print('  <head> in load order')
    print('  ' + '-' * 70)
    head_end = src.find('</head>')
    head = src[:head_end if head_end > 0 else len(src)]
    pos = 0
    n = 0
    pat = re.compile(
        r'<link[^>]*?>|<script[^>]*?>|<style[^>]*?>|</style>', re.I | re.S)
    for m in pat.finditer(head):
        tag = m.group(0)
        line_no = head.count('\n', 0, m.start()) + 1
        low = tag.lower()
        if low.startswith('</style'):
            print('       %4d  </style>' % line_no)
            continue
        if low.startswith('<style'):
            print('       %4d  <style>  ------------------------------' % line_no)
            continue
        href = re.search(r'(?:href|src)\s*=\s*["\']([^"\']+)', tag, re.I)
        url = href.group(1) if href else '(inline)'
        kind = 'CSS ' if low.startswith('<link') else 'JS  '
        # Shorten CDN noise but keep enough to identify the library
        short = url
        if len(short) > 62:
            short = short[:30] + '...' + short[-29:]
        print('       %4d  %s %s' % (line_no, kind, short))
        n += 1
    print('  ' + '-' * 70)
    print('       %d external resource(s) in <head>' % n)
    print('')

    # --- fonts. We must know this before adding one.
    print('  Webfonts already loaded')
    fonts = []
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']*(?:fonts\.googleapis|'
                         r'fonts\.gstatic|\.woff2?|\.ttf|typekit)[^"\']*)',
                         src, re.I):
        fonts.append(m.group(1))
    if fonts:
        for f in fonts:
            print('       %s' % f[:100])
    else:
        print('       (none - the system falls back to whatever Bootstrap sets)')
    ff = re.findall(r'font-family\s*:\s*([^;{}]+)', src, re.I)
    if ff:
        print('  font-family declared in base.html: %d' % len(ff))
        for f in ff[:6]:
            print('       %s' % ' '.join(f.split())[:80])
    print('')

    # --- the accent block we shipped, and what follows it
    acc = src.find('--alv-accent:')
    if acc < 0:
        print('  ! the accent block is NOT in base.html - did eca9db8 apply?')
    else:
        acc_line = src.count('\n', 0, acc) + 1
        end = src.find('</style>', acc)
        end_line = src.count('\n', 0, end) + 1 if end > 0 else -1
        print('  Accent block: lines %d-%d' % (acc_line, end_line))
        print('  The component CSS wants to sit immediately after line %d,'
              % end_line)
        print('  so it inherits the tokens and still beats Bootstrap.')
        if end > 0:
            after = src[end + len('</style>'):end + len('</style>') + 400]
            print('')
            print('  What currently follows it:')
            for ln in after.split('\n')[:8]:
                print('       | %s' % ln[:68])
    print('')

    # --- existing style blocks. A second one later in the file wins over ours.
    blocks = [(src.count('\n', 0, m.start()) + 1)
              for m in re.finditer(r'<style[^>]*>', src, re.I)]
    print('  <style> blocks in base.html at lines: %s'
          % ', '.join(str(b) for b in blocks))
    print('  (anything AFTER our block can override it - worth knowing)')

    # --- does base.html already define table rules?
    tbl = re.findall(r'^[^\n]*\.(?:table|data-table)[^\n{]*\{', src, re.M)
    print('')
    print('  Existing table-ish rules in base.html: %d' % len(tbl))
    for t in tbl[:12]:
        print('       %s' % t.strip()[:68])

    # --- the sprite, if we ever add one, must not collide
    print('')
    print('  Existing inline <svg> sprite: %s'
          % ('YES' if re.search(r'<svg[^>]*style="display:\s*none', src, re.I)
             else 'no'))
    print('  Font Awesome in use: %s'
          % ('YES - icons are <i class="fas ...">'
             if 'font-awesome' in src.lower() or 'fontawesome' in src.lower()
             else 'not linked from base.html'))


# ============================================================== 2. PILOT PAGES
BTN_RE = re.compile(r'class\s*=\s*["\']([^"\']*\bbtn[^"\']*)["\']', re.I)
TABLE_RE = re.compile(r'<table([^>]*)>', re.I)
MEDIA_RE = re.compile(r'@media[^{]*?\(\s*max-width\s*:\s*(\d+)px', re.I)


def page_detail(name):
    path = find_file(name)
    print('')
    print('-' * 74)
    if not path:
        print('  %-34s  ! NOT FOUND' % name)
        return
    src = read(path)
    print('  %s   (%d lines)' % (rel(path), src.count('\n') + 1))

    # tables and their classes
    tables = TABLE_RE.findall(src)
    print('    <table>: %d' % len(tables))
    for t in tables:
        cls = re.search(r'class\s*=\s*["\']([^"\']*)', t, re.I)
        idd = re.search(r'id\s*=\s*["\']([^"\']*)', t, re.I)
        print('        class="%s"%s'
              % (cls.group(1) if cls else '(none)',
                 '  id="%s"' % idd.group(1) if idd else ''))
    print('    wrapped in .table-responsive: %d'
          % len(re.findall(r'table-responsive', src, re.I)))

    # header cells - tells us how wide the grid is
    theads = re.findall(r'<thead.*?</thead>', src, re.I | re.S)
    for h in theads[:2]:
        ths = re.findall(r'<th[^>]*>(.*?)</th>', h, re.I | re.S)
        clean = [' '.join(re.sub(r'<[^>]+>', '', x).split())[:18] for x in ths]
        print('    thead (%d cols): %s' % (len(ths), ' | '.join(clean)))

    # every btn class in use, counted - this is the surface .row-btn replaces
    btns = {}
    for m in BTN_RE.finditer(src):
        key = ' '.join(sorted(m.group(1).split()))
        btns[key] = btns.get(key, 0) + 1
    print('    button classes in use: %d distinct' % len(btns))
    for k, v in sorted(btns.items(), key=lambda kv: -kv[1])[:10]:
        print('        %3d x  %s' % (v, k[:58]))

    # the mobile story
    media = MEDIA_RE.findall(src)
    print('    @media max-width breakpoints: %s'
          % (', '.join(m + 'px' for m in media) if media else 'NONE'))
    dl = len(re.findall(r'data-label', src, re.I))
    print('    data-label attributes: %d %s'
          % (dl, '(row-to-card pattern present)' if dl else
             '(no card conversion - mobile shows a raw table)'))

    # local style block: the rules that would fight base.html
    styles = re.findall(r'<style[^>]*>(.*?)</style>', src, re.I | re.S)
    total = sum(s.count('\n') for s in styles)
    print('    local <style>: %d block(s), %d lines' % (len(styles), total))
    collide = []
    for s in styles:
        for m in re.finditer(r'([^{}]+)\{', s):
            sel = ' '.join(m.group(1).split())
            if re.search(r'\b(table|thead|tbody|tr|th|td)\b', sel, re.I):
                collide.append(sel)
    print('    selectors touching table/tr/th/td: %d' % len(collide))
    for c in collide[:14]:
        print('        %s' % c[:66])
    if len(collide) > 14:
        print('        ... and %d more' % (len(collide) - 14))

    # status wording - decision 5 was about Manage / Approved / Paid
    for word in ('Manage', 'Approved', 'Paid', 'Active', 'Inactive',
                 'Pending', 'Overdue', 'Draft'):
        c = len(re.findall(r'>\s*%s\s*<' % word, src))
        if c:
            print('    status word ">%s<": %d' % (word, c))

    # empty state
    print('    "No ... found" empty state: %s'
          % ('present' if re.search(r'No\s+\w+(\s+\w+)?\s+found', src, re.I)
             else 'ABSENT - the table just renders nothing'))


def pilot_pages():
    print('')
    print('=' * 74)
    print(' 2. The nine pilot pages, in the agreed migration order')
    print('=' * 74)
    for name in PILOT:
        page_detail(name)


# ============================================================ 3. THE WIDER NET
def everything_else():
    print('')
    print('')
    print('=' * 74)
    print(' 3. Every OTHER template holding a <table>')
    print('=' * 74)
    print('  "Nine list pages" is the belief. This is the check.')
    print('')
    print('  %-46s %6s %6s %6s' % ('FILE', 'TABLE', 'BTN', 'd-lbl'))
    print('  ' + '-' * 68)
    rows = []
    for dirpath, dirnames, filenames in os.walk(TPL):
        dirnames[:] = [d for d in dirnames if d != 'staticfiles']
        for f in sorted(filenames):
            if not f.endswith('.html') or '.bak_' in f:
                continue
            if f in PILOT:
                continue
            p = os.path.join(dirpath, f)
            src = read(p)
            nt = len(TABLE_RE.findall(src))
            if not nt:
                continue
            rows.append((rel(p), nt, len(BTN_RE.findall(src)),
                         len(re.findall(r'data-label', src, re.I))))
    for r in sorted(rows, key=lambda x: -x[1]):
        print('  %-46s %6d %6d %6d' % (r[0][:46], r[1], r[2], r[3]))
    print('  ' + '-' * 68)
    print('  %d further template(s) contain a table.' % len(rows))
    print('')
    print('  A file with tables and ZERO data-label has no mobile story at')
    print('  all today - it renders a table too wide for the screen.')


# ================================================================ --full mode
def full_dump(name):
    path = find_file(name)
    if not path:
        sys.exit('! %s not found' % name)
    src = read(path)
    print('')
    print('=' * 74)
    print(' VERBATIM: %s' % rel(path))
    print('=' * 74)
    print('')
    print('--- <style> block(s) ------------------------------------------')
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', src, re.I | re.S):
        start = src.count('\n', 0, m.start()) + 1
        print('')
        print('    [line %d]' % start)
        # group(1) begins immediately after the '>' of <style>, so its first
        # element is the tail of the <style> line itself - hence start + i,
        # not start + i + 1. An off-by-one here would put every anchor we
        # later write one line out.
        for i, ln in enumerate(m.group(1).split('\n')):
            print('    %4d| %s' % (start + i, ln))
    print('')
    print('--- table markup ----------------------------------------------')
    for m in re.finditer(r'<table.*?</table>', src, re.I | re.S):
        start = src.count('\n', 0, m.start()) + 1
        body = m.group(0)
        print('')
        print('    [line %d, %d lines]' % (start, body.count('\n') + 1))
        for i, ln in enumerate(body.split('\n')):
            print('    %4d| %s' % (start + i, ln))
    print('')
    print('--- any @media block ------------------------------------------')
    for m in re.finditer(r'@media[^{]*\{', src, re.I):
        start = src.count('\n', 0, m.start()) + 1
        # walk braces to find the end of the media query
        i = m.end() - 1
        depth = 0
        while i < len(src):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = src[m.start():i + 1]
        print('')
        print('    [line %d, %d lines]' % (start, body.count('\n') + 1))
        for j, ln in enumerate(body.split('\n')):
            print('    %4d| %s' % (start + j, ln))


# ======================================================================= run
if FULL:
    full_dump(FULL)
else:
    base_anatomy()
    pilot_pages()
    everything_else()
    print('')
    print('=' * 74)
    print('  Read-only. Nothing was written.')
    print('  Next:  python Show-TableInventory.py --full suppliers.html')
    print('=' * 74)
