# -*- coding: utf-8 -*-
"""SECTION I, ROUND I2 - A HIDE THAT LOST ITS SCOPE

Demetri, on Project Detail at 386px: "Where do I add the Task or Subtask?
Can't see the buttons on Mobile."

Because they are display: none. Three pages in the Projects module carry
this inside their phone block:

    .action-secondary { display: none; }

UNSCOPED. base's rule - the one this was copied from - is scoped, and the
scope is the entire point:

    .page-action-buttons:has(.action-more-btn) .action-secondary
        { display: none; }

base hides a secondary ONLY inside an action bar that has a More menu,
because the More menu is where those actions went. A secondary anywhere
else on the page has nowhere to go, so hiding it removes the action.

WHAT VANISHES ON A PHONE, counted per page:

    projects_detail       Gantt Chart, Duplicate Project, Add Task,
                          Add Subtask, Add First Task, Cancel x4, Delete
    projects              Help
    project_task_list     one Greek-language conditional

The projects_detail list is the one that matters. Five of those ten are
inside MODALS - four Cancel buttons and a Delete confirmation - so on a
phone that page has had dialogs you could open and not answer. The three
Add buttons are the ones Demetri went looking for.

THE FIX IS TO DELETE THE RULE, not to rewrite it. base already carries
the scoped version, and all three pages have a More menu, so the bar
behaves exactly as it did - Help still moves into the menu on a phone.
Everything that was never in a bar simply stops disappearing.

Backups: .bak_secscope. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_secscope'
CRLF = {}

PAGES = (os.path.join('projects', 'project_task_list.html'),
         os.path.join('projects', 'projects.html'),
         os.path.join('projects', 'projects_detail.html'))

DEAD = re.compile(r'(?m)^[ \t]*\.action-secondary\s*\{[^}]*display\s*:\s*none'
                  r'[^}]*\}\n?')

NOTE = """        /* `.action-secondary { display: none; }` was here, unscoped,
           and it hid every secondary on the page below 768px - not just
           the ones in the action bar. On Project Detail that was Gantt
           Chart, Duplicate Project, Add Task, Add Subtask, Add First
           Task, four modal Cancels and a Delete confirmation. Demetri
           went looking for Add Task on a phone and there was nothing
           there.

           base has the scoped version - it hides a secondary only
           inside a bar that HAS a More menu to hold it - and every one
           of these pages has that menu, so the bar is unchanged.
           30 Sep 2026.                 [test_secondary_scope.py] */
"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('I2: %s is not a byte copy' % bak)


def secondaries(text):
    """Every .action-secondary control on the page, with its label."""
    b = re.sub(r'<(script|style)\b.*?</\1>', '',
               re.sub(r'<!--.*?-->', '', text, flags=re.S), flags=re.S)
    out = []
    for m in re.finditer(r'<a[^>]*class="[^"]*action-secondary[^"]*"[^>]*>'
                         r'(.*?)</a>'
                         r'|<button[^>]*class="[^"]*action-secondary[^"]*"'
                         r'[^>]*>(.*?)</button>', b, re.S):
        txt = ' '.join((m.group(1) or m.group(2) or '').split())
        out.append(re.sub(r'<[^>]+>', '', txt).strip()[:24] or '(icon only)')
    return out


# ==========================================================================
print('=' * 74)
print('SECTION I, ROUND I2 - A HIDE THAT LOST ITS SCOPE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# base MUST already carry the scoped version, or deleting these would
# change the bar as well as the page.
b = read(alv_tree.path_of('base.html'))[0]
bcss = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
    re.findall(r'<style\b[^>]*>(.*?)</style>', b, re.S)), flags=re.S)
if not re.search(r'\.page-action-buttons:has\(\.action-more-btn\)\s*'
                 r'\.action-secondary\s*\{[^}]*display\s*:\s*none', bcss):
    raise SystemExit('I2: base does not carry the scoped rule, so deleting '
                     'the page copies would change the action bar too')
