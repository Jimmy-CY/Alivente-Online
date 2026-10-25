# -*- coding: utf-8 -*-
"""test_landing_tab.py - round TB-1b, 15 Oct 2026.

A BACK BUTTON THAT LANDS ON A TABBED PAGE HAS TO NAME THE TAB.

Demetri, across three messages: My Profile should return to
Administration with the System tab, the six Finance Setup pages to
Finance with Setup, and CRS Reporting to Personal with Compliance. Nine
controls, by his count.

THE CENSUS SAID TWENTY-THREE, and my_profile is a twenty-fourth that also
landed on the wrong PAGE. Eight of his nine already reached the right
page and then showed the wrong tab.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 1 RUNS THE HELPER against nine requests, five of them forged
    - a path, a traversal, another page's key, and a fragment of markup,
    which is what a value taken at face value would put into a class
    attribute.

    Section 2 COMPARES THE VIEW WITH THE TEMPLATE. A tuple in the view
    and a set of ids in the markup are two spellings of one thing; this
    reads both and requires them equal, in order.

    Section 3 RENDERS each tab strip as it stands, for every key AND for
    an absent one. The absent case is a check because the first cut of
    this round painted NO active tab without one - worse than the
    hard-coded tab it replaced. Its control renders each BACKUP with the
    key it was asked for and requires the wrong tab to still be showing.

    Section 5 RE-DERIVES THE ASSIGNMENT. The patcher's table is not
    evidence of itself: for nineteen of the twenty-four the tab is a fact
    about the landing pages - whichever PANEL links to the page - and
    that is recomputed here from the panels and compared with what the
    links say. The four no panel claims are named, with the reason.

A FIXTURE THAT HAS BEEN REWRITTEN BEFORE IT IS MEASURED IS NOT THE PAGE
    The first attempt at section 3 fed the strip through a regex that
    removed Django tags, and the regex ate the {% if %} it existed to
    leave: every tab came back active and the round looked broken when it
    was not. The strip is rendered untouched, which it can be because it
    contains no {% url %} and no permission test.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The markup of the three strips and of the twenty-four controls is
    this round's snapshot: before is .bak_landingtab, after is the file.
    The helper's behaviour, the panels' ownership and the registers are
    INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That the template could catch a wrong key. It cannot without
    repeating the page's own list in the markup. The template guards the
    ABSENT case; the view guards the WRONG one.
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
import importlib.util
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_landingtab'
ME = 'test_landing_tab.py'
PATCHER = 'apply_landing_tab.py'
PS1 = 'Push-PendingChanges.ps1'
HELPER = os.path.join('pages', 'services', 'landing_tabs.py')
ADMIN_VIEW = os.path.join('pages', 'views', 'administration.py')
FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
CONVERTED_NOW = 84
N_BACKS = 26   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, whose Back names the System tab.   # (was 25)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 24)

# The three landing pages: template, url name, tabs, default.
LANDING = (
    ('admin_apms.html', 'admin_apms', ('functional', 'system'), 'functional'),
    ('personal.html', 'personal_page', ('personal', 'compliance'), 'personal'),
    ('finance.html', 'finance', ('reports', 'setup'), 'reports'),
)
# The four no panel claims, and why. Named here so they cannot be
# mistaken for derivations in section 5.
# CREATED AFTER THIS ROUND, so the control below must not read
# them: they have no backup to fall back from, and the live file is
# not evidence about TB-1b's past. ES-3a, 23 Oct 2026.
CREATED_LATER = {
    'lease_signing_list.html',
    # ES-7, 25 Oct 2026 - the Signature and Stamp screen.
    'house_marks.html',
}

# TILES ADDED AFTER THIS ROUND FROZE ITS COPY OF A LANDING PAGE - ES-7,
# 25 Oct 2026. panel_owner() reads each landing page AS THIS ROUND LEFT
# IT, so a tile added since is invisible to it, and a Back that names
# that tile's own panel would read as UNEXPLAINED. ES-3a's tile sat on
# the default panel and could be named in BY_DEFAULT; a tile on the
# OTHER panel cannot. So it is named here WITH its panel - and the
# claim is checked against the LIVE landing page below, so this register
# cannot say a tile is somewhere it is not.
ADDED_AFTER = {
    ('admin_apms', 'house_marks'): 'system',
}

BY_DEFAULT = {
    'household_member_management.html': 'the landing page action bar',
    'notification_settings.html': 'the landing page action bar',
    'act_expense.html': 'nothing links to it',
    'personal_notification_settings.html': 'nothing links to it',
    # ES-3a, 23 Oct 2026. The fourth Administration tile links
    # it, but panel_owner() reads admin_apms.html as THIS round
    # left it - so the tile is correctly invisible here, and the
    # Back landing on functional is a default rather than a
    # derivation. Naming it is what the register is for.
    'lease_signing_list.html': 'the fourth Administration tile, added after this round froze its copy of the panel',
}

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

print('=' * 74)
print('%s - TB-1b, THE TAB A BACK BUTTON ASKS FOR' % ME)
print('=' * 74)

BACK_TAG = re.compile(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>')
URL_IN = re.compile(r"\{%\s*url\s*'([a-z_:]+)'[^}]*%\}")
TABS_BY_URL = {u: t for _, u, t, _ in LANDING}


# ==========================================================================
head('1. THE HELPER, RUN - A KEY FROM THE PAGE OWN LIST')
# ==========================================================================
hp = os.path.join(ROOT, HELPER)
if not ok(os.path.isfile(hp), 'pages/services/landing_tabs.py is there'):
    skip('every case below', 'there is no helper to run')
else:
    spec = importlib.util.spec_from_file_location('_alv_lt', hp)
    lt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lt)

    class Req(object):
        def __init__(self, **kw):
            self.GET = kw

    CASES = (
        ({'tab': 'setup'}, 'setup', 'the key the six Setup pages send'),
        ({'tab': 'reports'}, 'reports', 'the other real key'),
        ({}, 'reports', 'nothing asked - a menu click, or a bookmark'),
        ({'tab': ''}, 'reports', 'an empty key'),
        ({'tab': 'Setup'}, 'reports', 'the right word, wrong case'),
        ({'tab': 'compliance'}, 'reports',
         "another page's key, which this page does not have"),
        ({'tab': '/admin/'}, 'reports', 'a path'),
        ({'tab': 'setup/../../admin'}, 'reports', 'a forged key'),
        ({'tab': '" onclick="x'}, 'reports',
         'markup, which is what a value taken at face value would put '
         'in a class attribute'),
    )
    for get, want, what in CASES:
        got = lt.landing_tab(Req(**get), ('reports', 'setup'), 'reports')
        ok(got == want, '%-24s -> %-8s  %s'
           % (str(get.get('tab', '(absent)'))[:24], got, what),
           'wanted %r' % want)

# ==========================================================================
head('2. THE VIEW NAMES THE TABS, AND THEY ARE THE TABS THE PAGE HAS')
# ==========================================================================
# A LIST IN THE VIEW AND A SET OF IDS IN THE TEMPLATE ARE TWO SPELLINGS
# OF ONE THING. This is the check that keeps them one: the constants are
# read out of the view and compared with the ids read out of the markup.
AV = python_code_only(now(os.path.join(ROOT, ADMIN_VIEW)), payloads=False)
FV = python_code_only(now(os.path.join(ROOT, FIN_VIEW)), payloads=False)
SRC = {'admin_apms.html': AV, 'personal.html': AV, 'finance.html': FV}
CONST = {'admin_apms.html': 'ADMIN_TABS',
         'personal.html': 'PERSONAL_TABS',
         'finance.html': 'FINANCE_TABS'}
for page, url_name, tabs, default in LANDING:
    src = SRC[page]
    m = re.search(CONST[page] + r"\s*=\s*\(([^)]*)\)", src)
    declared = tuple(re.findall(r"'([a-z]+)'", m.group(1))) if m else ()
    ok(declared == tabs,
       '%-18s the view declares %s' % (page, list(declared)), tabs)
    md = re.search(CONST[page].replace('_TABS', '_TAB_DEFAULT')
                   + r"\s*=\s*'([a-z]+)'", src)
    ok(md is not None and md.group(1) == default,
       '  and arrives on %s when nothing asks' % default,
       md.group(1) if md else 'no default declared')
    ids = re.findall(r'id="tab-([a-z]+)"', now(alv_tree.path_of(page)))
    ok(tuple(ids) == tabs,
       '  and the markup draws exactly those ids, in that order', ids)
    ok('landing_tab(request, %s, %s'
       % (CONST[page], CONST[page].replace('_TABS', '_TAB_DEFAULT'))
       in src,
       '  and the view resolves the key through the one helper')

# ==========================================================================
head('3. RENDERED - ONE TAB ACTIVE, FOR EVERY KEY AND FOR NONE')
# ==========================================================================
# THE STRIP IS RENDERED AS IT STANDS, WITH NOTHING STRIPPED. The first
# attempt at this fed the block through a regex that removed Django tags
# and the regex ate the {% if %} it was meant to leave: every tab came
# back active and the round looked broken when it was not. A fixture
# that has been rewritten before it is measured is not the page.
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, USE_TZ=False, INSTALLED_APPS=[])
        django.setup()
    from django.template import Context, Engine
    ENG = Engine(dirs=[ROOT])
except Exception as e:
    ENG = None
    print('  !! Django would not configure: %s' % str(e)[:90])


def strip_block(src):
    """The tab strip, balanced on its own divs. It contains no {% url %}
    and no permission test, which is why it can be rendered alone."""
    i = src.find('<div class="admin-tabs">')
    if i < 0:
        return ''
    d, j = 0, i
    for m in re.finditer(r'<div\b|</div\s*>', src[i:]):
        d += 1 if m.group(0).startswith('<div') else -1
        if d == 0:
            j = i + m.end()
            break
    return src[i:j]


def active_of(blk, ctx):
    t = ENG.from_string(blk).render(Context(ctx))
    pairs = re.findall(r'<div class="admin-tab([^"]*)" id="([\w-]+)"', t)
    return [i for c, i in pairs if 'active' in c.split()], len(pairs)


if ENG is None:
    skip('the render', 'Django could not be configured')
else:
    for page, url_name, tabs, default in LANDING:
        blk = strip_block(now(alv_tree.path_of(page)))
        if not ok(bool(blk) and '{% url' not in blk,
                  '%-18s the strip renders alone - no url, no perms'
                  % page, blk[:70]):
            continue
        for key in tabs:
            act, total = active_of(blk, {'tab': key})
            ok(act == ['tab-' + key] and total == 2,
               '  tab=%-11s paints tab-%s and only that one'
               % (key, key), act)
        # THE ABSENT CASE, AND WHY IT IS A CHECK. Rendered with no `tab`
        # at all, the first cut of this round painted NO active tab -
        # which is worse than the hard-coded one it replaced, because a
        # reader sees two inert tabs and no content.
        act, _ = active_of(blk, {})
        ok(act == ['tab-' + default],
           '  no tab in the context at all still paints %s, through '
           "tab|default:'%s'" % (default, default), act)
        act, _ = active_of(blk, {'tab': ''})
        ok(act == ['tab-' + default], '  and so does an empty one', act)
        # The panels move with the tabs.
        full = now(alv_tree.path_of(page))
        n_panel_tests = len(
            re.findall(r"class=\"tab-panel[^\"]*\{% if tab", full))
        ok(n_panel_tests == 2,
           '  both panels are decided by the view as well', n_panel_tests)
        ok(not re.search(r'class="(?:admin-tab|tab-panel)[^"{]*active', full),
           '  and nothing on the page carries active by hand any more')

    # THE CONTROL. The backup could not answer a key at all: it had one
    # tab hard-coded active, so ?tab=setup arrived and Reports was
    # showing. Rendered, with the key it was asked for.
    for page, url_name, tabs, default in LANDING:
        w = was(alv_tree.path_of(page))
        if not w:
            skip('%s control' % page, 'no backup on disk')
            continue
        blk = strip_block(w)
        asked = tabs[1]
        act, _ = active_of(blk, {'tab': asked})
        ok(act == ['tab-' + default] and act != ['tab-' + asked],
           'CONTROL: %-18s asked for %s and the backup still painted %s'
           % (page, asked, default), act)

# ==========================================================================
head('4. EVERY BACK CONTROL THAT LANDS ON A TABBED PAGE NAMES ITS TAB')
# ==========================================================================
def census(get):
    named, bare = {}, []
    for q in alv_tree.templates():
        t = get(q)
        for m in BACK_TAG.finditer(t):
            u = URL_IN.search(m.group(0))
            if not u or u.group(1) not in TABS_BY_URL:
                continue
            g = re.search(r'\?tab=([a-z]+)', m.group(0))
            if g and g.group(1) in TABS_BY_URL[u.group(1)]:
                named.setdefault(
                    alv_tree.rel(q).replace('\\', '/'), []
                ).append((u.group(1), g.group(1)))
            else:
                bare.append('%s -> %s' % (alv_tree.rel(q), u.group(1)))
    return named, bare


named, bare = census(now)
ok(not bare, 'no Back control lands on a tabbed page without naming a '
   'tab that page has', '\n'.join(bare[:6]))
total = sum(len(v) for v in named.values())
ok(total == N_BACKS,
   '  and all %d of them do - the nine Demetri reported and %d more the '
   'census found' % (total, total - 9), total)
# TWENTY-FOUR NOW, TWENTY-THREE BEFORE. my_profile joins this census
# BECAUSE of the round: its Back control used to point at home, which is
# not a tabbed page, so the census could not see it. The control below
# therefore finds 23 bare and not 24, and that difference is the one
# control whose PAGE was wrong rather than its tab.
if not was(alv_tree.path_of('finance.html')):
    skip('the control', 'no backups on disk')
else:
    n2, b2 = census(lambda q: was(q) or now(q))
    # ES-3a, 23 Oct 2026 - see CREATED_LATER.
    n2 = dict((k, v) for k, v in n2.items()
              if os.path.basename(k) not in CREATED_LATER)
    b2 = [x for x in b2
          if os.path.basename(x.split(' ->')[0]) not in CREATED_LATER]
    ok(len(b2) == 23 and not n2,   # ES-3a, 23 Oct 2026 - was N_BACKS - 1, which drifted with every later round.
       '  CONTROL: before this round not one of the %d the census could '
       'see named a tab' % len(b2),
       '%d named, %d bare' % (sum(len(v) for v in n2.values()), len(b2)))
    ok(len(b2) == 24 - 1,   # ES-3a, 23 Oct 2026 - was total - 1, which drifted the moment a later round added a Back.
       '  and the twenty-fourth was invisible to it, because my_profile '
       'pointed at home - which has no tabs to name')

# ==========================================================================
head('5. THE TAB IS DERIVED, NOT CHOSEN - RE-DERIVED HERE')
# ==========================================================================
# THE TABLE IN THE PATCHER IS NOT EVIDENCE OF ITSELF. For nineteen of the
# twenty-four the answer is a fact about the landing pages: the tab is
# whichever PANEL links to the page. That is recomputed here from the
# panels as they stand, and compared with what the links actually say.
def panel_owner():
    out = {}
    for page, url_name, tabs, default in LANDING:
        src = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '',
                     now(alv_tree.path_of(page)), flags=re.S)
        for m in re.finditer(r'<div id="(?:panel-)?([a-z]+)(?:-panel)?" '
                             r'class="tab-panel', src):
            key, start = m.group(1), m.end()
            nxt = src.find('class="tab-panel', start)
            seg = src[start: nxt if nxt > 0 else len(src)]
            for u in re.findall(URL_IN, seg):
                out[(url_name, u)] = key
    return out


OWNER = panel_owner()
# ES-7 - the register above, each entry proved against the LIVE page.
for (_land, _dest), _key in sorted(ADDED_AFTER.items()):
    _page = [p for p, u, _t, _d in LANDING if u == _land][0]
    _live = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '',
                   read(alv_tree.path_of(_page)), flags=re.S)
    _m = re.search(r'<div id="(?:panel-)?%s(?:-panel)?" class="tab-panel'
                   % _key, _live)
    _seg = _live[_m.end():] if _m else ''
    _nxt = _seg.find('class="tab-panel')
    _seg = _seg[:_nxt] if _nxt > 0 else _seg
    ok(_dest in re.findall(URL_IN, _seg),
       '%s is on the LIVE %s page\'s %s panel - added after this round, '
       'and named in ADDED_AFTER' % (_dest, _page, _key))
    OWNER[(_land, _dest)] = _key
ok(len(OWNER) >= 14,
   'the three landing pages claim %d destination(s) between their panels'
   % len(OWNER), len(OWNER))
derived = mismatch = by_default = 0
for rel, links in sorted(named.items()):
    stem = os.path.basename(rel)
    me = 'crs:index' if rel == 'crs/index.html' else stem[:-5]
    for land, key in links:
        owner = OWNER.get((land, me))
        if owner is None:
            by_default += 1
            default = [d for _, u, _, d in LANDING if u == land][0]
            why = BY_DEFAULT.get(stem, '')
            ok(key == default and bool(why),
               '%-38s no panel claims it -> %-10s (%s)'
               % (stem, key, why or 'UNEXPLAINED'),
               'it names %r and the default is %r' % (key, default))
        elif key == owner:
            derived += 1
        else:
            mismatch += 1
            ok(False, '%-38s is on the %s panel but its Back says %s'
               % (stem, owner, key))
ok(not mismatch and derived >= 18,
   'and %d Back control(s) name the tab whose panel links to them - '
   'derived from the pages, not from a table' % derived,
   '%d mismatch(es)' % mismatch)
ok(by_default == 5,   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 4)
   '  with exactly %d explained by the default, each one named above'
   % by_default, by_default)

# ==========================================================================
head('6. MY PROFILE WAS THE ONLY ONE ON THE WRONG PAGE')
# ==========================================================================
mp = alv_tree.path_of('my_profile.html')
t = now(mp)
tag = BACK_TAG.search(t)
ok(tag is not None, 'my_profile has a Back control')
if tag:
    ok("url 'admin_apms'" in tag.group(0) and '?tab=system' in tag.group(0),
       '  and it goes to Administration, SYSTEM tab', tag.group(0)[:100])
    ok('aria-label="Back to administration"' in tag.group(0),
       '  and says so to a screen reader, which it did not before')
w = was(mp)
if not w:
    skip('the control', 'no backup on disk')
else:
    oldtag = BACK_TAG.search(w)
    ok(oldtag is not None and "url 'home'" in oldtag.group(0),
       '  CONTROL: the backup went to the Home page',
       oldtag.group(0)[:100] if oldtag else '')
    ok(oldtag is not None and 'aria-label="Back to home"' in oldtag.group(0),
       '  and said Back to home out loud - the only one of the 24 whose '
       'own markup admitted it')

# ==========================================================================
head('7. THE VIEW PAINTS IT, NOT A SCRIPT ON LOAD')
# ==========================================================================
# A hash read on load would work and would paint the wrong tab first,
# then jump. The whole reason this is in the view is that it does not.
for page, url_name, tabs, default in LANDING:
    t = now(alv_tree.path_of(page))
    js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))
    ok('location.hash' not in js and 'window.location' not in js,
       '%-18s reads no URL in its script' % page)
    ok('DOMContentLoaded' not in js and 'switchTab(' not in
       re.sub(r'function switchTab[^{]*\{', '', js).split('</script>')[0]
       .replace('switchTab(tab)', ''),
       '  and calls switchTab only from an onclick, not on load')

# ==========================================================================
head('8. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tabnames'),
   '%s is in alv_rounds.ROUNDS, after TB-1a' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_landing_tab.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the template could catch a wrong key. It cannot, and')
print('  it should not try: the only way would be to repeat the page own')
print('  list in the markup, which is two spellings of one thing. The')
print('  template guards the ABSENT case with one filter; the view')
print('  guards the WRONG case with a key from a list. Section 1 and')
print('  section 3 prove one each, and neither pretends to do both.')
print('')
print('  Not that notification_settings belongs on FUNCTIONAL. It is')
print('  reached from the landing page action bar, which sits above the')
print('  tabs and belongs to none of them, so the default is what that')
print('  bar can honestly say. Carrying the tab you were on out to the')
print('  child and back is the complete answer and is its own round.')
print('')
print('  Not that switchTab should live in base. Three pages carry three')
print('  copies and TB-1 moved the TREATMENT there on 8 Oct and left the')
print('  BEHAVIOUR copied. Still true, still not this round.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
