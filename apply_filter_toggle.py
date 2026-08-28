#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Give every filter panel one owner, and move its control into the action bar.

WHAT THIS IS NOT: it is not a new feature. Eight of the nine pages already
toggle their filter panel from a chevron in the panel header. What they do NOT
have is one mechanism - four of them carry SEVEN separate recordings of the
same boolean (a class, a second class, an inline style.cssText, a data-
attribute, a sessionStorage key, a window global, a module global), each added
because the previous one failed to stick.

This round:
  - base.html gains .alv-filter (visibility), .action-filter (the button) and
    .alv-filter-active (the chips row), plus ONE script.
  - each page's panel gains the class .alv-filter BESIDE its existing
    .filter-panel, so every page-local rule keyed to the old name keeps
    working - print and mobile included. That is the friday_status_report
    precedent from the button sweep: ADD the name, never swap it.
  - the chips move OUT of the panel. This is the whole safety argument: a
    closed panel must never mean invisible filtering.
  - the seven mechanisms go.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
CHECK = '--check' in sys.argv
RESTORE = '--restore' in sys.argv

CSS_MARK = '/* ===== ALV-FILTER v1 ====='
JS_MARK  = '/* ===== alv-filter script v1 ====='


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def backup(p, tag='bak_filter'):
    b = p + '.' + tag
    if not os.path.exists(b):          # never overwrite: a backup is a
        shutil.copy2(p, b)             # snapshot of the FIRST run, not the last


def write(p, text):
    backup(p)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)


def braces_balance(css):
    return css.count('{') == css.count('}')


def one(text, needle, what):
    """Assert an anchor appears EXACTLY once. Matching twice has bitten."""
    n = text.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n  %s' % (what, n, needle[:90]))
    return True


# ---------------------------------------------------------------------------
# 1.  base.html  -  the component, and the one script
# ---------------------------------------------------------------------------
COMPONENT_CSS = """/* ====================================================================
   FILTER  -  one class, one owner.
   Replaces .filter-panel / .expanded / .force-expanded / the inline
   display:block !important escalation / four per-page toggle functions.
   ==================================================================== */

/* The panel. Hidden is the DEFAULT STATE, not a class you add - so a page
   that fails to run any JS shows a clean list rather than a sprung-open
   panel. `hidden` beats nothing: it is one class, no !important. */
.alv-filter            { display: none; }
.alv-filter.is-open    { display: block; }

/* The button. NOT .action-secondary: base hides those on a phone
   (`.page-action-buttons .action-secondary { display:none }`) and
   filtering matters MORE on a small screen, not less. Own position
   class, secondary TONE. */
.btn.action-filter {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-radius: var(--alv-radius);
  font-family: var(--alv-font-ui); font-weight: 600; font-size: 14px;
  background: var(--alv-paper);
  border: 1px solid var(--alv-line);
  color: var(--alv-ink);
}
/* Pressed. A toggle with no visible state gets pressed twice. */
.btn.action-filter[aria-pressed="true"] {
  background: var(--alv-accent-soft);
  border-color: var(--alv-accent-line);
  color: var(--alv-accent-ink);
}
/* The count rides the button, so "something is filtering this list" is
   legible from the bar without scrolling to the chips. */
.action-filter-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  border-radius: 9px; font-size: 11.5px; font-weight: 700; line-height: 1;
  background: var(--alv-accent); color: var(--alv-on-accent);
}
.btn.action-filter[aria-pressed="true"] .action-filter-count {
  background: var(--alv-accent-ink);
}
.action-filter-count:empty,
.action-filter-count[data-count="0"] { display: none; }


/* A FILTER MUST SHOW ITS OWN VALUE.
   Bootstrap 4.1.3 pins every control to a FIXED height -
   `.form-control { height: calc(2.25rem + 2px) }`, 38px - while these panels
   set `padding: 10px 14px` on top of it. With border-box that leaves ~14px of
   content box for a 14px font, so the chosen option is shaved off at the
   bottom and "All Properties" loses its descenders.
   Whether it actually clips depends on the font: it does on Segoe UI, it does
   not on the Linux faces this was first rendered against - which is precisely
   why this is fixed by removing the constraint rather than by tuning a number.
   The :not() pair is not decoration; Bootstrap's own selector carries it, and
   without matching that shape this rule loses on specificity, silently. */
.alv-filter select.form-control:not([size]):not([multiple]),
.alv-filter input.form-control,
.alv-filter textarea.form-control { height: auto; }

/* The chips move OUT of the panel. This is the whole safety argument:
   a closed panel must never mean invisible filtering. */
/* Default HIDDEN, shown by a class - not the reverse. Starting visible and
   hiding it in script means a flash of "Active filters:" with nothing after
   it on every page load. */
.alv-filter-active { display: none; }
.alv-filter-active.has-filters {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  margin: -8px 0 16px;
  font-family: var(--alv-font-ui); font-size: 13px;
}
.alv-filter-active-label { color: var(--alv-ink-soft); font-weight: 600; }

@media (max-width: 768px) {
  /* Same treatment Back gets: keep the target, drop the label. */
  .page-action-buttons .action-filter {
    flex: 0 0 auto; width: 44px; height: 38px;
    padding: 0; justify-content: center; gap: 0;
  }
  .page-action-buttons .action-filter .action-filter-label { display: none; }
  /* The count still has to show, or the phone loses the only cue. */
  .page-action-buttons .action-filter .action-filter-count {
    position: absolute; transform: translate(14px, -12px);
  }
  .page-action-buttons .action-filter { position: relative; }
}

@media print {
  .alv-filter, .btn.action-filter { display: none !important; }
  /* The chips DO print - they say what the page you are holding shows. */
  .alv-filter-active.has-filters { display: flex !important; }
}
"""

