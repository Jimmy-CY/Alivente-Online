# -*- coding: utf-8 -*-
"""apply_c_small.py - Section C, round C1: five small decisions of 22 Sep.

    python apply_c_small.py --check     dry run, nothing written
    python apply_c_small.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided on the Section C sheet, 22 Sep (claude/section_c_decision_sheet.md):

  1  Customer Name is REQUIRED on the customer invoice form. It already
     wore the red star, and the server already refuses a blank name on
     create and on edit - the browser now says so before the round trip.
     A locked invoice's field is readonly, and a browser does not validate
     a readonly field, so opening a locked invoice is unaffected.
  6  The Resolved Issues report shows each comment's author as the house
     chip - .alv-tag comment-author - after the date, as the Friday Status
     Report, the FSR details page and the Comments report already do. It
     was "(DM):" in capitals, in the date's grey.
  8  "Quick Actions:" is dropped above the two Translate buttons on the
     project and project-task edit screens. It labelled no field, so it
     was a label with nothing to point at; the buttons and their help text
     say what they do.
  7  The occupancy switch's model label reads "Include in Occupancy", as
     both screens already do. Label only: migration 0094 is an AlterField
     with no database change - `migrate` on Live records it and alters
     nothing.
  10 The commented-out DATABASES block in mysite/settings.py is deleted.
     Deleted only, as decided. THIS PATCHER HOLDS NO PASSWORD AND PRINTS
     NONE: the block is found by its shape, and settings.py's backup is
     written with the two commented PASSWORD values replaced by a marker,
     so the round does not leave a fresh plain copy of them on disk.

Also, as every round: the backup suffix registered in alv_rounds.ROUNDS,
test_c_small.py added to the push gate, and one LATER edit - the check in
test_resolved_report.py that recorded the authors as "left open on
purpose" is asserted on the file as it stood before this round, with the
new record beside it.
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
SUFFIX = '.bak_csmall'
SUITE = 'test_c_small.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'

CIF = os.path.join(T, 'customer_invoice_form.html')
RIR = os.path.join(T, 'resolved_issues_report.html')
PED = os.path.join(T, 'projects', 'projects_edit.html')
PTE = os.path.join(T, 'projects', 'project_tasks_edit.html')
MODELS = os.path.join('pages', 'models.py')
SETTINGS = os.path.join('mysite', 'settings.py')
MIG_DIR = os.path.join('pages', 'migrations')
MIG_PREV = '0093_cashreceipt_edited_at_cashreceipt_edited_by'
MIG_NAME = '0094_alter_props_prop_include_in_occupancy'
MIG = os.path.join(MIG_DIR, MIG_NAME + '.py')
RSUITE = 'test_resolved_report.py'

QA = ('          <div class="form-group">\n'
      '            <label>Quick Actions:</label>\n'
      '            <div class="translation-buttons">\n')
QA_NEW = ('          <div class="form-group">\n'
          '            <div class="translation-buttons">\n')

EDITS = {
    CIF: [(
        '          <input type="text" id="bill_name" name="bill_name" class="form-control"\n'
        '                 value="{% if form_data %}{{ form_data.bill_name }}{% else %}{{ pi.bill_name }}{% endif %}"\n'
        '                 maxlength="255" {% if not editable %}readonly{% endif %}>\n',
        '          <input type="text" id="bill_name" name="bill_name" class="form-control"\n'
        '                 value="{% if form_data %}{{ form_data.bill_name }}{% else %}{{ pi.bill_name }}{% endif %}"\n'
        '                 maxlength="255" required {% if not editable %}readonly{% endif %}>\n',
    )],
    RIR: [(
        '                            <span class="comment-date">{{ comment.comment_date|date:"Y-m-d" }} ({{ comment.user|upper }}):</span>\n',
        '                            <span class="comment-date">{{ comment.comment_date|date:"Y-m-d" }}</span>\n'
        '                            <span class="alv-tag comment-author">{{ comment.user }}</span>\n',
    )],
    PED: [(QA, QA_NEW)],
    PTE: [(QA, QA_NEW)],
    MODELS: [(
        '    prop_include_in_occupancy = models.BooleanField(\n'
        '        default=True,\n'
        '        verbose_name="Include in Occupancy Metrics",\n',
        '    prop_include_in_occupancy = models.BooleanField(\n'
        '        default=True,\n'
        '        verbose_name="Include in Occupancy",\n',
    )],
    RSUITE: [(
        "check('the comment authors still show as text, which was left open on '\n"
        "      'purpose rather than folded in',\n"
        "      'comment-date' in FMK and 'alv-tag' not in FMK)\n",
        "# LATER - test_c_small.py, 22 Sep. Left open here on purpose, and then\n"
        "# decided on the Section C sheet (item 6): a chip, like every other\n"
        "# comment author. This round's call is asserted on the file as it\n"
        "# stood before round C1, and the chip as the new record.\n"
        "_F1 = (read(RIR + '.bak_csmall') if os.path.isfile(RIR + '.bak_csmall')\n"
        "       else F)\n"
        "_M1 = markup_of(_F1)\n"
        "check('the comment authors still showed as text, which was left open on '\n"
        "      'purpose rather than folded in',\n"
        "      'comment-date' in _M1 and 'alv-tag' not in _M1)\n"
        "if _F1 is not F:\n"
        "    check('  and round C1 has since made them the house chip',\n"
        "          'alv-tag comment-author' in FMK)\n",
    )],
    # LATER, added after the laptop's gate caught it: section 18 of the
    # entry-sections suite compares every label on the Projects screens
    # with its push-4 backup, to prove stripping the icons changed no
    # label's words. Dropping "Quick Actions:" (item 8) is a label this
    # round removed on purpose, so that claim is now asked of the file as
    # push 4 LEFT it (alv_rounds.as_left_by), not of the file as it is now.
    'test_entry_sections.py': [(
        "        before, after = read(bak), read(p)\n"
        "        ok(not re.search(r'<label\\b[^>]*>\\s*<i\\s', markup_only(after)),\n",
        "        before, after = read(bak), read(p)\n"
        "        # LATER - test_c_small.py, 22 Sep. Round C1 dropped the label\n"
        "        # \"Quick Actions:\" from two of these screens, as decided. The\n"
        "        # claim here - stripping the icons changed no label's words - is\n"
        "        # about push 4, so it is asked of the file as push 4 LEFT it.\n"
        "        try:\n"
        "            from alv_rounds import as_left_by as _alb\n"
        "            _left4 = _alb(p, SUFFIX4, read)\n"
        "        except Exception:\n"
        "            _left4 = after\n"
        "        ok(not re.search(r'<label\\b[^>]*>\\s*<i\\s', markup_only(after)),\n",
    ), (
        "        ok(label_text4(before) == label_text4(after),\n",
        "        ok(label_text4(before) == label_text4(_left4),\n",
    )],
}

# The migration, written in the repo's own style. Label only - Django
# records it, the database is not touched.
MIGRATION = '''# Generated for round C1 on 2026-09-22 - a label change only.
# AlterField with the same type, default and help text: Django records it
# and the database is not altered.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '%s'),
    ]

    operations = [
        migrations.AlterField(
            model_name='props',
            name='prop_include_in_occupancy',
            field=models.BooleanField(default=True, help_text='Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)', verbose_name='Include in Occupancy'),
        ),
    ]
''' % MIG_PREV

# The commented-out block, found by SHAPE: a line `#DATABASES = {`, then
# only comment lines, then `#}`, then the blank line after it. Nothing in
# this file names what the block holds.
BLOCK = re.compile(r'(?m)^#DATABASES = \{\n(?:#[^\n]*\n)*?#\}\n\n')
# For the backup: a commented PASSWORD's value, whatever it is.
PWVAL = re.compile(r'(?m)^(#\s*"PASSWORD"\s*:\s*)"[^"\n]*"')
PW_MARK = '"<removed 22 Sep - see apply_c_small.py>"'

report, problems = [], []
planned = {}
BACKUP_TEXT = {}
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


# --- the text edits ------------------------------------------------------
for path, edits in EDITS.items():
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n = src, 0
    for old, new in edits:
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (path, cur.count(old), old.strip()[:60]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        planned[path] = (src, cur)
        report.append('%-48s %d edit(s)' % (path, n))
    else:
        report.append('%-48s already done' % path)

# --- settings.py ---------------------------------------------------------
if not os.path.isfile(SETTINGS):
    problems.append('%s not found' % SETTINGS)
else:
    s = read(SETTINGS)
    found = BLOCK.findall(s)
    if not found:
        if re.search(r'(?m)^#\s*DATABASES\s*=', s):
            problems.append('settings.py: a commented DATABASES block is '
                            'there but not in the expected shape - '
                            'nothing touched')
        else:
            report.append('%-48s already has no commented DATABASES'
                          % SETTINGS)
    elif len(found) != 1:
        problems.append('settings.py: %d commented DATABASES blocks, '
                        'expected 1' % len(found))
    else:
        blk = found[0]
        lines = blk.rstrip('\n').split('\n')
        if not all(l.startswith('#') for l in lines):
            problems.append('settings.py: the block holds a live line')
        elif 'django.db.backends' not in blk:
            problems.append('settings.py: the block is not a DATABASES '
                            'setting')
        else:
            new_s = s.replace(blk, '', 1)
            # Only the block went; the live DATABASES setting is intact.
            if new_s.count('\nDATABASES = {') != 1 \
                    or 'os.getenv("MYSQLPASSWORD")' not in new_s:
                problems.append('settings.py: the live DATABASES setting '
                                'would not survive')
            try:
                compile(new_s, SETTINGS, 'exec')
            except SyntaxError as e:
                problems.append('settings.py would not compile: line %s'
                                % e.lineno)
            planned[SETTINGS] = (s, new_s)
            BACKUP_TEXT[SETTINGS] = PWVAL.sub(lambda m: m.group(1) + PW_MARK,
                                              s)
            if re.search(r'(?m)^#\s*"PASSWORD"\s*:\s*"(?!<removed)',
                         BACKUP_TEXT[SETTINGS]):
                problems.append('settings.py: the backup would still hold '
                                'a commented password')
            report.append('%-48s commented DATABASES block deleted '
                          '(%d lines)' % (SETTINGS, len(lines)))

# --- the migration -------------------------------------------------------
if not os.path.isdir(MIG_DIR):
    problems.append('%s not found' % MIG_DIR)
else:
    names = sorted(n[:-3] for n in os.listdir(MIG_DIR)
                   if re.match(r'\d{4}_.*\.py$', n))
    if os.path.isfile(MIG):
        report.append('%-48s already there' % MIG)
    elif not names or names[-1] != MIG_PREV:
        problems.append('migrations: the latest is %s, not %s - a newer '
                        'migration exists, so 0094 would be a second leaf'
                        % (names[-1] if names else 'none', MIG_PREV))
    else:
        compile(MIGRATION, MIG, 'exec')
        planned[MIG] = (None, MIGRATION)
        # Same line endings as the migration before it.
        read(os.path.join(MIG_DIR, MIG_PREV + '.py'))
        CRLF[MIG] = CRLF[os.path.join(MIG_DIR, MIG_PREV + '.py')]
        report.append('%-48s new - label only' % MIG)

# --- the round is registered, and its suite is on the gate ---------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-48s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_stddoc',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_stddoc',\n]",
            "    '.bak_stddoc',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-48s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section C round C1: Customer Name required, Resolved authors as
    # chips, Quick Actions dropped, the occupancy label, settings tidied,
    'test_c_small.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-48s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-48s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# --- self-checks on what would be written --------------------------------
if RIR in planned:
    t = planned[RIR][1]
    if '|upper' in t.split('comments-container')[1].split('{% endfor %}')[0]:
        problems.append('resolved report: the author is still upper-cased')
for p in (PED, PTE):
    if p in planned and 'Quick Actions' in planned[p][1]:
        problems.append('%s: Quick Actions survives' % p)
    if p in planned and planned[p][1].count('translation-buttons') != \
            planned[p][0].count('translation-buttons'):
        problems.append('%s: the buttons moved' % p)
if MODELS in planned:
    try:
        compile(planned[MODELS][1], MODELS, 'exec')
    except SyntaxError as e:
        problems.append('models.py would not compile: line %s' % e.lineno)
if RSUITE in planned:
    try:
        compile(planned[RSUITE][1], RSUITE, 'exec')
    except SyntaxError as e:
        problems.append('%s would not compile: line %s' % (RSUITE, e.lineno))

print('\n' + '=' * 78)
print('SECTION C, ROUND C1 - %s' % ('DRY RUN' if CHECK else 'APPLY'))
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
    if src is not None:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, BACKUP_TEXT.get(path, src))
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  settings.py\'s backup has its two commented passwords replaced by a')
print('  marker, so no fresh plain copy of them is left on disk.')
print('')
print('  Next:  python %s' % SUITE)
print('  Migration 0094 is applied by the deploy itself.')
