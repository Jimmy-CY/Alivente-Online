# -*- coding: utf-8 -*-
"""test_subtree_tones.py - Section H round H7b, 28 Sep 2026.

H7 gave base an opinion about Bootstrap's SUCCESS and WARNING families.
Its census ran over `glob('pages/templates/*.html')`, which does not
descend, so it counted 120 templates where there are 138 - eighteen live
in six subdirectories, eleven of them in projects/.

SECTION 1 IS THE LESSON, AND IT IS A GATE. It counts the tree both ways
and FAILS if a flat listing ever agrees with a walk again by accident -
that is, it asserts the subtree still exists and is still bigger than
zero, so a future reader cannot conclude the flat glob was fine.

SECTION 2 IS THE ROUND: four hexes and one colour keyword leave three
projects/ pages, so the two families really do have one owner.

SECTION 3 IS THE TREE-WIDE GATE that stops this recurring. It walks
every one of the 143 and fails if any page declares a rule for one of
H7's families except the two that are named and reasoned.

THIS IS NOT A CONTRAST ROUND AND SECTION 6 SAYS SO IN NUMBERS. #856404
measures 5.49 on white and --alv-warn #8e6207 measures 5.38 - the house
token is a hair WORSE, and both pass AA. What changes is that there is
one amber instead of two. The alert EDGES do move visibly, from
Bootstrap's loud 2.76 rim to the house 1.25, which is where H7 put it.
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
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_subtree'
ME = 'test_subtree_tones.py'
PATCHER = 'apply_subtree_tones.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# The four hexes and the one keyword this round removes, per file.
GONE = {
    'projects/projects_detail.html': ['#0e7c8b'],
    'projects/project_tasks_edit.html': ['#856404', '#28a745', '#ffc107'],
    'projects/project_tasks_delete.html': ['#856404'],
}
# What had no wearer at all, in markup or in a script, before the round.
DEAD = [('projects/projects_detail.html', 'btn-warning'),
        ('projects/project_tasks_edit.html', 'text-warning')]
# What DID have one, built inside a script - which is the whole argument
# for base owning the family rather than each page.
LIVE = [('projects/project_tasks_edit.html', 'alert-success'),
        ('projects/project_tasks_edit.html', 'alert-warning'),
        ('projects/project_tasks_delete.html', 'text-warning')]
# Named exceptions to the tree-wide gate in section 3.
# The ONE named exception to the tree-wide gate in section 3. A print
# document paints these flat on purpose and its style block sits after
# base's, so it wins and should.
#
# personal_notification_settings is NOT here any more: it names
# .btn-success and sets a width and a padding, which the gate allows,
# because the gate is about paint rather than about the selector.
LEAVE = {
    'manual_pdf.html': 'a PRINT document, flat on purpose',
}
FAMILY = (r'\.(?:a\.)?(?:text|bg|btn|badge|alert|border|list-group-item'
          r'|table)-(?:outline-)?(?:success|warning)\b')

passed = failed = skipped = 0


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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


def walked():
    """Every template, at any depth."""
    out = []
    for folder, _, names in os.walk(T):
        for n in sorted(names):
            if n.endswith('.html'):
                rel = os.path.relpath(os.path.join(folder, n), T)
                out.append((rel.replace(os.sep, '/'),
                            os.path.join(folder, n)))
    return sorted(out)


def flat():
    """What H7's census saw: the top level, and nothing else."""
    return sorted(n for n in os.listdir(T) if n.endswith('.html'))