COMPONENT_JS = """/* ====================================================================
   FILTER  -  one mechanism, replacing seven.
   Before this, four pages each carried: a class, a SECOND class, an
   inline style.cssText, a data- attribute, a sessionStorage key, a
   window global and a module global - all recording one boolean.
   Here the open state is ONE class on the panel. Everything else reads
   it; nothing else writes it.
   ==================================================================== */
(function () {
  var KEY = 'alvFilterOpen';   // one-shot, consumed on read

  function setOpen(btn, panel, open) {
    panel.classList.toggle('is-open', open);
    btn.setAttribute('aria-pressed', open ? 'true' : 'false');
  }

  /* The count is NOT a second source of truth - it is derived from the
     chips, which are what the page already computes. A MutationObserver
     keeps it honest, so no page has to remember to update it. */
  function wireCount(btn) {
    var box = btn.querySelector('.action-filter-count');
    var chips = document.querySelector('.alv-filter-active');
    if (!box || !chips) return;
    function sync() {
      var n = chips.querySelectorAll('.filter-tag').length;
      box.textContent = n ? String(n) : '';
      box.setAttribute('data-count', String(n));
      /* ONE writer for the row's visibility. The pages used to set
         activeFiltersDiv.style.display themselves; that line is removed, or
         we would be back to two things recording one fact. */
      chips.classList.toggle('has-filters', n > 0);
    }
    sync();
    try { new MutationObserver(sync).observe(chips, {childList: true, subtree: true}); }
    catch (e) { /* no observer: the count is stale, the chips are not */ }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.action-filter');
    if (!btn) return;
    var panel = document.getElementById(btn.getAttribute('aria-controls'));
    if (!panel) return;

    /* WHY A FLAG AT ALL. The filter form SUBMITS - changing a dropdown or
       clearing a chip reloads the page. Without this the panel shuts under
       you every time you adjust one field, which is the problem the seven
       mechanisms above were all failing to solve. It is one-shot: consumed
       on read, so a genuine fresh visit starts closed. */
    var reopen = false;
    try {
      reopen = sessionStorage.getItem(KEY) === '1';
      sessionStorage.removeItem(KEY);
    } catch (e) { /* private mode: the panel starts closed, which is the default anyway */ }
    setOpen(btn, panel, reopen);
    wireCount(btn);

    btn.addEventListener('click', function () {
      setOpen(btn, panel, !panel.classList.contains('is-open'));
    });

    function remember() {
      try { if (panel.classList.contains('is-open')) sessionStorage.setItem(KEY, '1'); }
      catch (e) {}
    }
    /* Exactly two things reload the page as part of filtering. Not
       beforeunload - that would make the panel follow you around the app,
       which is persistence we deliberately did not want. */
    var form = panel.querySelector('form');
    if (form) form.addEventListener('submit', remember);
    var chips = document.querySelector('.alv-filter-active');
    if (chips) chips.addEventListener('click', function (e) {
      if (e.target.closest('.remove-tag')) remember();
    });
  });
})();
"""


def patch_base(text):
    """Add the CSS to the standard block and the script before </body>."""
    n = 0
    if CSS_MARK not in text:
        # The component goes at the END of the last <style> in base.html, so it
        # sits after the table standard and the action bar - both of which it
        # references by token. Inserting it earlier would work today and break
        # the day a token moves.
        i = text.rfind('</style>')
        if i < 0:
            sys.exit('! base.html has no </style> to append to')
        text = text[:i] + '\n' + CSS_MARK + ' */\n' + COMPONENT_CSS + '\n' + text[i:]
        n += 1
    if JS_MARK not in text:
        # BEFORE </body>, not in <head>: the script binds to elements, and a
        # DOMContentLoaded handler registered in <head> is fine but the whole
        # rest of base.html puts its scripts here. Consistency is worth more
        # than the microsecond.
        i = text.rfind('</body>')
        if i < 0:
            sys.exit('! base.html has no </body>')
        text = (text[:i] + '<script>\n' + JS_MARK + ' */\n' + COMPONENT_JS
                + '</script>\n' + text[i:])
        n += 1
    return text, n


# ---------------------------------------------------------------------------
# 2.  the pages
# ---------------------------------------------------------------------------
# The button. aria-controls names the panel, which is how the one script in
# base.html finds it - no per-page wiring, no id convention to remember.
BUTTON = ('<button type="button" class="btn action-filter" id="filterBtn"\n'
          '              aria-pressed="false" aria-controls="%s"\n'
          '              aria-label="Show filters">\n'
          '        <i class="fas fa-filter"></i>'
          '<span class="action-filter-label"> Filter</span>'
          '<span class="action-filter-count" data-count="0"></span>\n'
          '      </button>\n\n')


def bar_span(text):
    """(start, end) of the .page-action-buttons element.

    Counts <div>/</div>. The Tenants round lost an afternoon to a regex that
    matched a closing tag at a fixed indentation and sailed past the element
    it was supposed to stop at.
    """
    m = re.search(r'<div class="[^"]*page-action-buttons[^"]*"', text)
    if not m:
        return None, None
    d = 0
    for mm in re.finditer(r'<div\b|</div\s*>', text[m.start():]):
        d += 1 if mm.group(0).startswith('<div') else -1
        if d == 0:
            return m.start(), m.start() + mm.end()
    return m.start(), None


