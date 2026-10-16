# -*- coding: utf-8 -*-
"""apply_landing_tab.py - round TB-1b, 15 Oct 2026.

A BACK BUTTON THAT LANDS ON A TABBED PAGE HAS TO NAME THE TAB.

Demetri, across three messages in one module-by-module check:

  "When I am in My Profile and I press the Back button, it takes me back
   to the Home page. This should take me back to the Administration Page
   (with the System Tab selected)."

  "In Financials --> Revenue Types, when the Back button is selected it
   should take you back to Finance, but with the Setup Tab selected.
   This should apply to Revenue Types, Revenue Line Types, Revenues,
   Expense Types, Expense Line Types and Expenses."

  "when you go back from the CRS Reporting Screen, it must take you back
   to the Personal Module, but with the Compliance Tab selected."

Nine controls, by his count. The census says TWENTY-THREE, and
my_profile is a twenty-fourth that also lands on the wrong PAGE.


EIGHT OF THE NINE ALREADY LAND ON THE RIGHT PAGE
============================================================================
Only my_profile goes somewhere wrong - it goes to home. The other
twenty-three arrive correctly and then show the wrong tab, because the
active tab is written into the markup by hand and nothing reads a URL.
No localStorage on any of the three landing pages, so there is nothing
to fight.


THE TAB IS NOT CHOSEN. IT IS DERIVED.                           MEASURED
============================================================================
Nineteen of the twenty-three answer themselves: the tab is whichever
panel of the landing page links to that page.

    admin_apms   FUNCTIONAL   tenant_lease_agreement,
                              generate_lease_agreement,
                              title_deeds_management
                 SYSTEM       user_administration, my_profile
    personal     PERSONAL     celebration_dashboard, passport_management,
                              recipe_management
                 COMPLIANCE   crs:index
    finance      REPORTS      cashflow_forecast, financial_indicators,
                              vacancy_management, finance_valuations,
                              finance_pl_act, occupancy_trends
                 SETUP        the six Demetri named

FOUR ARE CLAIMED BY NO PANEL, and they were put to him as such.
household_member_management and notification_settings are reached from
the landing page's own ACTION BAR, which sits above the tabs and belongs
to none of them; act_expense and personal_notification_settings are
linked from nothing at all and are reached by URL or by script. His
answer: the default tab, which is also what happens today - the
difference being that it is now written down and gated rather than
accidental.

notification_settings therefore lands on FUNCTIONAL, which reads oddly
for a System-shaped page. It is what the action bar can honestly say,
and the alternative - carrying the tab you were on out to the child and
back - is a round of its own.


WHAT TRAVELS IS A KEY, AND THE VIEW PAINTS IT
============================================================================
    ?tab=setup   ->  landing_tab(request, FINANCE_TABS, 'reports')

A key chosen from THAT PAGE'S OWN LIST, never a value taken at face
value - the same rule PJ-1 settled for project origins this morning. The
view resolves it and the markup paints `active` on the first frame, so no
reader sees the wrong tab flash and then jump. A hash read on load cannot
do that, which is why this is in the view and not in three copies of a
script.

AND THE LIST LIVES BESIDE THE VIEW THAT RENDERS THE PAGE, as a module
constant the suite can read, so the view and the template can be checked
against each other rather than both being trusted.


THE GATE IS WORTH MORE THAN THE CHANGE
============================================================================
All twenty-four name a tab, so the census can be strict: a Back control
whose href resolves to one of the three landing pages and does NOT carry
?tab= refuses the round. Nine of them would have left fifteen bare, and a
gate that has to allow a bare link cannot refuse a wrong new one either.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_landingtab'
HELPER = os.path.join('pages', 'services', 'landing_tabs.py')
ADMIN_VIEW = os.path.join('pages', 'views', 'administration.py')
FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
ME = 'test_landing_tab.py'
PATCHER = 'apply_landing_tab.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
FTO = 'test_future_tab_off.py'
CT = 'test_compliance_tab.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 83, 84
ALIAS_WAS, ALIAS_NOW = 77, 79
ALIAS_P_WAS, ALIAS_S_WAS = 38, 39
ALIAS_P_NOW, ALIAS_S_NOW = 39, 40

# The three landing pages, their tabs, and the tab each arrives on when
# nothing asks for one.
LANDING = {
    'admin_apms': (('functional', 'system'), 'functional'),
    'personal_page': (('personal', 'compliance'), 'personal'),
    'finance': (('reports', 'setup'), 'reports'),
}

# EVERY Back control that lands on one of them, with the tab derived
# from the panel that links to it - or, for the four no panel claims,
# the default, which is what they do today.
#   (template, url name it targets, tab key, how many such controls)
BACKS = [
    ('act_expense.html', 'finance', 'reports', 1),
    ('celebration_dashboard.html', 'personal_page', 'personal', 1),
    (os.path.join('finance', 'cashflow_forecast.html'),
     'finance', 'reports', 1),
    (os.path.join('finance', 'financial_indicators.html'),
     'finance', 'reports', 1),
    (os.path.join('finance', 'vacancy_management.html'),
     'finance', 'reports', 1),
    ('finance_expense.html', 'finance', 'setup', 1),
    ('finance_expense_line_types.html', 'finance', 'setup', 1),
    ('finance_expense_types.html', 'finance', 'setup', 1),
    ('finance_revenue.html', 'finance', 'setup', 1),
    ('finance_revenue_line_types.html', 'finance', 'setup', 1),
    ('finance_revenue_types.html', 'finance', 'setup', 1),
    ('finance_valuations.html', 'finance', 'reports', 1),
    ('generate_lease_agreement.html', 'admin_apms', 'functional', 2),
    ('household_member_management.html', 'personal_page', 'personal', 1),
    ('notification_settings.html', 'admin_apms', 'functional', 1),
    ('passport_management.html', 'personal_page', 'personal', 1),
    ('personal_notification_settings.html', 'personal_page', 'personal', 1),
    ('recipe_management.html', 'personal_page', 'personal', 1),
    ('tenant_lease_agreement.html', 'admin_apms', 'functional', 1),
    ('title_deeds_management.html', 'admin_apms', 'functional', 1),
    ('user_administration.html', 'admin_apms', 'system', 1),
]
CRS_BACK = (os.path.join('crs', 'index.html'), 'personal_page',
            'compliance', 1)
N_BACKS = sum(n for _, _, _, n in BACKS) + 1 + 1   # + crs + my_profile

# ======================================================= the new helper
HELPER_SRC = '''# -*- coding: utf-8 -*-
"""Which tab a landing page opens on.               TB-1b, 15 Oct 2026

