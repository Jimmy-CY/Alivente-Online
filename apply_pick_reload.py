# -*- coding: utf-8 -*-
"""apply_pick_reload.py - round RL-1, 20 Oct 2026.

THE PICKER'S RELOAD NEVER BOUND.

Demetri, testing push 2 on production:

    "When I select a recipe in the picker, from the month view and then
     say Done, the recipe doesn't show on the month view. If I refresh
     the page, then it shows."

DRIVEN, NOT READ. A real server, a real session, a real browser:

    picker in the DOM     : True
    jQuery present        : True
    jQuery events bound   : []        <-- nothing
    pickerDirty now       : True
    navigations after Done: 0
    chips on the grid now : 1
    chips after a refresh : 2         <-- his report, exactly

PS-1 wrote the right code and registered it at the wrong moment:

    (function () {
        var el = document.getElementById('pickerModal');
        if (!el || !window.jQuery) { return; }     <-- here
        window.jQuery(el).on('hidden.bs.modal', ...
    })();

base loads jQuery near the END of the document. This block is in the
content, so when it runs the parser has not reached that script tag
yet and window.jQuery is undefined. The guard returns, and nothing
ever binds.

> THE GUARD WAS RIGHT AND ITS TIMING WAS NOT. PS-1 added it for a good
> reason - written as `$(function () {...})` it threw when jQuery was
> missing and took PF-2's outside-click handler down with it, because
> everything after a throw in the same script block never registers.
> The guard stopped the crash and turned "not loaded YET" into
> "silently never", which is the quieter of two failures and the
> harder to find. A guard answers "is it here?"; it cannot answer
> "will it be?".

DOMContentLoaded IS THE ANSWER, and it is not a retry or a timer. It
fires after every parser-inserted script in the document has executed,
so jQuery is certain to exist by then - certain, rather than likely,
which is what separates this from polling. The guard stays, because a
page that somehow has no jQuery should still not throw.

Idempotent. Every file backed up to .bak_pickreload.
"""
import os
import re
import sys

SUFFIX = '.bak_pickreload'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_pick_reload.py'
PATCHER = 'apply_pick_reload.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RL-1, 20 Oct 2026'
CHECK = False
CREATES = ()