def add_bar_button(fname, text, panel_id):
    if 'class="btn action-filter"' in text:
        return text, 0
    a, z = bar_span(text)
    if a is None or z is None:
        sys.exit('! %s: no action bar to put the Filter button in' % fname)
    seg = text[a:z]
    # Before the More wrapper if there is one, else before Back. Order in the
    # DOM is layout: Back is pushed right by margin-left:auto, which only
    # works while Back comes last.
    for anchor in ('<div class="action-more-wrapper">',
                   '<a href="{% url \'home\' %}" class="btn action-back"',
                   '<a href="{% url \'personal_page\' %}" class="btn action-back"',
                   '<a href="{% url \'invoices\' %}" class="btn action-back"',
                   'class="btn action-back"'):
        i = seg.find(anchor)
        if i >= 0:
            break
    else:
        sys.exit('! %s: found no anchor in the bar to insert before' % fname)
    # Rewind to the start of that element's own line, then PAST any comment
    # sitting directly above it. Without the second step the button lands
    # under `<!-- Mobile-only "More" dropdown -->`, and that comment starts
    # describing the wrong element - a small thing that makes the next person
    # reading this file believe something false.
    j = seg.rfind('\n', 0, i) + 1
    indent = seg[j:i]
    prev_start = seg.rfind('\n', 0, max(0, j - 1)) + 1
    prev = seg[prev_start:j].strip()
    if prev.startswith('<!--') and prev.endswith('-->'):
        j = prev_start
    btn = (BUTTON % panel_id).replace('\n      ', '\n' + indent)
    seg = seg[:j] + indent + btn.lstrip() + seg[j:]
    return text[:a] + seg + text[z:], 1


def name_the_panel(fname, text, panel_cls):
    """ADD .alv-filter beside the page's own name - never swap it.

    Swapping would orphan every page-local rule keyed to .filter-panel,
    including the ones supplying its background, border and padding, and
    including any @media print block. That mistake cost a round on
    friday_status_report.html during the button sweep: replacing
    .header-actions fixed the tone and silently started printing the buttons.
    """
    old = '<div class="%s"' % panel_cls
    if 'class="alv-filter ' in text:
        return text, 0
    one(text, old, fname + ' panel')
    return text.replace(old, '<div class="alv-filter %s"' % panel_cls), 1


def element_span(text, start):
    """(start, end) of the <div> whose opening tag begins at `start`."""
    d = 0
    for mm in re.finditer(r'<div\b|</div\s*>', text[start:]):
        d += 1 if mm.group(0).startswith('<div') else -1
        if d == 0:
            return start, start + mm.end()
    return start, None


def move_chips_out(fname, text, chips_id, chips_cls='active-filters'):
    """Lift the active-filter chips out of the panel, to just below the bar.

    THIS IS THE POINT OF THE ROUND, not a tidy-up. The chips are currently
    INSIDE .filter-content, inside the panel, on all eight pages - so hiding
    the panel would hide the only on-screen evidence that a list is filtered.
    I told the user the opposite and was wrong; the check that told me so had
    started counting <div>s from the id= attribute rather than the <div> tag
    and closed the span 638 characters into a 2,500-character element.
    """
    m = re.search(r'<div class="%s"[^>]*id="%s"[^>]*>' % (chips_cls, chips_id), text)
    if m is None:
        if 'alv-filter-active' in text:
            return text, 0                      # already moved
        sys.exit('! %s: no chips div with id=%s' % (fname, chips_id))
    a, z = element_span(text, m.start())
    if z is None:
        sys.exit('! %s: the chips div does not close' % fname)
    block = text[a:z]
    if '<input' in block or '<select' in block:
        sys.exit('! %s: the chips block holds a form control - moving it out '
                 'of the <form> would stop it submitting. Stopping.' % fname)
    # take it out, tidy the blank line it leaves
    rest = text[:a] + text[z:]
    rest = re.sub(r'\n[ \t]*\n[ \t]*\n', '\n\n', rest, count=1)
    # ... and put it back directly after the action bar
    ba, bz = bar_span(rest)
    if bz is None:
        sys.exit('! %s: no action bar to hang the chips under' % fname)
    block = block.replace('class="%s"' % chips_cls, 'class="alv-filter-active"', 1)
    # STRIP THE WHOLE style ATTRIBUTE, not a literal `display: none`.
    # projects/projects.html carries a TEMPLATED one -
    #   style="{% if not request.GET.search ... %}display: none;{% endif %}"
    # - which a literal match sails straight past, leaving an inline
    # display:none that beats base.html's class and pins the chips row shut
    # for ever. base.html owns this row's visibility now, so a page-side
    # style attribute on it is by definition a second writer.
    head_end = block.index('>') + 1
    head = re.sub(r'\s*style="[^"]*"', '', block[:head_end], count=1)
    if 'style=' in head:
        sys.exit('! %s: could not strip the style attribute from the chips '
                 'row - it would stay hidden. Stopping.' % fname)
    block = head + block[head_end:]
    return rest[:bz] + '\n\n    ' + block.strip() + rest[bz:], 1


def strip_header_toggle(fname, text, toggle_fn, icon_id):
    """The header stops being the control. Its Clear All button stays."""
    n = 0
    for pat in (' onclick="%s()"' % toggle_fn,):
        if pat in text:
            text = text.replace(pat, '', 1); n += 1
    # the chevron goes with it - it pointed at a gesture that no longer exists
    m = re.search(r'\s*<i class="fas fa-chevron-down[^"]*"[^>]*id="%s"[^>]*></i>'
                  % icon_id, text)
    if m:
        text = text[:m.start()] + text[m.end():]; n += 1
    return text, n


# ---------------------------------------------------------------------------
# 3.  CSS  -  drop what base owns now, REWRITE what it does not
# ---------------------------------------------------------------------------
# The distinction matters and has bitten before. `.lease-end-red` was rewritten
# in place during the Tenants round precisely because base.html does not define
# it; a rule nothing replaces must never simply be dropped. Here the trap is
# .filter-panel.expanded, which is where the panel's PADDING lives. Delete it
# as "expanded machinery" and the panel opens with no padding at all.

def css_blocks(text):
    return [(m.start(1), m.end(1)) for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                                        text, re.S)]


