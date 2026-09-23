# -*- coding: utf-8 -*-
"""apply_small_three.py - Section D, round D2: three small fixes.

    python apply_small_three.py --check     dry run, nothing written
    python apply_small_three.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 23 Sep, from claude/d2_small_fixes_survey.md. Three unrelated
pages, three unrelated one-line-ish faults, one round - because each is
separately provable and none of them touches the other.

  1. WORKSPACE MANAGEMENT'S HELP BUTTON WEARS A BACK LABEL.
     `<span class="action-back-label"> Help</span>` on a button that is
     `.action-secondary`, not `.action-back`. Base's hide rule is scoped
     to `.action-back`, so nothing breaks TODAY - but 74 other pages
     carry their own UNSCOPED copy of that rule, and the day this page
     gains one, the word Help disappears on a phone and leaves a bare
     question mark. 18 of the system's 20 Help buttons write bare text.
     This one joins them.

  2. THE COUNTRY FILTER IS TYPED INTO THE TEMPLATE, ON TWO PAGES.
     properties.html and fsr.html both filter `props.prop_country`, and
     both offer Cyprus / Greece / Spain because somebody typed those
     three names into the markup. Buy a property in Portugal and it is
     invisible to both filters for ever. finance_expense_add and
     finance_expense_edit already read the list from the data; these two
     now do the same, from the same queryset.

     NOT properties_add.html or properties_edit.html. Those are ENTRY
     forms: a list drawn from existing data would make it impossible to
     add the first property in a new country. A fixed list is correct
     there, and changing it would be a bug, not a fix.

  3. VACANCY MANAGEMENT'S SELECT ALL IS A PRIMARY BUTTON.
     Section D called it "Bootstrap blue". MEASURED, it is not: base
     repaints `.btn-info` to the house accent, so Select All renders as a
     SOLID TEAL button - which base's own standard reserves for "the one
     main thing you came to do". Selecting every property is not that.
     Select None beside it is `.btn-secondary`, raw Bootstrap grey, which
     is not a house colour at all.

     Its twin proves the target: finance/financial_indicators.html has
     the identical widget - same `selection-buttons` wrapper, same
     selectAllBtn / selectNoneBtn ids, same property-grid - written as
     `btn action-secondary`. This page joins it, and the page's own
     `.btn-sm` rules go with the class, since nothing else wore it.

     Measured before and after, at 1280 and at 375:
       now    desk 34px, solid #0e7c8b / #6c757d ; phone 40px
       after  desk 38px, outlined               ; phone 44px
     The 44 is not new CSS - C2's ALV TAP TARGET block already floors
     `.btn.action-secondary` at 44px on a phone, and the rename simply
     lets it apply. The phone's full-width split is kept, by moving the
     `flex: 1` off `.btn-sm` and onto `.btn`.

Nothing else in Section D is touched here: D1 took the dead files, and
the leftover Bootstrap buttons and act_expense's literals are D3.
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

import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_three'
SUITE = 'test_small_three.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'

WSM = os.path.join(T, 'workspace_management.html')
PROPS_HTML = os.path.join(T, 'properties.html')
PROPS_VIEW = os.path.join('pages', 'views', 'properties.py')
FSR_HTML = os.path.join(T, 'fsr.html')
FSR_VIEW = os.path.join('pages', 'views', 'issues.py')
VAC = os.path.join(T, 'finance', 'vacancy_management.html')

# The one line the whole system already writes, kept as one string so the
# suite can hold the patcher to the same spelling.
COUNTRIES = ("props.objects.values_list('prop_country', flat=True)"
             ".distinct().order_by('prop_country')")

EDITS = {}

# ==========================================================================
# 1. The Help button stops calling itself Back
# ==========================================================================
EDITS[WSM] = [(
    '            <i class="fas fa-question-circle"></i>'
    '<span class="action-back-label"> Help</span>\n',
    '            <i class="fas fa-question-circle"></i> Help\n')]

# ==========================================================================
# 2. The country filter comes from the data - properties, then FSR
# ==========================================================================
# The view. `results` is already filtered by the time the context is built,
# so the list has to come from props.objects, not from results - otherwise
# picking Greece would leave Greece as the only country you could pick.
EDITS[PROPS_VIEW] = [(
    "    context = {\n"
    "        'props': results,\n"
    "        'search_query': search_query,\n",
    "    context = {\n"
    "        'props': results,\n"
    "        # The filter's countries are the ones properties are actually\n"
    "        # IN, read from the data - not three names typed into the\n"
    "        # markup. From props.objects and not from `results`, which is\n"
    "        # already filtered: the list must not narrow to the choice\n"
    "        # just made. Same line as finance_expense_add/_edit. [D2]\n"
    "        'countries': %s,\n"
    "        'search_query': search_query,\n" % COUNTRIES)]

EDITS[PROPS_HTML] = [(
    '            <select name="country" class="form-control filter-select" '
    'id="countrySelect">\n'
    '              <option value="">All Countries</option>\n'
    "              <option value=\"Cyprus\" {% if selected_country == 'Cyprus' "
    '%}selected{% endif %}>Cyprus</option>\n'
    "              <option value=\"Greece\" {% if selected_country == 'Greece' "
    '%}selected{% endif %}>Greece</option>\n'
    "              <option value=\"Spain\" {% if selected_country == 'Spain' "
    '%}selected{% endif %}>Spain</option>\n'
    '            </select>\n',
    '            <select name="country" class="form-control filter-select" '
    'id="countrySelect">\n'
    '              <option value="">All Countries</option>\n'
    '              {# The countries properties are in, from the view. [D2] #}\n'
    '              {# `if c` skips the blank one: prop_country is nullable, #}\n'
    '              {# and a blank option would read as a second "All". #}\n'
    '              {# No hardcoded fallback - an empty list means there are #}\n'
    '              {# no properties, and offering ones you cannot pick lies. #}\n'
    '              {% for c in countries %}{% if c %}\n'
    '              <option value="{{ c }}"'
    ' {% if selected_country == c %}selected{% endif %}>{{ c }}</option>\n'
    '              {% endif %}{% endfor %}\n'
    '            </select>\n')]

# fsr_details() further down this file opens its context with the same
# three lines, and it has no country filter. The anchor runs on to
# "search_query", which only fsr() carries.
EDITS[FSR_VIEW] = [(
    '    context = {\n'
    '        "props": results,\n'
    '        "issues": isresults,\n'
    '        "issues_details": idresults,\n'
    '        "search_query": search_query,\n',
    '    context = {\n'
    '        "props": results,\n'
    '        # The same list as properties.html, from the same field and\n'
    '        # the same queryset, so the two filters can never disagree.\n'
    '        # props.objects, not `results`, which is already filtered. [D2]\n'
    '        "countries": %s,\n'
    '        "issues": isresults,\n'
    '        "issues_details": idresults,\n'
    '        "search_query": search_query,\n' % COUNTRIES)]

EDITS[FSR_HTML] = [(
    '                    <select name="propcountry" class="form-control '
    'filter-select" id="countrySelect">\n'
    '                        <option value="">All Countries</option>\n'
    '                        <option value="Cyprus" {% if '
    "request.POST.propcountry == 'Cyprus' %}selected{% endif %}>Cyprus"
    '</option>\n'
    '                        <option value="Greece" {% if '
    "request.POST.propcountry == 'Greece' %}selected{% endif %}>Greece"
    '</option>\n'
    '                        <option value="Spain" {% if '
    "request.POST.propcountry == 'Spain' %}selected{% endif %}>Spain"
    '</option>\n'
    '                    </select>\n',
    '                    <select name="propcountry" class="form-control '
    'filter-select" id="countrySelect">\n'
    '                        <option value="">All Countries</option>\n'
    '                        {# The countries properties are in, from the view - #}\n'
    '                        {# the same list properties.html now shows. [D2] #}\n'
    '                        {# `selected_country`, not request.POST: the view #}\n'
    '                        {# already strips it and already passes it. #}\n'
    '                        {% for c in countries %}{% if c %}\n'
    '                        <option value="{{ c }}"'
    ' {% if selected_country == c %}selected{% endif %}>{{ c }}</option>\n'
    '                        {% endif %}{% endfor %}\n'
    '                    </select>\n')]

# ==========================================================================
# 3. Select All stops claiming to be the page's main action
# ==========================================================================
EDITS[VAC] = [(
    '                        <button class="btn btn-info btn-sm" '
    'id="selectAllBtn">Select All</button>\n'
    '                        <button class="btn btn-secondary btn-sm" '
    'id="selectNoneBtn">Select None</button>\n',
    '                        <button class="btn action-secondary" '
    'id="selectAllBtn">Select All</button>\n'
    '                        <button class="btn action-secondary" '
    'id="selectNoneBtn">Select None</button>\n'), (
    # The desk rule. Nothing else on this page wore .btn-sm - counted, and
    # the suite counts it again - so the rule goes with the class rather
    # than sitting here naming nobody.
    '.btn-sm {\n'
    '    padding: 6px 12px;\n'
    '    font-size: 13px;\n'
    '    border-radius: 6px;\n'
    '}\n',
    ''), (
    # The phone rule. `flex: 1` is LAYOUT, not dialect - it is what makes
    # the two buttons split the row on a phone, and the twin page does not
    # do that because its pair sits in a header, not on its own line. So
    # the stretch is kept and simply re-aimed at .btn. The padding goes:
    # 9px was this page's own way of reaching for a bigger target, and C2's
    # 44px floor does that properly now.
    '    .selection-buttons .btn-sm {\n'
    '        flex: 1;\n'
    '        padding: 9px 12px;\n'
    '    }\n',
    '    /* The two buttons split the row on a phone. Height is not set\n'
    '       here: they are .action-secondary now, and base\'s ALV TAP\n'
    '       TARGET block floors every house button at 44px below 768. */\n'
    '    .selection-buttons .btn {\n'
    '        flex: 1;\n'
    '    }\n')]

# ==========================================================================
# LATER - test_button_sweep.py
# ==========================================================================
# That suite counts the Bootstrap-toned buttons built INSIDE a <script>,
# and it named this exact round in advance:
#
#   "The day a round decides vacancy_management's identical pair this
#    control will read seven, and the fix is to name that round's snapshot
#    here - NOT to lower the number."
#
# So its two HISTORICAL counts are re-pointed at the page as the BUTTON
# SWEEP left it, which is this round's backup - the claim about what the
# sweep found stays true, and stays eight. The one LIVE floor does come
# down, because it counts what is still undone and two of those are now
# done; the suite's own named list (cashflow_forecast 3, asset_detail 1)
# pins it exactly, and its scanner-level CONTROL - "would still see one on
# the day no page has any" - is what actually guards the scan.
SWEEP = 'test_button_sweep.py'
SWEEP_EDITS = [(
    "_LATER = {'finance/financial_indicators.html': '.bak_fiseg'}\n",
    "_LATER = {'finance/financial_indicators.html': '.bak_fiseg',\n"
    "          # D2, 23 Sep: this page's Select All / Select None are now\n"
    "          # house secondaries, decided the same way as the twin above.\n"
    "          'finance/vacancy_management.html': '.bak_three'}\n"), (
    "      len(_all) >= 6 and len(_js) >= 3)\n",
    "      # 6 in 3 until D2 decided vacancy_management's pair. What is\n"
    "      # left is the four this suite names below, on two pages.\n"
    "      len(_all) >= 4 and len(_js) >= 2)\n")]

report, problems, planned = [], [], {}
CRLF = {}

WHY = {
    WSM: 'Help is bare text, like the other 18',
    PROPS_VIEW: 'passes the countries properties are in',
    PROPS_HTML: 'the country filter reads the data',
    FSR_VIEW: 'passes the same list, from the same field',
    FSR_HTML: 'the country filter reads the data',
    VAC: 'Select All/None are house secondaries; .btn-sm retired',
    SWEEP: 'LATER: judges the sweep on the page the sweep left',
}
EDITS[SWEEP] = SWEEP_EDITS


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


for path in (WSM, PROPS_VIEW, PROPS_HTML, FSR_VIEW, FSR_HTML, VAC, SWEEP):
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n, done = src, 0, 0
    for old, new in EDITS[path]:
        if new and new in cur:
            done += 1
            continue
        if not new and old not in cur:
            done += 1
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (path, cur.count(old), old.strip()[:56]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n and path.endswith('.py'):
        try:
            compile(cur, path, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (path, e.lineno))
    if n:
        planned[path] = (src, cur)
        report.append('%-42s %s (%d edit(s))'
                      % (os.path.basename(path), WHY[path], n))
    elif done == len(EDITS[path]):
        report.append('%-42s already done' % os.path.basename(path))

# --- self-checks: what the round must NOT have done ---------------------
for path, (src, cur) in list(planned.items()):
    if path == VAC:
        if 'btn-sm' in cur:
            problems.append('%s: a .btn-sm is left behind' % path)
        if 'btn-info' in cur or 'btn-secondary' in cur:
            problems.append('%s: a Bootstrap tone is left behind' % path)
        if cur.count('flex: 1;') != src.count('flex: 1;'):
            problems.append('%s: the phone stretch was lost' % path)
    if path in (PROPS_HTML, FSR_HTML):
        # A Django {# #} comment is SINGLE LINE. Open one and close it on
        # the next and the parser never sees a comment at all - it renders
        # the whole thing as text, inside the <select> in this case. The
        # first draft of this round did exactly that, and test_delete_choice
        # caught it on the sweep. Caught here now as well, so the patcher
        # cannot write one again.
        for i, line in enumerate(cur.split('\n'), 1):
            if '{#' in line and '#}' not in line:
                problems.append('%s:%d opens a {# comment it does not close '
                                'on the same line - it would RENDER'
                                % (path, i))
        for word in ('Cyprus', 'Greece', 'Spain'):
            if word in cur:
                problems.append('%s: %s is still typed into the markup'
                                % (path, word))
        if cur.count('{% for') != src.count('{% for') + 1 \
                or cur.count('{% endfor %}') != src.count('{% endfor %}') + 1:
            problems.append('%s: the loop is not balanced' % path)
        if cur.count('{% if') - cur.count('{% endif %}') \
                != src.count('{% if') - src.count('{% endif %}'):
            problems.append('%s: the if/endif count moved' % path)
    if path in (PROPS_VIEW, FSR_VIEW):
        # The line this round ADDS, not the file - issues.py reads
        # `results.values_list('prop_id')` twice of its own accord, and
        # those are not this round's business.
        added = [ln for ln in cur.split('\n') if ln not in src.split('\n')]
        mine = '\n'.join(ln for ln in added if 'values_list' in ln)
        if 'props.objects.values_list' not in mine:
            problems.append('%s: the countries line is not the house one'
                            % path)
        if re.search(r'(?<!props\.objects\.)\bresults\.values_list', mine):
            problems.append('%s: the list was read from the filtered '
                            'queryset' % path)
    # An entry form is not a filter. If either Add/Edit screen has lost
    # its fixed list, this round has gone somewhere it was told not to.
for entry in ('properties_add.html', 'properties_edit.html'):
    p = os.path.join(T, entry)
    if os.path.isfile(p) and 'Cyprus' not in read(p):
        problems.append('%s: the ENTRY form lost its country list - an Add '
                        'screen must offer countries no property is in yet'
                        % entry)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-42s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_dead',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_dead) - '
                        'apply_dead_files.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_dead',\n]", "    '.bak_dead',\n    '%s',\n]" % SUFFIX,
            1))
        report.append('%-42s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D2: the Help label, the country filter read from
    # the data, and Select All as a secondary,
    'test_small_three.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-42s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION D, ROUND D2 - THREE SMALL FIXES - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
