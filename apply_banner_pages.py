"""apply_banner_pages.py - the teal page banner is retired.

    python apply_banner_pages.py --check     dry run, writes nothing
    python apply_banner_pages.py

Run from the repo root.

WHAT THE SURVEY FOUND, AND HOW MUCH OF IT WAS WRONG AT FIRST.

The running list carried this as "24 instances across 15+ templates". Scanned:
**19 rules with a teal background on a header-shaped selector, in 12 files**,
and it is ONE design spelled six ways -

    linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%)        8
    linear-gradient(135deg, #0e7c8b, #0a5e6a)                2   same gradient
    linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%) !imp   1   same again
    #0e7c8b                                                  5
    #0e7c8b !important                                       3
    Bootstrap's `bg-info` utility                            4   (2 files)

Then four narrowing passes, each of which corrected the one before:

  19 rules are not 19 banners. They are **4 banners**, the rest being
  descendant rules for their own titles and phone layouts.

  4 banners are not 4 pages. `manual_pdf`'s two `.cover-*` rules are a PDF
  cover sheet, and `notifications`' `.indicator-header` is a PANEL header
  whose markup is built inside a `<script>` - which also means it is not the
  dead rule the first pass called it. Both out.

  And `categories_management` is RECIPE-SIDE. It links to `recipe_management`
  and manages ingredient categories, so it sits outside the push gate by this
  project's own convention - but `Show-ButtonDrift.py`'s exclusion list is
  NAME-based and not one of its thirteen tokens appears in
  "categories_management". **The page has been inside every sweep's scope by
  accident.** Out of this round; the list itself wants fixing separately.

Which leaves **THREE pages**, and this round is those three.

WHY RETIRE IT RATHER THAN TOKENISE IT. Every signed-off page - Properties,
Tenants, Suppliers, Invoices - heads itself with a plain title and base's
`.page-action-buttons`. No band. Of 71 modal headers in the corpus, 38 are
styled by a page rule, 29 are plain, and only 9 are teal. The band is the
minority everywhere it appears, and base owns no banner component to make it
the majority with. (base's ONLY gradient is the sidebar avatar's
`#667eea -> #764ba2`, which is purple and belongs to no palette this project
has ever defined. Not this round, but somebody should know.)

Modal headers KEEP their teal and are a separate round with its own survey.

WHAT EACH PAGE GETS

  occupancy_trends      band -> plain title, and nothing else. Its action
                        row was already converted by an earlier round; this
                        round does not touch it. See the note in section 1
                        for the draft that did, and why the guard was right
                        to refuse it.

  notification_settings band -> plain title. Its `.settings-header-actions`
                        -> base's `.page-action-buttons`, with the buttons
                        carrying the tones they already had. Its bespoke
                        white-on-teal `.help-btn` dies with the band, and so
                        does a phone rule for `.settings-header-actions
                        .action-primary` that matched nothing, because the
                        markup said `action-secondary`.

  comments_report       band -> plain header row. Its `.stat-box` - a white
                        20%-alpha tile that only reads on teal - becomes
                        base's `.alv-stat`, which is what
                        `tenant_payment_days` already shows a headline figure
                        with. Its action row is already
                        `.page-action-buttons` and is untouched.

                        AND ITS PRINT RULE GOES WITH THE BAND. `.report-header
                        { background: #0e7c8b !important; print-color-adjust:
                        exact }` was not the file overriding itself - it was
                        a deliberate flat fallback, because a gradient does
                        not print. With no band there is nothing to force, and
                        the report prints as ink on paper like its four
                        siblings.

WHAT THIS ROUND DELIBERATELY DOES NOT DO.

  It does not rename comments_report's title classes to `.report-title-main`
  / `.report-title-sub` to match the other four report screens. That looks
  like a standard and is not one: `.report-title-sub` is 1.4rem on two of
  them, 1.2rem on a third and 1.1rem on the fourth, and `#2c3e50` on three
  while the fourth is now tokenised. Adding a fifth copy would cement a
  duplication, not join a standard. The four wanting to become ONE component
  in base is a real finding and its own round.

  It does not touch `.action-bar`, which **30 templates use and base does not
  define** - every one of them declaring it locally, including four
  signed-off pages. Its own survey.

  AND IT DOES NOT TOUCH A BUTTON'S TONE. A draft of this round promoted Help
  to `action-primary` on two pages, because base hides
  `.page-action-buttons .action-secondary` below 768px and neither page has
  a More menu to surface it - so Help is unreachable on a phone.
  test_button_sweep.py refused it and was right: its classifier holds that
  Help is never the verb, and the promotion wrote an exception to a correct
  rule. `.action-secondary` carries two meanings - "quieter than the
  primary" to the classifier, "hidden below 768px because the More menu
  carries it" to base - which agree on 22 bars and contradict on 11. That
  is a base fault, it is its own round, and it is written up in the running
  list rather than half-fixed here.

HOUSE RULES: idempotent, .bak_banner backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
CR = os.path.join(T, 'comments_report.html')
OT = os.path.join(T, 'occupancy_trends.html')
NS = os.path.join(T, 'notification_settings.html')
BASE = os.path.join(T, 'base.html')
for _p in (CR, OT, NS, BASE):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


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
    """Delete every rule opening with `selector`, by walking braces.

       Line-anchored, so `.stat-box` does not also take `.stat-box .stat-value`
       unless that is asked for separately - and `expect` is asserted, because
       a selector that matched three times when two were meant is how a round
       silently deletes a phone layout."""
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


STYLE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def sweep_css(text, mapping):
    """Literal -> token, INSIDE <style> and OUTSIDE its comments. A sweep that
       reads text edits prose; this one splits on comments and edits the gaps."""
    tally = {k: 0 for k in mapping}

    def one(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        out, last = [], 0
        for c in COMMENT.finditer(body):
            out.append(('code', body[last:c.start()]))
            out.append(('note', c.group(0)))
            last = c.end()
        out.append(('code', body[last:]))
        parts = []
        for kind, chunk in out:
            if kind == 'code':
                for lit, tok in mapping.items():
                    n = len(re.findall(re.escape(lit) + r'\b', chunk))
                    if n:
                        tally[lit] += n
                        chunk = re.sub(re.escape(lit) + r'\b', tok, chunk)
            parts.append(chunk)
        return head + ''.join(parts) + tail

    return STYLE.sub(one, text), tally


def tag_fault(src):
    """A WALKER, not a count. The 500 that shipped on 7 Sep came from an
       orphaned {% endif %} that a balanced COUNT was happy with."""
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


NOTE = """    /* THE TEAL BANNER WENT - 7 Sep.

       This page headed itself with a filled teal band:
       `linear-gradient(135deg, #0e7c8b 0%%, #0a5e6a 100%%)`, white text,
       12px radius, a drop shadow. Nineteen such rules were spelled six
       different ways across twelve files, and every one of them was a
       local invention: base owns no banner component, and never did.

       Every signed-off page - Properties, Tenants, Suppliers, Invoices -
       heads itself with a plain title and base's `.page-action-buttons`.
       The band was the minority, so it goes rather than becoming a
       component. Modal headers keep their teal; that is its own round.
%s */
"""

# ===========================================================================
# 1. occupancy_trends.html - band out, .action-bar -> .page-action-buttons
# ===========================================================================
OT_ORIG, OT_CRLF, ot = load(OT)
OT_DONE = 'THE TEAL BANNER WENT' in ot
if OT_DONE:
    print('  occupancy_trends.html already patched')
else:
    # THE ACTION ROW IS ALREADY DONE, AND THIS ROUND LEAVES IT ALONE.
    #
    # The build corpus had this page still using a local `.action-bar` with
    # Bootstrap's `btn-info`, so the first draft converted it. The repo is
    # AHEAD of that: an earlier round had already moved it to
    # `.page-action-buttons` and dropped the Bootstrap classes. Anchoring on
    # a stale corpus is how a patcher matches zero times, and the answer was
    # to fetch the real file rather than loosen the anchor until it matched.
    #
    # A SECOND DRAFT THEN PROMOTED Help FROM action-secondary TO
    # action-primary, here and on notification_settings, because base hides
    # `.page-action-buttons .action-secondary` below 768px and neither page
    # has an `.action-more-btn` to surface it - so Help is unreachable on a
    # phone. That much is true. The fix was not, and test_button_sweep.py
    # refused it.
    #
    # THE GUARD WAS RIGHT. Its classifier holds that Help is never the verb,
    # which is correct, and the promotion wrote an exception to a correct
    # rule. The real defect is that `.action-secondary` carries TWO
    # meanings - "quieter than the primary" to the classifier, "hidden below
    # 768px because the More menu carries it" to base. They agree on 22 bars
    # and contradict on 11, and promoting two buttons treats two instances
    # of a class-wide fault while leaving nine. It belongs in base and in
    # its own round. This round touches neither page's action row.
    if 'action-bar' in ot:
        sys.exit('! OT: this tree still has the old .action-bar row - that is '
                 'an older repo than this round was built against; re-read '
                 'before shipping rather than patching both shapes')

    # The band's own paint. The h1/p rules stay - they are sizing, not colour -
    # but they must stop assuming a dark ground.
    # PADDING AND RADIUS GO WITH THE FILL. They existed to hold the text off
    # the band's edge and to round that edge; with no band there is no edge,
    # and 32px of left padding just pushes the title out of line with the
    # action row above it. The render caught that; no text check could.
    ot = sub1(ot, """.page-header {
    background: linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%);
    color: white;
    padding: 26px 32px;
    border-radius: 12px;
    margin-bottom: 22px;
}""", """.page-header {
    color: var(--alv-ink);
    margin-bottom: 22px;
}""", 'OT: the band')
    # `opacity: 0.95` was how the subtitle sat back from white ON TEAL.
    # Opacity is not a colour: on paper it just makes ink slightly grey and
    # for no stated reason. The subtitle gets a real token instead.
    ot = sub1(ot, """.page-header p {
    margin: 0;
    font-size: 14px;
    opacity: 0.95;
}""", """.page-header p {
    margin: 0;
    font-size: 14px;
    color: var(--alv-ink-soft);
}""", 'OT: the subtitle stops being faded white')

    # (The three local `.action-bar` rules an earlier round deleted are
    #  already gone; the guard above refuses to run on a tree where they
    #  are not.)
    ot = sub1(ot, """.page-header {
    color: var(--alv-ink);""",
              (NOTE % '').replace('    /*', '/*').replace('\n    ', '\n')
              + """.page-header {
    color: var(--alv-ink);""", 'OT: say why the band went')

# ===========================================================================
# 2. notification_settings.html - band out, the bespoke button dies with it
# ===========================================================================
NS_ORIG, NS_CRLF, ns = load(NS)
NS_DONE = 'THE TEAL BANNER WENT' in ns
if NS_DONE:
    print('  notification_settings.html already patched')
else:
    # The band held title AND actions in one flex row. It becomes a title
    # block, and the actions become a sibling `.page-action-buttons` after
    # it - which is the order every signed-off page uses.
    # THE WHOLE BLOCK IN ONE SUBSTITUTION, deliberately. The band held title
    # AND actions inside one flex row, so unwrapping it changes how many
    # <div>s close where. Doing it as three edits left an orphaned </div> -
    # which is precisely the shape that shipped a 500 on 7 Sep - so the
    # anchor spans the entire block and the replacement is balanced by
    # construction rather than by arithmetic.
    ns = sub1(ns, """<div class="settings-header">
    <div class="settings-header-text">
        <h2><i class="fas fa-envelope"></i> Administration Notification Settings</h2>
        <p>Manage email recipients for property management and operational notifications</p>
    </div>
    <div class="settings-header-actions">
        <button type="button" class="btn action-secondary help-btn" data-toggle="modal" data-target="#admin_notification_settingsHelpModal" title="Help">
            <i class="fas fa-question-circle"></i> Help
        </button>
        <a href="{% url 'admin_apms' %}" class="btn action-back help-btn" aria-label="Back to Administration">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
</div>""",
              """<div class="settings-header">
    <h2><i class="fas fa-envelope"></i> Administration Notification Settings</h2>
    <p>Manage email recipients for property management and operational notifications</p>
</div>

<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#admin_notification_settingsHelpModal" title="Help">
        <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'admin_apms' %}" class="btn action-back" aria-label="Back to Administration">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
</div>""",
              'NS: the actions leave the band')

    ns = sub1(ns, """.settings-header {
    background: linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;""",
              (NOTE % """
       The buttons kept the tones the button sweep gave them. A draft
       promoted Help to `action-primary` here, because base hides
       `.page-action-buttons .action-secondary` below 768px on the
       assumption that an `.action-more-btn` surfaces it, and this page has
       none - so Help is unreachable on a phone. True, but the wrong fix:
       `.action-secondary` means "quieter" to the button classifier and
       "hidden, the More menu has it" to base, and those contradict on
       eleven bars. A base fault gets fixed in base, not by writing an
       exception into two pages.""").replace('    /*', '/*').replace('\n    ', '\n')
              + """.settings-header {
    color: var(--alv-ink);
    margin-bottom: 20px;""", 'NS: the band')
    ns = sub1(ns, """.settings-header p {
    margin: 0;
    opacity: 0.9;
}""", """.settings-header p {
    margin: 0;
    color: var(--alv-ink-soft);
}""", 'NS: the subtitle stops assuming a dark ground')

    for sel, n in (('.settings-header-text', 1), ('.settings-header .help-btn', 2),
                   ('.settings-header .help-btn:hover', 2),
                   ('.settings-header-actions', 2),
                   ('.settings-header-actions .action-primary', 1),
                   ('.settings-header-actions .action-back', 1)):
        ns = drop_rule(ns, sel, 'NS: %s dies with the band' % sel, n)

# ===========================================================================
# 3. comments_report.html - band out, the alpha tile becomes base's .alv-stat
# ===========================================================================
CR_ORIG, CR_CRLF, cr = load(CR)
CR_DONE = 'THE TEAL BANNER WENT' in cr
if CR_DONE:
    print('  comments_report.html already patched')
else:
    cr = sub1(cr, """        <div class="stat-box">
            <div class="stat-value">{{ comment_count }}</div>
            <div class="stat-label">Total Comments</div>
        </div>""",
              """        <div class="alv-stat">
            <div class="alv-stat-value">{{ comment_count }}</div>
            <div class="alv-stat-label">Total Comments</div>
        </div>""", 'CR: the tile that only read on teal')

    # The whole opening rule, so the band's padding and radius go with its
    # fill - see the same note on occupancy_trends. The flex row STAYS: the
    # title still sits opposite the figure, that is the page's layout rather
    # than the band's.
    cr = sub1(cr, """.report-header {
    background: linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%);
    color: white;
    padding: 20px 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}""", (NOTE % """
       Its `.stat-box` went with it: a white 20%%-alpha tile only reads on a
       dark ground, and base already has the component for a headline figure
       - `.alv-stat`, which is what tenant_payment_days shows one with.

       AND SO DID ITS PRINT RULE. `background: #0e7c8b !important` with
       `print-color-adjust: exact` was not this file overriding itself; it
       was a deliberate flat fallback, because a gradient does not print.
       With no band there is nothing left to force.""")
              .replace('    /*', '/*').replace('\n    ', '\n')
              + """.report-header {
    color: var(--alv-ink);
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}""", 'CR: the band')

    cr = sub1(cr, """.report-header-left .subtitle {
    margin: 5px 0 0 0;
    opacity: 0.9;
    font-size: 14px;
}""", """.report-header-left .subtitle {
    margin: 5px 0 0 0;
    color: var(--alv-ink-soft);
    font-size: 14px;
}""", 'CR: the subtitle stops assuming a dark ground')

    for sel, n in (('.stat-box', 2), ('.stat-box .stat-value', 2),
                   ('.stat-box .stat-label', 1)):
        cr = drop_rule(cr, sel, 'CR: %s dies with the band' % sel, n)

    # THE WHOLE PRINT BLOCK, because the print round already emptied it.
    #
    # `.report-header` opens THREE times in this file - the block itself,
    # this print rule, and a phone layout - so drop_rule(.report-header)
    # would take all three and silently delete the phone layout too. That is
    # "occurrences counted as rules" in its most expensive form.
    #
    # And the rule is not cut alone. THE PRINT ROUND WROTE DOWN THAT THIS
    # ROUND WOULD COME: its note lists everything that moved to base and
    # ends "The banner's fill is the one thing base cannot know about, so it
    # is the one thing left. It goes when the banner round takes the
    # banner." With the fill gone the block holds nothing, so the block goes
    # - which is what that note asked for. Four times this week a guard this
    # project wrote NAMED the round that would invalidate it; this is the
    # same habit paying off in the useful direction.
    _pblock = re.search(r'(?s)@media print \{.*?\n\}\n\n', cr)
    if _pblock is None or 'print-color-adjust' not in _pblock.group(0):
        sys.exit('! CR: the print block is not the one this round measured')
    if re.search(r'(?m)^\s*\.(?!report-header\b)[a-z-]+[^{\n]*\{',
                 re.sub(r'/\*.*?\*/', '', _pblock.group(0), flags=re.S)):
        sys.exit('! CR: the print block has gained a rule since the survey - '
                 'it is no longer empty once the banner fill goes, re-read it')
    cr = sub1(cr, _pblock.group(0), '',
              'CR: the print block the print round emptied')

# ===========================================================================
# SELF-CHECK - before a byte is written. PER FILE.
# ===========================================================================
BCSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', load(BASE)[2], re.S))
for need in ('.alv-stat', '.alv-stat-value', '.alv-stat-label',
             '.page-action-buttons'):
    want(need in BCSS, 'base does not define %s' % need)

# THE CLAIM IS ABOUT THE BANNER, SO THE CHECK IS ABOUT THE BANNER.
#
# The first draft asked each file for NO teal anywhere, and all three failed
# on a correct patch - because each also carries a MODAL header with the same
# gradient, which this round deliberately leaves for the modal round, plus
# legitimate accent on links, badges and focus rings. A check that fails a
# correct patch is not a strict check, it is a wrong one: it was measuring
# the whole file when the round is about one block. What is left over is
# REPORTED with a floor instead, so the next round inherits a number rather
# than a surprise.
BANNER = {'occupancy_trends': '.page-header',
          'notification_settings': '.settings-header',
          'comments_report': '.report-header'}
LEFT = {}
for name, txt in (('occupancy_trends', ot), ('notification_settings', ns),
                  ('comments_report', cr)):
    nc = COMMENT.sub('', re.sub(r'<!--.*?-->', '', txt, flags=re.S))
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', nc, re.S))
    mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', nc, flags=re.S)

    sel = BANNER[name]
    band = [m.group(0) for m in
            re.finditer(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{[^{}]*\}',
                        css)]
    want(band, '%s: %s has no rule left at all' % (name, sel))
    for b in band:
        want('linear-gradient' not in b, '%s: the band is still a gradient' % name)
        want(not re.search(r'#0e7c8b|#0a5e6a', b),
             '%s: the band still spells the teal' % name)
        want(not re.search(r'background', b),
             '%s: the band still paints a background' % name)
        want(not re.search(r'color:\s*(?:white|#fff\b)', b),
             '%s: the band still assumes a dark ground' % name)
    # Nothing INSIDE the banner may still be painted for a dark ground.
    for m3 in re.finditer(r'(?m)^[ \t]*' + re.escape(sel)
                          + r'[ \t][^{\n]*\{([^{}]*)\}', css):
        want(not re.search(r'color:\s*(?:white|#fff\b)|opacity:\s*0\.9',
                           m3.group(1)),
             '%s: a rule inside the band still dresses for teal' % name)
    LEFT[name] = len(re.findall(r'#0e7c8b|#0a5e6a', css))

    f = tag_fault(txt)
    want(f is None, '%s: the template will not parse - %s' % (name, f))
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', txt, re.S):
        want(blk.count('{') == blk.count('}'), '%s: unbalanced braces' % name)
    for m2 in COMMENT.finditer(txt):
        want(not re.search(r'</?(?:script|style)\b', m2.group(0)),
             '%s: a CSS comment spells a script or style tag' % name)
    want('THE TEAL BANNER WENT' in txt, '%s: the round is not explained' % name)

# --- occupancy_trends -------------------------------------------------------
_ot_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', ot, flags=re.S)
_ot_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                               COMMENT.sub('', ot), re.S))
want('class="page-action-buttons"' in _ot_mk,
     'OT: the row did not join the standard')
want('action-bar' not in _ot_mk, 'OT: the old row name survives in markup')
want(not re.search(r'(?m)^[ \t]*\.action-bar\b', _ot_css),
     'OT: a local .action-bar rule survives')
# ON THE ACTION ROW, not in the file. `btn-info` is also what the page's Help
# MODAL uses, and that modal is the next round's business - asking the whole
# file would fail a correct patch.
_ot_row = re.search(r'<div class="page-action-buttons">(.*?)</div>\s*\n',
                    _ot_mk, re.S)
want(_ot_row is not None, 'OT: the action row cannot be found to check')
want(_ot_row is not None and 'btn-info' not in _ot_row.group(1)
     and 'btn-secondary' not in _ot_row.group(1),
     'OT: a Bootstrap colour class survives on the action row')

# --- notification_settings --------------------------------------------------
_ns_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', ns, flags=re.S)
_ns_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                               COMMENT.sub('', ns), re.S))
want('class="page-action-buttons"' in _ns_mk, 'NS: the row did not move out')
want('settings-header-actions' not in _ns_mk,
     'NS: the band still holds the actions')
want('help-btn' not in _ns_mk, 'NS: the bespoke white-on-teal button survives')
# The rules that DIED with the band, named individually. `.settings-header h2`
# and `.settings-header p` are kept - they size the title - so a blanket
# "no descendant survives" fails a correct patch.
for _dead in ('.settings-header-text', '.settings-header-actions',
              '.settings-header .help-btn'):
    want(not re.search(r'(?m)^[ \t]*' + re.escape(_dead) + r'\b', _ns_css),
         'NS: %s survives the band it only made sense inside' % _dead)
want(re.search(r'(?m)^[ \t]*\.settings-header h2\b', _ns_css) is not None,
     'NS: the title rule was deleted along with the band\'s furniture')
# THE TONES ARE NOT THIS ROUND'S BUSINESS. Help keeps the class the button
# sweep gave it; a draft that changed it was refused by test_button_sweep.py,
# correctly. Asserted so the next draft does not quietly try again.
_help = re.search(r'<button[^>]*admin_notification_settingsHelpModal[^>]*>',
                  _ns_mk)
want(_help is not None and 'action-secondary' in _help.group(0),
     'NS: Help changed tone - that is the button sweep\'s call, and the '
     'phone-visibility fault behind it belongs in base, not here')
_oth = re.search(r'<button[^>]*occupancy_trendsHelpModal[^>]*>', _ot_mk)
want(_oth is not None and 'action-secondary' in _oth.group(0),
     'OT: Help changed tone - same as above')

# --- comments_report --------------------------------------------------------
_cr_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', cr, flags=re.S)
_cr_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                               COMMENT.sub('', cr), re.S))
want('alv-stat-value' in _cr_mk and 'alv-stat-label' in _cr_mk,
     'CR: the figure is not base\'s stat')
want('stat-box' not in _cr_mk, 'CR: the old tile survives in markup')
want(not re.search(r'(?m)^[ \t]*\.stat-box\b', _cr_css),
     'CR: a .stat-box rule survives')
want('print-color-adjust' not in _cr_css,
     'CR: the print fallback for a band that no longer exists survives')
want(_cr_css.count('.report-header {') == 0 or
     not re.search(r'\.report-header \{[^}]*background', _cr_css),
     'CR: .report-header still paints a background')
want('page-action-buttons' in _cr_mk,
     'CR: the action row this round did NOT touch has gone missing')

# THE DELTA. Against the backups when they exist, so a second run is measured
# against the pre-round file rather than against itself.
for p, txt, tag in ((OT, ot, 'OT'), (NS, ns, 'NS'), (CR, cr, 'CR')):
    bak = p + '.bak_banner'
    before = load(bak)[2] if os.path.exists(bak) else load(p)[2]
    wascss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                  COMMENT.sub('', before), re.S))
    want('linear-gradient(135deg, #0e7c8b' in wascss,
         '%s: the backup does not look like the pre-round file' % tag)

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
    bak = p + '.bak_banner'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(OT, OT_ORIG, OT_CRLF, ot, OT_DONE)
save(NS, NS_ORIG, NS_CRLF, ns, NS_DONE)
save(CR, CR_ORIG, CR_CRLF, cr, CR_DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