def edit_css(fname, text, plan):
    """plan: [(selector-REGEX, action)] where action is one of

         None                  drop the whole rule
         '.new-selector'       keep the declarations, rename the selector
         ('decls', ['display']) keep the rule, drop only those declarations

    The third one exists because `.filter-content { display: none;
    padding-top: 20px }` on invoices.html cannot be handled by the first two:
    drop it and the panel loses its internal spacing, keep it and the content
    stays hidden inside an OPEN panel. The unit that is wrong is the
    declaration, so that is the unit the plan needs to be able to name.


    Regexes, not literal selector strings, because these selectors are long
    and multi-part (`.filter-panel.expanded .filter-content,
    .filter-panel.force-expanded .filter-content`) and a plan built by
    transcribing them by hand is a plan with a typo in it. A pattern that
    matches nothing is REPORTED, never silent - that is the whole guard.
    """
    done = {p: 0 for p, _ in plan}
    out, last = [], 0
    for a, z in css_blocks(text):
        css = text[a:z]
        new, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).strip()
            sel = ' '.join(sel.split())
            hit = [(p, a) for p, a in plan if re.fullmatch(p, sel)]
            if not hit:
                continue
            if len(hit) > 1:
                sys.exit('! %s: selector %r matched %d plan patterns - '
                         'ambiguous, stopping.' % (fname, sel[:60], len(hit)))
            pat, act = hit[0]
            new.append(css[cur:m.start()])
            if isinstance(act, tuple) and act and act[0] == 'decls':
                body = m.group(2)
                for prop in act[1]:
                    body = re.sub(r'(?:^|;)\s*%s\s*:[^;}]*;?' % re.escape(prop),
                                  ';', body, flags=re.I)
                body = re.sub(r';\s*;', ';', body)
                # a leading `;` is legal CSS but reads as damage; strip it
                body = re.sub(r'^(\s*);', r'\1', body)
                new.append('%s{%s}' % (m.group(1), body))
            elif act is not None:
                # REWRITE: keep the declarations, change only the selector.
                # Replacing to the end of the RULE rather than the end of the
                # SELECTOR is how tenant_report.html ended up with a dangling
                # selector that closed its @media early.
                lead = m.group(1)[:len(m.group(1)) - len(m.group(1).lstrip())]
                new.append('%s%s {%s}' % (lead, act, m.group(2)))
            cur = m.end()
            done[pat] += 1
        if new:
            new.append(css[cur:])
            out.append(text[last:a]); out.append(''.join(new)); last = z
    text = ''.join(out) + text[last:]
    missing = [k for k, v in done.items() if v == 0]
    return text, sum(done.values()), missing


# ---------------------------------------------------------------------------
# 4.  JS  -  the seven mechanisms
# ---------------------------------------------------------------------------
def drop_function(js, name):
    """Remove `function NAME(...) { ... }` by counting braces, not by regex.

    The filter functions are interleaved with unrelated ones in the same
    <script> block - toggleFilters sits beside initializeMoreMenu and
    viewTitleDeed - so there is no block to delete and no lazy match that is
    safe.
    """
    m = re.search(r'\n[ \t]*function\s+%s\s*\([^)]*\)\s*\{' % re.escape(name), js)
    if not m:
        return js, 0
    d, i = 0, m.end() - 1
    while i < len(js):
        if js[i] == '{':
            d += 1
        elif js[i] == '}':
            d -= 1
            if d == 0:
                return js[:m.start()] + js[i + 1:], 1
        i += 1
    sys.exit('! function %s does not close - refusing to guess where' % name)


# A DECLARATION IS NOT A STATEMENT YOU CAN DELETE.
#
# `const wasForceExpanded = sessionStorage.getItem('FORCE_...') === 'true';`
# matches the dead-statement pattern for those storage keys - but deleting it
# leaves `if (wasForceExpanded || ...)` two lines down referencing nothing.
# That is a ReferenceError on the FIRST line of the DOMContentLoaded handler,
# so every listener registered after it - search, the country dropdown, Enter,
# Clear All - is never attached. The panel toggled perfectly and the page
# stopped filtering, which is exactly how this shipped.
#
# The correct edit is not deletion. It is to keep the name and make the value
# permanently false, so every condition built on it is dead and every
# reference still resolves.
DECL_REWRITES = [
    (r"((?:const|let|var)\s+\w+\s*=\s*)sessionStorage\.getItem\(\s*"
     r"['\"](?:\w*FORCE_|\w*CLEAR_ALL_PROTECTION)[^;]*;", r"\1false;"),
    (r"((?:const|let|var)\s+\w+\s*=\s*)window\.\w*"
     r"(?:PANEL_MUST_STAY_EXPANDED|CLEAR_ALL_PROTECTION_ACTIVE)\w*\s*;",
     r"\1false;"),
]


def drop_statements(js, patterns):
    """Remove whole LINES matching any pattern. Used for the leftovers that
    live inside functions that must survive - clearFilter still has to clear a
    filter, it just no longer has to force a panel open six ways."""
    n = 0
    keep = []
    declared_gone = set()
    for line in js.splitlines(True):
        if any(re.search(p, line) for p in patterns):
            # If this line DECLARES something, remember the name. Deleting a
            # declaration is fine when nothing reads it any more - which is
            # true of PANEL_IS_MANUALLY_EXPANDED, because drop_if_blocks
            # removes its readers a step later - and fatal when something
            # still does. The rule is not "never delete a declaration"; it is
            # "never leave a reference without one", and that can only be
            # judged AFTER every edit. So: record now, verify at the end.
            d = re.search(r'(?:const|let|var)\s+(\w+)\s*=', line)
            if d:
                declared_gone.add(d.group(1))
            n += 1
            continue
        keep.append(line)
    return ''.join(keep), n, declared_gone


# Some leftovers are READS, not writes, and they sit inside functions that
# have to survive - `const isOpen = filterPanel.classList.contains('expanded')
# || filterPanel.classList.contains('force-expanded');`. Deleting that line
# breaks the declaration it belongs to. Rewriting the expression keeps the
# statement valid and points it at the one class that now means anything.
REWRITES = [
    (r"\w+\.classList\.contains\('expanded'\)\s*\|\|\s*"
     r"(\w+)\.classList\.contains\('force-expanded'\)",
     r"\1.classList.contains('is-open')"),
]

