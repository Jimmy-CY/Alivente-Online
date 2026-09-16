"""apply_map_provider.py - the map stops asking OpenStreetMap's volunteers
   for tiles, and asks a provider whose terms cover a business doing it.

    python apply_map_provider.py --check      # report, write nothing
    python apply_map_provider.py              # apply

Run from the repo root.

WHAT WENT WRONG

  Properties > Add drew Cyprus with a yellow-and-black square over it:

      403  Access blocked
      App is not following the tile usage policy of OpenStreetMap's
      volunteer-run servers: osm.wiki/Blocked

  Nothing had changed in the app. tile.openstreetmap.org is a volunteer
  service under a usage policy aimed at OSM's own site and small, casual
  use; blocks are applied by referring domain, which is why every page
  went at once. The wiki lists the triggers, and two of them fit:

    * ATTRIBUTION WITHOUT A LINK. properties_add and properties_edit both
      credited OpenStreetMap as plain text. map_view was the only one of
      the four that linked to the copyright page.

    * NOMINATIM FROM A BROWSER. "Find Address on Map" called
      nominatim.openstreetmap.org directly. That service asks for an
      identifying User-Agent, which a browser will not let a page set, so
      the call cannot comply however politely it is made.

  There is a third, quieter reason to move: a property-management system
  is a for-profit product, and the tile policy is not written for one.

WHAT THIS ROUND DOES

  Points the four pages that draw a map at Geoapify - free plan, 3,000
  credits a day, a tile costs a quarter of a credit, and the terms permit
  commercial use provided the attribution names them. osm-carto is their
  rendering of the classic OpenStreetMap style, so the map looks the same
  as it did before it stopped drawing.

  The same key serves the address lookup, so Nominatim goes in the same
  change rather than waiting to be noticed separately.

ONE DEFINITION, FOUR CONSUMERS

  The URL, the attribution and the zoom ceiling live in ONE place -
  mysite/context_processors.py - and reach every template through the
  context. Before this round four templates each spelled the tile URL
  out, and map_view's own comment records what that cost: it had drifted
  to CARTO, CARTO started gating those tiles behind a key, and CARTO does
  not fail when you have no key - it returns tiles with API KEY REQUIRED
  printed INTO the image. The map drew, the pins landed, the console
  stayed clean, and every tile carried a watermark.

  That is the argument for one definition, and it is also the reason the
  keyless stopgap was refused when this round was agreed.

THE KEY IS NOT A SECRET, AND IS NOT IN THE REPO

  A browser map key travels to the browser; there is no arrangement in
  which it does not. It is protected by being restricted to one origin in
  the provider's dashboard, not by being hidden. So it comes from the
  environment - GEOAPIFY_KEY, set in Railway - and nothing in git ever
  holds it.

  WITH NO KEY THE PAGE SAYS SO. The tile layer is not added at all and a
  notice covers the map box. A map with no basemap is an empty grey
  square, and an empty grey square reads as a bug in the page rather than
  as a setting nobody has filled in. That distinction is the whole reason
  the CARTO drift went unnoticed for months.

WHAT IT DOES NOT DO

  maxZoom stays at 18, though Geoapify serves 20 and 20 would be better
  for dropping a pin on a specific building. A round that changes two
  things cannot say which one fixed it - map_view's own comment already
  says that, about this same number.

  map_test.html is a debug page and is migrated rather than deleted, so
  that "all four configure the map identically" stays a checkable claim.
  Deleting it is its own decision.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
SUFFIX = '.bak_mapprov'

PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUITE = 'test_map_provider.py'
SUITE_ANCHOR = "    'test_console_encoding.py'\n)\n"
SUITE_ADD = """    'test_console_encoding.py',
    # The map asks a provider whose terms cover a business doing it, from one
    # definition, and says so when it has no key. Its section 2 RENDERS each
    # page's map block through Django in BOTH key states, because escapejs
    # rewrites four of the characters in the tile URL and nothing that reads
    # the template source can see what reached the browser. Newest, so most
    # likely to be what breaks.
    'test_map_provider.py'
)
"""

SETTINGS = os.path.join(ROOT, 'mysite', 'settings.py')
CTXPROC = os.path.join(ROOT, 'mysite', 'context_processors.py')
BASE = os.path.join(T, 'base.html')

# rel path -> (indent, the id of the element Leaflet was given)
PAGES = {
    'properties_add.html': ('    ', 'propertyMap'),
    'properties_edit.html': ('    ', 'propertyMap'),
    'map_view.html': ('    ', 'map'),
    'map_test.html': ('        ', 'map'),
}

# --------------------------------------------------------------- settings.py
S_ANCHOR = ("# Anthropic API Key (from environment variable)\n"
            "ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')\n")

S_ADD = """
# The map tile and geocoding key, for Geoapify. Set in Railway; never in the
# repo. It is not a secret and cannot be one - a browser map key travels to
# the browser by definition - so it is protected by being restricted to one
# origin in the provider's dashboard. Empty is a supported state: the map
# says it has no key rather than drawing an empty grey square. See
# apply_map_provider.py.
GEOAPIFY_KEY = os.getenv('GEOAPIFY_KEY', '')
"""

S_REGISTERED = '"mysite.context_processors.map_provider"'
S_CTX_ANCHOR = '                "mysite.context_processors.user_preferences", \n'
S_CTX_ADD = ('                "mysite.context_processors.user_preferences", \n'
             '                "mysite.context_processors.map_provider",\n')

# ------------------------------------------------------- context_processors.py
CTX_ADD = '''

# ---------------------------------------------------------------------------
# THE MAP PROVIDER. One definition; four templates consume it.
#
# Before this, each of the four pages that draw a map spelled the tile URL out
# itself, and map_view's comment records what that cost: it had drifted to
# CARTO, CARTO began gating those tiles behind a key, and CARTO does not fail
# without one - it returns tiles with API KEY REQUIRED printed into the image.
# The map drew, the pins landed, the console stayed clean, and nobody saw it.
# ---------------------------------------------------------------------------

# osm-carto is Geoapify's rendering of the classic OpenStreetMap style, so the
# map looks the way it looked before OpenStreetMap stopped serving it.
MAP_STYLE = 'osm-carto'

# 18 and not the 20 Geoapify will serve. 20 would be better for dropping a pin
# on one building, and that is a separate change: a round that moves two things
# cannot say which one fixed it.
MAP_MAX_ZOOM = 18

# The attribution is a LINK, not a line of text. Two of these four pages
# credited OpenStreetMap in plain prose, and an unlinked credit is one of the
# reasons the OSM wiki gives for blocking an application.
MAP_ATTRIBUTION = (
    'Powered by <a href="https://www.geoapify.com/">Geoapify</a> '
    '| &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap'
    '</a> contributors'
)

# format=json, not the default geojson, because it returns lat and lon on each
# result exactly as Nominatim did - so the pages that read the answer change by
# one word rather than by a shape.
_TILES = 'https://maps.geoapify.com/v1/tile/%s/{z}/{x}/{y}.png?apiKey=%s'
_GEOCODE = 'https://api.geoapify.com/v1/geocode/search?format=json&limit=1&apiKey=%s&text='


def map_provider(request):
    """Where the map gets its tiles, its words and its address lookup.

    Every value is EMPTY when no key is configured, and the templates treat
    empty as "say so". A missing key is a setting nobody has filled in; it
    should not look like a broken page.
    """
    from django.conf import settings as _settings
    key = (getattr(_settings, 'GEOAPIFY_KEY', '') or '').strip()
    return {
        'MAP_KEY_PRESENT': bool(key),
        'MAP_TILE_URL': (_TILES % (MAP_STYLE, key)) if key else '',
        'MAP_GEOCODE_URL': (_GEOCODE % key) if key else '',
        'MAP_ATTRIBUTION': MAP_ATTRIBUTION,
        'MAP_MAX_ZOOM': MAP_MAX_ZOOM,
    }
'''

# ------------------------------------------------------------------- base.html
B_ANCHOR = '.icon-color-manage { color: var(--alv-view); }\n</style>\n'
B_ADD = """.icon-color-manage { color: var(--alv-view); }

