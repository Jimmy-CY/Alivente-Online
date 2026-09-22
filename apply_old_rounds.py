# -*- coding: utf-8 -*-
"""apply_old_rounds.py - the five off-gate suites judge their own rounds
again and go on the gate; the Comments Report takes base's report title.

    python apply_old_rounds.py --check     dry run, nothing written
    python apply_old_rounds.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, claude/offgate_suites_survey.md)

  test_banner_pages, test_comments_report, test_finance_headings,
  test_fi_seg and test_map_tiles have failed on every sweep for weeks, and
  none of them has found a fault in a page. Each judges ITS round against
  the file as it is NOW, and a later agreed round changed that file. One
  more was the suite's own error: test_finance_headings expected
  occupancy_trends to sit on a band, but the banner round had taken it
  off the day before its round ran.

WHAT THIS DOES - agreed 21 Sep

  1. alv_rounds.as_left_by() learns rounds OLDER than its list: the file as
     such a round left it is the first of the file's backups written after
     that round's own, by modification time. as_of() gives a file as it
     stood at a moment - for files a round read but did not back up.
  2. The five suites read base and their pages through them, so each
     checks what its round promised. Two checks in test_comments_report
     belong to the banner round and read the page as THAT round left it.
     test_finance_headings records occupancy_trends as already plain.
     test_map_tiles no longer crashes when a page has no tile layer.
     test_banner_pages no longer walks into a virtualenv kept inside the
     repo (added 22 Sep, after the laptop's sweep showed it - a failure
     that had been hidden behind four others for weeks).
  3. All five go on the push gate.
  4. comments_report.html: its header becomes base's report title - the
     row, the titles, ALIVENTE ONLINE on paper, the title as an h2 and the
     period as the subtitle - with the comment count kept on the right.
     Its own header rules go.
  5. alv_rounds.py learns this round; test_old_rounds.py goes on the gate.
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

import ast
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_oldrounds'
SUITE = 'test_old_rounds.py'
PS1 = 'Push-PendingChanges.ps1'
CR = os.path.join(T, 'comments_report.html')
FIVE = ['test_banner_pages.py', 'test_comments_report.py',
        'test_finance_headings.py', 'test_fi_seg.py', 'test_map_tiles.py']

# (file, old, new) - exact, applied in order, each anchor found once.
EDITS = [
    ('test_map_tiles.py',
     "if not os.path.exists(BAK):\n    sys.exit('! no map_view.html.bak_maptiles - run apply_map_tiles.py first.')\n\nF, WAS = read(MV), read(BAK)\nFC, WC = code_of(F), code_of(WAS)\nOSM = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'\n",
     "if not os.path.exists(BAK):\n    sys.exit('! no map_view.html.bak_maptiles - run apply_map_tiles.py first.')\n\n# LATER - test_old_rounds.py, 21 Sep: judged on map_view as THIS round left\n# it. The map-provider round (16 Sep) replaced these tiles on purpose, so\n# the file now is not this round's to answer for.\nsys.path.insert(0, ROOT)\nfrom alv_rounds import as_left_by\nF, WAS = as_left_by(MV, '.bak_maptiles', read), read(BAK)\nFC, WC = code_of(F), code_of(WAS)\nOSM = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'\n"),
    ('test_map_tiles.py',
     "check('  CONTROL: it was in the old URL', '{r}' in WC)\n\n_url, _opts = layer_of(F)\ncheck('exactly one tile layer on the page', FC.count('L.tileLayer(') == 1,\n      str(FC.count('L.tileLayer(')))\ncheck('  and its url is the OSM one', _url == OSM, str(_url))",
     "check('  CONTROL: it was in the old URL', '{r}' in WC)\n\n_url, _opts = layer_of(F)\n# A page with no tile layer FAILS the checks below; it must not crash them.\n_opts = _opts or {}\ncheck('exactly one tile layer on the page', FC.count('L.tileLayer(') == 1,\n      str(FC.count('L.tileLayer(')))\ncheck('  and its url is the OSM one', _url == OSM, str(_url))"),
    ('test_map_tiles.py',
     "        print('  SKIP  %s not present' % name)\n        continue\n    _seen += 1\n    purl, popts = layer_of(read(p))\n    check('%-24s uses the same tile URL' % name, purl == OSM, str(purl))\n    check('  and sets no subdomains either - Leaflet defaults to abc',\n          'subdomains' not in popts)",
     "        print('  SKIP  %s not present' % name)\n        continue\n    _seen += 1\n    # LATER - test_old_rounds.py: the peer as it stood when this round ran.\n    from alv_rounds import as_of\n    purl, popts = layer_of(as_of(p, os.path.getmtime(BAK), read))\n    popts = popts or {}\n    check('%-24s uses the same tile URL' % name, purl == OSM, str(purl))\n    check('  and sets no subdomains either - Leaflet defaults to abc',\n          'subdomains' not in popts)"),
    ('test_fi_seg.py',
     "for p in (BASE, FI):\n    if not os.path.exists(p):\n        sys.exit('! %s not found - run from the repo root' % p)\nBS, F = read(BASE), read(FI)\nif 'alv-seg' not in F:\n    print('\\n! not patched - run apply_fi_seg.py first.')\n    sys.exit(1)",
     'for p in (BASE, FI):\n    if not os.path.exists(p):\n        sys.exit(\'! %s not found - run from the repo root\' % p)\n# LATER - test_old_rounds.py, 21 Sep: base and the page as THIS round left\n# them. Twenty later rounds have added to base; they are not this round\'s\n# delta, and "base changed by comment only" is a claim about 5 Sep.\nsys.path.insert(0, ROOT)\nfrom alv_rounds import as_left_by\nBS, F = as_left_by(BASE, \'.bak_fiseg\', read), as_left_by(FI, \'.bak_fiseg\', read)\nif \'alv-seg\' not in F:\n    print(\'\\n! not patched - run apply_fi_seg.py first.\')\n    sys.exit(1)'),
    ('test_finance_headings.py',
     "    if not os.path.exists(path_of(_r) + '.bak_hdr'):\n        sys.exit('! no %s.bak_hdr - run apply_finance_headings.py first.' % _r)\n\nNOW = {r: read(path_of(r)) for r in PAGES}\nWAS = {r: read(path_of(r) + '.bak_hdr') for r in PAGES}\nBCSS = css_of(read(BASE))\n\n# ===========================================================================\nhead('1. the band is gone, and only the band')",
     "    if not os.path.exists(path_of(_r) + '.bak_hdr'):\n        sys.exit('! no %s.bak_hdr - run apply_finance_headings.py first.' % _r)\n\n# LATER - test_old_rounds.py, 21 Sep: judged on each page, and on base, as\n# THIS round left them. The heading-components round (16 Sep) moved every\n# <h2><center> onto h2.page-title-h2 on purpose; that is its decision, and\n# this suite checks this one's.\nsys.path.insert(0, ROOT)\nfrom alv_rounds import as_left_by, as_of\nNOW = {r: as_left_by(path_of(r), '.bak_hdr', read) for r in PAGES}\nWAS = {r: read(path_of(r) + '.bak_hdr') for r in PAGES}\n_T_HDR = max(os.path.getmtime(path_of(r) + '.bak_hdr') for r in PAGES)\nBCSS = css_of(as_of(BASE, _T_HDR, read))\n\n# ===========================================================================\nhead('1. the band is gone, and only the band')"),
    ('test_finance_headings.py',
     "    return tuple(int(x) for x in re.findall(r'\\d+', s)[:3])\n\n\nif sync_playwright is not None and FIX:\n    for rel in PAGES:\n        now, was = paint(rel, True), paint(rel, False)\n        check('%-38s BEFORE the heading sat on a gradient' % rel,\n              was is not None and was['gradient'])\n        check('  AFTER it sits on none', now is not None and not now['gradient'])",
     "    return tuple(int(x) for x in re.findall(r'\\d+', s)[:3])\n\n\n# LATER - test_old_rounds.py, 21 Sep: occupancy_trends' band was already\n# gone when this round ran - the banner round took it on 7 Sep, the day\n# before (its .bak_banner is older than its .bak_hdr). This check has\n# failed on it ever since; it asserted a BEFORE this round never saw.\n_ALREADY_PLAIN = {'occupancy_trends.html'}\nif sync_playwright is not None and FIX:\n    for rel in PAGES:\n        now, was = paint(rel, True), paint(rel, False)\n        if rel in _ALREADY_PLAIN:\n            check('%-38s BEFORE it was already plain - the banner round '\n                  'had been' % rel, was is not None and not was['gradient'])\n            check('  AFTER it sits on none',\n                  now is not None and not now['gradient'])\n            check('  AFTER it is dark on paper',\n                  now is not None and sum(rgb(now['ink'])) < 330,\n                  str(now and now['ink']))\n            check('  and it is centred in its container',\n                  now is not None and now['centred'])\n            continue\n        check('%-38s BEFORE the heading sat on a gradient' % rel,\n              was is not None and was['gradient'])\n        check('  AFTER it sits on none', now is not None and not now['gradient'])"),
    ('test_banner_pages.py',
     "    if not os.path.exists(os.path.join(T, _n + '.bak_banner')):\n        sys.exit('! no %s.bak_banner - run apply_banner_pages.py first.' % _n)\n\nNOW = {n: read(os.path.join(T, n)) for n in PAGES}\nWAS = {n: read(os.path.join(T, n + '.bak_banner')) for n in PAGES}\nBCSS = css_of(read(BASE))\n\n# ===========================================================================\nhead('1. the band is gone from the stylesheet')",
     "    if not os.path.exists(os.path.join(T, _n + '.bak_banner')):\n        sys.exit('! no %s.bak_banner - run apply_banner_pages.py first.' % _n)\n\n# LATER - test_old_rounds.py, 21 Sep: judged on each page, and on base, as\n# THIS round left them. The finance-headings round (8 Sep) rebuilt\n# occupancy_trends' header the next morning, and later rounds fixed the\n# base fault this suite's CONTROL points at - both on purpose.\nsys.path.insert(0, ROOT)\nfrom alv_rounds import as_left_by, as_of\nNOW = {n: as_left_by(os.path.join(T, n), '.bak_banner', read) for n in PAGES}\nWAS = {n: read(os.path.join(T, n + '.bak_banner')) for n in PAGES}\n_T_BANNER = max(os.path.getmtime(os.path.join(T, n + '.bak_banner'))\n                for n in PAGES)\nBCSS = css_of(as_of(BASE, _T_BANNER, read))\n\n# ===========================================================================\nhead('1. the band is gone from the stylesheet')"),
    ('test_comments_report.py',
     'for p in (BASE, CR):\n    if not os.path.exists(p):\n        sys.exit(\'! %s not found - run from the repo root\' % p)\nBS, C = read(BASE), read(CR)\nif \'class="alv-table"\' not in C:\n    print(\'\\n! not patched - run apply_comments_report.py first.\')\n    sys.exit(1)',
     'for p in (BASE, CR):\n    if not os.path.exists(p):\n        sys.exit(\'! %s not found - run from the repo root\' % p)\n# LATER - test_old_rounds.py, 21 Sep: judged on the page, and on base, as\n# THIS round (.bak_crb, 2 Sep) left them. The banner round took the teal\n# band off on 7 Sep and the report-title round moved the header onto\n# base\'s report title on 21 Sep - both on purpose, neither this round\'s.\nsys.path.insert(0, ROOT)\nfrom alv_rounds import as_left_by, as_of\nBS = as_of(BASE, os.path.getmtime(CR + \'.bak_crb\'), read)\nC = as_left_by(CR, \'.bak_crb\', read)\nif \'class="alv-table"\' not in C:\n    print(\'\\n! not patched - run apply_comments_report.py first.\')\n    sys.exit(1)'),
    ('test_comments_report.py',
     "# CC, not C. The page still EXPLAINS the removal in prose, and reading the\n# raw file finds the explanation and calls the removal a failure. That is\n# the same trap the note twenty lines above this one is about.\ncheck('  and its .stat-box has gone to base, as the page says it should',\n      '.stat-box {' not in CC, 'still defined' if '.stat-box {' in CC else '')\ncheck('    CONTROL: the page still says why, in prose the stripper removes',\n      '.stat-box' in C and '.stat-box' not in CC)\nif sync_playwright is not None:\n    check('  rendered: the banner still carries a gradient',\n          'gradient' in DESK['headBg'], DESK['headBg'][:48])",
     "# CC, not C. The page still EXPLAINS the removal in prose, and reading the\n# raw file finds the explanation and calls the removal a failure. That is\n# the same trap the note twenty lines above this one is about.\n# LATER - test_old_rounds.py, 21 Sep: this suite now judges its own round\n# on the page as THAT round left it (.bak_crb). These two were written by\n# the banner round, 7 Sep, about ITS change - so they read the page as the\n# banner round left it.\n_CB = as_left_by(CR, '.bak_banner', read)\n_CCB = nocomment_html(_CB)\ncheck('  and its .stat-box has gone to base, as the page says it should',\n      '.stat-box {' not in _CCB,\n      'still defined' if '.stat-box {' in _CCB else '')\ncheck('    CONTROL: the page still says why, in prose the stripper removes',\n      '.stat-box' in _CB and '.stat-box' not in _CCB)\nif sync_playwright is not None:\n    check('  rendered: the banner still carries a gradient',\n          'gradient' in DESK['headBg'], DESK['headBg'][:48])"),
    ('alv_rounds.py',
     '\ndef as_left_by(path, suffix, read):\n    """The text of `path` as the round whose backups end in `suffix` left\n    it - the earliest later round\'s backup of it, or the file itself."""\n    later = ROUNDS[ROUNDS.index(suffix) + 1:] if suffix in ROUNDS else []\n    for s in later:\n        if os.path.isfile(path + s):\n            return read(path + s)\n    return read(path)\n',
     '\ndef as_left_by(path, suffix, read):\n    """The text of `path` as the round whose backups end in `suffix` left\n    it - the earliest later round\'s backup of it, or the file itself.\n\n    A round in ROUNDS is placed by the list. A round OLDER than the list\n    is placed by its backups\' times: see later_backup()."""\n    if suffix in ROUNDS:\n        for s in ROUNDS[ROUNDS.index(suffix) + 1:]:\n            if os.path.isfile(path + s):\n                return read(path + s)\n        return read(path)\n    return read(later_backup(path, suffix) or path)\n\n\ndef later_backup(path, suffix):\n    """For a round older than ROUNDS: of the file\'s backups, the one\n    written FIRST AFTER this round\'s own - by modification time, which is\n    when the next round saved the file before touching it, so its content\n    is the file exactly as this round left it. None when no later round\n    touched the file (the file itself is then the answer), or when this\n    round left no backup to date it by."""\n    own = path + suffix\n    if not os.path.isfile(own):\n        return None\n    return backup_after(path, os.path.getmtime(own), own)\n\n\ndef backup_after(path, when, skip=None):\n    """The file\'s first backup written after `when`, or None."""\n    folder, name = os.path.split(path)\n    best = None\n    for n in os.listdir(folder or \'.\'):\n        p = os.path.join(folder, n)\n        if not n.startswith(name + \'.bak_\') or p == skip:\n            continue\n        t = os.path.getmtime(p)\n        if t > when and (best is None or t < best[0]):\n            best = (t, p)\n    return best[1] if best else None\n\n\ndef as_of(path, when, read):\n    """The text of `path` as it stood at time `when` - for a file a round\n    READ but did not back up: its first backup written after `when`, or\n    the file itself if nothing has touched it since."""\n    return read(backup_after(path, when) or path)\n'),
    ('alv_rounds.py',
     "    '.bak_appliesfrom',\n]",
     "    '.bak_appliesfrom',\n    '.bak_oldrounds',\n]"),
    ('test_banner_pages.py',
     "    for _dir, _sub, _files in os.walk(ROOT):\n        if os.path.basename(_dir) != 'templatetags':\n            continue",
     "    for _dir, _sub, _files in os.walk(ROOT):\n        # LATER - test_old_rounds.py, 22 Sep: never walk into a virtualenv.\n        # The laptop keeps one INSIDE the repo, so this walk handed Django\n        # every installed package's templatetags under a wrong module path,\n        # and the Engine refused them all - a failure hidden for weeks\n        # behind the four FAIL lines above it.\n        _sub[:] = [s for s in _sub if s != 'site-packages' and\n                   not os.path.isfile(os.path.join(_dir, s, 'pyvenv.cfg'))]\n        if os.path.basename(_dir) != 'templatetags':\n            continue"),
]