DEAD_STATEMENTS = [
    r"classList\.(?:add|remove)\([^)]*['\"]force-expanded['\"]",
    r"style\.cssText\s*\+=",
    r"(?:set|remove)Attribute\(\s*['\"]data-force-expanded",
    r"sessionStorage\.(?:set|get|remove)Item\(\s*['\"]FORCE_",
    r"window\.\w*(?:PANEL|EXPANDED)\w*\s*=",
    r"(?:let|var|const)\s+PANEL_IS_MANUALLY_EXPANDED",
    r"\bPANEL_IS_MANUALLY_EXPANDED\s*=",
    r"className\s*=\s*\w+\.className\.replace\(",
    # base.html toggles .has-filters now; a page that also writes
    # style.display is a second writer for one fact.
    r"[Aa]ctiveFilters(?:Div)?\.style\.display\s*=",
    r"\blockPanelState\(\)",
    r"LOCKING PANEL STATE",
    r"\bsetupInterferenceProtection\(\)",
    # NOT EXTERNAL_INTERFERENCE_DETECTED. It appears as
    #   setInterval(() => { if (EXTERNAL_INTERFERENCE_DETECTED) { ... } }, 2000)
    # and deleting that `if (...) {` LINE orphans its closing brace. The whole
    # <script> then failed to parse, so every function in it - all of fsr's
    # filter wiring - simply did not exist. The page looked perfect and
    # filtered nothing.
    #
    # The variable is declared `= false` and nothing sets it true any more
    # (the two functions that did are gone), so leaving it costs an inert
    # branch and buys a file that parses. Deleting a line from the middle of
    # a block is never worth that trade.
    # every prefix of the same two ideas: "force this panel open" and
    # "protect it from being closed". Six storage keys and six window
    # globals across four pages, all saying what one class now says.
    r"sessionStorage\.\w+Item\(\s*['\"](?:\w*FORCE_|\w*CLEAR_ALL_PROTECTION)",
    r"window\.\w*(?:PANEL_MUST_STAY_EXPANDED|CLEAR_ALL_PROTECTION_ACTIVE)\w*\s*=",
]


def drop_if_blocks(js, var):
    """Remove `if (... var ...) { ... }` blocks whose bodies are now inert.

    Removing the DECLARATION of a global and leaving the READS is worse than
    leaving both: `if (PANEL_IS_MANUALLY_EXPANDED)` against an undefined
    variable is a ReferenceError, which takes out the rest of the handler it
    sits in. So the block goes as a unit - but only after asserting there is
    nothing left in it worth keeping, because "delete the if" is otherwise a
    licence to delete behaviour nobody looked at.
    """
    n = 0
    while True:
        m = re.search(r'\n[ \t]*if\s*\([^)]*\b%s\b[^)]*\)\s*\{' % re.escape(var), js)
        if not m:
            return js, n
        d, i = 0, m.end() - 1
        while i < len(js):
            if js[i] == '{':
                d += 1
            elif js[i] == '}':
                d -= 1
                if d == 0:
                    break
            i += 1
        else:
            sys.exit('! an if(%s) block does not close' % var)
        body = js[m.end():i]
        # inert = whitespace, comments, and lookups whose results are unused
        residue = re.sub(r'/\*.*?\*/|//[^\n]*', '', body, flags=re.S)
        residue = re.sub(r'(?:const|let|var)\s+\w+\s*=\s*document\.'
                         r'getElementById\([^)]*\)\s*;?', '', residue)
        # An if whose body the gutting emptied is itself inert. Repeat until
        # stable, because these nest: `if (X) { if (filterPanel) { } }`.
        prev = None
        while prev != residue:
            prev = residue
            residue = re.sub(r'if\s*\([^()]*\)\s*\{\s*\}', '', residue)
            residue = re.sub(r'\{\s*\}', '', residue)
        if residue.strip():
            sys.exit('! an if(%s) block still has live code in it - refusing '
                     'to delete behaviour nobody looked at:\n   %s'
                     % (var, ' '.join(residue.split())[:200]))
        js = js[:m.start()] + js[i + 1:]
        n += 1


def delims(js):
    """(braces, parens, brackets) net balance, ignoring strings and comments.

    Not a parser - it does not need to be. It is compared BEFORE and AFTER on
    the same text, so what matters is that it counts the same way twice. Any
    change in the net balance means an edit cut through a block.
    """
    b = p = k = 0
    i, n = 0, len(js)
    while i < n:
        c = js[i]
        if c in '"\'`':
            q, i = c, i + 1
            while i < n and js[i] != q:
                i += 2 if js[i] == '\\' else 1
        elif c == '/' and i + 1 < n and js[i + 1] == '/':
            while i < n and js[i] != '\n':
                i += 1
        elif c == '/' and i + 1 < n and js[i + 1] == '*':
            i = js.find('*/', i + 2)
            i = n if i < 0 else i + 1
        else:
            if c == '{': b += 1
            elif c == '}': b -= 1
            elif c == '(': p += 1
            elif c == ')': p -= 1
            elif c == '[': k += 1
            elif c == ']': k -= 1
        i += 1
    return b, p, k


