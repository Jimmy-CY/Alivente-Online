# -*- coding: utf-8 -*-
"""test_print_queries.py - every phone query says `screen`, so no phone
layout reaches paper; and the screen did not move.

    python test_print_queries.py

Run from the repo root. Paired with apply_print_queries.py (21 Sep).

  1. No template but base carries a bare max-width clause - one that names
     no media type and so also matches print. base keeps its <=991px block
     on purpose.
  2. Each touched file is its backup plus `screen and `, exactly: take the
     words back out and the bytes are identical.
  3. PROBES. A marker is put into every block this round guarded and read
     back in Chromium at a width where the block's own condition holds:
     on screen it must fire; printed it must NOT. The same block from the
     backup must fire on BOTH - "it does not fire on paper" passes equally
     on a block that is gone, a probe that never worked and a selector
     that never matched.
  4. THE PAGES THAT PRINTED THE WRONG THING - the P&L, the P&L dashboard,
     the lease timeline and occupancy trends, printed at 718: the content
     is there and the rotate-your-phone prompt is not. From the backup the
     content was missing - the control that proves this check can fail.
  5. THE SCREEN DID NOT MOVE - every touched page at 375 and 1280, every
     element's display, visibility, font-size and width identical to the
     backup's.
  6. It is on the gate.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_printq'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_print_queries.py'
ADD = 'screen and '
PAGE = 718

passed = failed = skipped = 0
notes = []


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def blank(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def mask_css(css):
    css = re.sub(r'/\*.*?\*/', blank, css, flags=re.S)
    css = re.sub(r'\{#.*?#\}', blank, css, flags=re.S)
    return re.sub(r'\{%.*?%\}', blank, css, flags=re.S)


TYPED = re.compile(r'\s*(only\s+|not\s+)?(screen|print|all|speech)\b', re.I)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def bare_clauses(t):
    out = []
    for css in styles_of(t):
        for mm in re.finditer(r'@media\b([^{;]*)\{', mask_css(css)):
            for part in mm.group(1).split(','):
                if re.search(r'max-width\s*:', part, re.I) and \
                        not TYPED.match(part):
                    out.append(' '.join(part.split()))
    return out


def templates():
    out = []
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if f.endswith('.html') and 'OLD DO NOT USE' not in f:
                p = os.path.join(d, f)
                out.append((os.path.relpath(p, ROOT).replace('\\', '/'), p))
    return sorted(out)


ALL = templates()
TOUCHED = [(r, p) for r, p in ALL if os.path.isfile(p + SUFFIX)]

# ==========================================================================
print('=' * 74)
print('1. NO PHONE QUERY IN ANY TEMPLATE CAN REACH PAPER')
print('=' * 74)
left = [(r, c) for r, p in ALL if r != 'base.html'
        for c in bare_clauses(read(p))]
ok(len(ALL) > 100, 'CONTROL: %d template(s) read, subfolders included'
   % len(ALL))
ok(not left, 'no template but base has a bare max-width clause',
   '\n'.join('%s: %s' % x for x in left[:8]))
bb = bare_clauses(read(os.path.join(ROOT, 'base.html')))
ok(any('991' in c for c in bb),
   'base keeps its bare <=991px block - on paper it hides the sidebar, '
   'which the print-leak round decided is right')
ctl = bare_clauses('<style>/* @media (max-width: 900px) { */'
                   '@media (min-width: 1px) and (max-width: 800px), '
                   'screen and (max-width: 700px) {}</style>')
ok(ctl == ['(min-width: 1px) and (max-width: 800px)'],
   'CONTROL: the scan judges each clause of a list alone, and reads no '
   'comment as CSS', str(ctl))

# ==========================================================================
print('\n' + '=' * 74)
print('2. EACH FILE IS ITS BACKUP PLUS THE WORDS, EXACTLY')
print('=' * 74)
if not TOUCHED:
    skip('the byte invariant', 'no %s backups - round not applied here'
         % SUFFIX)
else:
    bad = []
    n_add = 0
    for rel, p in TOUCHED:
        # LATER - test_print_buttons.py, 21 Sep. That round marked home's
        # dashboard rows print-keep, in a file this round had touched. The
        # file is judged as it stood before that round when its backup is
        # there.
        # LATER - test_div_balance.py, 21 Sep. That round fixed unpaired
        # </div> tags in three files this round had touched. The earliest
        # later round's backup is the file as this round left it.
        from alv_rounds import as_left_by
        now = as_left_by(p, SUFFIX, read)
        was = read(p + SUFFIX)
        k = now.count(ADD) - was.count(ADD)
        n_add += k
        if len(now) - len(was) != k * len(ADD):
            bad.append('%s: grew %d for %d insertion(s)'
                       % (rel, len(now) - len(was), k))
        elif len(bare_clauses(was)) != k:
            bad.append('%s: %d bare clause(s) before, %d guarded'
                       % (rel, len(bare_clauses(was)), k))
        else:
            # Remove the new ones: walk both texts together.
            i = j = 0
            out = []
            while i < len(now):
                if now.startswith(ADD, i) and not was.startswith(ADD, j):
                    i += len(ADD)
                    continue
                out.append(now[i])
                i += 1
                j += 1
            if ''.join(out) != was:
                bad.append('%s: more changed than the words' % rel)
    ok(not bad, '%d file(s): every one is its backup plus `%s`, %d time(s) '
       'in all' % (len(TOUCHED), ADD.strip(), n_add), '\n'.join(bad[:8]))

# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def block_probes(t, tag):
    """The page's styles with a marker in every @media block that has a
    max-width clause: (styles, [(name, width, height)]). The width is one
    where the block's own condition holds on screen."""
    out, probes, k = [], [], 0
    for css in styles_of(t):
        msk = mask_css(css)
        pieces, last = [], 0
        for mm in re.finditer(r'@media\b([^{;]*)\{', msk):
            pre = mm.group(1)
            want = None
            for part in pre.split(','):
                w = re.search(r'max-width\s*:\s*([\d.]+)px', part)
                if not w:
                    continue
                lo = re.search(r'min-width\s*:\s*([\d.]+)px', part)
                if 'print' in part.lower() or 'hover' in part.lower():
                    continue
                width = int(float(w.group(1))) - 1
                if lo and width < float(lo.group(1)):
                    continue
                land = 'landscape' in part.lower()
                mh = re.search(r'max-height\s*:\s*([\d.]+)px', part)
                height = (int(float(mh.group(1))) - 1 if mh else
                          (max(200, width // 2) if land else width * 2))
                if land and height >= width:
                    continue
                want = (width, height)
                break
            if not want:
                continue
            k += 1
            name = '--alvq-%s-%d' % (tag, k)
            pieces.append(css[last:mm.end()])
            pieces.append(':root{%s:1}' % name)
            last = mm.end()
            probes.append((name, want[0], want[1]))
        pieces.append(css[last:])
        out.append(''.join(pieces))
    return out, probes


PROBE_JS = """(names) => names.map(n =>
    getComputedStyle(document.documentElement).getPropertyValue(n).trim())"""


def fixture(boot, base_css, page_styles, markup=''):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<title>q</title><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar"><div>%s</div></div></body></html>'
            % (boot, base_css, ''.join('<style>%s</style>' % c
                                       for c in page_styles), markup))


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S | re.I)
    body = re.sub(r'\{#.*?#\}', '', body, flags=re.S)
    body = re.sub(r'\{%.*?%\}', '', body, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', body, flags=re.S)


print('\n' + '=' * 74)
print('3. PROBES - EVERY GUARDED BLOCK FIRES ON SCREEN AND NOT ON PAPER')
print('=' * 74)
if sync_playwright is None or not os.path.isfile(BOOT):
    for s in ('3. probes', '4. the pages that printed the wrong thing',
              '5. the screen did not move'):
        skip(s, 'playwright or %s missing' % BOOT)
elif not TOUCHED:
    for s in ('3. probes', '4. the pages that printed the wrong thing',
              '5. the screen did not move'):
        skip(s, 'no %s backups - round not applied here' % SUFFIX)
else:
    boot = read(BOOT)
    base_css = '\n'.join(styles_of(read(os.path.join(ROOT, 'base.html'))))
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def load(br, html, w, h, media):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pq_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': h})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        return ctx, pg

    def probe(br, styles, probes, media):
        got = {}
        for w, h in sorted(set((p[1], p[2]) for p in probes)):
            names = [p[0] for p in probes if (p[1], p[2]) == (w, h)]
            ctx, pg = load(br, fixture(boot, base_css, styles), w, h, media)
            for nm, v in zip(names, pg.evaluate(PROBE_JS, names)):
                got[nm] = v == '1'
            ctx.close()
        return got

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        bad, total, guarded = [], 0, 0
        for rel, p in TOUCHED:
            now, was = read(p), read(p + SUFFIX)
            s_now, pr_now = block_probes(now, 'n')
            s_was, pr_was = block_probes(was, 'w')
            if len(pr_now) != len(pr_was):
                bad.append('%s: %d probe-able block(s) now, %d before'
                           % (rel, len(pr_now), len(pr_was)))
                continue
            scr = probe(br, s_now, pr_now, 'screen')
            prn = probe(br, s_now, pr_now, 'print')
            old_s = probe(br, s_was, pr_was, 'screen')
            old_p = probe(br, s_was, pr_was, 'print')
            for (a, w, h), (b, _w, _h) in zip(pr_now, pr_was):
                total += 1
                if not scr[a]:
                    bad.append('%s: block at %dpx no longer fires on screen'
                               % (rel, w))
                if prn[a]:
                    bad.append('%s: block at %dpx still fires on paper'
                               % (rel, w))
                if not old_s[b]:
                    bad.append('%s: block at %dpx did not fire on screen in '
                               'the backup either - the probe cannot see it'
                               % (rel, w))
                if old_p[b]:
                    guarded += 1
        ok(total > 0 and not bad,
           '%d block(s) on %d page(s): each fires on screen and not on '
           'paper' % (total, len(TOUCHED)), '\n'.join(bad[:8]))
        ok(guarded > 0,
           'CONTROL: from the backups, %d of those block(s) DID fire on '
           'paper - the probe sees a leak when there is one' % guarded)
        notes.append('%d block(s) fired on paper of their own width before '
                     'this round and fire on none now.' % guarded)

        # ==================================================================
        print('\n' + '=' * 74)
        print('4. THE PAGES THAT PRINTED THE WRONG THING')
        print('=' * 74)
        SEEN = r"""(sels) => sels.map(s => {
            const e = document.querySelector(s);
            return e ? e.checkVisibility() : null; })"""
        CASES = (
            ('finance_pl_act.html', 'td.text-right', '.rotate-prompt'),
            ('dashboard_pl.html', 'td.text-right', '.rotate-prompt'),
            ('lease_timeline.html', '.timeline-ui', '.rotate-prompt'),
            ('occupancy_trends.html', '.yearly-summary-table',
             '.rotate-prompt'),
        )
        for rel, content, prompt in CASES:
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p + SUFFIX):
                skip(rel, 'no backup')
                continue
            res = []
            for t in (read(p), read(p + SUFFIX)):
                ctx, pg = load(br, fixture(boot, base_css, styles_of(t),
                                           body_markup(t)),
                               PAGE, 1000, 'print')
                res.append(pg.evaluate(SEEN, [content, prompt]))
                ctx.close()
            (c_now, p_now), (c_was, p_was) = res
            ok(c_now is True and p_now is False,
               '%-26s printed: %s shows, the rotate prompt does not'
               % (rel, content), 'content %s, prompt %s' % (c_now, p_now))
            # The CONTROL is the content, not the prompt. finance_pl_act's
            # prompt carries an inline display:none its script lifts, so on
            # paper it printed NEITHER - the table was hidden and nothing
            # took its place. The other three printed the prompt instead.
            ok(c_was is False,
               '%-26s CONTROL: from the backup, the content was missing on '
               'paper (%s)' % (rel, 'the prompt printed instead' if p_was
                               else 'and nothing replaced it'),
               'content %s, prompt %s' % (c_was, p_was))

        # ==================================================================
        print('\n' + '=' * 74)
        print('5. THE SCREEN DID NOT MOVE')
        print('=' * 74)
        SNAP = r"""() => Array.from(document.querySelectorAll('body *'))
            .map(e => { const s = getComputedStyle(e);
                return [e.checkVisibility(), s.display, s.fontSize,
                        Math.round(e.getBoundingClientRect().width)]; })"""
        moved = []
        for rel, p in TOUCHED:
            # LATER - test_div_balance.py, 21 Sep. Section 5 renders the
            # page as this round left it: the earliest later round's backup,
            # when there is one.
            from alv_rounds import as_left_by
            now = as_left_by(p, SUFFIX, read)
            was = read(p + SUFFIX)
            for w in (375, 1280):
                snaps = []
                for t in (now, was):
                    ctx, pg = load(br, fixture(boot, base_css, styles_of(t),
                                               body_markup(t)),
                                   w, 900, 'screen')
                    snaps.append(pg.evaluate(SNAP))
                    ctx.close()
                if snaps[0] != snaps[1]:
                    moved.append('%s at %d' % (rel, w))
        ok(not moved, 'every touched page, at 375 and 1280, renders exactly '
           'as it did', '\n'.join(moved[:8]))
        br.close()

# ==========================================================================
print('\n' + '=' * 74)
print('6. IT IS ON THE GATE')
print('=' * 74)
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    for x in notes:
        print('  - ' + x)
    print('')
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
