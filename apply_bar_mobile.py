# -*- coding: utf-8 -*-
"""SECTION H, ROUND H2b - THREE THINGS H2 GOT WRONG ON A PHONE

Found in testing straight after H2 deployed. Three complaints, and MEASURED
they have three different causes - two mine, one much older than this round.

1. THE DASHBOARD BAR OVERFLOWS. Rendered at 390px, H2 left four controls in
   a bar with no More menu:

       action-primary    150x44  CLIPPED
       action-secondary   85x44  CLIPPED
       action-secondary   56x44
       action-back        44x44

   base already answers this - `.page-action-buttons:has(.action-more-btn)
   .action-secondary { display: none }` - so the two secondaries go behind a
   More menu and the phone gets primary + More + Back. celebration_management
   already carries that exact markup; this copies its shape.

2. THE CALENDAR'S BACK SITS ON THE LEFT - AND THAT IS NOT AN H2 REGRESSION.
   base's phone block says:

       .page-action-buttons .action-back { margin-left: 0; ... }

   which is right only while a `.action-primary { flex: 1 1 auto }` is there
   to push Back along. WHEN A BAR HAS NO PRIMARY, NOTHING PUSHES IT. Counted:
   FIFTEEN bars hold a Back and no primary. Measured at 390px, how far Back
   sits from the right edge:

       celebration_calendar        316px adrift
       unit_conversions_wizard     300
       finance, notification_settings  236
       occupancy_trends            220
       passport_management         184
       properties (HAS a primary)    0   correct

   So this predates H2 by a long way, on about thirteen pages; H2 putting the
   calendar's Back into a bar is only what made it visible. The fix is one
   rule in base, using :has(), which base already uses twice.

3. THE SEARCH FIELD IS IN A SHAPE THE HOUSE DOES NOT HAVE. H2 put it above
   the bar as a permanently visible 250px box. Rendered, Properties' and
   Suppliers' search inputs come back 0x0: the house keeps search INSIDE a
   `.alv-filter` panel behind the `.action-filter` button, hidden until it
   is asked for. passport_management does the same.

   base owns that whole mechanism - the panel's `.is-open` class, the button,
   the count, and the script that pairs them through aria-controls - so the
   page needs MARKUP ONLY. searchContacts() is untouched and keeps working.

Backups: .bak_barmobile. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_barmobile'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

# ---- 1. base: a bar with no primary keeps Back on the right --------------
BASE_ANCHOR = """        .page-action-buttons .action-back {
          margin-left: 0;
          flex: 0 0 auto;
          width: 44px;
          height: 44px;
          padding: 0;
        }"""
BASE_ADD = """
        /* A BAR WITH NO PRIMARY HAS NOTHING TO PUSH BACK RIGHT.
           `margin-left: 0` above is correct only while a
           `.action-primary { flex: 1 1 auto }` is in the bar taking the
           slack. Fifteen bars hold a Back and NO primary, and on a phone
           every one of them packed Back hard against its neighbours:
           measured at 390px, celebration_calendar left it 316px from the
           right edge, unit_conversions_wizard 300, finance and
           notification_settings 236, occupancy_trends 220,
           passport_management 184. properties came out at 0 - because it
           HAS a primary.
           Found 27 Sep, reported as "the Back is wrong here" on one page;
           it was wrong on about thirteen. */
        .page-action-buttons:not(:has(.action-primary)) .action-back {
          margin-left: auto;
        }"""

# ---- 2. the dashboard's two secondaries go behind a More menu ------------
DASH_OLD = """    <a href="{% url 'celebration_calendar' %}" class="btn action-secondary">
        <i class="fas fa-calendar-alt"></i> View Events
    </a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#celebration_dashboardHelpModal" title="Help">
            <i class="fas fa-question-circle"></i> Help
        </button>
