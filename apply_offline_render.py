"""apply_offline_render.py - the push gate stops depending on a CDN.

    python apply_offline_render.py --check     dry run, writes nothing
    python apply_offline_render.py

Run from the repo root.

WHAT HAPPENED. The push gate stopped on this, with nothing wrong in the tree:

    3. the negative control
    playwright._impl._errors.TimeoutError: Page.set_content: Timeout 30000ms
      - setting frame content, waiting until "load"

Sections 1 and 2 had already passed. Nothing had regressed. The gate simply
could not finish, and a gate that cannot finish blocks a push exactly as
loudly as a gate that fails.

WHY IT HUNG, AND WHY IT WILL HANG AGAIN.

`page.set_content()` defaults to `wait_until="load"`, which does not return
until every subresource of the page has resolved. FOURTEEN of the sixty-seven
templates this suite renders carry a remote stylesheet INSIDE their content
block:

    act_expense, asset_detail, customer_form, edit_asset, fsr, invoices,
    physical_invoice_list, properties, properties_add, properties_edit,
    property_assets, property_detail, suppliers, tenant
        -> https://cdnjs.cloudflare.com/.../font-awesome/6.0.0/css/all.min.css
    properties_add, properties_edit
        -> https://cdnjs.cloudflare.com/.../leaflet/1.9.4/leaflet.min.css
    property_detail
        -> https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css

So every run of this suite made a few dozen live requests to two third-party
CDNs, twice over - once for the real sweep, once for the negative control -
and any one of them being slow, rate-limited or dropped stops the push for
thirty seconds and then a traceback. It has passed all week because the
network happened to hold.

AND IT WAS NOT ONLY FRAGILE, IT WAS WRONG.

The suite's claim is about LAYOUT under two stylesheets it injects itself -
the pinned Bootstrap fixture and base.html. Letting a CDN serve a third one
into the same page means the measurement varies with what cdnjs returns that
afternoon. `property_detail.html` is the sharp case: its remote link is
Bootstrap 4.5.2, whose own `.form-control` height rule lands on top of the
fixture the suite deliberately pinned. That page has been measured against
whichever Bootstrap the CDN felt like serving, not against the fixture.

The map round already wrote this lesson down, about itself:

    a green result would be a fact about that machine's network on that
    afternoon, not about the change

- and then declined to render at all rather than pretend otherwise. This
suite was quietly doing the thing that round refused to do.

THE FIX, TWO LINES OF INTENT.

  * every http(s) request the page makes is ABORTED at the browser, so the
    render is hermetic - what is measured is the fixture plus base plus the
    page's own <style>, which is what the suite says it measures;
  * and `wait_until="domcontentloaded"`, so the page is measured when its
    markup and its inline CSS are in, not when a network it no longer uses
    has finished saying no.

Faster, deterministic, and it can no longer be stopped by somebody else's
outage.

WHAT THIS CHANGES ABOUT THE RESULT. The 14 pages above are now measured
without font-awesome, and property_detail without a second Bootstrap. Both
are the correct measurement: this suite is about control heights under the
project's own CSS. Re-run in the sandbox after the change, section 2 stays
at 0 pages with a problem and the negative control stays at 148 controls
across 41 pages - the same numbers, now honestly obtained.

NOT THIS ROUND, WRITTEN DOWN SO IT IS A DECISION. Eleven other browser
suites in the gate also call `set_content`, and not one of them blocks the
network either. Most feed hand-built fragments with no remote link in them,
so they are exposed but not currently reaching out. Sweeping all twelve
wants a scan first - the same shape as the teal-banner round - and doing it
here, inside a push the user is blocked on, would be the second change of
the evening nobody asked for.

HOUSE RULES: idempotent, .bak_offline backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
CH = os.path.join(ROOT, 'test_control_height.py')
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.exists(CH):
    sys.exit('! %s not found - run from the repo root' % CH)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:110]))
    return t.replace(old, new, 1)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


F_ORIG, F_CRLF, f = load(CH)
DONE = 'OFFLINE' in f

if DONE:
    print('  test_control_height.py already patched')
else:
    # ------------------------------------------------ 1. refuse the network
    f = sub1(f, """    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1900, 'height': 900})
""",
             """    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1900, 'height': 900})

        # OFFLINE. Fourteen of these templates carry a remote <link> inside
        # their content block - font-awesome, leaflet, and on property_detail
        # a whole second Bootstrap. Left alone, set_content()'s default
        # wait_until="load" does not return until a CDN answers, so the push
        # gate was one outage away from a 30s hang and a traceback; it took
        # one on 7 Sep. It was also the wrong measurement: this suite pins a
        # Bootstrap fixture on purpose, and a CDN serving 4.5.2 on top of it
        # measures whatever cdnjs felt like sending that afternoon. Nothing
        # leaves the machine now, and every request that tries is counted so
        # the control below can prove the refusal is doing work.
        blocked.clear()

        async def _offline(route, request):
            blocked.append(request.url)
            await route.abort()

        await pg.route(re.compile(r'^https?://'), _offline)
