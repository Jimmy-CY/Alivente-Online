#!/usr/bin/env python
"""
install_passport_actions_compact.py  --  tidy the "Actions" column on the
Passport / ID management page so the View / Edit / Delete icon buttons sit on
ONE row instead of wrapping to two.

Problem: the desktop Actions cell holds three (or two) Bootstrap `btn btn-sm`
icon buttons with no wrapper. In the narrow 14%-wide column the default button
padding pushes the third button onto a second line, so the trash icon drops
under the others and the cell looks untidy.

Fix (CSS only, no HTML change): add a desktop rule that
  * keeps the row from breaking  ->  .desktop-action-cell { white-space: nowrap; }
  * shrinks each icon button      ->  smaller padding / font, tight margins
so all the icons line up side by side on a single row. The rule lives OUTSIDE
the @media(max-width:768px) block, so the mobile action bar (a separate <td>)
is completely untouched.

Edits one file (backup passport_management.html.bak_actionscompact):
  * pages/templates/passport_management.html
      - inserts the .desktop-action-cell rule right after the existing
        `.mobile-sort-control { display: none !important; }` desktop rule.

SAFE: idempotent (marker guard); exact-anchor (verified unique); preserves
CRLF/LF; --dry-run. No migration. Template/CSS only.

    python install_passport_actions_compact.py --dry-run
    python install_passport_actions_compact.py
Then restart the dev server (or redeploy) and reload the Passport management
page — the View/Edit/Delete icons sit on one line.
"""
import base64, os, sys

DRY = '--dry-run' in sys.argv

OLD = "Lm1vYmlsZS1zb3J0LWNvbnRyb2wgeyBkaXNwbGF5OiBub25lICFpbXBvcnRhbnQ7IH0="
NEW = "Lm1vYmlsZS1zb3J0LWNvbnRyb2wgeyBkaXNwbGF5OiBub25lICFpbXBvcnRhbnQ7IH0KCi8qIERlc2t0b3AgYWN0aW9ucyDigJQgY29tcGFjdCBpY29uIGJ1dHRvbnMsIGtlcHQgb24gb25lIHJvdyAqLwouZGVza3RvcC1hY3Rpb24tY2VsbCB7IHdoaXRlLXNwYWNlOiBub3dyYXA7IH0KLmRlc2t0b3AtYWN0aW9uLWNlbGwgLmJ0biB7CiAgICBwYWRkaW5nOiA0cHggOHB4OwogICAgZm9udC1zaXplOiAxMnB4OwogICAgbGluZS1oZWlnaHQ6IDE7CiAgICBtYXJnaW46IDAgMnB4OwogICAgdmVydGljYWwtYWxpZ246IG1pZGRsZTsKfQ=="

MARKER = '.desktop-action-cell { white-space: nowrap; }'


def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p, 'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p, s, nl):
    with open(p, 'w', encoding='utf-8', newline=nl) as f: f.write(s)
def b64(s): return base64.b64decode(s).decode()


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root (where manage.py lives).'); sys.exit(1)
    tpl = os.path.join(root, 'pages', 'templates', 'passport_management.html')
    if not os.path.exists(tpl):
        print('!! Could not find pages/templates/passport_management.html.'); sys.exit(1)
    print('template:', tpl + ('   (dry run)' if DRY else ''))
    print('')

    txt = read(tpl)
    if MARKER in txt:
        print('[skip] compact-actions rule already applied.'); print(''); return

    old, new = b64(OLD), b64(NEW)
    c = txt.count(old)
    if c != 1:
        print('!! desktop-rule anchor not matched (found %d).' % c)
        print('   Expected exactly one occurrence of:')
        print('     ' + old)
        print('   Nothing changed.'); sys.exit(1)

    work = txt.replace(old, new, 1)
    if work.count('{') != work.count('}'):
        print('!! brace balance changed after edit (%d { vs %d }). Nothing changed.'
              % (work.count('{'), work.count('}'))); sys.exit(1)

    if DRY:
        print('[dry-run] would add a desktop .desktop-action-cell rule:')
        print('   - white-space:nowrap  (keeps View/Edit/Delete on one row)')
        print('   - compact .btn padding/font (smaller icon buttons)')
        print('   Mobile action bar untouched.')
        print(''); return

    nl = detect_nl(tpl); bak = tpl + '.bak_actionscompact'
    if not os.path.exists(bak): write(bak, txt, nl)
    write(tpl, work, nl)
    print('[OK] passport_management.html updated (.bak_actionscompact).')
    print('')
    print('Compact actions installed. Restart the dev server / redeploy, reload the'
          ' Passport management page — the View/Edit/Delete icons now sit on one line.')


if __name__ == '__main__':
    main()