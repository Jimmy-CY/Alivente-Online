"""test_map_provider.py - the map asks a provider whose terms cover it, from
   one definition, and says so when it has no key.

    python test_map_provider.py

Run from the repo root, after apply_map_provider.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST
-------------------------------------
It cannot prove tiles arrive. That needs a live HTTPS request to a third
party, which the build sandbox refuses outright, and which on any machine
where it did succeed would be a fact about that machine's network on that
afternoon rather than about this change. The previous round said the same
thing and was right to; what it could not say was that the tiles had
ALREADY stopped arriving, because nothing it could check had changed.

So this suite checks the two things that are checkable and were the actual
faults:

  * THE PROVIDER IS DEFINED ONCE. Four pages used to spell the tile URL out
    themselves, which is how map_view quietly drifted to CARTO and spent
    months drawing tiles with API KEY REQUIRED printed into the image. It
    drew. The pins landed. The console was clean. Nobody looked.

  * THE PAGE SAYS WHEN IT HAS NO KEY. A tile layer with no key does not
    fail loudly; it leaves an empty grey square, and an empty grey square
    reads as a fault in the page rather than as a setting nobody filled in.

SECTION 2 IS THE ONE THAT EARNS ITS KEEP. It does not read the templates
with a regex and call that a proof - it RENDERS each page's map block
through Django twice, once with a key and once without, and reads the
JavaScript that comes out. escapejs rewrites every one of `<`, `>`, `&`,
`=`, `-` and `;` into a \\u escape, and the tile URL contains four of them;
a check that only looked at the template source would never see whether
what reached the browser was still a URL.

The remaining verification is a person loading the page - and this time the
page will say which of the two answers it is.
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

import os
import re
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
SETTINGS = os.path.join(ROOT, 'mysite', 'settings.py')
CTXPROC = os.path.join(ROOT, 'mysite', 'context_processors.py')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

# map_test.html was the fourth until round D1, 23 Sep: a developer
# page no view or URL rendered. The round deleted it and asserts
# below that it is gone, so this list is three by decision.
PAGES = ('properties_add.html', 'properties_edit.html',
         'map_view.html')
assert not os.path.exists(os.path.join(T, 'map_test.html')), \
    'map_test.html is back - it was deleted as dead in round D1'
GEOCODERS = ('properties_add.html', 'properties_edit.html')

# The hosts this round exists to stop calling. Spelled in pieces so that a
# scan of this file for them does not find its own checks - the trap this
# project has now met twenty-odd times.
OSM_TILES = 'tile.' + 'openstreetmap.org'
OSM_GEOCODE = 'nominatim.' + 'openstreetmap.org'

FAKE = 'k' * 32          # a key-shaped string; not a key

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
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def templates():
    """Every template in the project, not just the ones at the top level.

    The sweep in section 4 is a claim about the WHOLE corpus, and six of
    this project's template directories are subdirectories. A survey that
    walks one level and reports zero is the shape of mistake that had me
    tell the user the gate was complete while their machine said nineteen
    suites were missing.
    """
    out = []
    for dirpath, _dirs, names in os.walk(T):
        for n in names:
            if n.endswith('.html'):
                out.append(os.path.join(dirpath, n))
    return sorted(out)


if not os.path.isdir(T):
    print('! %s not found - run from the project root' % T)
    sys.exit(1)

# ---------------------------------------------------------------------- 1
head('1. ONE DEFINITION, AND IT READS THE ENVIRONMENT')

S = read(SETTINGS)
check('settings reads the key from the environment',
      re.search(r"GEOAPIFY_KEY\s*=\s*os\.getenv\(\s*['\"]GEOAPIFY_KEY['\"]",
                S) is not None)
check('  and defaults to empty rather than to something',
      re.search(r"os\.getenv\(\s*['\"]GEOAPIFY_KEY['\"]\s*,\s*['\"]{2}\s*\)",
                S) is not None)
check('  and registers the context processor',
      'mysite.context_processors.map_provider' in S)

# The key must never be in the repo. It is not a secret - it travels to the
# browser by definition - but a key in git is a key that cannot be rotated
# without a deploy, and a key that outlives whoever set it.
literal = []
for p in [SETTINGS, CTXPROC] + templates():
    txt = read(p)
    for m in re.finditer(r'apiKey=([A-Za-z0-9_\-]{8,})', txt):
        literal.append('%s: %s...' % (os.path.basename(p), m.group(1)[:6]))
check('no key is written into the repo', not literal, '; '.join(literal[:3]))
check('  CONTROL: the scan can see one',
      len(re.findall(r'apiKey=([A-Za-z0-9_\-]{8,})',
                     'x?apiKey=' + FAKE)) == 1)

# ---- load the context processor, with the database driver stubbed out.
# It imports mysql.connector at module level and this suite has no business
# opening a database to ask what a URL looks like.
for name in ('mysql', 'mysql.connector'):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.path.insert(0, ROOT)

import django                                              # noqa: E402
from django.conf import settings as dj                     # noqa: E402

if not dj.configured:
    dj.configure(DEBUG=True, GEOAPIFY_KEY='', TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}])
    django.setup()

from django.template import Context, Template               # noqa: E402

try:
    from mysite.context_processors import map_provider
except Exception as e:                                      # pragma: no cover
    check('the context processor imports', False, str(e))
    print('\nStopping: nothing below can run.')
    sys.exit(1)
check('the context processor imports', True)


def ctx(key):
    dj.GEOAPIFY_KEY = key
    return map_provider(None)


WITH, WITHOUT = ctx(FAKE), ctx('')

check('with a key, the tile URL is Geoapify',
      WITH['MAP_TILE_URL'].startswith('https://maps.geoapify.com/v1/tile/'),
      WITH['MAP_TILE_URL'][:52])
check('  and it is the classic OpenStreetMap style',
      '/osm-carto/' in WITH['MAP_TILE_URL'])
check('  and it carries the key',
      WITH['MAP_TILE_URL'].endswith('apiKey=' + FAKE))
check('  and Leaflet\'s own placeholders survived',
      all(t in WITH['MAP_TILE_URL'] for t in ('{z}', '{x}', '{y}')))
check('  and the geocoder takes the same key',
      WITH['MAP_GEOCODE_URL'].startswith('https://api.geoapify.com/')
      and FAKE in WITH['MAP_GEOCODE_URL'])
check('  and asks for the format whose answer has lat and lon on it',
      'format=json' in WITH['MAP_GEOCODE_URL'])
check('  and for one result, as the pages expect',
      'limit=1' in WITH['MAP_GEOCODE_URL'])

check('with NO key, both URLs are empty - so the page can branch',
      WITHOUT['MAP_TILE_URL'] == '' and WITHOUT['MAP_GEOCODE_URL'] == '',
      repr(WITHOUT['MAP_TILE_URL']))
check('  and the flag says so out loud',
      WITHOUT['MAP_KEY_PRESENT'] is False and WITH['MAP_KEY_PRESENT'] is True)
check('  and whitespace is not a key',
      ctx('   ')['MAP_TILE_URL'] == '')

# ---------------------------------------------------------------------- 2
head('2. RENDERED, IN BOTH STATES - NOT READ WITH A REGEX')

# escapejs rewrites <, >, &, =, - and ; into \\u escapes, and the tile URL
# holds four of them. Reading the template source would never see whether
# what reaches the browser is still a URL.
BLOCK = re.compile(
    r'(//\s*MAP TILES\..*?insertAdjacentHTML.*?\n\s*\}\s*\n)', re.S)


def block_of(rel):
    m = BLOCK.search(read(os.path.join(T, rel)))
    return m.group(1) if m else None


rendered = {}
for rel in PAGES:
    blk = block_of(rel)
    if not check('%-22s has a map block to render' % rel, blk is not None):
        continue
    out = {}
    for state, c in (('key', WITH), ('nokey', WITHOUT)):
        try:
            out[state] = Template(blk).render(Context(c))
        except Exception as e:
            check('  %s renders (%s)' % (rel, state), False, str(e))
            out[state] = ''
    rendered[rel] = out

for rel, out in sorted(rendered.items()):
    got, blank = out.get('key', ''), out.get('nokey', '')

    # What the browser will actually assign, after escapejs.
    m = re.search(r"var mapTileUrl = '([^']*)';", got)
    js = m.group(1) if m else ''
    # \\uXXXX back to the character, which is what a JS engine does.
    plain = re.sub(r'\\u([0-9A-Fa-f]{4})',
                   lambda mm: chr(int(mm.group(1), 16)), js)
    check('%-22s assigns a usable URL' % rel,
          plain == WITH['MAP_TILE_URL'], plain[:46])
    check('  and the escaping left no raw quote to end the string early',
          "'" not in js and '\\n' not in js)

    a = re.search(r"attribution: '([^']*)'", got)
    attr = re.sub(r'\\u([0-9A-Fa-f]{4})',
                  lambda mm: chr(int(mm.group(1), 16)), a.group(1) if a else '')
    check('  the credit survives as a LINK, which is what was missing',
          '<a href=' in attr and 'openstreetmap.org/copyright' in attr)
    check('  and names the provider, as its free terms require',
          'Geoapify' in attr)

    check('  maxZoom renders as a number, not as a variable name',
          re.search(r'maxZoom: (\d+)', got) is not None,
          re.search(r'maxZoom: (\S+)', got).group(1) if
          re.search(r'maxZoom: (\S+)', got) else '')

    # THE OTHER STATE. This is the half nobody sees until the day it matters.
    m2 = re.search(r"var mapTileUrl = '([^']*)';", blank)
    check('  with no key the URL is the empty string, so the else runs',
          m2 is not None and m2.group(1) == '', repr(m2.group(1) if m2 else '?'))
    check('  and the notice names the variable somebody has to set',
          'GEOAPIFY_KEY' in blank and 'alv-map-nokey' in blank)
    # .find, not .index. The first draft used .index and CRASHED rather than
    # failing when the sabotage control moved the tile layer out of the branch
    # - and a crash blocks a push exactly as hard as a failure while saying
    # far less about why. That lesson cost a push this morning; it is not
    # allowed to cost a second one from inside the suite written to record it.
    _if, _tl = blank.find('if (mapTileUrl)'), blank.find('L.tileLayer(')
    check('  and the tile layer is inside the branch, not beside it',
          blank.count('L.tileLayer(') == 1 and _if >= 0 and _tl > _if,
          'if at %d, tileLayer at %d' % (_if, _tl))

# ---------------------------------------------------------------------- 3
head('3. THE FOUR PAGES ASK THE SAME WAY')

shapes = {}
for rel in PAGES:
    blk = block_of(rel)
    if blk is None:
        continue
    # Strip the indent each page happens to sit at, and the element id each
    # page happens to have given Leaflet. What is left must be identical.
    flat = '\n'.join(ln.strip() for ln in blk.split('\n') if ln.strip())
    flat = re.sub(r"getElementById\('[^']*'\)", "getElementById('X')", flat)
    shapes.setdefault(flat, []).append(rel)

check('every page configures the map identically', len(shapes) == 1,
      '%d shape(s): %s' % (len(shapes), ' | '.join(
          ','.join(v) for v in shapes.values())))
check('  and it really is all four of them',
      sum(len(v) for v in shapes.values()) == len(PAGES),
      '%d page(s)' % sum(len(v) for v in shapes.values()))

for rel in GEOCODERS:
    txt = read(os.path.join(T, rel))
    check('%-22s builds its lookup from the context' % rel,
          "'{{ MAP_GEOCODE_URL|escapejs }}' + encodeURIComponent(address)"
          in txt)
    check('  and reads lat and lon off the results array',
          'data.results' in txt and 'hits[0].lat' in txt
          and 'hits[0].lon' in txt)
    check('  and no longer indexes the answer as a bare array',
          'data[0].lat' not in txt)

# ---------------------------------------------------------------------- 4
head('4. NOTHING IN THE CORPUS STILL ASKS THE VOLUNTEERS')

ALL = templates()
_dirs = set(os.path.dirname(p) for p in ALL)
# Two claims, not one. The first is that the walk RECURSED - six of this
# project's template directories are subdirectories, and a sweep that reads
# one level and reports zero is how I told the user the gate was complete
# while their machine said nineteen suites were missing. The second is a
# FLOOR, not a pinned count: a pinned corpus size is a scope guard waiting
# for the next page somebody adds.
check('the sweep reached more than the top level', len(_dirs) >= 2,
      '%d director(ies)' % len(_dirs))
check('  and found a corpus, not a handful', len(ALL) >= 60,
      '%d template(s)' % len(ALL))

tiles = [os.path.relpath(p, T) for p in ALL if OSM_TILES in read(p)]
geo = [os.path.relpath(p, T) for p in ALL if OSM_GEOCODE in read(p)]
check('no template asks OpenStreetMap for a tile', not tiles,
      '%d: %s' % (len(tiles), ', '.join(tiles[:4])))
check('no template calls the OpenStreetMap geocoder', not geo,
      '%d: %s' % (len(geo), ', '.join(geo[:4])))
check('  CONTROL: the sweep can see one when there is one',
      OSM_TILES in ('https://a.' + OSM_TILES + '/1/2/3.png'))

# A backup is a record of what a page used to be, so the sweep must not
# read one and call it a live page. This is the check that would have
# failed had the walk above collected .bak_ files.
check('  and it swept live templates only, not their backups',
      not [p for p in ALL if '.bak_' in os.path.basename(p)])

# ---------------------------------------------------------------------- 5
head('5. base OWNS THE NOTICE')

B = read(BASE)
_at = B.find('.alv-map-nokey {')
check('base defines the no-key notice', _at >= 0)
check('  exactly once', B.count('.alv-map-nokey {') == 1,
      str(B.count('.alv-map-nokey {')))
# Slice defensively. Everything below reads this rule, and a missing rule is
# a thing to REPORT, not a thing to die of - see the note in section 2.
rule = ''
if _at >= 0:
    rule = B[_at:]
    _end = rule.find('}')
    rule = rule[:_end + 1] if _end >= 0 else rule[:400]
for prop, why in (('position: absolute', 'sits over the map, not beside it'),
                  ('inset: 0', 'covers the whole box'),
                  ('z-index', 'draws above Leaflet\'s own panes')):
    check('  and it %s' % why, prop in rule, prop)
check('  and it takes its colours from base tokens, not from literals',
      rule.count('var(--alv-') >= 3 and not re.search(r':\s*#[0-9a-fA-F]{3,6}',
                                                      rule),
      '%d token(s)' % rule.count('var(--alv-'))
check('  and no page defines its own',
      not [os.path.relpath(p, T) for p in ALL
           if p != BASE and '.alv-map-nokey {' in read(p)])

# ---------------------------------------------------------------------- 6
head('6. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 7
print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
print('')
print('  NOT PROVED HERE: that tiles arrive. That needs a live request to a')
print('  third party, and a green answer would be a fact about one machine')
print('  on one afternoon. What is proved is that ONE definition reaches all')
print('  four pages intact, and that a missing key produces a sentence')
print('  rather than a grey square. Load Properties > Add to see which.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
