"""test_heading_prefix.py - the brand is in the tab, not on the heading.

    python test_heading_prefix.py

Run from the repo root, after apply_heading_prefix.py.

WHAT THIS SUITE IS FOR

  * SECTION 1 renders base's <title> through Django, with a control, rather
    than matching a string. The round's whole claim is that the brand now
    arrives from base at no cost to the page - a claim about what a browser
    receives, so it is checked against what Django actually produces.

  * SECTION 2 checks the 65 headings against their own backups: the prefix
    is gone, and every other word of the title survived. A round about a
    constant must not rename a page.

  * SECTION 3 measures the WHOLE corpus and holds a floor, so a page added
    next month that reintroduces the prefix shows up here.

  * SECTION 4 is the tab, checked so that it can fail. Non-empty is not
    enough - see the note there; a formatting bug in the patcher produced a
    twenty-thousand-byte tab that passed a non-empty check.

  * SECTION 5 is the exception, by name.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot tell you whether a tab
title is the right words for its page, only that it is short, unbranded,
present, and free of markup. And it cannot see the sidebar: whether the
brand is legible in the chrome is a screenshot's job, not a parser's.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')

PREFIX = 'ALIVENTE ONLINE - '
BRAND = 'Alivente Online'
SEP = ' | '
KEEPS_THE_BRAND = 'error_pages/connectivity_error.html'

# A different application sharing the repo; not this system's standard.
SKIP = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
        'unit_conversions', 'celebration_', 'import_recipe',
        'map_ingredients', 'measurement_units', 'household_member',
        'categories_management')

# Except this one, which extends base and would otherwise state the brand
# twice - once in the tab base now supplies, once in its own heading. A
# defect this round would have introduced, so this round fixes it.
ALSO_IN_SCOPE = ('recipe_management.html',)

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            _p = os.path.join(_d, _f)
            if rel_of(_p) in ALSO_IN_SCOPE \
                    or not any(s in rel_of(_p) for s in SKIP):
                TEMPLATES.append(_p)
TEMPLATES.sort()

B = read(BASE)
TITLE_TAG = re.search(r'<title>.*?</title>', B, re.S)


def title_of(src):
    m = re.search(r'<(h1|h2)\b[^>]*>(.*?)</\1>', markup_of(src), re.S | re.I)
    return m.group(0) if m else None


def words_of(t):
    """The alphabetic words a reader sees, Django constructs removed."""
    t = re.sub(r'\{[{%#][^}]*[}%#]\}', ' ', t or '')
    t = re.sub(r'<[^>]+>', ' ', t)
    return [w for w in re.findall(r'[A-Za-z]{3,}', t)]


def tab_of(src):
    """(text, well_formed). Closing on `{% endblock` ALONE is what let a
       malformed replacement slip through: with `{%% endblock %%}` in the
       file the search ran on to the next endblock thousands of bytes away
       and returned the rest of the page, which is non-empty and passed."""
    m = re.search(r'\{%\s*block title\s*%\}(.*?)\{%\s*endblock[^%]*%\}',
                  src, re.S)
    if m is None:
        return None, ('{% block title %}' not in src)
    return re.sub(r'\s+', ' ', m.group(1)).strip(), True


# ===========================================================================
head('1. base renders the tab, and the brand arrives from there')
# ===========================================================================
check('base carries a title tag', TITLE_TAG is not None)
if TITLE_TAG:
    _t = TITLE_TAG.group(0)
    check('  it holds the title block', '{% block title %}' in _t, _t)
    check('  and appends the brand', BRAND in _t)
    check('  with the separator six pages already used', SEP in _t)
    check('  and the placeholder is gone', 'Hello, world!' not in B)

try:
    import django
    from django.conf import settings
    from django.template import Engine, Context
    if not settings.configured:
        settings.configure(TEMPLATES=[], USE_TZ=True,
                           INSTALLED_APPS=['django.contrib.staticfiles'])
        django.setup()

    # RENDER IT. The claim is about what a browser receives, so the title is
    # rendered rather than matched. Two in-memory templates: base's own
    # title tag as the parent, and a child that fills the block the way a
    # real page does. Nothing else of base is involved, so no tag library
    # and no context are needed.
    PARENT = TITLE_TAG.group(0) if TITLE_TAG else ''
    eng = Engine(loaders=[('django.template.loaders.locmem.Loader', {
        'p.html': PARENT,
        'page.html': '{% extends "p.html" %}'
                     '{% block title %}Properties{% endblock %}',
        'empty.html': '{% extends "p.html" %}'
                      '{% block title %}{% endblock %}',
    })])
    out = eng.get_template('page.html').render(Context({}))
    check('Django renders the tab for a real page',
          out == '<title>Properties' + SEP + BRAND + '</title>', repr(out))
    check('  and the brand appears exactly once', out.count(BRAND) == 1,
          '%d time(s)' % out.count(BRAND))

    # THE CONTROL. An empty block gives a title that leads with the
    # separator - visibly wrong, and the reason section 4 refuses to let any
    # page ship an empty block. If this rendered the same as the one above,
    # section 4 would be measuring nothing.
    bad = eng.get_template('empty.html').render(Context({}))
    check('  CONTROL: an EMPTY block renders a leading separator',
          bad == '<title>' + SEP.lstrip() + BRAND + '</title>'
          or bad.startswith('<title> ' + SEP.strip()), repr(bad))
    check('  CONTROL: .. so the two differ, and section 4 is measuring',
          bad != out)
except ImportError:
    print('  SKIP  django not importable - the render check needs it')
except Exception as e:
    check('Django renders the tab', False, '%s: %s' % (type(e).__name__,
                                                       str(e)[:60]))

# ===========================================================================
head('2. the headings this round moved, against their own backups')
# ===========================================================================
MOVED = [p for p in TEMPLATES if os.path.exists(p + '.bak_pfx')
         and rel_of(p) != 'base.html']
check('the round left backups to compare against', len(MOVED) >= 60,
      '%d found' % len(MOVED))

_hdr = 0
for p in MOVED:
    rel = rel_of(p)
    now, was = read(p), read(p + '.bak_pfx')
    t_now, t_was = title_of(now), title_of(was)
    if t_was is None or PREFIX not in t_was:
        continue                          # a tab-only or comment-only change
    _hdr += 1
    check('%-44s the prefix is gone' % rel,
          t_now is not None and PREFIX not in t_now,
          re.sub(r'<[^>]+>', '', t_now or '')[:34])
    check('  and the heading is not empty',
          bool(re.sub(r'<[^>]+>', '', t_now or '').strip()))
    # THE WORDS MUST SURVIVE. A round about a constant must not rename a
    # page. ALIVENTE and ONLINE are the constant and are expected to go.
    _w = [w for w in words_of(t_was) if w.upper() not in ('ALIVENTE',
                                                          'ONLINE')]
    _now = ' '.join(words_of(t_now)).upper()
    check('  and every other word survived',
          all(w.upper() in _now for w in _w),
          '%s -> %s' % (' '.join(_w)[:22], _now[:26]))
    # Structure untouched: this round edits text.
    for tag in ('div', 'h2', 'h1', 'center'):
        a = (len(re.findall(r'<%s\b' % tag, markup_of(now)))
             - len(re.findall(r'</%s>' % tag, markup_of(now))))
        b = (len(re.findall(r'<%s\b' % tag, markup_of(was)))
             - len(re.findall(r'</%s>' % tag, markup_of(was))))
        if a != b:
            check('  <%s> balance unchanged' % tag, False,
                  '%+d -> %+d' % (b, a))
check('  it moved the headings it said it would', _hdr >= 61,
      '%d heading(s)' % _hdr)

# ===========================================================================
head('3. the whole corpus - nobody still heads themselves with the brand')
# ===========================================================================
STILL, TOTAL = [], 0
for p in TEMPLATES:
    rel = rel_of(p)
    if rel in ('base.html', KEEPS_THE_BRAND):
        continue
    t = title_of(read(p))
    if t is None:
        continue
    TOTAL += 1
    if 'ALIVENTE ONLINE' in t:
        STILL.append(rel)
print('        %d page(s) carry a heading; %d still name the brand in it.'
      % (TOTAL, len(STILL)))
for rel in STILL:
    print('          still branded: %s' % rel)
check('no heading outside the one exception names the brand', not STILL,
      str(STILL[:4]))
# A REPORT WITH A FLOOR, not an equality. A hardcoded corpus count has
# failed correct work twelve times on this codebase.
check('  CONTROL: and there really are headings to have got wrong',
      TOTAL >= 90, '%d' % TOTAL)

# ===========================================================================
head('4. the browser tab, checked so that it can fail')
# ===========================================================================
# NON-EMPTY IS NOT ENOUGH, AND THIS IS WHY. The patcher built its
# replacement two ways, and one branch left a literal `{%% endblock %%}` in
# eleven files. The self-check looked for `{% endblock` to find the end of
# the block, did not find it, matched the NEXT one thousands of bytes later,
# and measured a tab of twenty thousand bytes of markup - which is
# non-empty, and passed. Short, well-formed, markup-free, brand-free.
EXTENDS, BAD = 0, []
for p in TEMPLATES:
    rel = rel_of(p)
    src = read(p)
    if rel == 'base.html' or '{% extends' not in src:
        continue
    EXTENDS += 1
    txt, wellformed = tab_of(src)
    if not wellformed:
        BAD.append((rel, 'the block opens but never closes'))
        continue
    if txt is None:
        BAD.append((rel, 'no title block at all'))
    elif txt == '':
        BAD.append((rel, 'empty - the tab renders as " | Alivente Online"'))
    elif len(txt) > 120:
        BAD.append((rel, '%d characters - it has swallowed the page'
                    % len(txt)))
    elif '<' in txt:
        BAD.append((rel, 'contains markup: %r' % txt[:40]))
    elif '%%' in txt:
        BAD.append((rel, 'contains a literal %% - a formatting bug'))
    elif 'livente' in txt.lower():
        BAD.append((rel, 'still names the brand, which base now adds'))
for rel, why in BAD:
    print('          %-42s %s' % (rel, why))
check('every page that extends base sets a sound tab title', not BAD,
      '%d of %d bad' % (len(BAD), EXTENDS))
check('  CONTROL: and there really are pages to have got wrong',
      EXTENDS >= 90, '%d extend base' % EXTENDS)

# The nine standalone templates never inherit base, so base's tab tag does
# not reach them. Named, so nobody looks for them in the count above.
_alone = [rel_of(p) for p in TEMPLATES
          if '{% extends' not in read(p) and rel_of(p) != 'base.html']
print('        %d standalone template(s) do not inherit the tab: %s'
      % (len(_alone), ', '.join(_alone)))
check('  the standalone set is small and known', len(_alone) <= 12,
      '%d' % len(_alone))

# ===========================================================================
head('5. the exception, and the comments that named the old rule')
# ===========================================================================
_p = os.path.join(T, KEEPS_THE_BRAND.replace('/', os.sep))
if os.path.exists(_p):
    _t = title_of(read(_p))
    check('%s keeps its heading' % KEEPS_THE_BRAND,
          _t is not None and 'ALIVENTE ONLINE' in _t,
          re.sub(r'<[^>]+>', '', _t or '')[:30])
    check('  and it is the whole heading, which is why it stays',
          _t is not None
          and re.sub(r'<[^>]+>', '', _t).strip() == 'ALIVENTE ONLINE',
          repr(re.sub(r'<[^>]+>', '', _t or '').strip()))
    check('  CONTROL: stripping it would leave nothing',
          _t is not None
          and not re.sub(r'<[^>]+>', '', _t).replace('ALIVENTE ONLINE',
                                                     '').strip())

_stale = [rel_of(p) for p in TEMPLATES
          if 'prefixed "ALIVENTE ONLINE - "' in read(p)]
check('no round comment still states the prefix rule', not _stale,
      str(_stale[:4]))
_new = [rel_of(p) for p in TEMPLATES
        if 'the brand is in the browser tab' in read(p)]
check('  and the reworded note is on the pages that carried the old one',
      len(_new) >= 25, '%d page(s)' % len(_new))

# ===========================================================================
head('6. what the round did NOT do')
# ===========================================================================
# Named so that the next round inherits a decision rather than a silence.
_rec = []
for p in TEMPLATES:
    t = title_of(read(p))
    if t and '{{' in t:
        _rec.append(rel_of(p))
print('        %d page(s) carry a record name in the heading - shape B'
      '\n        (module on the h2, MODE LABEL - Record Name on the h4, em '
      'dash\n        because the data contains hyphens) is agreed for those:'
      % len(_rec))
for rel in _rec:
    print('          %s' % rel)

# THE CLAIM IS THAT THIS ROUND LEFT THE RECORD NAMES ALONE, and it is
# measured that way rather than by counting how many are left.
#
# The first version asserted `len(_rec) >= 10`, which was true the day it was
# written and would have failed the moment the NEXT round did its job - a
# check that decays into a scope guard. What this round actually promises is
# that it removed a constant and touched nothing else, so the variables in
# every heading are the same before and after. That stays true for good.
_moved_names = []
for p in TEMPLATES:
    bak = p + '.bak_pfx'
    if not os.path.exists(bak):
        continue
    a = set(re.findall(r'\{\{\s*([^}]+?)\s*\}\}', title_of(read(p)) or ''))
    b = set(re.findall(r'\{\{\s*([^}]+?)\s*\}\}',
                      title_of(read(bak)) or ''))
    if a != b:
        _moved_names.append('%s %s -> %s' % (rel_of(p), sorted(b), sorted(a)))
check('this round changed no heading\'s record name', not _moved_names,
      str(_moved_names[:2]))
check('  CONTROL: and some headings really do carry one', len(_rec) >= 1,
      '%d' % len(_rec))

_mode = [rel_of(p) for p in TEMPLATES
         if (title_of(read(p)) or '') and
         re.match(r'^(ADD|EDIT)\b',
                  re.sub(r'<[^>]+>', '', title_of(read(p))).strip())]
print('        %d page(s) head themselves with a MODE where the module name'
      '\n        belongs - correct under the old rule, wrong under shape B.'
      '\n        That is the Add/Edit round, not this one:' % len(_mode))
for rel in _mode:
    print('          %s' % rel)

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that a tab title is the RIGHT words for its page,')
print('  or that the brand reads well in the printed chrome. Both want eyes.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
