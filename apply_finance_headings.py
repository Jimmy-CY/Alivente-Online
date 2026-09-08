"""apply_finance_headings.py - Financials stops heading its pages a different
   way from the rest of the system.

    python apply_finance_headings.py --check     dry run, writes nothing
    python apply_finance_headings.py

Run from the repo root. TWENTY templates.

WHAT THE EARLIER SURVEY GOT WRONG, TWICE.

The teal-banner round scanned for `#0e7c8b` in `*.html`. Both halves of that
were too narrow, and Demetri found it by looking at three screens:

  * IT ONLY GLOBBED THE TOP LEVEL. Six subdirectories - finance/, projects/,
    invoices/, receipts/, components/, error_pages/ - were never opened, so
    `finance/vacancy_management.html` kept a banner identical to the three
    the round retired. Not a decision; a directory nobody walked.

  * AND IT ONLY LOOKED FOR TEAL. The same `.page-header` component exists in
    FIVE hues, and the round could not see four of them:

        green   #28a745 -> #20c997    9   Revenue, Revenue Types, Line Types
        purple  #667eea -> #764ba2    9   users, workspaces, my_profile
        red     #dc3545 -> #e83e8c    9   Expenses, Expense Types, Line Types
        teal    #0e7c8b -> #0a5e6a    3   Performance Trends, Vacancy Mgmt
        violet  #6f42c1 -> #5a32a3    1   measurement units

    "The teal banner round" was named after the colour it happened to find
    first, and a survey named after a symptom finds only that symptom.

THIS ROUND IS FINANCIALS PLUS PERFORMANCE TRENDS: the nine green, the nine
red, Performance Trends and Vacancy Management. Administration's purple nine
and the Personal ones follow with those modules' own reviews.

WHAT THE STANDARD ACTUALLY IS, MEASURED RATHER THAN ASSERTED.

Of 125 templates, 65 head themselves the same way:

    <h2><center>Title</center></h2>
    <h5><center>Subtitle</center></h5>      (optional)
    <br/>

`finance/cashflow_forecast.html` is one of them - the same folder, doing it
correctly - which is why Forecasted Cashflows reads as belonging and its
neighbours do not. **Not one of those 65 headings carries an icon**, so the
`<i class="fas fa-coins">` in these twenty goes with the band. That is what
complying means; keeping the icons would leave these twenty as the only
pages in the system with one.

THE COLOUR CODING GOES, DELIBERATELY. Financials paints Revenue green and
Expenses red. It is a real idea, but no other module does it, and green/red
already mean something else system-wide: `--alv-good` and `--alv-bad` are
healthy and overdue. A heading that is green because it is about revenue and
a figure that is green because it is on time cannot both be the vocabulary.
Revenue and Expense are already told apart by their titles, their menus and
their figures.

WHAT MUST SURVIVE. Six of the twenty carry an `.editing-pill` inside the
band - "Editing: Apolloneon - Monthly - EUR 900" - and it is
`rgba(255,255,255,0.22)` with a white border, which is a shape only on a
coloured ground and nothing at all on paper. That is the same defect the
Resolved Issues Report round met in `.stat-box`, and it gets the same answer:
base already owns the component, `.alv-pill` / `.alv-pill-neutral`.

HOUSE RULES: idempotent, .bak_hdr backups never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')

REVENUE = ['finance_revenue.html', 'finance_revenue_add.html',
           'finance_revenue_edit.html', 'finance_revenue_line_types.html',
           'finance_revenue_line_types_add.html',
           'finance_revenue_line_types_edit.html',
           'finance_revenue_types.html', 'finance_revenue_types_add.html',
           'finance_revenue_types_edit.html']
EXPENSE = [n.replace('revenue', 'expense') for n in REVENUE]
OTHER = ['occupancy_trends.html', 'finance/vacancy_management.html']
PAGES = REVENUE + EXPENSE + OTHER

for _n in PAGES:
    if not os.path.exists(os.path.join(T, _n.replace('/', os.sep))):
        sys.exit('! %s not found - run from the repo root' % _n)


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


def drop_rule(text, selector, what, expect):
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != expect:
        sys.exit('! %s: %r matched %d openings, expected %d'
                 % (what, selector, len(hits), expect))
    for m in reversed(hits):
        i, depth, k = m.start(), 1, m.end()
        while depth and k < len(text):
            if text[k] == '{':
                depth += 1
            elif text[k] == '}':
                depth -= 1
            k += 1
        if depth:
            sys.exit('! %s: unbalanced braces after %r' % (what, selector))
        while k < len(text) and text[k] in '\r\n':
            k += 1
        text = text[:i] + text[k:]
    return text


COMMENT = re.compile(r'/\*.*?\*/', re.S)


def div_span(mk, start):
    """The [open, close) span of the <div> opening at `start`, by walking
       nested <div>s. A regex to the first </div> stops inside the first
       child, which on the six edit pages is the .editing-pill."""
    i = mk.index('>', start) + 1
    depth, k = 1, i
    for t in re.finditer(r'</?div\b', mk[i:]):
        depth += 1 if t.group(0) == '<div' else -1
        if depth == 0:
            k = i + t.start()
            return i, k, mk.index('>', i + t.start()) + 1
    sys.exit('! a .page-header <div> is never closed')


def tag_fault(src):
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith', 'comment': 'endcomment',
            'spaceless': 'endspaceless', 'autoescape': 'endautoescape'}
    CLOSE = {v: k for k, v in OPEN.items()}
    stack = []
    for m in re.finditer(r'\{%\s*(\w+)', src):
        t = m.group(1)
        ln = src.count('\n', 0, m.start()) + 1
        if t in OPEN:
            stack.append((t, ln))
        elif t in CLOSE:
            if not stack:
                return 'line %d: %s with nothing open' % (ln, t)
            top, at = stack.pop()
            if OPEN[top] != t:
                return ('line %d: %s closes {%% %s %%} from line %d'
                        % (ln, t, top, at))
    return 'unclosed {%% %s %%} from line %d' % stack[-1] if stack else None


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


PILL = """        /* THE CONTEXT CHIP CAME OUT OF A COLOURED BAND - 8 Sep.
           It was rgba(255,255,255,0.22) with a white border: a shape only on
           a gradient, and nothing at all on paper. base already owns the
           component for a small neutral chip, and the Resolved Issues Report
           round met the identical problem in its .stat-box. */
        .editing-pill {
          display: inline-block;
          margin-top: 4px;
          padding: 5px 12px;
          background: var(--alv-neutral-soft);
          border: 1px solid var(--alv-line);
          border-radius: 999px;
          color: var(--alv-ink);
          font-size: 12px;
        }