def edit_js(fname, text, drop_fns):
    n = 0
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<script[^>]*>(.*?)</script>', text, re.S)][::-1]:
        js = text[a:z]
        if JS_MARK in js:
            continue                      # never edit the component's own script
        before = js
        for pat, rep in DECL_REWRITES + REWRITES:
            js, k = re.subn(pat, rep, js); n += k
        for fn in drop_fns:
            js, k = drop_function(js, fn)
            n += k
            # AND ITS CALL SITES. Dropping a definition and leaving the calls
            # is the same fault as dropping a declaration and leaving the
            # reads: `expandFilterPanel()` against nothing is a
            # ReferenceError that takes out the rest of its handler. The call
            # expression goes, not the whole line - `setTimeout(() => {
            # expandPassportFilterPanel(); }, 100)` must survive as a
            # harmless empty timeout rather than losing its statement.
            # A CALL IN STATEMENT POSITION CAN BE DELETED. A CALL IN AN
            # EXPRESSION CANNOT - deleting it leaves a hole. `if
            # (checkForActiveFilters()) {` became `if () {`, which does not
            # parse, which killed the whole <script>, which meant invoices
            # had no filter wiring at all. Balanced parens, so the delimiter
            # check above saw nothing wrong.
            #
            # So: whole-line calls go; anything else becomes `false`, which
            # is the right answer for every one of these - they were all
            # predicates asking "should the panel be open?", and the answer
            # is now decided by base.html.
            js, k2 = re.subn(r'^[ \t]*%s\s*\(\s*\)\s*;?[ \t]*\n'
                             % re.escape(fn), '', js, flags=re.M)
            js, k3 = re.subn(r'\b%s\s*\(\s*\)' % re.escape(fn), 'false', js)
            n += k2 + k3
        js, k, orphan_risk = drop_statements(js, DEAD_STATEMENTS); n += k
        # AFTER the gutting, so the emptiness of each body is evidence.
        js, k = drop_if_blocks(js, 'PANEL_IS_MANUALLY_EXPANDED'); n += k
        # THE VERIFICATION THAT WAS MISSING. Every name whose declaration was
        # deleted must be gone from the file entirely. `wasForceExpanded` was
        # not - its declaration matched a dead-statement pattern while the
        # `if` two lines below still used it - and the page threw on the first
        # line of DOMContentLoaded, so not one filter listener was attached.
        for name in sorted(orphan_risk):
            if re.search(r'\b%s\b' % re.escape(name), js):
                sys.exit('! %s: the declaration of `%s` was removed but '
                         'something still references it. That is a '
                         'ReferenceError, and it would take out every '
                         'statement after it.' % (fname, name))
        if js != before:
            # NESTING MUST SURVIVE THE EDIT. drop_statements works on whole
            # LINES, and a line can be the opening of a block - remove it and
            # its closing brace is orphaned, the <script> stops parsing, and
            # EVERY function in it ceases to exist. That is not a subtle
            # failure: the page renders perfectly and does nothing. It is
            # also completely invisible to a checker that only looks for
            # undefined names, because nothing ever runs to be undefined.
            if delims(js) != delims(before):
                sys.exit('! %s: an edit changed the nesting of a <script> '
                         'block (braces/parens/brackets %s -> %s). Something '
                         'was cut out of the middle of a block. Stopping.'
                         % (fname, delims(before), delims(js)))
            text = text[:a] + js + text[z:]
    return text, n


# ---------------------------------------------------------------------------
# 5.  the page registry  -  named, one at a time, from the real markup
# ---------------------------------------------------------------------------
# Eight pages is a listable number, and the eight are NOT the same shape:
# function names differ (toggleFilters / toggleFilterPanel /
# togglePassportFilterPanel), one page prefixes everything, two carry no
# toggle at all. A rule broad enough to catch all eight would be broad enough
# to catch something nobody looked at.

_DROP_COMMON = [
    (r'\.filter-panel:not\(\.expanded\) \.filter-content', None),
    (r'\.filter-panel\.expanded \.filter-content, ?\.filter-panel\.force-expanded \.filter-content', None),
    (r'\.filter-panel\.force-expanded', None),
    (r'\.filter-panel\.force-expanded \.filter-content', None),
    (r'\.filter-toggle-icon', None),
    (r'\.filter-toggle-icon\.rotated', None),
    (r'\.filter-content\.show', None),
    (r'\.filter-header\.expanded:hover', None),
    (r'\.filter-header:hover', None),
    # REWRITTEN, not dropped: this is where the panel's padding lives.
    (r'\.filter-panel\.expanded', '.filter-panel'),
    (r'\.filter-header\.expanded', '.filter-header'),
]

_STD = dict(panel_cls='filter-panel', panel_id='filterPanel',
            chips_id='activeFilters', toggle_fn='toggleFilters',
            icon_id='filterToggleIcon',
            drop_fns=['forceExpandPanel', 'toggleFilters',
                      # a MutationObserver that watched the panel's class
                      # attribute and put `expanded` BACK whenever anything
                      # removed it - a watchdog fighting the other nine.
                      'setupInterferenceProtection'],
            css=_DROP_COMMON)


def _std(**kw):
    d = dict(_STD); d.update(kw); return d