/* ===== ALV-MAP-NOKEY v1 ===== */
/* The map draws from a keyed provider, and the key arrives from the
   environment. When it is absent the tile layer is not added at all and this
   notice covers the map box instead, because a map with no basemap is an
   empty grey square, and an empty grey square reads as a fault in the page
   rather than as a setting nobody has filled in. That distinction is not
   theoretical: the same four pages spent months drawing CARTO tiles with
   API KEY REQUIRED printed into every image, and it drew, so nobody looked.
   Absolute inside Leaflet's own container, above its tile panes. */
.alv-map-nokey {
    position: absolute;
    inset: 0;
    z-index: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 1rem;
    background: var(--alv-paper);
    color: var(--alv-ink-soft);
    border: 1px solid var(--alv-line);
    border-radius: 6px;
    font-size: .9rem;
}
</style>
"""

# ------------------------------------------------------------- the tile blocks
ADD_TILE_ANCHOR = """    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
"""

TEST_TILE_ANCHOR = """        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
"""

VIEW_TILE_START = '    // OpenStreetMap tiles - keyless, and the same ones properties_add,'
VIEW_TILE_END = '    }).addTo(map);\n'

TILE_BLOCK = """{i}// MAP TILES. The URL, the words under them and the zoom ceiling are
{i}// defined ONCE, in mysite/context_processors.py, and arrive here through
{i}// the context. They used to be spelled out on each of the four pages that
{i}// draw a map, and map_view's old comment records what that cost.
{i}//
{i}// AN EMPTY URL MEANS NO KEY IS CONFIGURED, and the page says so. It does
{i}// not add a tile layer and hope: a map with no basemap is an empty grey
{i}// square, which reads as a fault in the page rather than as a setting
{i}// nobody has filled in. See apply_map_provider.py.
{i}var mapTileUrl = '{{{{ MAP_TILE_URL|escapejs }}}}';
{i}if (mapTileUrl) {{
{i}    L.tileLayer(mapTileUrl, {{
{i}        attribution: '{{{{ MAP_ATTRIBUTION|escapejs }}}}',
{i}        maxZoom: {{{{ MAP_MAX_ZOOM }}}}
{i}    }}).addTo(map);
{i}}} else {{
{i}    document.getElementById('{el}').insertAdjacentHTML('afterbegin',
{i}        '<div class="alv-map-nokey">Map unavailable &mdash; no map key is ' +
{i}        'configured. Set GEOAPIFY_KEY and redeploy.</div>');
{i}}}
"""

# ---------------------------------------------------------------- the geocoder
GEO_URL_ANCHOR = ("        var geocodeUrl = `https://nominatim.openstreetmap.org"
                  "/search?format=json&q=${encodeURIComponent(address)}"
                  "&limit=1`;\n")
GEO_URL_ADD = """        // The address lookup, from the same provider and the same key. It
        // used to call OpenStreetMap's Nominatim service straight from the
        // page, and that service asks for an identifying User-Agent, which
        // a browser will not let a page set - so the call could not comply
        // however politely it was made. The host is deliberately not spelled
        // out here: a scanner looking for it would find this sentence.
        // See apply_map_provider.py.
        var geocodeUrl = '{{ MAP_GEOCODE_URL|escapejs }}' + encodeURIComponent(address);
