"""apply_map_tiles.py - the Properties map stops asking for an API key.

    python apply_map_tiles.py --check     dry run, writes nothing
    python apply_map_tiles.py

Run from the repo root.

THE BUG, AND WHY IT LOOKS LIKE A STYLING PROBLEM AND IS NOT.

map_view.html draws its basemap from CARTO's Voyager raster tiles:

    https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png

CARTO now gates that behind an API key. It does not fail: it returns tiles
with "API KEY REQUIRED" and "carto.com/basemaps/apikey" PRINTED INTO THE
IMAGE. So the map loads, Leaflet is happy, the pins land in the right places,
the console is clean - and every tile carries a watermark. Nothing throws,
which is why it can sit there looking like a rendering glitch.

THE FIX IS ALREADY IN THIS REPO, THREE TIMES OVER. properties_add.html,
properties_edit.html and map_test.html all draw the same kind of map from
OpenStreetMap's own tiles, which need no key:

    https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

Those three were confirmed drawing cleanly before this round was written, so
the tiles are known to work from this deployment. map_view.html is the odd
one out, and its own comment already says `// Add OpenStreetMap tiles` - the
comment was right and the code had drifted away from it.

THREE THINGS CHANGE TOGETHER, AND THE SECOND IS THE TRAP.

  1. the URL          cartocdn voyager -> tile.openstreetmap.org

  2. subdomains       'abcd' -> REMOVED. CARTO serves a, b, c and d;
                      OpenStreetMap serves a, b and c. Leaflet's default is
                      'abc', which is why the three working pages set no
                      subdomains option at all. Swap the URL and leave
                      `subdomains: 'abcd'` behind and a QUARTER of every
                      screen's tile requests go to d.tile.openstreetmap.org,
                      which does not exist. The map would come up mostly
                      right, with a scatter of blank squares that moves as
                      you pan - a partial fix that reads as a whole one.

  3. {r} retina       gone with the URL. It is a CARTO convention; the OSM
                      standard layer serves no @2x tiles, and a request for
                      one is a 404.

  maxZoom stays at the 18 the three working pages use. OSM's standard layer
  serves 19, but matching the pages that are known to work here is worth more
  than one extra zoom level, and a round that changes two things at once
  cannot say which one fixed it.

WHAT THIS ROUND CANNOT PROVE, SAID PLAINLY. Every other round this week
carried a rendered check. This one does not, and cannot: the build sandbox
blocks outbound HTTPS, so Leaflet never loads and no tile is ever requested -
`typeof L` is `undefined` and the requests fail with ERR_TUNNEL_CONNECTION_
FAILED. Claiming a rendered proof here would be a claim about a machine that
cannot make the request.

So the suite asserts the strongest thing that IS checkable: that
map_view.html now configures its tile layer EXACTLY as the three pages you
have confirmed are working. Not "OSM tiles work" - "this page now asks for
tiles the same way the pages that work ask for them". The remaining
verification is loading the page, and that is the user's, not the suite's.

ONE THING NOT CHANGED. OpenStreetMap's public tile server is a courtesy
service with a usage policy, not a CDN with a contract. At this scale that is
fine, and it is what the rest of the system already relies on. If the map
ever needs a guaranteed provider, that is an account and a key and a
different conversation - noted here so the choice is visible rather than
inherited.

HOUSE RULES: idempotent, .bak_maptiles backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
MV = os.path.join(T, 'map_view.html')
PEERS = [os.path.join(T, n) for n in ('properties_add.html',
                                      'properties_edit.html',
                                      'map_test.html')]
if not os.path.exists(MV):
    sys.exit('! %s not found - run from the repo root' % MV)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:120]))
    return t.replace(old, new, 1)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


OSM = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

F_ORIG, F_CRLF, f = load(MV)
DONE = 'basemaps.cartocdn.com' not in f
if DONE:
    print('  map_view.html already patched')
else:
    f = sub1(f, """    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);""",
             """    // OpenStreetMap tiles - keyless, and the same ones properties_add,
    // properties_edit and map_test already use.
    //
    // THIS USED TO ASK CARTO FOR VOYAGER TILES, and CARTO now gates those
    // behind an API key. It does not fail: it returns tiles with "API KEY
    // REQUIRED" printed into the image, so the map drew, the pins landed
    // correctly, the console stayed clean, and every tile carried a
    // watermark. The comment above this call already said OpenStreetMap -
    // the comment was right and the code had drifted.
    //
    // NO `subdomains` OPTION, DELIBERATELY. CARTO serves a-d; OSM serves
    // a-c, and Leaflet's default is 'abc'. Carrying `subdomains: 'abcd'`
    // across would send a quarter of every screen's requests to
    // d.tile.openstreetmap.org, which does not exist - a map that comes up
    // mostly right with a scatter of blank squares that moves as you pan.
    // The three working pages set no subdomains option, and neither does
    // this one now.
    //
    // maxZoom matches those three at 18 rather than the 19 OSM will serve,
    // because a round that changes two things cannot say which one fixed it.
    L.tileLayer('%s', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);""" % OSM, 'MAP: the tile layer')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
# WHOLE-LINE COMMENTS ONLY. The first draft stripped `//` to end of line
# anywhere, and every URL in the file contains `//` - so the stripper ate
# `https://{s}.tile.openstreetmap.org/...` and then reported it missing. A
# comment-stripper that does not know what a scheme is will quietly delete
# the thing the round is about.
_nc = re.sub(r'(?m)^[ \t]*//[^\n]*$', '', f)
_nc = re.sub(r'/\*.*?\*/', '', _nc, flags=re.S)
# CONTROL for the stripper itself: the prose above the call must be gone and
# the call must survive.
want('the comment was right and the code had drifted' not in _nc,
     'MAP: the comment stripper did not strip')
want('L.tileLayer(' in _nc, 'MAP: the comment stripper ate the code')

want('cartocdn' not in _nc, 'MAP: a CARTO tile URL survives outside a comment')
want(OSM in _nc, 'MAP: the OSM tile URL is not there')
want('subdomains' not in _nc,
     'MAP: a subdomains option survives - abcd would 404 a quarter of tiles')
want('{r}' not in _nc, 'MAP: the CARTO retina suffix survives')
want(_nc.count('L.tileLayer(') == 1,
     'MAP: expected exactly one tile layer, got %d'
     % _nc.count('L.tileLayer('))
want('maxZoom: 18' in _nc, 'MAP: maxZoom does not match the working pages')

# THE CLAIM WORTH MAKING, since this round cannot render: the page now asks
# for tiles the same way the pages that are known to work ask for them.
for _p in PEERS:
    if not os.path.exists(_p):
        continue
    _peer = load(_p)[2]
    _pm = re.search(r"L\.tileLayer\('([^']+)'", _peer)
    want(_pm is not None and _pm.group(1) == OSM,
         'MAP: %s does not use the OSM URL this round copied - the premise '
         'of the round is wrong' % os.path.basename(_p))
    want('subdomains' not in _peer,
         'MAP: %s sets a subdomains option after all - check the default'
         % os.path.basename(_p))

# The map's own machinery must be untouched: this is a one-call round.
for hook in ('propertyCount', 'properties_json', 'L.map(', 'addTo(map)',
             'markers', 'fitBounds'):
    want(hook in f, 'MAP: the page lost %s' % hook)
want(f.count('L.marker') == F_ORIG.replace('\r\n', '\n').count('L.marker')
     or DONE, 'MAP: the marker code changed - this round is one call')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-22s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_maptiles'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(MV, F_ORIG, F_CRLF, f, DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