THREE PAGES, TWO VIEW MODULES, ONE RULE. admin_apms and personal_page
live in pages/views/administration.py and finance lives in
pages/views/finance.py, so the alternative to a module of its own is one
view module importing a helper out of another for no reason but
proximity.

WHAT TRAVELS IS A KEY, NOT A TAB. ?tab=/anything/ read back at face
value is how a URL parameter becomes a way to put arbitrary text into a
class attribute. The key is checked against THAT PAGE'S OWN LIST, which
the view passes in, and anything else falls to the page's default - so a
stale bookmark opens the page it always did rather than a blank one.

WHY THE VIEW AND NOT A HASH READ ON LOAD. #setup would work, and the
reader would see the wrong tab painted and then jump. The server knows
the answer before the first frame, so it says so in the markup.
"""


def landing_tab(request, tabs, default):
    """The tab key this landing page should open on.

    `tabs` is the page's own tuple of keys and `default` is the one it
    arrives on when nothing asks. An unrecognised key - a typo, an old
    bookmark, or something forged - is not an error: it is the default,
    silently, because a landing page that refuses to render is worse
    than one that opens where it always did.
    """
    key = request.GET.get('tab', '')
    return key if key in tabs else default
'''

# ============================================================= the views
ADMIN_IMPORT_WAS = """from ..models import UserProfile, props, tenant"""

ADMIN_IMPORT_NOW = """from ..models import UserProfile, props, tenant
# TB-1b - which tab a Back button asked this page to open on.
from ..services.landing_tabs import landing_tab