"""
DASH_NEW = """    <a href="{% url 'celebration_calendar' %}" class="btn action-secondary">
        <i class="fas fa-calendar-alt"></i> View Events
    </a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#celebration_dashboardHelpModal" title="Help">
            <i class="fas fa-question-circle"></i> Help
        </button>

        <!-- MOBILE-ONLY "More": base hides .action-secondary in a bar that
             has a .action-more-btn, so the two above move in here below
             768px and the phone gets primary + More + Back. -->
        <div class="action-more-wrapper">
            <button type="button" class="btn action-more-btn" id="actionMoreBtn"
                    aria-label="More actions" aria-expanded="false" aria-haspopup="true">
                <i class="fas fa-ellipsis-v"></i>
            </button>
            <div class="action-more-menu" id="actionMoreMenu" role="menu" hidden>
                <a href="{% url 'celebration_calendar' %}" class="action-more-item" role="menuitem">
                    <i class="fas fa-calendar-alt"></i> View Events
                </a>
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#celebration_dashboardHelpModal">
                    <i class="fas fa-question-circle"></i> Help
                </button>
            </div>
        </div>
"""

# ---- 3. the search moves into a house filter panel -----------------------
MGMT_SEARCH_OLD = """<div class="toolbar-search">
        <input type="text"
               id="contactSearch"
               class="form-control"
               placeholder="Search contacts..."
               onkeyup="searchContacts()"
               style="width: 250px;">
    </div>"""
# The panel goes AFTER the bar, which is where base's own pages put it.
MGMT_PANEL = """<div class="alv-filter" id="celebrationFilterPanel">
    <div class="filter-group">
        <label class="filter-label" for="contactSearch">
            <i class="fas fa-search"></i> <strong>Search contacts</strong>
        </label>
        <div class="search-input-group">
            <input type="text"
                   id="contactSearch"
                   class="form-control search-input"
                   placeholder="Search contacts..."
                   onkeyup="searchContacts()">
        </div>
    </div>
</div>"""
# The button that opens it, in the bar, before Back.
MGMT_BTN_BEFORE = """        <!-- BACK -->
        <a href="{% url 'celebration_dashboard' %}" class="btn action-back" aria-label="Back to Dashboard">"""
MGMT_BTN_NEW = """        <button type="button" class="btn action-filter" id="filterBtn"
                aria-pressed="false" aria-controls="celebrationFilterPanel"
                aria-label="Show filters">
            <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
        </button>

        <!-- BACK -->
        <a href="{% url 'celebration_dashboard' %}" class="btn action-back" aria-label="Back to Dashboard">"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol_of(text):
    return ((lambda s: s.replace('\n', '\r\n')) if '\r\n' in text
            else (lambda s: s))


def swap(path, pairs, done_when):
    """Exact-count replacements in one file, line endings honoured."""
    text = read(path)
    before = text
    if done_when(text):
        return None                                   # already applied
    eol = eol_of(text)
    for old, new in pairs:
        o, n = eol(old), eol(new)
        if text.count(o) != 1:
            raise SystemExit('H2b: %s - anchor matched %d time(s): %r'
                             % (os.path.basename(path), text.count(o),
                                old[:70]))
        text = text.replace(o, n)
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return before, text


def patch_base():
    path = os.path.join(ROOT, 'base.html')
    r = swap(path, [(BASE_ANCHOR, BASE_ANCHOR + BASE_ADD)],
             lambda t: ':not(:has(.action-primary)) .action-back' in t)
    if r is None:
        return False
    before, text = r
    # the edit is CSS only, and adds exactly one rule
    if re.sub(r'<style[^>]*>.*?</style\s*>', '', before, flags=re.S | re.I) \
            != re.sub(r'<style[^>]*>.*?</style\s*>', '', text,
                      flags=re.S | re.I):
        raise SystemExit('H2b: base.html - the edit reached the markup')
    # COUNT BRACES OUTSIDE COMMENTS. The note added above quotes
    # `.action-primary { flex: 1 1 auto }` to explain WHY the old rule was
    # conditional - and a naive count read that brace as a second rule.
    # A comment is not code (lesson 21), in this direction too.
    nocomment = lambda css: re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    a = nocomment(''.join(STYLE.findall(before))).count('{')
    b = nocomment(''.join(STYLE.findall(text))).count('{')
    if b != a + 1:
        raise SystemExit('H2b: base.html - %d rule(s) added, wanted 1'
                         % (b - a))
    return True


