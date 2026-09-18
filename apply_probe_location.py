"""apply_probe_location.py - browser fixtures leave the repo root.

    python apply_probe_location.py --check     survey, write nothing
    python apply_probe_location.py             apply

Run from the repo root.

WHAT BROKE, AND WHY IT LOOKED LIKE A GATE FAULT

test_table_lease_agreement.py crashed on the push gate:

    playwright._impl._errors.Error: Page.goto: net::ERR_FAILED at
      file:///C:/.../Alivente-Online/_sup_probe.html

and passed under Show-GateAudit.py, which runs the very same suites. That
difference is the whole diagnosis.

FOUR SUITES WRITE ONE FILENAME. test_table_lease_agreement.py,
test_table_properties.py, test_table_suppliers.py and test_table_tenants.py
each build their fixture at `_sup_probe.html` IN THE REPO ROOT, render it,
and delete it in a finally.

    the gate      runs all four: suppliers at 569, properties at 572,
                  tenants at 582, lease_agreement at 583. That one path is
                  created, uploaded by OneDrive, deleted and created again
                  FOUR TIMES in one run, and the fourth is answered with
                  ERR_FAILED.

    the audit     runs sorted(glob('test_*.py')), so lease_agreement comes
                  FIRST of the four and the others follow it. Same suites,
                  same machine, different order, and it passes.

MY FIRST ACCOUNT OF THIS WAS TOO NARROW AND THE EVIDENCE CORRECTED IT. I
said the cause was tenants running immediately before lease_agreement - but
run by hand, one after the other, in exactly that order, lease_agreement
passes with all 101 checks. What the gate adds is not the adjacency, it is
the REPETITION: two more creates and deletes of the same path, earlier in
the same run.

I CANNOT MEASURE THE MECHANISM FROM HERE - whether it is OneDrive holding a
handle, Defender chasing a file that keeps reappearing, or something else
about a path churned four times in one run. What I can say is that the
number of times that one name is reused is the thing that differs between
the run that fails and the run that passes, and that a shared name in a
synced, version-controlled directory is wrong on its own terms whether or
not it is tonight's cause.

So the round does not try to out-guess the sync client. It removes the
shared name, and the shared directory with it.

WHAT IT DOES

1.  EVERY FIXTURE MOVES TO A PRIVATE DIRECTORY.

        SCRATCH = tempfile.mkdtemp(prefix='alv_probe_')

    mkdtemp gives THIS PROCESS a directory whose name no other process
    knows, so two suites cannot collide however they are ordered. An
    atexit hook removes it. Three consequences beyond the collision:

      - nothing is written into a git working tree any more, so a suite
        that dies before its own cleanup cannot leave an untracked file
        where the next commit will see it;
      - OneDrive never sees the file, so it is never uploaded, never
        chased, and never a conflict copy;
      - .gitignore does not need an entry for it. It already carries one
        for /error_*.html, which is the same habit having cost something
        once already.

    THE SET IS FOUND BY A RULE, NOT READ OFF A LIST - and the first
    version of that rule was wrong, in a way worth keeping on the page.
    It said "a ROOT-built path opened for writing", and on the real tree
    that is twenty-eight PATCHERS: apply_table_standard.py writes
    pages/templates/base.html, apply_open_items.py writes .gitignore,
    apply_invoice_verification.py writes requirements.txt. Writing source
    into the working tree is what a patcher is FOR. My own checkout held
    eight apply_*.py files and the real tree holds a hundred and
    twenty-four, so the corpus I tested against could not show me that.

    The rule asks for BOTH halves now: written here, AND handed to the
    browser. No apply_*.py in this repo contains the word goto, and
    neither .gitignore nor base.html is ever navigated to. The suite
    checks that separation rather than assuming it.

    EXPECTED below is what the corrected rule finds; if a run finds a
    different set the patcher stops and prints both, rather than quietly
    doing less than it says. That is what happened above - it wrote
    nothing, three times, and was right to.

2.  A NAVIGATION FAILURE SAYS WHY.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls pg.goto bare. A file:// navigation fails for reasons that
    have nothing to do with the page under test. _goto() reports the
    path, whether it is on disk, its size and the message, then exits 1.

    So this round either fixes the crash or explains it. If the gate is
    green afterwards the ordering account above was right; if it is not,
    the next run says what it could not open and why, instead of a
    traceback through six frames of Playwright.

WHAT IT DELIBERATELY DOES NOT TOUCH

  'file://' + path IS NOT A VALID FILE URL ON WINDOWS. The drive letter
  lands in the URL's authority slot and the separators are backslashes;
  Chromium repairs it, and has repaired it every day for months.
  pathlib.Path(p).as_uri() is the written-down form. There are 53 such
  sites in 35 tools and NOT ONE of them has a failure attached to it, so
  correcting them belongs to a round of its own - a round that says it is
  correcting file URLs. Putting it here would make this round unable to
  answer the only question it exists to answer.

  _goto() is where that change will land, one line, once per file.

  Everything else written into the repo root. test_db_error_page.py
  leaves two sample pages there; every patcher rewrites source there.
  None of it is rendered, so none of it is in scope, and none of it
  needs an exception list to say so.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_probe'
MARK = '# --- SCRATCH '

# What the rule found on 18 Sep 2026. This is a CROSS-CHECK, not the
# scope: the scope is whatever the rule finds today. A disagreement stops
# the run and prints both sides.
EXPECTED = {
    'test_accent_shades.py': ('_shades_probe.html',),
    'test_action_standard.py': ('_action_probe.html',),
    'test_button_reach.py': ('_reach_probe.html',),
    'test_card_standard.py': ('_card_actions.html', '_card_probe.html'),
    'test_detail_property.py': ('_detail_probe.html',),
    'test_filter_toggle.py': ('_filt_%s.html',),
    'test_pl_indicators.py': ('_pl_picker_probe.html',),
    'test_sticky_cue.py': ('_cue_probe.html',),
    'test_table_lease_agreement.py': ('_sup_probe.html',),
    'test_table_polish.py': ('_polish_probe.html',),
    'test_table_properties.py': ('_sup_probe.html',),
    'test_table_standard.py': ('_table_probe.html',),
    'test_table_suppliers.py': ('_sup_probe.html',),
    'test_table_tenant_report.py': ('_report_probe.html',),
    'test_table_tenants.py': ('_sup_probe.html',),
}

# The name four of them share. Named here so the report can say so.
SHARED = '_sup_probe.html'

PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_probe_location.py'
GATE_ENTRY = """    # A fixture belongs to ONE process. Four suites used to build
    # _sup_probe.html in this directory; on this list two of them run back
    # to back, and the second was answered with net::ERR_FAILED. Every
    # fixture now lives in a mkdtemp directory, and this is what says so.
    '%s'