# The tabs each landing page has, and the one it arrives on when nothing
# asks. BESIDE THE VIEW THAT RENDERS THE PAGE, as a constant, so the
# template and the view can be checked against each other rather than
# both being trusted. test_landing_tab reads these.
ADMIN_TABS = ('functional', 'system')
ADMIN_TAB_DEFAULT = 'functional'
PERSONAL_TABS = ('personal', 'compliance')
PERSONAL_TAB_DEFAULT = 'personal'"""

ADMIN_VIEW_WAS = """    return render(request, "admin_apms.html", {
        "props": results,
        "tenant": tresults
    })"""

ADMIN_VIEW_NOW = """    return render(request, "admin_apms.html", {
        "props": results,
        "tenant": tresults,
        # TB-1b - the tab this page was asked for, painted on the first
        # frame rather than switched to after it.
        "tab": landing_tab(request, ADMIN_TABS, ADMIN_TAB_DEFAULT),
    })"""

PERSONAL_VIEW_WAS = """    return render(request, "personal.html", {'perms_map': perms_map})"""

PERSONAL_VIEW_NOW = """    return render(request, "personal.html", {
        'perms_map': perms_map,
        # TB-1b - Compliance is where CRS Reporting lives, and its Back
        # button now says so.
        'tab': landing_tab(request, PERSONAL_TABS, PERSONAL_TAB_DEFAULT),
    })"""

FIN_VIEW_WAS = """def finance(request):
    return render(request, "finance.html", {})"""

FIN_VIEW_NOW = """def finance(request):
    # TB-1b - the six Setup pages' Back buttons ask for the Setup tab,
    # and the Reports pages say Reports rather than relying on it being
    # the default.
    return render(request, "finance.html", {
        "tab": landing_tab(request, FINANCE_TABS, FINANCE_TAB_DEFAULT),
    })"""

FIN_IMPORT_ANCHOR = """@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance(request):"""

FIN_TABS_BLOCK = """# TB-1b - the tabs this landing page has, and the one it arrives on when
# nothing asks. Beside the view that renders it, as a constant, so the
# template and the view can be checked against each other.
FINANCE_TABS = ('reports', 'setup')
FINANCE_TAB_DEFAULT = 'reports'


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance(request):"""

# ========================================================= the templates
TAB_EDITS = {
    'admin_apms.html': [
        ('<div class="admin-tab active" id="tab-functional"',
         '<div class="admin-tab{% if tab|default:\'functional\' == \'functional\' %} active{% endif %}" id="tab-functional"'),
        ('<div class="admin-tab" id="tab-system"',
         '<div class="admin-tab{% if tab == \'system\' %} active{% endif %}" id="tab-system"'),
        ('<div id="panel-functional" class="tab-panel active">',
         '<div id="panel-functional" class="tab-panel{% if tab|default:\'functional\' == \'functional\' %} active{% endif %}">'),
        ('<div id="panel-system" class="tab-panel">',
         '<div id="panel-system" class="tab-panel{% if tab == \'system\' %} active{% endif %}">'),
    ],
    'personal.html': [
        ('<div class="admin-tab personal-tab active" id="tab-personal"',
         '<div class="admin-tab personal-tab{% if tab|default:\'personal\' == \'personal\' %} active{% endif %}" id="tab-personal"'),
        ('<div class="admin-tab compliance-tab" id="tab-compliance"',
         '<div class="admin-tab compliance-tab{% if tab == \'compliance\' %} active{% endif %}" id="tab-compliance"'),
        ('<div id="personal-panel" class="tab-panel personal-panel active">',
         '<div id="personal-panel" class="tab-panel personal-panel{% if tab|default:\'personal\' == \'personal\' %} active{% endif %}">'),
        ('<div id="compliance-panel" class="tab-panel compliance-panel">',
         '<div id="compliance-panel" class="tab-panel compliance-panel{% if tab == \'compliance\' %} active{% endif %}">'),
    ],
    'finance.html': [
        ('<div class="admin-tab active" id="tab-reports"',
         '<div class="admin-tab{% if tab|default:\'reports\' == \'reports\' %} active{% endif %}" id="tab-reports"'),
        ('<div class="admin-tab" id="tab-setup"',
         '<div class="admin-tab{% if tab == \'setup\' %} active{% endif %}" id="tab-setup"'),
        ('<div id="reports-panel" class="tab-panel active">',
         '<div id="reports-panel" class="tab-panel{% if tab|default:\'reports\' == \'reports\' %} active{% endif %}">'),
        ('<div id="setup-panel" class="tab-panel">',
         '<div id="setup-panel" class="tab-panel{% if tab == \'setup\' %} active{% endif %}">'),
    ],
}

# my_profile is the only one whose PAGE was wrong, and its aria-label
# said so out loud.
PROFILE_WAS = """        <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">"""