"""

GEO_READ_ANCHOR = """                if (data && data.length > 0) {
                    var lat = parseFloat(data[0].lat);
                    var lng = parseFloat(data[0].lon);
"""
GEO_READ_ADD = """                // format=json was asked for, so a hit carries lat and lon
                // exactly as Nominatim's did - one word of difference.
                var hits = (data && data.results) || [];
                if (hits.length > 0) {
                    var lat = parseFloat(hits[0].lat);
                    var lng = parseFloat(hits[0].lon);
"""

# What must no longer appear anywhere once this has run.
GONE = ('tile.openstreetmap.org', 'nominatim.openstreetmap.org')


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def once(text, anchor, what, problems):
    n = text.count(anchor)
    if n != 1:
        problems.append('%s matches %d times, not once' % (what, n))
    return n == 1


def plan_settings(problems):
    text, nl, raw = read(SETTINGS)
    if 'GEOAPIFY_KEY' in text and S_REGISTERED in text:
        return None, text, nl, raw, ['already done']
    new, did = text, []
    if 'GEOAPIFY_KEY' not in new:
        if once(new, S_ANCHOR, 'settings: the key anchor', problems):
            new = new.replace(S_ANCHOR, S_ANCHOR + S_ADD)
            did.append('GEOAPIFY_KEY read from the environment')
    # NOT `if 'map_provider' not in new`. The comment this round writes into
    # settings ends with "See apply_map_provider.py", which contains the word
    # map_provider - so the first draft of this guard skipped the very edit it
    # was guarding, silently, and the suite caught it. Prose shaped like code,
    # for the twenty-somethingth time. Ask for the REGISTRATION.
    if S_REGISTERED not in new:
        if once(new, S_CTX_ANCHOR, 'settings: the processor anchor', problems):
            new = new.replace(S_CTX_ANCHOR, S_CTX_ADD)
            did.append('map_provider registered as a context processor')
    return new, text, nl, raw, did


def plan_ctxproc(problems):
    text, nl, raw = read(CTXPROC)
    if 'def map_provider' in text:
        return None, text, nl, raw, ['already done']
    return text.rstrip('\n') + '\n' + CTX_ADD, text, nl, raw, ['map_provider added']


def plan_gate(problems):
    if not os.path.exists(PS1):
        problems.append('Push-PendingChanges.ps1 is not here')
        return None, '', '\n', b'', []
    text, nl, raw = read(PS1)
    if "'" + SUITE + "'" in text:
        return None, text, nl, raw, ['already runs ' + SUITE]
    if not once(text, SUITE_ANCHOR, 'the gate: the suite-list anchor',
                problems):
        return None, text, nl, raw, []
    new = text.replace(SUITE_ANCHOR, SUITE_ADD)
    # It must land INSIDE the array, which a closing bracket on the next line
    # is what proves. A suite listed after the bracket is a syntax error the
    # gate would not survive.
    after = new[new.index("'" + SUITE + "'"):]
    if after.split('\n')[1].strip() != ')':
        problems.append('the gate: the suite would not land inside the array')
        return None, text, nl, raw, []
    return new, text, nl, raw, [SUITE + ' on the gate']


def plan_base(problems):
    text, nl, raw = read(BASE)
    if 'alv-map-nokey' in text:
        return None, text, nl, raw, ['already done']
    if not once(text, B_ANCHOR, 'base: the stylesheet anchor', problems):
        return None, text, nl, raw, []
    return text.replace(B_ANCHOR, B_ADD), text, nl, raw, ['.alv-map-nokey defined']


def plan_page(rel, problems):
    path = os.path.join(T, rel)
    text, nl, raw = read(path)
    if 'MAP_TILE_URL' in text:
        return None, text, nl, raw, ['already done']
    indent, el = PAGES[rel]
    block = TILE_BLOCK.format(i=indent, el=el)
    new, did = text, []

    if rel == 'map_test.html':
        anchor = TEST_TILE_ANCHOR
    elif rel == 'map_view.html':
        i = new.find(VIEW_TILE_START)
        if i < 0:
            problems.append('%s: the tile comment is not where it was' % rel)
            return None, text, nl, raw, []
        j = new.find(VIEW_TILE_END, i)
        if j < 0:
            problems.append('%s: the tile call does not close' % rel)
            return None, text, nl, raw, []
        anchor = new[i:j + len(VIEW_TILE_END)]
    else:
        anchor = ADD_TILE_ANCHOR

    if not once(new, anchor, '%s: the tile block' % rel, problems):
        return None, text, nl, raw, []
    new = new.replace(anchor, block)
    did.append('tiles from the context')

    if rel in ('properties_add.html', 'properties_edit.html'):
        if not once(new, GEO_URL_ANCHOR, '%s: the geocode URL' % rel, problems):
            return None, text, nl, raw, []
        new = new.replace(GEO_URL_ANCHOR, GEO_URL_ADD)
        if not once(new, GEO_READ_ANCHOR, '%s: the geocode reader' % rel,
                    problems):
            return None, text, nl, raw, []
        new = new.replace(GEO_READ_ANCHOR, GEO_READ_ADD)
        did.append('address lookup from the context')

    return new, text, nl, raw, did


def self_check(rel, old, new, problems):
    """Everything here is about THIS file."""
    bad = []
    for token in GONE:
        if token in new:
            bad.append('still names %s' % token)
    if new.count('MAP_TILE_URL') != 1:
        bad.append('MAP_TILE_URL lands %d times' % new.count('MAP_TILE_URL'))
    if new.count('alv-map-nokey') != 1:
        bad.append('the no-key notice lands %d times'
                   % new.count('alv-map-nokey'))
    # The tile layer is added exactly once, and only inside the branch.
    if new.count('L.tileLayer(') != 1:
        bad.append('L.tileLayer is called %d times' % new.count('L.tileLayer('))
    if 'L.tileLayer(mapTileUrl' not in new:
        bad.append('the tile layer no longer reads the context URL')
    # Nothing outside the map block moved.
    if len(new) <= len(old) - 400:
        bad.append('the file shrank by %d bytes, which is too much'
                   % (len(old) - len(new)))
    # Braces still balance inside the script the round edited.
    for tag in ('script',):
        for blk in re.findall(r'<%s[^>]*>(.*?)</%s>' % (tag, tag), new, re.S):
            if blk.count('{') != blk.count('}'):
                bad.append('a %s block no longer balances its braces' % tag)
                break
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


def main():
    check_only = '--check' in sys.argv
    for p in (SETTINGS, CTXPROC, BASE, PS1):
        if not os.path.exists(p):
            print('! %s not found - run from the project root' % p)
            sys.exit(1)

    problems = []
    planned = []

    new, old, nl, raw, did = plan_settings(problems)
    if new is not None:
        planned.append((SETTINGS, 'mysite/settings.py', old, new, nl, raw, did))
    elif did:
        print('  ---   mysite/settings.py %s' % did[0])

    new, old, nl, raw, did = plan_ctxproc(problems)
    if new is not None:
        planned.append((CTXPROC, 'mysite/context_processors.py', old, new, nl,
                        raw, did))
    elif did:
        print('  ---   mysite/context_processors.py %s' % did[0])

    new, old, nl, raw, did = plan_gate(problems)
    if new is not None:
        planned.append((PS1, 'Push-PendingChanges.ps1', old, new, nl, raw, did))
    elif did:
        print('  ---   Push-PendingChanges.ps1 %s' % did[0])

    new, old, nl, raw, did = plan_base(problems)
    if new is not None:
        planned.append((BASE, 'base.html', old, new, nl, raw, did))
    elif did:
        print('  ---   base.html %s' % did[0])

    for rel in sorted(PAGES):
        path = os.path.join(T, rel)
        if not os.path.exists(path):
            problems.append('%s is not here' % rel)
            continue
        new, old, nl, raw, did = plan_page(rel, problems)
        if new is None:
            if did:
                print('  ---   %s %s' % (rel, did[0]))
            continue
        if self_check(rel, old, new, problems):
            planned.append((path, rel, old, new, nl, raw, did))

    if problems:
        print('')
        for p in problems:
            print('  FAIL  %s' % p)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    if not planned:
        print('')
        print('  Nothing to do - everything is already in place.')
        return

    for _path, name, _old, _new, _nl, _raw, did in planned:
        for d in did:
            print('  %s %s: %s' % ('WOULD' if check_only else 'OK   ', name, d))

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for path, _name, _old, new, nl, raw, _did in planned:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)

    print('')
    print('  %d file(s) written. Backups are <name>%s and are never '
          'overwritten.' % (len(planned), SUFFIX))
    print('')
    print('  NEXT, AND THE MAP STAYS BLANK UNTIL YOU DO IT:')
    print('    1. Create a free Geoapify account and generate an API key.')
    print('    2. Restrict that key to alivente.online in their dashboard.')
    print('    3. Add GEOAPIFY_KEY to the Railway service variables.')
    print('    4. python test_map_provider.py')


if __name__ == '__main__':
    main()