def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    c = [(x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4)
         for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return round((max(la, lb) + 0.05) / (min(la, lb) + 0.05), 2)


print('=' * 74)
print("%s - H7b, THE HEXES H7'S GLOB NEVER SAW" % ME)
print('=' * 74)

tree = walked()
top = flat()
sub = [(rel, p) for rel, p in tree if '/' in rel]

# ==========================================================================
head('1. THE CENSUS BUG, MADE PERMANENT')
# ==========================================================================
# 138 and 120 until 1 Oct 2026, when Section A round A1 added the
# four public set-password pages. All four sit at the ROOT of
# pages/templates, so both numbers move by four and the eighteen
# that live in subdirectories - the whole point of this section -
# is still eighteen.
ok(len(tree) == 143, 'a WALK finds 143 templates', len(tree))
ok(len(top) == 125, '  a flat listing finds 125 - 120 was what H7 counted',
   len(top))
ok(len(sub) == 18, '  so 18 live in subdirectories and H7 never saw them',
   len(sub))
folders = sorted({rel.split('/')[0] for rel, _ in sub})
ok(len(folders) == 6, '  across %d folders: %s' % (len(folders),
                                                   ', '.join(folders)),
   folders)
ok(sum(1 for rel, _ in sub if rel.startswith('projects/')) == 11,
   '  eleven of them in projects/ alone')
ok(len(tree) > len(top),
   '  a flat listing is NOT the tree, and a suite that assumes it is '
   'will miss a whole folder')

# ==========================================================================
head('2. THE FOUR HEXES AND THE ONE KEYWORD ARE GONE')
# ==========================================================================
for rel, hexes in sorted(GONE.items()):
    p = os.path.join(T, *rel.split('/'))
    css_now, css_was = css_of(now(p)), css_of(was(p))
    for h in hexes:
        here = [m for m in RULE.finditer(css_now)
                if re.search(FAMILY, m.group(1)) and h in m.group(2)]
        there = [m for m in RULE.finditer(css_was)
                 if re.search(FAMILY, m.group(1)) and h in m.group(2)]
        ok(not here and there,
           '%-38s no longer writes %s in a %s rule'
           % (rel, h, 'success/warning'),
           '%d now, %d before' % (len(here), len(there)))
p = os.path.join(T, 'projects', 'projects_detail.html')
fam_now = [m.group(2) for m in RULE.finditer(css_of(now(p)))
           if re.search(FAMILY, m.group(1))]
fam_was = [m.group(2) for m in RULE.finditer(css_of(was(p)))
           if re.search(FAMILY, m.group(1))]
ok(not fam_now and any('white' in b for b in fam_was),
   "  and the colour KEYWORD `white` went with the rules that carried "
   'it - 3.1 bans a keyword for the same reason it bans a hex, that an '
   'audit which greps for # cannot see one',
   '%d rule(s) now, %d before' % (len(fam_now), len(fam_was)))

# ==========================================================================
head('3. THE TREE-WIDE GATE - WALKED, NOT GLOBBED')
# ==========================================================================
# THE GATE IS ABOUT COLOUR, NOT ABOUT THE SELECTOR. A page may still
# say `.notification-card .btn-success { width: 100% }` - that is
# layout, and where a control sits is the page's own business. What no
# page may do is PAINT one of these families, because base owns what
# they mean. Written this way after the first cut failed on a rule that
# sets a font-weight and a margin and no colour at all.
PAINTS = re.compile(r'(?:^|[;{])\s*(?:colou?r|background|background-color'
                    r'|border|border-color|border-\w+-color|fill|stroke)'
                    r'\s*:', re.I)
offenders, layout_only = [], []
for rel, p in tree:
    if rel == 'base.html' or rel in LEAVE:
        continue
    for m in RULE.finditer(css_of(now(p))):
        if not re.search(FAMILY, m.group(1)):
            continue
        if PAINTS.search(m.group(2)):
            offenders.append('%s  %s  { %s }'
                             % (rel, ' '.join(m.group(1).split())[:40],
                                ' '.join(m.group(2).split())[:40]))
        else:
            layout_only.append('%s  %s' % (rel,
                                           ' '.join(m.group(1).split())[:40]))
ok(not offenders,
   'no page anywhere PAINTS a success or warning family - base owns what '
   'they mean', '\n'.join(offenders[:6]))
ok(len(layout_only) == 2,
   '  %d rule(s) name one and set only layout, which is allowed'
   % len(layout_only), '\n'.join(layout_only))
for line in layout_only:
    print('        %s' % line)
for rel, why in sorted(LEAVE.items()):
    p = os.path.join(T, rel)
    n = sum(1 for m in RULE.finditer(css_of(now(p)))
            if re.search(FAMILY, m.group(1)))
    ok(n >= 1, '  and %s is the one named exception, keeping %d - %s'
       % (rel, n, why), n)

# ==========================================================================
head('4. TWO WERE DEAD BEFORE THE ROUND, AND ARE PROVED SO')
# ==========================================================================
for rel, cls in DEAD:
    p = os.path.join(T, *rel.split('/'))
    w = was(p)
    ok(len(re.findall(r'\b%s\b' % cls, markup(w))) == 0
       and len(re.findall(r'\b%s\b' % cls, js_of(w))) == 0,
       '%-38s .%s had NO wearer, in markup or script' % (rel, cls),
       'markup %d, script %d'
       % (len(re.findall(r'\b%s\b' % cls, markup(w))),
          len(re.findall(r'\b%s\b' % cls, js_of(w)))))

# ==========================================================================
head('5. THREE WERE LIVE - AND TWO OF THEM ONLY IN A SCRIPT')
# ==========================================================================
for rel, cls in LIVE:
    p = os.path.join(T, *rel.split('/'))
    n = now(p)
    mk = len(re.findall(r'\b%s\b' % cls, markup(n)))
    js = len(re.findall(r'\b%s\b' % cls, js_of(n)))
    ok(mk + js >= 1,
       '%-38s .%s is worn (markup %d, script %d)' % (rel, cls, mk, js))
ok(len(re.findall(r'\balert-success\b',
                  js_of(now(os.path.join(T, 'projects',
                                         'project_tasks_edit.html'))))) >= 1,
   '  an alert built inside a script wears the same class a template '
   'would, which is why base owning the family reaches it')

dp = os.path.join(T, 'projects', 'project_tasks_delete.html')
rule = [m.group(2) for m in RULE.finditer(css_of(now(dp)))
        if 'subtasks-warning' in m.group(1) and 'text-warning' in m.group(1)]
ok(rule and 'font-weight' in rule[0] and 'margin-bottom' in rule[0]
   and 'color' not in rule[0],
   'the one EDITED rule kept its layout and lost only its colour',
   ' '.join(rule[0].split()) if rule else 'rule not found')

# ==========================================================================
head('6. THE NUMBERS - AND ONE OF THEM GOES THE WRONG WAY')
# ==========================================================================
# Said plainly rather than left for someone to find: this round is not a
# contrast fix. It is a one-owner fix.
for surface, name in (('#ffffff', 'white'), ('#f8f9fa', 'bg-light'),
                      ('#e9ecef', 'the wash')):
    b, h = ratio('#856404', surface), ratio('#8e6207', surface)
    ok(b >= 4.5 and h >= 4.5,
       'text-warning on %-9s  page hex %.2f -> house token %.2f  '
       '(both pass AA)' % (name, b, h))
ok(ratio('#8e6207', '#ffffff') < ratio('#856404', '#ffffff'),
   '  the house token is a HAIR WORSE on white, and that is the honest '
   'trade for having one amber instead of two',
   '%.2f vs %.2f' % (ratio('#8e6207', '#ffffff'),
                     ratio('#856404', '#ffffff')))
ok(ratio('#28a745', '#e6f4ec') > ratio('#bfe0cd', '#e6f4ec'),
   "the alert EDGE gets quieter - Bootstrap's rim %.2f, the house line "
   '%.2f' % (ratio('#28a745', '#e6f4ec'), ratio('#bfe0cd', '#e6f4ec')))
ok('--alv-good-line' in css_of(now(BASE))
   and '--alv-warn-line' in css_of(now(BASE)),
   '  and base is what draws it now, on the tokens H7 added')

# ==========================================================================
head('7. RENDERED - THE EDGE AND THE INK, BEFORE AND AFTER')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

FRAG = ('<div class="alert alert-success" id="s">saved</div>'
        '<div class="alert alert-warning" id="w">careful</div>'
        '<div class="subtasks-warning"><h6 class="text-warning" id="t">'
        'Warning</h6></div>')
PROBE = """() => {
  const g = id => {
    const e = document.getElementById(id);
    const s = getComputedStyle(e);
    return [s.borderTopColor, s.color];
  };
  return {s: g('s'), w: g('w'), t: g('t')};
}"""


def paint(page_css, tag):
    from playwright.sync_api import sync_playwright
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body>%s</body></html>'
            % (read(BOOT), '\n'.join(STYLE.findall(now(BASE))), page_css,
               FRAG))
    fx = os.path.join(SCRATCH, 'h7b_%s.html' % tag)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(html)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 700, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(PROBE)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    ep = os.path.join(T, 'projects', 'project_tasks_edit.html')
    before = paint(css_of(was(ep)) + css_of(was(dp)), 'before')
    after = paint(css_of(now(ep)) + css_of(now(dp)), 'after')
    ok(before['s'][0] == 'rgb(40, 167, 69)',
       "CONTROL: the success alert's edge WAS Bootstrap #28a745",
       before['s'][0])
    ok(after['s'][0] == 'rgb(191, 224, 205)',
       '  and is now --alv-good-line #bfe0cd', after['s'][0])
    ok(before['w'][0] == 'rgb(255, 193, 7)',
       "CONTROL: the warning alert's edge WAS Bootstrap #ffc107",
       before['w'][0])
    ok(after['w'][0] == 'rgb(236, 211, 158)',
       '  and is now --alv-warn-line #ecd39e', after['w'][0])
    ok(before['t'][1] == 'rgb(133, 100, 4)',
       'CONTROL: the warning heading WAS the page hex #856404',
       before['t'][1])
    ok(after['t'][1] == 'rgb(142, 98, 7)',
       '  and is now --alv-warn #8e6207, which base owns', after['t'][1])