PROFILE_NOW = """        <a href="{% url 'admin_apms' %}?tab=system" class="btn action-back" aria-label="Back to administration">"""

FTO_WAS = """page = read(alv_tree.path_of(PAGE))"""

FTO_NOW = """# TB-1b, 15 Oct 2026 - AS P2 LEFT IT, not as it stands today. This
# suite had no as_left_by at all and read the page live, which is the
# one thing a round's own suite must not do with the file it changed:
# every claim here is about the state P2 produced when it switched the
# FUTURE tab off on 29 Sep.
#
# TB-1b moved this page's `active` out of the markup and into the view,
# so the class attribute now carries a {% if %} and section 4's
# `class="tab-panel ([\\w\\- ]+)"` matches nothing. The panels are all
# still there; the attribute stopped being a plain list of words.
try:
    from alv_rounds import as_left_by as _alb
except Exception:
    _alb = None
page = (_alb(alv_tree.path_of(PAGE), SUFFIX, read) if _alb
        else read(alv_tree.path_of(PAGE)))"""

# PR-1'S OWN SUITE RECORDS HOW P2 READS ITS PAGE, which is the thing
# this round changes. A re-point that leaves a second suite asserting
# the old habit has moved the defect rather than fixed it.
CT_WAS = """ok('page = read(' in p2,
   'test_future_tab_off.py reads the LIVE page, so it did go red')"""

CT_NOW = """# TB-1b, 15 Oct 2026 - IT DOES NOT ANY MORE, AND THAT IS WHY THIS LINE
# MOVED. PR-1 recorded here that P2 read the live page, which was true
# and was the reason P2 went red when Compliance arrived. TB-1b moved
# `active` out of that page's markup and into the view, so the class
# attribute carries a {% if %} and P2's word-list regex matched nothing
# - the same breakage a third time, from the same cause.
#
# So P2 now reads the page AS P2 LEFT IT, like P6 three checks above,
# and the claim here becomes the one worth keeping: both of them judge
# the tree their own round produced, and neither can be broken by a
# later one.
ok('as_left_by' in p2 and 'TB-1b, 15 Oct 2026' in p2,
   'test_future_tab_off.py read the LIVE page - which is why it went red '
   'twice - and reads it as P2 left it now, like P6 above')"""