OLD_HEAD = """    <div class="report-header">
        <div class="report-header-left">
            <h1><i class="fas fa-comments"></i> Comments Report</h1>
            <p class="subtitle">{{ period_label }}</p>
        </div>"""
NEW_HEAD = """    <div class="alv-report-head">
        <div class="alv-report-titles">
            <div class="alv-report-brand">ALIVENTE ONLINE</div>
            <h2 class="alv-report-title">Comments Report</h2>
            <p class="alv-report-sub">{{ period_label }}</p>
        </div>"""
GONE = ('.report-header', '.report-header-left h1',
        '.report-header-left .subtitle')
PHONE_NOTE = '    /* Header — stack title and stat box */\n'

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def rule_re(sel):
    return re.compile(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{[^{}]*\}'
                      r'[ \t]*\n(?:[ \t]*\n)?')


# ---- 1. the suites and alv_rounds -----------------------------------------
done_files = set()
for name, old, new in EDITS:
    if not os.path.isfile(name):
        problems.append('%s not found' % name)
        continue
    cur = planned[name][1] if name in planned else read(name)
    if new in cur:
        done_files.add(name)
        continue
    if cur.count(old) != 1:
        problems.append('%s: anchor found %d time(s): %r'
                        % (name, cur.count(old), old[:60]))
        continue
    orig = planned[name][0] if name in planned else cur
    planned[name] = (orig, cur.replace(old, new, 1))