def patch_dashboard():
    path = os.path.join(ROOT, 'celebration_dashboard.html')
    r = swap(path, [(DASH_OLD, DASH_NEW)],
             lambda t: 'action-more-btn' in t)
    if r is None:
        return False
    before, text = r
    if text.count('View Events') != 2 or text.count('Help') < 2:
        raise SystemExit('H2b: the dashboard should now name each control '
                         'TWICE - once in the bar, once in the More menu')
    # COUNT OUTSIDE COMMENTS - twice in one round now. The note added above
    # names .action-more-btn while explaining what base does with it, and a
    # naive count read that as a second More button.
    body = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    if body.count('action-more-btn') != 1:
        raise SystemExit('H2b: the dashboard has %d More button(s)'
                         % body.count('action-more-btn'))
    return True


def patch_management():
    path = os.path.join(ROOT, 'celebration_management.html')
    r = swap(path,
             [(MGMT_SEARCH_OLD, ''),
              (MGMT_BTN_BEFORE, MGMT_BTN_NEW)],
             lambda t: 'celebrationFilterPanel' in t)
    if r is None:
        return False
    before, text = r
    # the panel goes after the bar
    bar = re.search(r'<div[^>]*class="[^"]*page-action-buttons[^"]*"[^>]*>',
                    text)
    if not bar:
        raise SystemExit('H2b: the management bar vanished')
    d, end = 0, None
    for x in re.finditer(r'</?div\b', text[bar.start():]):
        d += 1 if x.group(0) == '<div' else -1
        if d == 0:
            end = text.find('>', bar.start() + x.end()) + 1
            break
    eol = eol_of(text)
    text = text[:end] + eol('\n\n') + eol(MGMT_PANEL) + text[end:]

    if text.count('id="contactSearch"') != 1:
        raise SystemExit('H2b: contactSearch appears %d time(s)'
                         % text.count('id="contactSearch"'))
    if 'onkeyup="searchContacts()"' not in text:
        raise SystemExit('H2b: the search lost its handler')
    if 'toolbar-search' in re.sub(r'<style[^>]*>.*?</style\s*>', '', text,
                                  flags=re.S | re.I):
        raise SystemExit('H2b: the old search wrapper survived in markup')
    # THE PANEL'S id, NOT ITS NAME. The first mention of the name is the
    # button's aria-controls, which is INSIDE the bar - so looking for the
    # name found the button and said the panel came first.
    pi = text.index('id="celebrationFilterPanel"')
    if pi < end:
        raise SystemExit('H2b: the panel must come AFTER the bar '
                         '(panel at %d, bar ends at %d)' % (pi, end))
    if not CHECK:
        write(path, text)
    return True


LATER = [
    ('alv_rounds.py',
     "    '.bak_bodybacks',\n]",
     "    '.bak_bodybacks',\n    '.bak_barmobile',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_body_backs.py'",
     "    'test_body_backs.py'\n    'test_bar_mobile.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('H2b/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION H, ROUND H2b - THREE THINGS H2 GOT WRONG ON A PHONE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    print('  base.html                  %s'
          % ('a bar with no primary keeps Back on the right (~13 pages)'
             if patch_base() else 'already has the rule'))
    print('  celebration_dashboard      %s'
          % ('two secondaries move behind a More menu'
             if patch_dashboard() else 'already has a More menu'))
    print('  celebration_management     %s'
          % ('search moves into a .alv-filter panel behind Filter'
             if patch_management() else 'already has the filter panel'))
    later = patch_later()
    print('-' * 74)
    print('  %d LATER edit(s).' % later)
    print('=' * 74)


if __name__ == '__main__':
    main()