# ============================================================= registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ TB-1b, 15 Oct 2026
    # Nine Back buttons reported, twenty-three found, and my_profile a
    # twenty-fourth that landed on Home. The tab is derived from the
    # panel that links to the page, and the view paints it.
    @{ File = 'pages\\\\services\\\\landing_tabs.py'; Text = 'def landing_tab'; What = 'a landing page opens on the tab it was asked for, by key' },
    @{ File = 'pages\\\\templates\\\\finance_revenue_types.html'; Text = '?tab=setup'; What = 'and the six Finance Setup pages ask for Setup by name' },
    @{ File = 'pages\\\\templates\\\\my_profile.html'; Text = 'url ''home'' %}" class="btn action-back"'; Absent = $true; Code = $true; What = 'My Profile stops sending you to the Home page' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_tab_names.py'
)"""

SUITE_NOW = """    'test_tab_names.py',
    'test_landing_tab.py'
)"""

TREE_WAS = """    'test_tab_names.py',
]"""

TREE_NOW = """    'test_tab_names.py',
    # TB-1b, 15 Oct 2026 - twenty-four Back controls name the tab they
    # want, the view resolves the key and the markup paints it on the
    # first frame. Wide from birth.
    'test_landing_tab.py',
]"""

ROUNDS_WAS = """    '.bak_tabnames',
]"""

ROUNDS_NOW = """    '.bak_tabnames',
    # TB-1b, 15 Oct 2026 - ?tab=<key> read in the view against the page's
    # own list, so a Back button lands on the tab it means. Twenty-four
    # controls, nineteen of them derived from the panel that links to
    # them.
    '.bak_landingtab',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('TB-1b REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


BACK_TAG = re.compile(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>')
URL_IN = re.compile(r"\{%\s*url\s*'([a-z_:]+)'[^}]*%\}")


def name_the_tab(text, url_name, key, expect, where):
    """Append ?tab=<key> to every action-back control that targets
    `url_name`, and refuse unless exactly `expect` of them were found.

    A TARGETED REWRITE OVER A MEASURED LIST, not a loose regex over the
    file: the tag has to BE a Back control and its href has to resolve
    to the page named in the table.
    """
    out, done, pos = [], 0, 0
    for m in BACK_TAG.finditer(text):
        u = URL_IN.search(m.group(0))
        if not u or u.group(1) != url_name:
            continue
        tag = m.group(0)
        if '?tab=' in tag:
            refuse('%s: a Back control already names a tab' % where)
        new = URL_IN.sub(lambda mm: mm.group(0) + '?tab=' + key, tag, count=1)
        out.append(text[pos:m.start()] + new)
        pos = m.end()
        done += 1
    if done != expect:
        refuse('%s: found %d Back control(s) to %s, expected %d'
               % (where, done, url_name, expect))
    out.append(text[pos:])
    return ''.join(out)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the TREE.
    hp = os.path.join(root, HELPER)
    if os.path.exists(hp):
        print('TB-1b  already applied - the landing tab helper is there.')
        return 0
    # AND TB-1a FIRST. Its rename is why this round never has to write
    # down that the key `system` means the id `future`.
    if 'id="tab-system"' not in read(alv_tree.path_of('admin_apms.html')):
        refuse('TB-1a is not applied - this round names the tab `system` '
               'and that id does not exist yet')

    out = {}
    new_files = {}

    # ---------------------------------------------------------------- 1
    new_files[hp] = HELPER_SRC

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, ADMIN_VIEW)
    s = read(p)
    s = swap(s, ADMIN_IMPORT_WAS, ADMIN_IMPORT_NOW,
             '%s (the import and the two lists)' % ADMIN_VIEW)
    s = swap(s, ADMIN_VIEW_WAS, ADMIN_VIEW_NOW,
             '%s (admin_apms context)' % ADMIN_VIEW)
    s = swap(s, PERSONAL_VIEW_WAS, PERSONAL_VIEW_NOW,
             '%s (personal_page context)' % ADMIN_VIEW)
    out[p] = s

    p = os.path.join(root, FIN_VIEW)
    s = read(p)
    s = swap(s, FIN_IMPORT_ANCHOR, FIN_TABS_BLOCK,
             '%s (the tab list)' % FIN_VIEW)
    s = swap(s, FIN_VIEW_WAS, FIN_VIEW_NOW,
             '%s (finance context)' % FIN_VIEW)
    if 'from ..services.landing_tabs import landing_tab' not in s:
        s = swap(s, '# TB-1b - the tabs this landing page has',
                 'from ..services.landing_tabs import landing_tab\n\n'
                 '# TB-1b - the tabs this landing page has',
                 '%s (the import)' % FIN_VIEW)
    out[p] = s

    # ---------------------------------------------------------------- 3
    for page, edits in TAB_EDITS.items():
        q = alv_tree.path_of(page)
        s = read(q)
        for was, now in edits:
            s = swap(s, was, now, '%s (%s)' % (page, was[:46]))
        # EXACTLY ONE TAB AND ONE PANEL ARE DECIDED BY THE VIEW, and
        # none by hand. PR-1 and TB-2 each shipped a page where `active`
        # accumulated; a page that still hard-codes one is a page where
        # two can be active at once.
        if re.search(r'class="admin-tab[^"{]*active', s):
            refuse('%s: a tab still carries active by hand' % page)
        if re.search(r'class="tab-panel[^"{]*active', s):
            refuse('%s: a panel still carries active by hand' % page)
        # FOUR TESTS PER PAGE, AND TWO OF THEM DEFAULT. Rendered with
        # no `tab` in the context at all, the first cut of this painted
        # NO active tab - a worse state than the hard-coded one it
        # replaces. tab|default:'<key>' gives the default tab an answer
        # whatever the context does, and only a render with an empty
        # context shows the difference.
        n_tests = len(re.findall(r"\{% if tab(?:\|default:'[a-z]+')? == '",
                                 s))
        n_default = s.count("{% if tab|default:'")
        if n_tests != 4 or n_default != 2:
            refuse('%s: expected four tab tests of which two defaulted, '
                   'found %d and %d' % (page, n_tests, n_default))
        out[q] = s

    # ---------------------------------------------------------------- 4
    for rel, url_name, key, expect in BACKS:
        q = alv_tree.join(rel)
        out[q] = name_the_tab(read(q), url_name, key, expect, rel)
    rel, url_name, key, expect = CRS_BACK
    q = alv_tree.path_of('index.html', base=None) \
        if False else os.path.join(alv_tree.roots()[-1], 'crs', 'index.html')
    if not os.path.isfile(q):
        q = [x for x in alv_tree.templates()
             if alv_tree.rel(x).replace('\\', '/') == 'crs/index.html'][0]
    out[q] = name_the_tab(read(q), url_name, key, expect, rel)

    q = alv_tree.path_of('my_profile.html')
    out[q] = swap(read(q), PROFILE_WAS, PROFILE_NOW,
                  'my_profile.html (the Back control)')

    # ---------------------------------------------------------------- 5
    # THE CENSUS, AND THE REAL GATE. Every Back control that lands on a
    # tabbed page names its tab. All twenty-four are named, so this can
    # refuse a bare one - nine would have left fifteen, and a gate that
    # must allow a bare link cannot refuse a wrong new one either.
    named, bare = 0, []
    for q in alv_tree.templates():
        t = out.get(q, read(q))
        for m in BACK_TAG.finditer(t):
            u = URL_IN.search(m.group(0))
            if not u or u.group(1) not in LANDING:
                continue
            tabs = LANDING[u.group(1)][0]
            got = re.search(r'\?tab=([a-z]+)', m.group(0))
            if got and got.group(1) in tabs:
                named += 1
            else:
                bare.append('%s -> %s: %r'
                            % (alv_tree.rel(q), u.group(1),
                               (got.group(1) if got else 'nothing')))
    if bare:
        refuse('a Back control lands on a tabbed page without naming a '
               'tab this page has:\n   ' + '\n   '.join(bare))
    if named != N_BACKS:
        refuse('expected %d Back control(s) naming a tab, found %d'
               % (N_BACKS, named))

    # ---------------------------------------------------------------- 6
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_landing_tab.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'TB-1b, 15 Oct 2026 - this round own suite. Twenty-four '
                  'Back controls name the tab they land on, after Demetri '
                  'reported nine of them.',
                  '%s (the converted count)' % WD)

    # THE ONE SUITE THIS ROUND RE-POINTS, and it is a repair: P2's
    # claims keep their exact words and start being asked of the page P2
    # left rather than of whatever the tree holds today.
    p = os.path.join(root, FTO)
    s = read(p)
    if 'as_left_by' in s:
        refuse('%s already reads its page as the round left it' % FTO)
    out[p] = swap(s, FTO_WAS, FTO_NOW, '%s (the page it judges)' % FTO)

    p = os.path.join(root, CT)
    s = read(p)
    if "'as_left_by' in p2" in s:
        refuse('%s already records P2 reading its own snapshot' % CT)
    out[p] = swap(s, CT_WAS, CT_NOW, '%s (what it says about P2)' % CT)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'TB-1b, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('TB-1b --check  %d file(s) would change, %d new'
              % (len(out), len(new_files)))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        for q in sorted(new_files):
            print('   %s   NEW' % os.path.relpath(q, root))
        print('   %d Back control(s) name a tab' % named)
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)
    for q, t in sorted(new_files.items()):
        write(q, t)

    print('TB-1b applied.')
    print('   %d Back control(s) name the tab they land on - %d of them'
          % (named, named - 9))
    print('         beyond the nine reported, and nineteen derived from')
    print('         the panel that links to the page')
    print('   the view resolves the key against the page own list and')
    print('         paints active on the first frame - no flash, no hash')
    print('   my_profile stops sending you to the Home page')
    print('   %d file(s) written + %d new, backups end %s'
          % (len(out), len(new_files), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