BIND_WAS = """(function () {
    var el = document.getElementById('pickerModal');
    if (!el || !window.jQuery) { return; }
    window.jQuery(el).on('hidden.bs.modal', function () {
        if (pickerDirty) { window.location.reload(); }
    });
})();"""
BIND_NOW = """(function () {
    // BOUND WHEN THE DOCUMENT IS PARSED, NOT WHILE IT IS - RL-1,
    // 20 Oct 2026. base loads jQuery near the END of the document and
    // this block is in the content, so at the moment it first runs
    // window.jQuery is undefined. The guard below then returned and
    // NOTHING EVER BOUND: adding a meal from the month view left the
    // grid stale until the page was refreshed by hand.
    //
    // DOMContentLoaded fires after every parser-inserted script has
    // executed, so jQuery is certain to be there - certain, not
    // likely, which is what makes this different from a timer.
    //
    // THE GUARD STAYS. PS-1 added it because `$(function(){...})`
    // threw when jQuery was missing and took every statement after it
    // in the same block with it, PF-2's outside-click handler
    // included. It was right about the crash; it was asked the wrong
    // question - "is jQuery here?" rather than "will it be?".
    function bind() {
        var el = document.getElementById('pickerModal');
        if (!el || !window.jQuery) { return; }
        window.jQuery(el).on('hidden.bs.modal', function () {
            if (pickerDirty) { window.location.reload(); }
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();"""


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = "document.addEventListener('DOMContentLoaded', bind)"; What = 'RL-1: the picker reload is bound after the document is parsed - base loads jQuery near the end, so PS-1 guard found none and silently bound nothing, and the month grid stayed stale until a hand refresh' },"""

SUITE_WAS = """    'test_chip_pill.py'
)"""
SUITE_NOW = """    'test_chip_pill.py',
    # RL-1, 20 Oct 2026 - the picker reload binds. Section 3 DRIVES a
    # real server in a real browser and counts navigations after Done,
    # because nothing readable in the source says whether a handler
    # was registered.
    'test_pick_reload.py'
)"""

TREE_WAS = """    # CL-1, 20 Oct 2026 - the chip is a pill, and a later stylesheet
    # stops overruling the rule that draws it.
    'test_chip_pill.py',
]"""
TREE_NOW = """    # CL-1, 20 Oct 2026 - the chip is a pill, and a later stylesheet
    # stops overruling the rule that draws it.
    'test_chip_pill.py',
    # RL-1, 20 Oct 2026 - a guard that asked "is jQuery here" when it
    # meant "will it be", and bound nothing for a day.
    'test_pick_reload.py',
]"""

RD_WAS = """    # CL-1, 20 Oct 2026 - a meal in the calendar is a pill again.
    '.bak_chippill',
]"""
RD_NOW = """    # CL-1, 20 Oct 2026 - a meal in the calendar is a pill again.
    '.bak_chippill',
    # RL-1, 20 Oct 2026 - the picker reload actually binds.
    '.bak_pickreload',
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
    raise SystemExit('RL-1 REFUSED: %s' % msg)


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


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if "document.addEventListener('DOMContentLoaded', bind)" in t:
        print('RL-1  already applied - the picker reload binds.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    js = T.code_only_js(t)

    # ---- THE FAULT MUST BE THERE: the handler PS-1 wrote, and the
    # flag it reads, and base loading jQuery late enough to matter.
    if 'hidden.bs.modal' not in js:
        refuse('%s: there is no close handler to bind, so this round '
               'has nothing to repair' % TPL)
    if 'pickerDirty' not in js:
        refuse('%s: nothing records that the picker changed anything, '
               'so a reload would be unconditional' % TPL)

    base = read(os.path.join(root, 'pages', 'templates', 'base.html'))
    nb = base.replace('\r\n', '\n')
    jq = nb.find('jquery')
    if jq < 0:
        refuse('base.html: jQuery is not loaded there at all, which is '
               'not the tree this round was written for')
    # THE WHOLE REASON THIS BUG EXISTS, asked rather than assumed: the
    # script tag must come LATE. If base ever moves it into the head,
    # this round is unnecessary and should not be shipped quietly.
    if jq < len(nb) * 0.5:
        refuse('base.html: jQuery now loads in the first half of the '
               'document, so a guard at parse time would find it and '
               'this round is answering a question nobody is asking')

    t = swap(t, BIND_WAS, BIND_NOW, '%s (the close handler)' % TPL)
    out[pt] = t

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s
    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # RL-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    njs = T.code_only_js(out[pt])

    # ONE BINDING, AND IT IS DEFERRED. Two would reload twice.
    if njs.count("on('hidden.bs.modal'") != 1:
        refuse('%s: %d close handler(s), expected 1'
               % (TPL, njs.count("on('hidden.bs.modal'")))
    if njs.count('function bind()') != 1:
        refuse('%s: the binding is not in one named function' % TPL)

    # THE GUARD SURVIVES. Removing it would fix this bug and restore
    # the crash PS-1 fixed, which is a trade and not a repair.
    if '!el || !window.jQuery' not in njs:
        refuse('%s: the guard is gone - without it a page with no '
               'jQuery throws and takes the rest of the block with it'
               % TPL)

    # AND THE READY CHECK COVERS BOTH STATES. A listener added after
    # DOMContentLoaded has fired never runs.
    if "document.readyState === 'loading'" not in njs:
        refuse('%s: nothing handles the case where the document is '
               'already parsed, where the listener would never fire'
               % TPL)

    if CHECK:
        print('RL-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RL-1  applied - the picker reload binds.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