"""

NOTE = """        /* THE COLOURED BANNER WENT - 8 Sep.

           This page headed itself with a filled %s gradient band and a
           white %s title. Twenty templates across Financials did, in two
           colours - green for revenue, red for expenses - and the same
           component exists in five hues system-wide.

           It is now the heading 65 of the 125 templates already use, and
           that finance/cashflow_forecast.html in this very folder already
           used: a centred <h2>, an optional centred <h5> beneath it, and no
           icon. Not one of those 65 carries an icon, which is why this
           one's went with the band.

           The colour coding went deliberately. Green and red already mean
           --alv-good and --alv-bad - on time and overdue - everywhere else
           in this system, and a heading cannot be green for one reason
           while a figure beside it is green for another. */
"""

BAND = {
    'green': 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
    'red': 'linear-gradient(135deg, #dc3545 0%, #e83e8c 100%)',
    'teal': 'linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%)',
}

CHANGED = {}
for rel in PAGES:
    path = os.path.join(T, rel.replace('/', os.sep))
    orig, crlf, f = load(path)
    if 'THE COLOURED BANNER WENT' in f:
        CHANGED[rel] = (path, orig, crlf, f, True, '')
        continue

    hue = ('green' if rel in REVENUE else
           'red' if rel in EXPENSE else 'teal')

    # ---------------------------------------------------------------- markup
    if f.count('<div class="page-header">') != 1:
        sys.exit('! %s: %d .page-header divs, expected 1'
                 % (rel, f.count('<div class="page-header">')))
    start = f.index('<div class="page-header">')
    i, close_at, after = div_span(f, start)
    inner = f[i:close_at]

    # The title. The icon goes: no centred heading in the corpus has one.
    m_h1 = re.search(r'<h1[^>]*>(.*?)</h1>', inner, re.S)
    if not m_h1:
        sys.exit('! %s: no <h1> inside the banner' % rel)
    title = re.sub(r'<i\b[^>]*>\s*</i>\s*', '', m_h1.group(1)).strip()
    want('<i ' not in title, '%s: an icon survived in the title' % rel)

    # The subtitle(s). occupancy_trends has TWO <p>s inside an {% if %}, so
    # each is converted in place rather than the block being rebuilt - which
    # would have to reproduce the conditional and would get it wrong.
    body = inner[:m_h1.start()] + inner[m_h1.end():]
    body = re.sub(r'<p>(.*?)</p>',
                  lambda m: '<h5><center>%s</center></h5>' % m.group(1).strip(),
                  body, flags=re.S)

    # The context chip is centred with the heading it belongs to. Left
    # alone it sat hard left under a centred title and read as orphaned -
    # visible in the render, invisible to every check above.
    body = re.sub(r'(<div class="editing-pill">.*?</div>)',
                  lambda m: '<center>%s</center>' % m.group(1),
                  body, flags=re.S)
    new_head = ('<h2><center>%s</center></h2>\n%s\n        <br/>'
                % (title, body.strip('\n')))
    f = f[:start] + new_head + f[after:]

    # ------------------------------------------------------------------- css
    n_hdr = len(re.findall(r'(?m)^[ \t]*\.page-header[ \t]*\{', f))
    f = drop_rule(f, '.page-header', '%s: the band' % rel, n_hdr)
    for sel in ('.page-header h1', '.page-header p'):
        n = len(re.findall(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{', f))
        if n:
            f = drop_rule(f, sel, '%s: %s' % (rel, sel), n)

    if '.editing-pill' in f:
        n = len(re.findall(r'(?m)^[ \t]*\.editing-pill[ \t]*\{', f))
        f = drop_rule(f, '.editing-pill', '%s: the white chip' % rel, n)
        _m = re.search(r'(<style[^>]*>)', f)
        f = f[:_m.end()] + '\n' + PILL + f[_m.end():]

    _m = re.search(r'(<style[^>]*>)', f)
    f = f[:_m.end()] + '\n' + (NOTE % (hue, 'white')) + f[_m.end():]
    CHANGED[rel] = (path, orig, crlf, f, False, hue)

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_bcss = ''
_bp = os.path.join(T, 'base.html')
if os.path.exists(_bp):
    _bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', load(_bp)[2],
                                 re.S))
for _need in ('--alv-neutral-soft', '--alv-line', '--alv-ink'):
    want(_need in _bcss, 'base does not declare %s' % _need)

for rel, (path, orig, crlf, f, done, hue) in CHANGED.items():
    if done:
        continue
    nc = COMMENT.sub('', re.sub(r'<!--.*?-->', '', f, flags=re.S))
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', nc, re.S))
    mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', nc, flags=re.S)

    want('page-header' not in mk, '%s: the banner div survives' % rel)
    want(not re.search(r'(?m)^[ \t]*\.page-header\b', css),
         '%s: a .page-header rule survives' % rel)
    # THE BANNER'S GRADIENT, NOT EVERY GRADIENT.
    #
    # This first asked each file for no gradient and no green/red/teal at
    # all, and failed 20 correct patches. These pages legitimately keep
    # those colours elsewhere: .btn-row-edit is a green or red ROW action,
    # .property-header td has its own pale gradient behind a property name,
    # occupancy_trends keeps a teal year-detail modal, and vacancy_management
    # is teal throughout. A check that fails correct work is not strict, it
    # is aimed at the wrong thing - the third time in two days. What must be
    # gone is the BAND: this exact gradient, on a header selector.
    # ON A PAGE-HEADER SELECTOR, not anywhere in the file. The first draft
    # asked for the band's gradient string to be absent entirely, and three
    # pages failed on a correct patch because their MODAL header uses the
    # identical gradient - finance_expense_add, finance_expense_edit and
    # occupancy_trends. Modal headers keep their colour on purpose; that is
    # the next round. Fourth time in two days a whole-file claim has been
    # written for a component-level change.
    _modal = 0
    for _m4 in re.finditer(r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{([^{}]*)\}', css):
        _sel, _body = _m4.group(1).strip(), _m4.group(2)
        if 'modal' in _sel.lower():
            if BAND[hue] in _body:
                _modal += 1
            continue
        if re.search(r'page-header|\bbanner\b', _sel, re.I):
            want('linear-gradient' not in _body,
                 '%s: a header-shaped rule still paints a gradient (%s)'
                 % (rel, _sel[:40]))
        want(BAND[hue] not in _body,
             '%s: the band gradient survives on %s' % (rel, _sel[:40]))
    # And the modal that keeps it must STILL keep it - a round that quietly
    # took it too would be doing the next round's work without saying so.
    _was_css = COMMENT.sub('', '\n'.join(re.findall(
        r'<style[^>]*>(.*?)</style>', orig.replace('\r\n', '\n'), re.S)))
    _was_modal = len([1 for _m5 in re.finditer(
        r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{([^{}]*)\}', _was_css)
        if 'modal' in _m5.group(1).lower() and BAND[hue] in _m5.group(2)])
    want(_modal == _was_modal,
         '%s: a modal header changed - modals are the next round (%d -> %d)'
         % (rel, _was_modal, _modal))

    _h2 = re.search(r'<h2><center>(.*?)</center></h2>', mk, re.S)
    want(_h2 is not None, '%s: no centred <h2> heading' % rel)
    want(_h2 is not None and '<i ' not in _h2.group(1),
         '%s: the heading still carries an icon' % rel)
    want(_h2 is not None and _h2.group(1).strip(),
         '%s: the heading lost its words' % rel)
    want('<h1' not in mk, '%s: an <h1> survives' % rel)

    if '.editing-pill' in mk:
        want('var(--alv-neutral-soft)' in css,
             '%s: the chip is still dressed for a coloured ground' % rel)
        want('rgba(255, 255, 255' not in css.split('/*')[0],
             '%s: a white-on-colour chip survives' % rel)

    _f = tag_fault(f)
    want(_f is None, '%s: the template will not parse - %s' % (rel, _f))
    want(len(re.findall(r'<div\b', mk)) == len(re.findall(r'</div>', mk)),
         '%s: the <div>s do not balance - %d open, %d close'
         % (rel, len(re.findall(r'<div\b', mk)),
            len(re.findall(r'</div>', mk))))
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
        want(blk.count('{') == blk.count('}'), '%s: unbalanced braces' % rel)
    want('THE COLOURED BANNER WENT' in f, '%s: the round is not explained' % rel)

    # The words that were on screen must still be on screen.
    _was_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '',
                     orig.replace('\r\n', '\n'), flags=re.S)
    _wh1 = re.search(r'<h1[^>]*>(.*?)</h1>', _was_mk, re.S)
    if _wh1:
        _words = re.sub(r'<[^>]*>', '', _wh1.group(1)).strip()
        want(_words and _words in mk,
             '%s: the title text %r is no longer on the page' % (rel, _words))

want(len([1 for v in CHANGED.values() if not v[4]]) in (0, 20),
     'the round covers 20 templates, not %d'
     % len([1 for v in CHANGED.values() if not v[4]]))

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL[:24]:
        print('   - %s' % x)
    sys.exit(1)

_n = 0
for rel, (path, orig, crlf, f, done, hue) in CHANGED.items():
    if done:
        print('  %-42s already patched' % rel)
        continue
    out = f.replace('\n', '\r\n') if crlf else f
    print('  %-42s %d -> %d bytes'
          % (rel, len(orig.encode('utf-8')), len(out.encode('utf-8'))))
    _n += 1
    if CHECK:
        continue
    bak = path + '.bak_hdr'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)

print('\n  --check: nothing written (%d file(s) would change).' % _n
      if CHECK else '\n  done - %d file(s).' % _n)
