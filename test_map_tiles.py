"""test_map_tiles.py - the Properties map asks for tiles the way the working
   pages ask for them.

    python test_map_tiles.py

Run from the repo root, after apply_map_tiles.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST
-------------------------------------
It cannot prove the tiles arrive. Every other round this week carried a
rendered check; this one has none, because the only honest render would be a
live HTTPS request to a third-party tile server, and:

  * in the build sandbox that request is blocked outright - Leaflet does not
    even load, `typeof L` is `undefined`, and the fetch fails with
    ERR_TUNNEL_CONNECTION_FAILED;
  * and on any machine where it DID succeed, a green result would be a fact
    about that machine's network on that afternoon, not about the change.

A suite that shells out to the internet and calls the answer a proof is
worse than one that says what it is measuring. So this one measures
SAMENESS, which is checkable, deterministic, and the actual argument:

    map_view.html now configures its tile layer EXACTLY as
    properties_add.html, properties_edit.html and map_test.html do -
    and those three are confirmed drawing cleanly.

Not "OSM tiles work". "This page now asks the way the pages that work ask."
The remaining verification is a person loading the page.

THE TRAP THIS PINS. Swapping the URL and leaving `subdomains: 'abcd'` behind
would send a quarter of every screen's requests to d.tile.openstreetmap.org,
which does not exist - a map that comes up mostly right with a scatter of
blank squares that moves as you pan. That is the "reads as fixed" shape this
project keeps meeting, so the absence of that option is asserted directly,
and against the peers rather than against a remembered default.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
MV = os.path.join(T, 'map_view.html')
BAK = MV + '.bak_maptiles'
PEERS = ('properties_add.html', 'properties_edit.html', 'map_test.html')

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


def code_of(src):
    """Source with WHOLE-LINE // comments and /* */ blocks removed.

       Whole-line only, deliberately: `https://` contains `//`, so a stripper
       that cuts from any `//` to end of line eats every URL in the file. The
       patcher's first draft did exactly that and then reported the URL it
       had just deleted as missing."""
    src = re.sub(r'(?m)^[ \t]*//[^\n]*$', '', src)
    return re.sub(r'/\*.*?\*/', '', src, flags=re.S)


def layer_of(src):
    """The tile layer as a comparable shape: url plus its options."""
    m = re.search(r"L\.tileLayer\(\s*'([^']+)'\s*,\s*\{(.*?)\}\s*\)",
                  code_of(src), re.S)
    if not m:
        m2 = re.search(r"L\.tileLayer\(\s*'([^']+)'", code_of(src))
        return (m2.group(1), {}) if m2 else (None, None)
    opts = {}
    for k, v in re.findall(r'(\w+)\s*:\s*([^,\n]+)', m.group(2)):
        opts[k] = v.strip().rstrip(',').strip()
    return m.group(1), opts


if not os.path.exists(MV):
    sys.exit('! %s not found - run from the repo root' % MV)
if not os.path.exists(BAK):
    sys.exit('! no map_view.html.bak_maptiles - run apply_map_tiles.py first.')

F, WAS = read(MV), read(BAK)
FC, WC = code_of(F), code_of(WAS)
OSM = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

# ===========================================================================
head('1. the CARTO tiles are gone, and so is everything that came with them')
# ===========================================================================
check('CONTROL: the comment stripper strips',
      'the comment was right and the code had drifted' not in FC)
check('CONTROL: .. and does not eat the URL it is meant to leave',
      'https://' in FC and 'L.tileLayer(' in FC)

check('no cartocdn URL survives outside a comment', 'cartocdn' not in FC)
check('  CONTROL: there WAS one', 'cartocdn' in WC)
check('the OSM tile URL is there', OSM in FC)
check('  CONTROL: it was not before', OSM not in WC)

# THE TRAP. abcd would 404 a quarter of every screen.
check('no subdomains option survives - abcd would 404 a quarter of the tiles',
      'subdomains' not in FC)
check('  CONTROL: it WAS abcd', re.search(r"subdomains\s*:\s*'abcd'", WC)
      is not None)
check('the CARTO retina suffix is gone - OSM serves no @2x', '{r}' not in FC)
check('  CONTROL: it was in the old URL', '{r}' in WC)

_url, _opts = layer_of(F)
check('exactly one tile layer on the page', FC.count('L.tileLayer(') == 1,
      str(FC.count('L.tileLayer(')))
check('  and its url is the OSM one', _url == OSM, str(_url))
check('  and its only options are attribution and maxZoom',
      set(_opts) == {'attribution', 'maxZoom'}, str(sorted(_opts)))
check('  with maxZoom 18', _opts.get('maxZoom') == '18',
      str(_opts.get('maxZoom')))
check('the attribution still credits OpenStreetMap',
      'openstreetmap.org/copyright' in _opts.get('attribution', ''))
check('  and no longer credits CARTO, which no longer serves it',
      'carto' not in _opts.get('attribution', '').lower())

# ===========================================================================
head('2. the same as the three pages that are known to work')
# ===========================================================================
# THIS IS THE ROUND'S ACTUAL CLAIM. Not "the tiles arrive" - that is a fact
# about a network - but "this page now asks the way the working pages ask".
_seen = 0
for name in PEERS:
    p = os.path.join(T, name)
    if not os.path.exists(p):
        print('  SKIP  %s not present' % name)
        continue
    _seen += 1
    purl, popts = layer_of(read(p))
    check('%-24s uses the same tile URL' % name, purl == OSM, str(purl))
    check('  and sets no subdomains either - Leaflet defaults to abc',
          'subdomains' not in popts)
    check('  and map_view now matches its maxZoom' if name != 'map_test.html'
          else '  (map_test sets none, which is Leaflet\'s own default)',
          popts.get('maxZoom', '18') == _opts.get('maxZoom'),
          '%s vs %s' % (popts.get('maxZoom'), _opts.get('maxZoom')))
check('CONTROL: at least one peer was actually read - otherwise the section '
      'above is vacuous', _seen >= 2, '%d of %d' % (_seen, len(PEERS)))

# ===========================================================================
head('3. what the round did NOT touch')
# ===========================================================================
# One call changed. Everything the map DOES is somebody else's round.
for hook in ('propertyCount', 'properties_json', 'L.map(', 'addTo(map)',
             'fitBounds', 'markers'):
    check('the page keeps %s' % hook, hook in F)
check('the marker code is untouched',
      F.count('L.marker') == WAS.count('L.marker'),
      '%d vs %d' % (F.count('L.marker'), WAS.count('L.marker')))
check('the map still centres where it did',
      re.search(r'setView\(\[([-\d.]+),\s*([-\d.]+)\],\s*(\d+)\)', F).groups()
      == re.search(r'setView\(\[([-\d.]+),\s*([-\d.]+)\],\s*(\d+)\)',
                   WAS).groups())
check('Leaflet is still loaded from the same place',
      re.findall(r'leaflet[^"\']*\.(?:min\.)?(?:js|css)', F)
      == re.findall(r'leaflet[^"\']*\.(?:min\.)?(?:js|css)', WAS))

# The delta: this round is ONE call plus its note.
_a = re.sub(r'(?m)^[ \t]*//[^\n]*$\n?', '', F)
_b = re.sub(r'(?m)^[ \t]*//[^\n]*$\n?', '', WAS)
import difflib                                                   # noqa: E402
_changed = [l for l in difflib.unified_diff(_b.split('\n'), _a.split('\n'),
                                            lineterm='', n=0)
            if l[:1] in '+-' and l[:3] not in ('+++', '---')]
check('once the note is set aside, only the tile call changed (%d line(s))'
      % len(_changed), len(_changed) <= 8,
      ' | '.join(x.strip()[:34] for x in _changed[:6]))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that the tiles arrive. That is a live request to')
print('  a third-party server, and a green tick for it would be a fact about')
print('  one machine\'s network. Load /properties/map/ - the watermarks')
print('  should be gone and the pins in the same places.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