PAGES = {
    # Six pages are the same shape as the pilot, verbatim.
    'suppliers.html':  _std(),
    'properties.html': _std(),
    'tenant.html':     _std(),
    # invoices and projects never had force-expanded either, and each hides
    # its content in its own way. Written from the real selector list, not
    # from the assumption that "the same shape" meant "the same CSS".
    'invoices.html': _std(
        drop_fns=['checkForActiveFilters', 'toggleFilters'],
        css=[
            (r'\.filter-toggle-icon', None),
            (r'\.filter-toggle-icon\.rotated', None),
            (r'\.filter-content\.show', None),
            # keep padding-top, lose the display gate
            (r'\.filter-content', ('decls', ['display'])),
            (r'\.filter-panel\.expanded', '.filter-panel'),
        ]),
    'projects/projects.html': _std(
        drop_fns=['toggleFilters'],
        css=[
            (r'\.filter-toggle-icon', None),
            (r'\.filter-toggle-icon\.rotated', None),
            (r'\.filter-content\.show', None),
            # AND the display gate itself. Dropping only `.show` left
            # `.filter-content { ...; display: none }` standing, so the panel
            # opened to reveal its own header and nothing else. The rule that
            # HIDES has to go with the rule that showed it - always both, or
            # neither. Keeps padding-top, border-top and margin-top.
            (r'\.filter-content', ('decls', ['display'])),
        ]),
    # fsr has a FOURTH selector shape the others do not: its mobile padding
    # sits on a COMBINED rule, `.filter-panel.expanded, .filter-panel
    # .force-expanded`. The common plan matches neither half of that (the
    # patterns fullmatch, deliberately), so without this line fsr would have
    # lost its panel padding on a phone - silently, because no count changes
    # and no tag unbalances when a padding declaration goes.
    # lockPanelState is fsr's EIGHTH mechanism, and the most desperate: it
    # monkey-patches window.hideFilters to a no-op for 100ms so the page
    # cannot close its own panel mid-submit. window.hideFilters was never
    # defined anywhere - all four mentions are inside this function, which
    # saves undefined, replaces it, and restores undefined. It was blocking a
    # call that could not happen. The one-shot flag replaces the whole thing.
    'fsr.html': _std(drop_fns=['forceExpandPanel', 'toggleFilters',
                               'lockPanelState',
                               'setupInterferenceProtection'],
                     css=_DROP_COMMON + [
                         (r'\.filter-panel\.expanded, ?\.filter-panel\.force-expanded',
                          '.filter-panel'),
                     ]),

    # act_expense names its toggle differently and hides the CONTENT rather
    # than gating it on the panel, so it needs its own two lines.
    # act_expense carries ONE of the seven mechanisms, not seven, and gates
    # the content directly rather than through the panel. Handing it the
    # common plan made ten patterns match nothing - which the guard caught.
    'act_expense.html': _std(
        toggle_fn='toggleFilterPanel',
        drop_fns=['expandFilterPanel', 'toggleFilterPanel'],
        css=[
            (r'\.filter-toggle-icon', None),
            # DROP both: base.html owns visibility now, and a content div left
            # at display:none stays hidden inside an OPEN panel.
            (r'\.filter-content', None),
            (r'\.filter-content\.expanded', None),
        ]),

    # passport prefixes every name. It also carries only ONE of the seven
    # mechanisms, which is why it needs the least surgery.
    'passport_management.html': dict(
        panel_cls='passport-filter-panel', panel_id='passportFilterPanel',
        chips_id='passportActiveFilters', chips_cls='passport-active-filters',
        toggle_fn='togglePassportFilterPanel',
        icon_id='passportFilterToggleIcon',
        drop_fns=['expandPassportFilterPanel', 'togglePassportFilterPanel'],
        chip_rename=True,
        css=[
            (r'\.passport-filter-toggle-icon', None),
            # DROP, not rename: base.html owns visibility now, and a content
            # div left at display:none would stay hidden inside an OPEN panel.
            (r'\.passport-filter-content', None),
            (r'\.passport-filter-content\.expanded', None),
        ]),
}

# physical_invoice_list.html is DELIBERATELY out of this round, and the reason
# is not that it is awkward - it is that hiding its panel would be unsafe.
#
# It is the one page with no active-filter chips at all: no .active-filters
# row, no .filter-tag, nothing. Its filter state is legible only from the
# panel itself. Hide that and a filtered list looks like the whole list, which
# is the exact hazard this round exists to avoid - and the reason the chips
# had to come out of the panel everywhere else.
#
# It needs a chips row BEFORE it can have a Filter button. That is one of the
# edits already queued for it in outstanding item 2.2, so it belongs to that
# round, not this one.
NOT_YET = ['physical_invoice_list.html']


# ---------------------------------------------------------------------------
# 6.  self-checks  -  run BEFORE anything is written
# ---------------------------------------------------------------------------
def counts(text):
    css = ''.join(text[a:z] for a, z in css_blocks(text))
    return dict(
        divs_open   = len(re.findall(r'<div\b', text)),
        divs_close  = len(re.findall(r'</div\s*>', text)),
        forms       = len(re.findall(r'<form\b', text)),
        inputs      = len(re.findall(r'<input\b', text)),
        selects     = len(re.findall(r'<select\b', text)),
        gates       = len(re.findall(r'\{%\s*if perms\.', text)),
        urls        = len(re.findall(r'\{%\s*url ', text)),
        css_open    = css.count('{'),
        css_close   = css.count('}'),
    )


def self_check(fname, before, after, panel_cls='filter-panel', drop_fns=()):
    b, a = counts(before), counts(after)
    bad = []
    # The chips move OUT of the panel: div counts must not change, because
    # nothing was created or destroyed - only relocated.
    for k in ('divs_open', 'divs_close', 'forms', 'inputs', 'selects',
              'gates', 'urls'):
        if b[k] != a[k]:
            bad.append('%s changed %d -> %d' % (k, b[k], a[k]))
    if a['css_open'] != a['css_close']:
        bad.append('CSS braces do not balance (%d open, %d close)'
                   % (a['css_open'], a['css_close']))
    if a['divs_open'] != a['divs_close']:
        bad.append('div tags do not balance')
    if len(re.findall(r'class="btn action-filter"', after)) != 1:
        bad.append('expected exactly one Filter button, found %d'
                   % len(re.findall(r'class="btn action-filter"', after)))
    if 'force-expanded' in after:
        bad.append('force-expanded survived')
    if 'filter-toggle-icon' in after:
        bad.append('the chevron survived')
    # the chips must now sit OUTSIDE the panel - the whole point
    pm = re.search(r'<div class="alv-filter [^"]*"', after)
    if pm:
        pa, pz = element_span(after, pm.start())
        cm = re.search(r'<div class="alv-filter-active"', after)
        if cm is None:
            if 'alv-filter-active' in before:
                bad.append('the chips row vanished')
        elif pz and pa < cm.start() < pz:
            bad.append('the chips are STILL inside the panel')
    # THE PANEL MUST STILL HAVE PADDING. On most pages that declaration lives
    # on `.expanded`, which this round removes - so "delete the expanded
    # machinery" and "keep the panel usable" are in direct tension, and the
    # loss would be silent: no count changes, no tag unbalances, nothing
    # throws. A panel that opens with its fields flush against the border is
    # the failure mode, and it is only visible to a person or to this check.
    css_after = ''.join(after[a:z] for a, z in css_blocks(after))
    pad = False
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_after):
        sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        if re.fullmatch(re.escape('.' + panel_cls), sel) and 'padding' in m.group(2):
            pad = True
            break
    if not pad:
        bad.append('.%s no longer declares padding anywhere - the round took '
                   'it with the .expanded rules' % panel_cls)
    # A page with a chips row must speak the component's vocabulary, or the
    # count reads zero and the row never shows.
    if 'alv-filter-active' in after and 'filter-tag' not in after:
        bad.append('the chips row exists but nothing on this page produces a '
                   '.filter-tag - base.html would count zero and never show it')
    # NOTHING MAY STILL CALL WHAT THIS ROUND DELETED. Two pages shipped past
    # every other check here with a live ReferenceError in them, and only a
    # harness that actually RAN the page's scripts noticed.
    for fn in drop_fns:
        if re.search(r'\b%s\s*\(' % re.escape(fn), after):
            bad.append('%s() is gone but something still calls it' % fn)
    for g in ('PANEL_IS_MANUALLY_EXPANDED',):
        if g in after:
            bad.append('%s is gone but something still reads it' % g)
    if bad:
        sys.exit('! %s self-check FAILED, nothing written:\n   - %s'
                 % (fname, '\n   - '.join(bad)))