""", 'CH: the offline route')

    # ---------------------------------------- 2. and stop waiting for `load`
    f = sub1(f, """                "<body>%s</body></html>" % (BOOTSTRAP, base_css, css_of(t), html))""",
             """                "<body>%s</body></html>" % (BOOTSTRAP, base_css, css_of(t), html),
                wait_until='domcontentloaded')""",
             'CH: stop waiting for a network it no longer uses')

    # ----------------------------------------------- 3. somewhere to count it
    f = sub1(f, """async def sweep(free_height):""",
             """blocked = []


async def sweep(free_height):""", 'CH: the tally')

    # ----------------------------------------------- 4. and prove it mattered
    # A refusal nobody counts is indistinguishable from a page that never
    # asked. This is the negative control ON THE FIX: the corpus must still
    # contain remote links, and the browser must have refused them all.
    f = sub1(f, """    print('\\n' + '-' * 72 + '\\n 3. the negative control\\n' + '-' * 72)""",
             """    # base.html is excluded because the sweep above skips it, and a control
    # that counts a page the sweep never rendered is counting the wrong set.
    _remote = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(TPL, '*.html'))
        if os.path.basename(p) != 'base.html' and 'form-control' in read(p)
        and re.search(r'<link[^>]+https?://', re.sub(
            r'<script[^>]*>.*?</script>', '', read(p), flags=re.S)))
    check('CONTROL: %d page(s) still carry a remote <link>, and the browser '
          'refused all %d request(s) - the gate does not need a CDN'
          % (len(_remote), len(blocked)),
          len(_remote) >= 10 and len(blocked) >= len(_remote),
          ', '.join(_remote[:4]))

    print('\\n' + '-' * 72 + '\\n 3. the negative control\\n' + '-' * 72)""",
         'CH: prove the refusal is doing work')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
# EVERY QUESTION BELOW IS ASKED OF THE CODE, NOT OF THE FILE.
#
# It was asked of the file first, and the first run failed on this:
#
#     - CH: a set_content call was left waiting for the network
#
# on a correct patch. The comment installed two lines above explains the
# defect by NAMING it - "set_content()'s default wait_until" - so counting
# the string in the whole file found two calls where there is one. That is
# the twenty-fourth time in this project that a check reading text has read
# prose, and the third time this week that the prose was the patcher's own
# explanation of the very thing it was checking.
_code = re.sub(r'"""(?:.|\n)*?"""', '', f)
_code = re.sub(r'(?m)^\s*#[^\n]*$', '', _code)

want('.route(' in _code, 'CH: no route was installed')
want("wait_until='domcontentloaded'" in _code,
     'CH: set_content still waits for load')
want(_code.count('set_content(')
     == _code.count("wait_until='domcontentloaded'"),
     'CH: a set_content call was left waiting for the network')
want('await route.abort()' in _code, 'CH: the route does not abort')
want(re.search(r'(?m)^blocked = \[\]', _code) is not None,
     'CH: nothing to count refusals in')
want(_code.count('blocked.append') == 1 and _code.count('blocked.clear()') == 1,
     'CH: the tally is not reset per sweep - the control would double-count')

# The suite imports on one line - `import os, re, sys, glob, asyncio` - so
# asking for the string 'import re' says no on a file that imports re. Ask
# Python what the module actually binds.
_imports = set()
for _m in re.finditer(r'(?m)^import\s+([^\n#]+)', _code):
    _imports.update(x.strip().split(' as ')[-1].strip()
                    for x in _m.group(1).split(','))
for _mod in ('re', 'glob', 'os'):
    want(_mod in _imports,
         'CH: the round needs %s and the suite does not import it (%s)'
         % (_mod, sorted(_imports)))
try:
    compile(f, 'test_control_height.py', 'exec')
except SyntaxError as e:
    want(False, 'CH: the suite will not compile - line %s: %s' % (e.lineno, e.msg))

# The corpus half of the claim, measured rather than remembered.
if os.path.isdir(T):
    _n = 0
    for _p in os.listdir(T):
        if not _p.endswith('.html'):
            continue
        _t = load(os.path.join(T, _p))[2]
        if 'form-control' in _t and re.search(
                r'<link[^>]+https?://',
                re.sub(r'<script[^>]*>.*?</script>', '', _t, flags=re.S)):
            _n += 1
    want(_n >= 10, 'CH: only %d template(s) carry a remote link - the round\'s '
                   'premise does not hold, re-read before shipping' % _n)
    print('  %d template(s) with a form control carry a remote <link>' % _n)

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-32s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_offline'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(CH, F_ORIG, F_CRLF, f, DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