print('  base carries the scoped rule - a secondary hides only in a bar')
print('  that HAS a More menu to hold it')

EDITED = {}
done = 0
for rel in PAGES:
    p = alv_tree.join(rel)
    if not os.path.isfile(p):
        raise SystemExit('I2: %s is not where alv_tree says' % rel)
    t, raw = read(p)
    shown = rel.replace(os.sep, '/')
    if 'test_secondary_scope.py' in t:
        print('  %-40s already done' % shown)
        continue

    a = t.find('<style')
    z = t.find('</style>', a)
    if a < 0 or z < 0:
        raise SystemExit('I2: %s has no style block' % shown)
    css = t[a:z]
    hits = DEAD.findall(css)
    if len(hits) != 1:
        raise SystemExit('I2: %s - %d unscoped hide(s), not 1'
                         % (shown, len(hits)))
    at = DEAD.search(css).start()
    depth = css.count('{', 0, at) - css.count('}', 0, at)
    if depth != 1:
        raise SystemExit('I2: %s - the rule is at depth %d, not inside a '
                         'media block' % (shown, depth))
    # THE PAGE MUST HAVE A MORE MENU, or deleting this would leave its
    # bar secondaries on screen where they were meant to move into it.
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
    if 'action-more' not in body:
        raise SystemExit('I2: %s has no More menu, so base\'s scoped rule '
                         'would not hide its bar secondaries' % shown)

    lost = secondaries(t)
    css2 = css[:at] + eol(p, NOTE) + DEAD.sub('', css[at:])
    t = t[:a] + css2 + t[z:]
    print('  %-40s %d control(s) stop vanishing' % (shown, len(lost)))
    for x in lost[:6]:
        print('       %s' % x)
    if len(lost) > 6:
        print('       ... and %d more' % (len(lost) - 6))

    # GATES.
    left = re.sub(r'/\*.*?\*/', ' ', t[a:t.find('</style>', a)], flags=re.S)
    if DEAD.search(left):
        raise SystemExit('I2: %s still hides them' % shown)
    # AND NOTHING ELSE ON THE PAGE HIDES A SECONDARY UNSCOPED.
    for m in re.finditer(r'([^{}]*\.action-secondary[^{}]*)\{([^}]*)\}', left):
        sel = ' '.join(m.group(1).split())
        if 'display: none' in ' '.join(m.group(2).split()) \
                and 'page-action-buttons' not in sel:
            raise SystemExit('I2: %s still hides a secondary outside a bar: '
                             '%s' % (shown, sel[:60]))
    # THE MARKUP IS NOT TOUCHED.
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
    if strip(raw.decode('utf-8')) != strip(t):
        raise SystemExit('I2: %s - the markup changed' % shown)
    EDITED[alv_tree.rel(p)] = t
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    done += 1

print('-' * 74)
print('  %d page(s) changed' % done)

# ---- nowhere else in the tree ------------------------------------------
left_over = {}
for q in alv_tree.templates():
    if os.path.basename(q) == 'base.html':
        continue
    # THE EDITED TEXT, NOT THE FILE. With --check nothing has been
    # written, so reading disk finds the rule this round has just
    # removed - D1 hit the same trap an hour ago.
    src = EDITED.get(alv_tree.rel(q)) or read(q)[0]
    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', src, re.S)), flags=re.S)
    for m in re.finditer(r'([^{}]*\.action-secondary[^{}]*)\{([^}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        if 'display: none' in ' '.join(m.group(2).split()) \
                and 'page-action-buttons' not in sel:
            left_over.setdefault(alv_tree.rel(q), []).append(sel[:60])
if left_over:
    raise SystemExit('I2: %d page(s) still hide a secondary outside a bar: '
                     '%s' % (len(left_over), left_over))
print('  and no page in the tree hides a secondary outside an action bar')

print('-' * 74)
print('  Add Task and Add Subtask are on the phone again, and so are the')
print('  four Cancels and the Delete confirmation in the modals.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
