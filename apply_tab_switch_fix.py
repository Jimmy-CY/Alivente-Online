# -*- coding: utf-8 -*-
"""apply_tab_switch_fix.py - Section TB round TB-2, 8 Oct 2026.

TB-1 TOOK THE LINES THAT TURN A TAB OFF.

Demetri, testing the deployed page within the hour: "When I first land on
the page, everything looks perfect. Then when I click on the System tab,
the lines below Functional and System disappear. Also, the Functional tab
should now be white. And when I click back on Functional, it still
doesn't work." And then: "The same happens with Personal and Compliance."

=====================================================================
WHAT TB-1 DID
=====================================================================

The page's switchTab() looked like this before the round:

    // Update tab buttons
    document.getElementById('tab-alivente').classList.remove('active', 'future-active');
    document.getElementById('tab-future').classList.remove('active', 'alivente-active');

TB-1 was removing the cross-classes - `alivente-active` and
`future-active` only ever coloured the OTHER tab's edges, which ONE
treatment has no use for. It should have removed the second ARGUMENT. It
removed the whole LINE, both of them, and those lines were also the only
thing that took `active` OFF a tab.

So `active` accumulates. Click SYSTEM and both tabs carry it; click back
to FUNCTIONAL and both still do. The PANELS are removed correctly, which
is why the content was always right and only the tabs were wrong - and
why it reads as "it still doesn't work" rather than as a dead page.

Same fault on personal.html, where PR-1's switchTab lost the same two
lines the same way. finance.html is NOT affected: FN-2 wrote its
switchTab fresh and removes both tabs by name.

=====================================================================
AND NO SUITE CAUGHT IT, WHICH IS THE WORSE HALF
=====================================================================

test_house_tabs, test_system_teal, test_compliance_tab and
test_finance_tabs all prove the TREATMENT: they add `.active` to a tab
IN THE PROBE and measure what the browser computes. Every one of them
would have passed with switchTab deleted entirely.

A CLASS NOBODY APPLIES IS A CLASS NOBODY TESTED. test_tab_switch.py
clicks the tabs in Chromium, on all three pages, and asserts exactly one
tab carries `active` after each click. The control is these two pages as
this round finds them - two tabs active, and it must FAIL.

=====================================================================
ONE SHAPE, THREE PAGES
=====================================================================

The fix is written in the shape finance.html already uses: every tab
turned off by name, then the chosen one turned on. All three pages now
read identically, because a second spelling of the same behaviour is a
second thing to keep in step - which is the lesson TB-1 was FOR, and it
is the reason this fix does not invent a fourth.

FILES: admin_apms.html, personal.html (+ .bak_tabswitch), alv_rounds.py,
the PS1 $suites, and the new test_tab_switch.py.
"""
import os
import re
import sys

SUFFIX = '.bak_tabswitch'
SUITE_NAME = 'test_tab_switch.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

