# -*- coding: utf-8 -*-
"""apply_div_balance.py - three templates whose <div> tags did not pair.

    python apply_div_balance.py --check     dry run, nothing written
    python apply_div_balance.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep)

  The old list named five templates from a plain count of `<div` against
  `</div>`. Measured again with a scan that follows Django's if / elif /
  else branches - a template that opens a div in each branch and closes it
  once after the endif is balanced, and a plain count calls it broken - and
  that reads a `{% if x >= 0 %}` inside a div's attributes as part of the
  tag, which fooled its own first draft:

    fsr_email, open_invoices_report   balanced - the branch pattern
    asset_detail          +1  the Maintenance History card opens
                              <div class="table-container"> around its
                              table and never closes it, so the card
                              swallows the three modals after it
    property_detail       -2  the Property Report tab closes two divs too
                              many, ending the page's own card early
    property_report       -1  one </div> too many, which closes base's
                              content wrapper

  Nothing else in any template is unbalanced on any branch.

WHAT THIS DOES - agreed 21 Sep

  asset_detail     adds the missing </div> after the maintenance </table>
  property_detail  removes the two surplus </div> lines at the end of the
                   property-report branch - the one kept is the one at the
                   section's own indent
  property_report  removes the surplus </div> - the one at the indent of
                   nothing that is open
  test_print_queries.py judges these files as they stood before this round
  (it asserts each file it touched is its backup plus `screen and `, and
  these are three of them). test_div_balance.py joins the push gate.
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

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_divbal'
SUITE = 'test_div_balance.py'
PS1 = 'Push-PendingChanges.ps1'

report, problems = [], []
planned = {}
CRLF = {}


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


# (file, old, new) - each anchor must match exactly once, and the change is
# whole lines of </div> and nothing else.
EDITS = [
    ('asset_detail.html',
     """                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            {% if perms.auth.can_edit_properties %}
                <div class="alert alert-info maintenance-empty">""",
     """                    {% endfor %}
                </tbody>
            </table>
            </div>
        {% else %}
            {% if perms.auth.can_edit_properties %}
                <div class="alert alert-info maintenance-empty">"""),
    ('property_detail.html',
     """                            {% endif %}
                                </div>
                            </div>
                        </div>

                    {% elif box_type == 'tenant' %}""",
     """                            {% endif %}
                        </div>

                    {% elif box_type == 'tenant' %}"""),
    ('property_report.html',
     """            {% endif %}

        </div>
    </div>
</div>

<style>""",
     """            {% endif %}

    </div>
</div>

