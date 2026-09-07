.\Push-PendingChanges.ps1 -Push `
  -Message "The Properties map stops asking CARTO for an API key" `
  -Body @'
map_view.html drew its basemap from CARTO's Voyager raster tiles:

    https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png

CARTO now gates those behind an API key, and it does not fail. It returns
tiles with "API KEY REQUIRED" and "carto.com/basemaps/apikey" PRINTED INTO
THE IMAGE. So the map loaded, Leaflet was happy, the pins landed in the right
places, the console stayed clean - and every tile carried a watermark.
Nothing throws, which is why it sat there looking like a rendering glitch
rather than a broken dependency.

THE FIX WAS ALREADY IN THIS REPO, THREE TIMES OVER. properties_add.html,
properties_edit.html and map_test.html all draw the same kind of map from
OpenStreetMap's own tiles, which need no key. Those three were confirmed
drawing cleanly before the round was written, so the tiles are known to work
from this deployment. map_view.html was the odd one out - and its own comment
already said `// Add OpenStreetMap tiles`. The comment was right and the code
had drifted away from it.

THREE THINGS CHANGED TOGETHER, AND THE SECOND IS THE TRAP.

  the URL        cartocdn voyager -> tile.openstreetmap.org

  subdomains     'abcd' -> REMOVED. CARTO serves a, b, c and d; OSM serves
                 a, b and c, and Leaflet's default is 'abc' - which is why
                 the three working pages set no subdomains option at all.
                 Swap the URL and leave `subdomains: 'abcd'` behind and a
                 QUARTER of every screen's tile requests go to
                 d.tile.openstreetmap.org, which does not exist. The map
                 would come up mostly right, with a scatter of blank squares
                 that moves as you pan. A partial fix that reads as a whole
                 one - the same shape as the print round's half-guarded comma
                 list, and the suite pins it directly.

  {r} retina     gone with the URL. A CARTO convention; the OSM standard
                 layer serves no @2x tiles and a request for one is a 404.

maxZoom drops from 19 to the 18 the three working pages use. OSM will serve
19, but matching the pages known to work here is worth more than one zoom
level, and a round that changes two things cannot say which one fixed it.

WHAT THIS ROUND CANNOT PROVE, SAID PLAINLY, because every other round this
week carried a rendered check and this one has none. The only honest render
would be a live HTTPS request to a third-party tile server. In the build
sandbox that request is blocked outright - Leaflet never loads, `typeof L` is
`undefined`, and the fetch fails with ERR_TUNNEL_CONNECTION_FAILED. And on a
machine where it DID succeed, a green tick would be a fact about that
machine's network on that afternoon, not about the change.

So the suite measures SAMENESS instead, which is checkable and deterministic
and is the actual argument: map_view.html now configures its tile layer
EXACTLY as the three pages you have confirmed are working. Not "OSM tiles
work" - "this page now asks the way the pages that work ask". The remaining
verification is a person loading /properties/map/, and the suite says so in
its own output rather than implying it has done more than it has.

36 checks. Three negative controls, each the real failure rather than an
invented one: leave `subdomains: 'abcd'` behind, carry the `{r}` suffix
across, or break one of the three peer pages so the round's premise no longer
holds - all three fail.

AND THE PATCHER'S COMMENT STRIPPER ATE THE URL. Its first draft removed `//`
to end of line anywhere, and every URL in the file contains `//` - so the
stripper deleted `https://{s}.tile.openstreetmap.org/...` and then reported
the URL as missing. Whole-line comments only now, with a control on the
stripper itself: the prose must be gone AND the code must survive.

NOT CHANGED, but worth having visible rather than inherited: OpenStreetMap's
public tile server is a courtesy service with a usage policy, not a CDN with
a contract. At this scale that is fine, and it is what the rest of the system
already relies on. If the map ever needs a guaranteed provider that is an
account and a key and a different conversation.

map_view.html   11,915 -> 12,972 bytes.
'@ `
  -Checks "python test_map_tiles.py","python test_issues_table.py","python test_ia_drill.py","python test_ia_tiles.py","python test_ia_palette.py","python test_print_leaks.py","python test_fsr_palette.py","python test_notify_btns.py","python test_comment_tint.py","python test_fi_seg.py","python test_button_sweep.py","python test_action_standard.py","python test_table_standard.py"