""" % SUITE

BLOCK = '''
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
'''

AGOTO = '''

async def _agoto(pg, path):
    """_goto, for the one suite that drives Playwright asynchronously."""
    try:
        await pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
'''

TAIL = '# ------------------------------------------------------------------------\n'


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def fixtures(src):
    """A ROOT-built path this tool WRITES and then HANDS TO THE BROWSER.

    THE RULE, and the first draft of it was wrong in a way worth keeping
    on the page. It said "a ROOT-built path opened for writing", and on
    the real tree that is 28 patchers: apply_table_standard.py writes
    pages/templates/base.html, apply_open_items.py writes .gitignore,
    apply_invoice_verification.py writes requirements.txt. Writing source
    into the working tree is what a patcher is FOR. The rule stopped the
    run and wrote nothing, which is the one thing it got right.

    A BROWSER FIXTURE is the narrower thing this round is about: a file
    written so that Chromium can be pointed at it with file://. So the
    rule asks for both halves - written here, and navigated to. No
    apply_*.py in this repo contains the word goto; neither .gitignore
    nor requirements.txt nor base.html is ever navigated to. That is what
    makes this a rule rather than a list of names I happened to know.

    Returns [(var, literal, start, end)] spanning the ROOT token only.
    """
    out = []
    for m in re.finditer(
            r"(\w+)\s*=\s*os\.path\.join\(\s*(ROOT)\s*,\s*(['\"])(.+?)\3",
            src):
        var, lit = m.group(1), m.group(4)
        if not re.search(r"open\(\s*%s\s*,\s*['\"]w" % re.escape(var), src):
            continue
        # HANDED TO THE BROWSER, in either shape. Before this round that
        # is goto('file://' + name); after it, _goto(pg, name). Asking
        # only for the first made the rule blind to its own output - a
        # suite that moved its fixture BACK into the repo root passed,
        # which a sabotage run found and is the only reason this line
        # has two alternatives in it.
        if not re.search(
                r"(?:goto\(\s*'file://'\s*\+\s*%s\s*\)"
                r"|_a?goto\(\s*\w+\s*,\s*%s\s*\))"
                % (re.escape(var), re.escape(var)), src):
            continue
        out.append((var, lit, m.start(2), m.end(2)))
    return out


def gotos(src, names):
    """goto sites whose path is one of the names we are moving.

    Returns [(is_await, whole_span, page_var, path_var)].
    """
    out = []
    for m in re.finditer(
            r"(await\s+)?(\w+)\.goto\(\s*'file://'\s*\+\s*(\w+)\s*\)", src):
        if m.group(3) not in names:
            continue
        out.append((bool(m.group(1)), m.span(), m.group(2), m.group(3)))
    return out


def finished(src):
    """Already done? Both halves, not just the marker."""
    if MARK not in src:
        return False
    if 'SCRATCH = _tempfile.mkdtemp' not in src:
        return False
    return not fixtures(src)


def plan_gate(problems):
    """The new suite joins the list the gate runs.

    A suite nobody runs is a comment. Inserted at the END of $suites, after
    the last entry, because it is the newest thing here.
    """
    path = os.path.join(ROOT, PS1)
    if not os.path.exists(path):
        problems.append('%s not found - run from the repo root' % PS1)
        return None
    text, nl, raw = read(path)
    if "'%s'" % SUITE in text:
        return None
    i = text.find('$suites = @(')
    if i < 0:
        problems.append('%s: no $suites = @( to add to' % PS1)
        return None
    j = text.find('\n)', i)
    if j < 0:
        problems.append('%s: $suites = @( is not closed' % PS1)
        return None
    # The last entry has no trailing comma, so one has to be added to it.
    before = text[:j]
    k = before.rfind("'")
    if k < 0:
        problems.append('%s: could not find the last suite entry' % PS1)
        return None
    new = before[:k + 1] + ',\n' + GATE_ENTRY.rstrip('\n') + text[j:]
    n_before = len(re.findall(r"^\s*'test_[\w]+\.py',?", text, re.M))
    n_after = len(re.findall(r"^\s*'test_[\w]+\.py',?", new, re.M))
    if n_after != n_before + 1:
        problems.append('%s: the list went from %d to %d entries, not %d'
                        % (PS1, n_before, n_after, n_before + 1))
        return None
    return (PS1, path, text, new, nl, raw)


def plan(problems):
    out = []
    found = {}

    for name in sorted(os.listdir(ROOT)):
        if not name.endswith('.py'):
            continue
        if not (name.startswith('test_') or name.startswith('Show-')
                or name.startswith('apply_')):
            continue
        # This patcher holds the inserted block as a string, and the suite
        # holds example paths for its own controls. Both would match the
        # rule, and neither renders anything. The suite enumerates its own
        # examples in section 1 rather than being trusted here.
        if name in (os.path.basename(__file__), SUITE):
            continue
        path = os.path.join(ROOT, name)
        text, nl, raw = read(path)

        if finished(text):
            continue

        fx = fixtures(text)
        if not fx:
            continue
        found[name] = tuple(sorted(set(lit for _v, lit, _a, _b in fx)))

    # THE CROSS-CHECK. The scope is what the rule found; EXPECTED is what
    # it found on the day this was written. Disagreement is not something
    # to patch around - it means the tree moved, or my copy is stale, and
    # the last time I assumed otherwise I reported two files as changed
    # that this patcher had never touched.
    already = set(EXPECTED) - set(found)
    for name in sorted(set(found) - set(EXPECTED)):
        problems.append('%s writes a fixture into the repo root and is not '
                        'in EXPECTED: %s' % (name, ', '.join(found[name])))
    for name in sorted(already):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            problems.append('%s: in EXPECTED but not in this checkout' % name)
        elif not finished(read(p)[0]):
            problems.append('%s: in EXPECTED, present, and the rule finds no '
                            'fixture in it - my copy may be stale' % name)
    for name in sorted(set(found) & set(EXPECTED)):
        if found[name] != tuple(sorted(EXPECTED[name])):
            problems.append('%s: found %s, EXPECTED %s'
                            % (name, ', '.join(found[name]),
                               ', '.join(sorted(EXPECTED[name]))))

    if problems:
        return []

    for name in sorted(found):
        path = os.path.join(ROOT, name)
        text, nl, raw = read(path)
        fx = fixtures(text)
        names = set(v for v, _l, _a, _b in fx)

        if 'SCRATCH' in re.findall(r'^\s*(\w+)\s*=', text, re.M):
            problems.append('%s: already binds the name SCRATCH' % name)
            continue

        m = re.search(r'^ROOT\s*=\s*os\.path\.dirname.*$', text, re.M)
        if not m:
            problems.append('%s: no ROOT = os.path.dirname(...) line to '
                            'insert after' % name)
            continue

        # 1. the fixtures move. Replace only the ROOT TOKEN inside each
        #    join call - nothing else on the line is touched.
        new = text
        for _v, _l, a, b in sorted(fx, key=lambda x: -x[2]):
            new = new[:a] + 'SCRATCH' + new[b:]

        # 2. the navigations report. THE SPANS ARE RE-FOUND on the text
        #    step (1) produced, not carried over from before it: ROOT is
        #    four characters and SCRATCH is seven, so every span after a
        #    fixture line had moved by three per replacement. The
        #    self-check below caught that as a parse error on all fifteen
        #    files at once, which is the only reason it is not in the
        #    version you are reading.
        gs = gotos(new, names)
        n_sync = n_async = 0
        for is_await, (a, b), pgv, pv in sorted(gs, key=lambda x: -x[1][0]):
            if is_await:
                rep = 'await _agoto(%s, %s)' % (pgv, pv)
                n_async += 1
            else:
                rep = '_goto(%s, %s)' % (pgv, pv)
                n_sync += 1
            new = new[:a] + rep + new[b:]

        # 3. the block goes in after ROOT, so SCRATCH exists before the
        #    first use of it further down the file.
        block = BLOCK + (AGOTO if n_async else '') + TAIL
        at = new.index('\n', new.index(m.group(0))) + 1
        new = new[:at] + block + new[at:]

        # ----------------------------------------------- SELF-CHECK
        bad = []
        try:
            ast.parse(new)
        except SyntaxError as e:
            bad.append('it no longer parses (%s)' % e)
        if fixtures(new):
            bad.append('a ROOT-built fixture survives')
        if new.count('SCRATCH = _tempfile.mkdtemp') != 1:
            bad.append('SCRATCH is not defined exactly once')
        first_use = re.search(r'os\.path\.join\(\s*SCRATCH', new)
        if first_use and first_use.start() < new.index(
                'SCRATCH = _tempfile.mkdtemp'):
            bad.append('SCRATCH is used before it is defined')
        if n_async and 'async def _agoto' not in new:
            bad.append('an await site was rewritten with no _agoto to call')
        if not n_async and '_agoto' in new:
            bad.append('_agoto was inserted with nothing to call it')
        # NOTHING ELSE MAY HAVE MOVED. Undo the two substitutions on the
        # new text and require the original back, byte for byte.
        undo = new.replace(block, '', 1)
        undo = re.sub(r'os\.path\.join\(\s*SCRATCH\s*,',
                      lambda mm: mm.group(0).replace('SCRATCH', 'ROOT'), undo)
        undo = re.sub(r'await _agoto\((\w+), (\w+)\)',
                      r"await \1.goto('file://' + \2)", undo)
        undo = re.sub(r'(?<!await )_goto\((\w+), (\w+)\)',
                      r"\1.goto('file://' + \2)", undo)
        if undo != text:
            bad.append('something outside the fixture paths and the goto '
                       'calls changed')

        for x in bad:
            problems.append('%s: %s' % (name, x))
        if not bad:
            out.append((name, path, text, new, nl, raw, found[name],
                        n_sync, n_async))
    return out


def main():
    check_only = '--check' in sys.argv
    problems = []
    todo = plan(problems)
    gate = plan_gate(problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('')
    print('  BROWSER FIXTURES LEAVE THE REPO ROOT')
    print('')
    if not todo and not gate:
        print('    no tool writes a fixture into the repo root, and the new')
        print('    suite is already on the gate - nothing to do. (Run it')
        print('    twice; this is what the second run says.)')
        return
    if not todo:
        print('    no tool writes a fixture into the repo root - that half')
        print('    is already done.')

    shared = [n for n, _p, _t, _nw, _nl, _r, lits, _s, _a in todo
              if SHARED in lits]
    for name, _p, _t, _nw, _nl, _r, lits, ns, na in todo:
        mark = '  <-- the shared name' if SHARED in lits else ''
        print('    %-30s %-34s %d goto(s)%s'
              % (name[:30], ', '.join(lits)[:34], ns + na, mark))
    if todo:
        print('')
        print('    %d tool(s), %d fixture(s). %d of them wrote %s into one'
              % (len(todo), sum(len(l) for _a1, _a2, _a3, _a4, _a5, _a6, l,
                                _a7, _a8 in todo), len(shared), SHARED))
        print('    directory, which is the collision this round exists to')
        print('    end.')
        print('')
        print('    Each now uses tempfile.mkdtemp(), which is unique per')
        print('    PROCESS - so the gate\'s order and the audit\'s order can')
        print('    no longer disagree, and nothing lands in the working')
        print('    tree.')

    print('')
    print('  THE GATE')
    if gate:
        print('    %s joins $suites. A suite nobody runs is a comment.'
              % SUITE)
    else:
        print('    %s is already on it - nothing to do.' % SUITE)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for name, path, _t, new, nl, raw, _l, _s, _a in todo:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)
    if gate:
        _n, path, _t, new, nl, raw = gate
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.'
          % SUFFIX)
    print('  Now run:  python %s' % SUITE)


if __name__ == '__main__':
    main()