# ---------------------------------------------------------------------------
# 7.  main
# ---------------------------------------------------------------------------
def main():
    changed = 0

    # --restore puts every .bak_filter back over its live file. Needed because
    # the patcher's "already migrated" guard means a second run is a no-op:
    # once a page carries the Filter button, re-running cannot repair it. So
    # a fix to this script is applied by restoring and re-running, not by
    # running again. The backups themselves are never touched - backup() has
    # always refused to overwrite, so they still hold the pre-round file.
    if RESTORE:
        n = 0
        for r, _d, fs in os.walk(TPL):
            for f in fs:
                if not f.endswith('.bak_filter'):
                    continue
                b = os.path.join(r, f)
                live = b[:-len('.bak_filter')]
                shutil.copy2(b, live)
                n += 1
                print('  restored %s' % os.path.relpath(live, TPL))
        print('\n  %d file(s) restored. Re-run without --restore to apply.' % n)
        return

    bp = os.path.join(TPL, 'base.html')
    src = read(bp)
    out, n = patch_base(src)
    if n:
        print('  base.html            + component CSS and one script')
        if not CHECK:
            write(bp, out)
        changed += 1
    else:
        print('  base.html            already carries the component')

    for fname, cfg in sorted(PAGES.items()):
        p = os.path.join(TPL, fname.replace('/', os.sep))
        if not os.path.exists(p):
            sys.exit('! %s is not on disk' % fname)
        src = read(p)
        # THREE STATES, NOT TWO - and the two-state version cost a run here
        # exactly as it did in apply_button_sweep.py's named_repairs(). A css
        # pattern matching nothing means "this page is not at the stage the
        # plan was written against", which is an ERROR on a fresh page and
        # NORMAL on one already migrated. Telling them apart needs a marker,
        # not a guess: the page either carries the button or it does not.
        if 'class="btn action-filter"' in src:
            print('  %-22s already migrated' % fname)
            continue
        t = src
        t, a = add_bar_button(fname, t, cfg['panel_id'])
        t, b = name_the_panel(fname, t, cfg['panel_cls'])
        c = d = 0
        # Not every page has every part. A page with no chips row is NOT
        # silently fine - see NOT_YET - but a page with no chevron simply has
        # no chevron, and stepping over that is different from ignoring it.
        if cfg.get('toggle_fn'):
            t, c = strip_header_toggle(fname, t, cfg['toggle_fn'], cfg['icon_id'])
        if cfg.get('chips_id'):
            t, d = move_chips_out(fname, t, cfg['chips_id'],
                                  cfg.get('chips_cls', 'active-filters'))
        if cfg.get('chip_rename'):
            # base.html counts `.filter-tag` to drive the count and to decide
            # whether the chips row is shown at all. passport calls its chips
            # `.passport-filter-tag`, so the shared component would have found
            # ZERO on that page and its chips row would never have appeared -
            # on the one page where a hidden panel most needs them. The fix is
            # one vocabulary, not a special case inside the component.
            before_n = len(re.findall(r'\bpassport-filter-tag\b(?!s)', t))
            t = re.sub(r'\bpassport-filter-tag\b(?!s)', 'filter-tag', t)
            if before_n == 0:
                sys.exit('! %s: chip_rename was asked for but nothing '
                         'matched' % fname)
        t, e, missing = edit_css(fname, t, cfg['css'])
        t, f = edit_js(fname, t, cfg['drop_fns'])
        if missing:
            sys.exit('! %s: %d css pattern(s) matched NOTHING:\n   %s\n'
                     '  A plan that half-applies is worse than one that stops: '
                     'the page keeps machinery the round claims it removed.'
                     % (fname, len(missing), '\n   '.join(missing)))
        if t == src:
            print('  %-22s no change' % fname)
            continue
        self_check(fname, src, t, cfg['panel_cls'], cfg['drop_fns'])
        print('  %-22s button:%d panel:%d header:%d chips:%d css:%d js:%d'
              % (fname, a, b, c, d, e, f))
        if not CHECK:
            write(p, t)
        changed += 1

    print('\n  %d file(s) %s' % (changed, 'would change' if CHECK else 'changed'))
    if NOT_YET:
        print('  %d page(s) NOT in this round yet: %s'
              % (len(NOT_YET), ', '.join(NOT_YET)))


if __name__ == '__main__':
    main()