# page -> (the two tab ids, the anchor the fix goes in front of)
PAGES = {
    'admin_apms.html': (
        ('tab-alivente', 'tab-future'),
        """function switchTab(tab) {
    // Update tab buttons

    // Update panels
    document.getElementById('panel-alivente').classList.remove('active');""",
        """function switchTab(tab) {
    // TB-2, 8 Oct 2026 - THESE TWO LINES ARE THE DEFECT TB-1 SHIPPED.
    // They were here before that round, carrying a cross-class as a
    // second argument:
    //     .classList.remove('active', 'future-active');
    // TB-1 was retiring the cross-classes and removed the whole LINE
    // instead of the ARGUMENT - and the line was also the only thing
    // that took `active` OFF a tab. `active` then accumulated: click
    // the second tab and both carried it. The panels below were
    // removed correctly, which is why the content was always right.
    // Demetri found it in the deployed page within the hour.
    document.getElementById('tab-alivente').classList.remove('active');
    document.getElementById('tab-future').classList.remove('active');

    // Update panels
    document.getElementById('panel-alivente').classList.remove('active');"""),

    'personal.html': (
        ('tab-personal', 'tab-compliance'),
        """function switchTab(tab) {

    document.getElementById('personal-panel').classList.remove('active');""",
        """function switchTab(tab) {
    // TB-2, 8 Oct 2026 - the same defect as admin_apms.html, arrived
    // the same way: PR-1 wrote this function with the cross-class
    // removals in it, TB-1 retired the cross-classes by deleting the
    // lines, and `active` was never taken off a tab again. See
    // apply_tab_switch_fix.py for the whole account.
    document.getElementById('tab-personal').classList.remove('active');
    document.getElementById('tab-compliance').classList.remove('active');

    document.getElementById('personal-panel').classList.remove('active');"""),
}


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def body(txt):
    """Just the switchTab function, so a count means what it says."""
    i = txt.find('function switchTab')
    if i < 0:
        return ''
    j = txt.find('\n}', i)
    return txt[i:j + 2] if j > 0 else txt[i:]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('TB-2  already applied')
        return 1 if CHECK else 0

    out = {}
    for name, (ids, old, new) in PAGES.items():
        path = T.path_of(name)
        txt = read(path)

        # WHAT THE DEFECT IS, MEASURED, NOT ASSUMED. The round refuses
        # unless this page really does fail to turn its tabs off - a
        # fix applied to a page that does not have the fault is a fix
        # nobody can account for.
        fn = body(txt)
        for tid in ids:
            got = fn.count("getElementById('%s').classList.remove('active')" % tid)
            if got:
                raise SystemExit('TB-2: %s already turns %s off (%d time(s)) - '
                                 'this page does not have the defect'
                                 % (name, tid, got))
            if ("getElementById('%s').classList.add('active')" % tid) not in fn:
                raise SystemExit('TB-2: %s never turns %s ON either, so this '
                                 'is not the function this round means'
                                 % (name, tid))

        o = fit(txt, old)
        if txt.count(o) != 1:
            raise SystemExit('TB-2: the switchTab head of %s matched %d '
                             'time(s), not once' % (name, txt.count(o)))
        res = txt.replace(o, fit(txt, new), 1)

        # ---- what must be true of the result -----------------------
        fn2 = body(res)
        for tid in ids:
            if fn2.count("getElementById('%s').classList.remove('active')"
                         % tid) != 1:
                raise SystemExit('TB-2: %s does not turn %s off exactly once'
                                 % (name, tid))
            if fn2.count("getElementById('%s').classList.add('active')"
                         % tid) != 1:
                raise SystemExit('TB-2: %s does not turn %s on exactly once'
                                 % (name, tid))
        # The cross-classes stay retired. TB-1 was right about those.
        #
        # AND THE CHECK READS CODE, NOT THE NOTE ABOUT THE CODE. The
        # first cut was `if cls in res` and it refused - on the comment
        # above, which has to name `future-active` to explain what TB-1
        # removed. That is the SIXTH time in three days a check has
        # fired on prose: 'btn-future-disabled', '#adb5bd', 'Coming
        # Soon', 'CONFIGURATION', and the inverse in TB-1 itself. A
        # round that cannot document itself without tripping its own
        # gate has the gate pointed at the wrong thing. This one tests
        # the SHAPE - the class as an argument or as a selector.
        code = T.code_only_js(res)
        for cls in ('alivente-active', 'future-active', 'personal-active',
                    'compliance-active'):
            hit = (re.search(r"classList\.(?:add|remove|toggle)\([^)]*'%s'"
                             % re.escape(cls), code)
                   or re.search(r'(^|[}\s,])\.%s\s*[,{:.]' % re.escape(cls),
                                code))
            if hit:
                raise SystemExit('TB-2: %s reinstated the %s cross-class as '
                                 '%r. TB-1 was right to retire those; this '
                                 'round is only about the line they were on'
                                 % (name, cls, hit.group(0)))
        # Markup untouched: this round changes a function, nothing else.
        def markup(t):
            return re.sub(r'<script\b.*?</script>', '', t, flags=re.S | re.I)
        if markup(res) != markup(txt):
            raise SystemExit('TB-2: %s changed outside its <script> - this '
                             'round is two lines of JavaScript' % name)
        out[path] = res
        print('TB-2  %-18s %d -> %d bytes, both tabs turned off by name'
              % (name, len(txt), len(res)))

    # finance.html is the page that already does it right, and the round
    # says so rather than leaving it to be noticed.
    fin = body(read(T.path_of('finance.html')))
    for tid in ('tab-reports', 'tab-setup'):
        if ("getElementById('%s').classList.remove('active')" % tid) not in fin:
            raise SystemExit('TB-2: finance.html does NOT turn %s off, so '
                             'this round is one page short' % tid)
    print('TB-2  finance.html already correct - FN-2 wrote its switchTab '
          'fresh; this round takes its shape')

    reg = resolve_registration(rounds, ps)
    print('TB-2  %d registry file(s) resolved, every anchor found' % len(reg))

    if CHECK:
        print('TB-2  NOT APPLIED')
        return 1
    for p, t in out.items():
        backup(p)
        write(p, t)
    for p, t in reg.items():
        backup(p)
        write(p, t)
    print('TB-2  ok')
    return 0


def resolve_registration(rounds, ps):
    reg = {}
    NOTE = """    # TB-2, 8 Oct 2026 - THE LINES THAT TURN A TAB OFF, PUT BACK.
    # TB-1 retired the alivente-active / future-active cross-classes by
    # deleting the two lines that carried them, and those lines also
    # carried 'active' - the only thing that took it OFF a tab. Click
    # the second tab and both carried it; click back and both still
    # did. The panels were removed correctly, so the content was always
    # right and only the tabs were wrong. Demetri found it in the
    # deployed page within the hour, on Administration and Personal
    # both. finance.html was never affected: FN-2 wrote its switchTab
    # fresh, and this fix takes that shape so all three read alike.
    #
    # AND THE SUITES ALL PASSED. Every tab suite adds .active in its own
    # probe and measures the CSS; not one ever called switchTab. A class
    # nobody applies is a class nobody tested. test_tab_switch.py clicks.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_fintabs',\n]", "    '.bak_housetabs',\n]",
                   "    '.bak_compliance',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('TB-2: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    PS_NOTE = """    # TB-2, 8 Oct 2026 - the tabs are CLICKED, on all three pages, and
    # exactly one carries .active after each click. The control is the
    # two pages as this round found them, where two did.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_finance_tabs.py'\n)",
                   "    'test_house_tabs.py'\n)",
                   "    'test_compliance_tab.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('TB-2: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