for name in sorted(set(e[0] for e in EDITS)):
    if name in planned:
        report.append('%-44s %s' % (name, 'the time-ordered fallback and '
                                    'as_of()' if name == 'alv_rounds.py'
                                    else 'judges its own round'))
    else:
        report.append('%-44s already done' % name)

# ---- 2. the Comments Report -----------------------------------------------
t = read(CR)
if 'class="alv-report-head"' in t:
    report.append('%-44s already done' % 'comments_report.html')
elif t.count(OLD_HEAD) != 1:
    problems.append('comments_report.html: the header block found %d '
                    'time(s)' % t.count(OLD_HEAD))
else:
    new = t.replace(OLD_HEAD, NEW_HEAD, 1)
    n = 0
    for sel in GONE:
        new, k = rule_re(sel).subn('', new)
        n += k
    new = new.replace(PHONE_NOTE, '', 1)
    if n != 6:
        problems.append('comments_report.html: %d header rule(s) removed, '
                        'expected 6' % n)
    else:
        planned[CR] = (t, new)
        report.append('%-44s header -> base\'s report title; %d rule(s) '
                      'removed' % ('comments_report.html', n))

# ---- 3. the gate ----------------------------------------------------------
NOTES = {
    'test_banner_pages.py': 'The coloured page banners went (7 Sep); judged '
                            'on the pages as that round left them.',
    'test_comments_report.py': 'The Comments Report onto the table '
                               'standard (2 Sep), as that round left it.',
    'test_finance_headings.py': 'Financials headings off their bands '
                                '(8 Sep), as that round left them.',
    'test_fi_seg.py': 'FI\'s segmented control on base\'s .alv-seg (5 Sep), '
                      'as that round left base and the page.',
    'test_map_tiles.py': 'Map tiles off CARTO onto OSM (7 Sep), as that '
                         'round left the map pages.',
    SUITE: 'The five above judge their own rounds again, and the Comments '
           'Report wears base\'s report title. Newest, so most likely to be '
           'what breaks.',
}
if os.path.isfile(PS1):
    psrc = read(PS1)
    add = [s for s in FIVE + [SUITE] if "'%s'" % s not in psrc]
    if not add:
        report.append('%-44s already runs all six' % PS1)
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            block = ',\n'.join('    # %s\n    \'%s\'' % (NOTES[s], s)
                               for s in add)
            planned[PS1] = (psrc, psrc[:j] + ',\n' + block + psrc[j:])
            report.append('%-44s + %s' % (PS1, ', '.join(add)))

# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text) in planned.items():
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (path, e.lineno))
if CR in planned:
    src, text = planned[CR]
    for tag in ('{% if', '{% endif %}', '{% for', '{% endfor %}', '{{'):
        if src.count(tag) != text.count(tag):
            problems.append('comments_report.html: %s count changed' % tag)
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    if re.search(r'\.report-header', css):
        problems.append('comments_report.html: a .report-header rule survives')
    if text.count('class="alv-stat"') != src.count('class="alv-stat"'):
        problems.append('comments_report.html: the stat moved')

print('\n' + '=' * 74)
print('OLD ROUNDS - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