# ==========================================================================
head('8. CONTROLS, AND THE GATE')
# ==========================================================================
ok(re.search(FAMILY, '.btn-outline-success') is not None,
   'the family pattern matches an outline variant')
ok(re.search(FAMILY, '.btn-successful') is None,
   '  and does NOT match a longer class that merely starts the same way')
ok(re.search(FAMILY, '.alert-danger') is None,
   '  and leaves the danger family alone')
ok(not re.search(FAMILY, css_of('<style>/* .btn-success */ a{x:1}</style>')),
   '  and cannot be tripped by a class named inside a CSS comment')
ok(ratio('#ffffff', '#ffc107') == 1.63,
   '  the contrast maths agrees with the published value for #ffc107')

for rel in sorted(GONE):
    p = os.path.join(T, *rel.split('/'))
    ok(any(h in css_of(was(p)) for h in GONE[rel]),
       'reverting %s puts its hex back, so section 2 would FAIL' % rel)

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_moremenu' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_moremenu'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE REAL FINDING IS NOT THE FOUR HEXES. It is that a census')
print('  written as glob(*.html) has been the measuring instrument for')
print('  every round this session, and it was blind to thirteen per cent')
print('  of the tree. H7 is the one it cost; the others changed base or')
print('  named their pages. Section 1 is here so the next census cannot')
print('  quietly make the same assumption.')
print('=' * 74)
sys.exit(1 if failed else 0)