<style>"""),
]

for name, old, new in EDITS:
    path = os.path.join(ROOT, name)
    src = read(path)
    if src.count(new) == 1 and src.count(old) == 0:
        report.append('%-26s already balanced' % name)
        continue
    if src.count(old) != 1:
        problems.append('%s: anchor found %d time(s), expected 1'
                        % (name, src.count(old)))
        continue
    planned[path] = (src, src.replace(old, new, 1))
    d = new.count('</div>') - old.count('</div>')
    report.append('%-26s %+d </div>' % (name, d))

# ---- test_print_queries.py judges these as they stood before this round --
PQ = 'test_print_queries.py'
PQ_OLD = """        now = (read(p + '.bak_printbtn') if os.path.isfile(p + '.bak_printbtn')
               else read(p))"""
PQ_NEW = """        # LATER - test_div_balance.py, 21 Sep. That round fixed unpaired
        # </div> tags in three files this round had touched. The earliest
        # later round's backup is the file as this round left it.
        now = next((read(p + s) for s in ('.bak_printbtn', '.bak_divbal')
                    if os.path.isfile(p + s)), None) or read(p)"""
if os.path.isfile(PQ):
    src = read(PQ)
    if 'LATER - test_div_balance.py' in src:
        report.append('%-26s already reads the pre-round file' % PQ)
    elif src.count(PQ_OLD) != 1:
        problems.append('%s: anchor found %d time(s), expected 1'
                        % (PQ, src.count(PQ_OLD)))
    else:
        planned[PQ] = (src, src.replace(PQ_OLD, PQ_NEW, 1))
        report.append('%-26s reads the file as it was before this round' % PQ)

# ---- three more suites, found by sweeping every suite before and after -
# Each asserts something about the file as ITS round left it, and this round
# moves </div> lines in the same files:
#   test_print_queries  section 5 renders each touched page against its
#                       backup and requires the DOM to be identical;
#   test_heading_prefix / test_heading_standard  assert their round left the
#                       <div> balance where it was - +1 on asset_detail,
#                       which is exactly what this round corrects.
# Each now reads the file as it stood before this round when that backup is
# there, with the reason written in.
SUITE_EDITS = [
    ('test_print_queries.py', 'LATER - test_div_balance.py, 21 Sep. Section 5',
     """        moved = []
        for rel, p in TOUCHED:
            now, was = read(p), read(p + SUFFIX)""",
     """        moved = []
        for rel, p in TOUCHED:
            # LATER - test_div_balance.py, 21 Sep. Section 5 renders the
            # page as this round left it: the earliest later round's backup,
            # when there is one.
            now = next((read(p + s) for s in ('.bak_printbtn', '.bak_divbal')
                        if os.path.isfile(p + s)), None) or read(p)
            was = read(p + SUFFIX)"""),
    ('test_heading_prefix.py', 'LATER - test_div_balance.py',
     """    now, was = read(p), read(p + '.bak_pfx')
    t_now, t_was = title_of(now), title_of(was)""",
     """    # LATER - test_div_balance.py, 21 Sep. That round paired the <div>
    # tags this check found at +1 and left alone - correctly, it edits text.
    # The file is judged as it stood before that round.
    now = (read(p + '.bak_divbal') if os.path.isfile(p + '.bak_divbal')
           else read(p))
    was = read(p + '.bak_pfx')
    t_now, t_was = title_of(now), title_of(was)"""),
    ('test_heading_standard.py', 'LATER - test_div_balance.py',
     """    now, was = markup_of(read(p)), markup_of(read(p + '.bak_hstd'))""",
     """    # LATER - test_div_balance.py, 21 Sep. That round paired the <div>
    # tags this check found at +1 and left alone; the file is judged as it
    # stood before that round.
    now = markup_of(read(p + '.bak_divbal') if os.path.isfile(p + '.bak_divbal')
                    else read(p))
    was = markup_of(read(p + '.bak_hstd'))"""),
]
for name, marker, old, new in SUITE_EDITS:
    if not os.path.isfile(name):
        report.append('%-26s not on disk - nothing to adjust' % name)
        continue
    src = planned[name][1] if name in planned else read(name)
    if marker in src:
        report.append('%-26s already reads the pre-round file' % name)
    elif src.count(old) != 1:
        problems.append('%s: anchor found %d time(s), expected 1'
                        % (name, src.count(old)))
    else:
        orig = planned[name][0] if name in planned else src
        planned[name] = (orig, src.replace(old, new, 1))
        report.append('%-26s reads the file as it was before this round'
                      % name)

# ---- the gate -------------------------------------------------------------
GATE_NOTE = """    # Every <div> pairs, on every branch of every if. Its rendered
    # section runs three templates through Django's own engine on the
    # branch that was broken and asks the browser where the page's last
    # element landed - inside the content wrapper now, outside it (or
    # swallowed by a card) from the backups. Newest, so most likely to be
    # what breaks.
    'test_div_balance.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-26s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-26s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK - only whole </div> lines moved in the templates
# ==========================================================================
for path, (src, text) in planned.items():
    name = os.path.basename(path)
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (name, e.lineno))
        continue
    if not path.endswith('.html'):
        continue
    a, b = src.split('\n'), text.split('\n')
    import difflib
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == 'equal':
            continue
        moved = a[i1:i2] + b[j1:j2]
        if tag == 'replace' or any(x.strip() != '</div>' for x in moved):
            problems.append('%s: a line other than </div> changed' % name)

print('\n' + '=' * 74)
print('UNPAIRED DIVS - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
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
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
