#!/usr/bin/env python
"""
fix_login_csrf.py — make the login page always hand out a fresh CSRF cookie.

Symptom this fixes: after a deploy/restart, visiting /login/ with no prior
csrftoken cookie can produce a login form whose token doesn't validate, so the
POST fails with 403 "CSRF verification failed / CSRF token missing".

The fix: decorate the `login_user` view with Django's @ensure_csrf_cookie, which
forces the GET /login/ response to set the csrftoken cookie every time. The
form's {% csrf_token %} then always has a matching cookie to validate against.

Run from the project root (where manage.py lives):

    python fix_login_csrf.py             # apply (backs up the file once)
    python fix_login_csrf.py --dry-run   # preview only, writes nothing

Safe: idempotent (re-running makes no further changes) and non-destructive
(the file it edits is copied to <file>.bak_csrf first, once).
"""
import os
import re
import sys

DRY = '--dry-run' in sys.argv

IMPORT_LINE = "from django.views.decorators.csrf import ensure_csrf_cookie"


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def find_py(root, needle):
    """First .py under root whose text contains `needle`."""
    for dirpath, _, files in os.walk(root):
        if '__pycache__' in dirpath:
            continue
        for fn in sorted(files):
            if fn.endswith('.py'):
                p = os.path.join(dirpath, fn)
                try:
                    if needle in read(p):
                        return p
                except Exception:
                    pass
    return None


def backup(p):
    b = p + '.bak_csrf'
    if not os.path.exists(b) and not DRY:
        with open(b, 'w', encoding='utf-8') as f:
            f.write(read(p))
    return b


def write(p, text, note):
    if DRY:
        print(f"   [dry-run] would write {p}  ({note})")
        return
    backup(p)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"   [OK] {note}  -> {p} (backup: {os.path.basename(p)}.bak_csrf)")


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print("!! Run this from the project root (the folder with manage.py).")
        sys.exit(1)

    print("Applying the login CSRF cookie fix" + (" (dry run)" if DRY else "") + " ...")

    vf = find_py(os.path.join(root, 'pages'), 'def login_user(')
    if not vf:
        print("!! Could not find the view that defines login_user. Nothing changed.")
        sys.exit(1)
    print(f"Login view file: {vf}")
    text = read(vf)

    changed = False

    # 1) ensure the import is present
    if IMPORT_LINE in text:
        print("   [skip] ensure_csrf_cookie already imported")
    else:
        # place it right after the last top-of-file import line we can find,
        # or failing that, at the very top.
        m = None
        for mm in re.finditer(r'^(from|import)\s.+$', text, re.M):
            m = mm
        if m:
            insert_at = m.end()
            text = text[:insert_at] + "\n" + IMPORT_LINE + text[insert_at:]
        else:
            text = IMPORT_LINE + "\n" + text
        changed = True
        print("   [OK] added ensure_csrf_cookie import")

    # 2) decorate def login_user
    dm = re.search(r'^(\s*)def login_user\(', text, re.M)
    if not dm:
        print("   [WARN] found the file but not `def login_user(` — decorate it manually.")
    else:
        indent = dm.group(1)
        line_start = dm.start()
        # look at the line directly above the def for an existing decorator
        preceding = text[:line_start].rstrip('\n')
        last_line = preceding.split('\n')[-1] if preceding else ''
        if last_line.strip() == '@ensure_csrf_cookie':
            print("   [skip] login_user already decorated with @ensure_csrf_cookie")
        else:
            decorator = f"{indent}@ensure_csrf_cookie\n"
            text = text[:line_start] + decorator + text[line_start:]
            changed = True
            print("   [OK] decorated login_user with @ensure_csrf_cookie")

    if changed:
        write(vf, text, "updated login view")
    else:
        print("   Nothing to change — the fix is already in place.")

    print("\nDone." + (" (dry run — nothing written)" if DRY else
          "\nNext: set DEBUG back to False on Railway, commit, and push to redeploy."))


if __name__ == '__main__':
    main()