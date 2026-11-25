# -*- coding: utf-8 -*-
"""apply_ra23_criteria_table.py - round RA23, 25 Nov 2026.

RELEASE RA23 - THE CRITERIA TABLE FITS ITS CARD.

    Demetri, 25 Nov: "Why does the criteria table cut off the right hand
    information??" - seven columns needed 747px in a 680px card, and the
    house table box clips, so the edit and delete buttons were cut off.

    - acquisitions/templates/acquisitions/scenario_edit.html: six columns
      at fixed widths (Actions 92px); the field sits under the criterion's
      name instead of a column of its own.
    - acquisitions/templates/acquisitions/_style.html: table-layout fixed,
      long words wrap in their cell; the field line's look.
    - acquisitions/services.py: a year reads 1995, not 1,995; a rent rule
      reads in euros.
    - test_ra19_acquisitions_screens.py: finds the Points cell by its label,
      now the Field column has gone (says RA23).
    - Registers test_ra23_criteria_table.py (shipped beside this file).

Stands on RA22. Idempotent. Edits backed up to .bak_ra23. No migration.
    python apply_ra23_criteria_table.py --check    (changes nothing)
    python apply_ra23_criteria_table.py
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




import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_ra23'
SHIPPED = ('test_ra23_criteria_table.py',)
RETIRED = ()
# (file, the text it holds now, what it becomes) - exact, line endings
# included.
EDITS = json.loads('[["acquisitions/templates/acquisitions/scenario_edit.html", "      cell(tr, d.field_label || d.field, \'Field\');\\r\\n", "      var fld = document.createElement(\'div\');     // RA23 - the field, under the name\\r\\n      fld.className = \'acq-crit-field\';\\r\\n      fld.textContent = d.field_label || d.field;\\r\\n      first.appendChild(fld);\\r\\n"], ["acquisitions/templates/acquisitions/scenario_edit.html", "          <thead><tr><th style=\\"text-align: left; width: 24%\\">Criterion</th><th style=\\"width: 17%\\">Field</th><th style=\\"width: 27%\\">Rule</th><th style=\\"width: 9%\\">Type</th><th style=\\"width: 7%\\">Points</th><th style=\\"width: 8%\\">Checked by</th><th class=\\"desktop-action-cell cell-actions\\" style=\\"width: 8%\\">Actions</th></tr></thead>\\r\\n", "          {# RA23 - six columns, fixed widths: the field sits under the criterion\'s name (Demetri: \\"Why does the criteria table cut off the right hand information??\\" - seven columns needed 747px in a 680px card, and the Actions were clipped). #}\\r\\n          <thead><tr><th style=\\"text-align: left; width: 29%\\">Criterion</th><th style=\\"width: 21%\\">Rule</th><th style=\\"width: 16%\\">Type</th><th style=\\"width: 10%\\">Points</th><th style=\\"width: 12%\\">Checked by</th><th class=\\"desktop-action-cell cell-actions\\" style=\\"width: 92px\\">Actions</th></tr></thead>\\r\\n"], ["acquisitions/templates/acquisitions/_style.html", "  .acq-crit-table td, .acq-crit-table th { vertical-align: middle; }\\r\\n", "  .acq-crit-table td, .acq-crit-table th { vertical-align: middle; }\\r\\n  /* RA23 - fixed widths, so long words wrap in their cell rather than push\\r\\n     the Actions off the card. */\\r\\n  .acq-crit-table { table-layout: fixed; width: 100%; }\\r\\n  .acq-crit-table td { overflow-wrap: break-word; }\\r\\n  .acq-crit-table th { white-space: normal; }\\r\\n  .acq-crit-field { font-size: 12px; color: var(--alv-ink-soft); margin-top: 2px; }\\r\\n"], ["acquisitions/services.py", "    if field in (\\"price_incl_vat\\", \\"asking_price\\", \\"price_per_m2\\", \\"price_per_buildable_m2\\"):\\r\\n", "    if field in (\\"price_incl_vat\\", \\"asking_price\\", \\"price_per_m2\\", \\"price_per_buildable_m2\\",\\r\\n                 \\"monthly_rent\\"):\\r\\n"], ["acquisitions/services.py", "        return euros(x)\\r\\n", "        return euros(x)\\r\\n    if field == \\"year_built\\":       # RA23 - a year is 1995, not 1,995\\r\\n        return str(int(x))\\r\\n"], ["acquisitions/services.py", "        \\"price_per_buildable_m2\\": \\"\\u20ac\\"}\\r\\n", "        \\"price_per_buildable_m2\\": \\"\\u20ac\\", \\"monthly_rent\\": \\"\\u20ac\\"}   # RA23 - the rent too\\r\\n"], ["Push-PendingChanges.ps1", "    \'test_ra22_rules_wizard.py\'\\n", "    \'test_ra22_rules_wizard.py\',\\n    # RA23, 25 Nov 2026 - the criteria table fits its card; a year reads 1995.\\n    \'test_ra23_criteria_table.py\'\\n"], ["alv_rounds.py", "    \'.bak_ra22\',\\n", "    \'.bak_ra22\',\\n    # RA23, 25 Nov 2026 - the criteria table fits its card; a year reads 1995.\\n    \'.bak_ra23\',\\n"], ["test_ra19_acquisitions_screens.py", "        must = pg.eval_on_selector_all(\\n            \'#acqCritBody tr:first-child td\',\\n            \\"els => els.map(e => e.textContent.trim())\\")\\n        ok(len(must) > 4 and must[4] == \'\\u2014\',\\n", "        # RA23, 25 Nov 2026 - the Field column went (it sits under the\\n        # name now), so the Points cell is found by its label, not its place.\\n        must = pg.eval_on_selector_all(\\n            \'#acqCritBody tr:first-child td[data-label=\\"Points\\"]\',\\n            \\"els => els.map(e => e.textContent.trim())\\")\\n        ok(must == [\'\\u2014\'],\\n"]]')


def refuse(msg):
    raise SystemExit('RA23 REFUSED: %s' % msg)


def load(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf'


def main():
    check = '--check' in sys.argv[1:]
    ps1, _ = load('Push-PendingChanges.ps1')
    if "'test_ra23_criteria_table.py'" in ps1:
        print('RA23 already applied.')
        return 0
    if "'test_ra22_rules_wizard.py'" not in ps1:
        refuse('RA22 (apply_ra22_rules_wizard.py) is not applied - '
               'this round registers after it.')
    for rel in SHIPPED:
        if not os.path.isfile(os.path.join(ROOT, *rel.split('/'))):
            refuse('%s is not in place - it ships with this patcher; copy it '
                   'in first.' % rel)
    # A file's edits are made one after another on the same text, in the
    # order listed; every anchor must be found exactly once when its turn
    # comes, or nothing at all is written.
    texts, order = {}, []
    for rel, old, new in EDITS:
        if rel not in texts:
            texts[rel] = list(load(rel))
            order.append(rel)
        text = texts[rel][0]
        if text.count(old) != 1:
            refuse('%s: the anchor is found %d time(s), not once'
                   % (rel, text.count(old)))
        texts[rel][0] = text.replace(old, new)
    plan = [(rel, texts[rel][0], texts[rel][1]) for rel in order]
    for rel, text, bom in plan:
        if check:
            print('RA23 --check: %s would change' % rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p + SUFFIX):
            shutil.copy2(p, p + SUFFIX)
        with open(p, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))
        print('  changed %s' % rel)
    for rel in RETIRED:
        p = os.path.join(ROOT, *rel.split('/'))
        if not os.path.isfile(p):
            continue
        if check:
            print('RA23 --check: %s would be moved to %s' % (rel, SUFFIX))
            continue
        if os.path.exists(p + SUFFIX):
            os.remove(p)
        else:
            os.rename(p, p + SUFFIX)
        print('  retired %s (kept as %s)' % (rel, SUFFIX))
    if not check:
        print('RA23 applied - the criteria table fits its card. No migration.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
