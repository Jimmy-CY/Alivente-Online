# -*- coding: utf-8 -*-
"""SECTION P, ROUND P4 - THE LAST TWO PROJECTS PAGES

P3 converted projects_detail.html and said in its own suite that two
pages still carried the same private status colours:

    projects/projects.html         the Status column of the list
    projects/project_gantt.html    the pill beside the project name

Both are the SAME SPAN with the same chain, and between them eight
rules:

    .status-badge        (padding, radius, size - base's .alv-pill does it)
    .status-completed    #d4edda / #155724
    .status-in-progress  #fff3cd / #856404
    .status-pending      #f8d7da / #721c24

#f8d7da is Demetri's first Projects finding - "why is the Pending on the
right that colour" - and this is the last place in the module it lives.

NO NEW DECISIONS. The tone map is the one agreed for P2 on 1 Oct and
used again by P3:

    Completed -good | In Progress -info | On Hold -attn
    Pending, and anything unforeseen, -neutral

These two pages only ever show three of those, because the chain they
carry has three branches. The -attn arm comes with the shared chain and
costs nothing; a status this page has not been told about lands on
-neutral rather than on nothing, which is what the old {% else %} did
with status-pending.

WHAT IS NOT TOUCHED. project_gantt's .project-status-info is layout and
stays. So does everything about the chart itself - the red bars Demetri
has not commented on are the Gantt library's, not a page stylesheet's.

Backups: .bak_projpills. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_projpills'
CRLF = {}
SENTINEL = 'test_projects_pills.py'

STATUS = ("{% if project.get_calculated_status == 'Completed' %}"
          "alv-pill-good"
          "{% elif project.get_calculated_status == 'In Progress' %}"
          "alv-pill-info"
          "{% elif project.get_calculated_status == 'On Hold' %}"
          "alv-pill-attn"
          "{% else %}alv-pill-neutral{% endif %}")

PAGES = (os.path.join('projects', 'projects.html'),
         os.path.join('projects', 'project_gantt.html'))


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
            raise SystemExit('P4: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('P4: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P4 - THE LAST TWO PROJECTS PAGES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

b = read(alv_tree.path_of('base.html'))[0]
bcss = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
    re.findall(r'<style\b[^>]*>(.*?)</style>', b, re.S)), flags=re.S)
for n in ('.alv-pill', '.alv-pill-good', '.alv-pill-info',
          '.alv-pill-attn', '.alv-pill-neutral'):
    if not re.search(r'(?<![-\w])' + re.escape(n) + r'\s*\{', bcss):
        raise SystemExit('P4: base does not draw %s' % n)
print('  base draws the pill and the four tones these pages need')

EDITED = {}
done = 0
for rel in PAGES:
    PATH = alv_tree.join(rel)
    if not os.path.isfile(PATH):
        raise SystemExit('P4: %s is not where alv_tree says' % rel)
    t, raw = read(PATH)
    shown = rel.replace(os.sep, '/')
    if SENTINEL in t:
        print('  %-34s already done' % shown)
        continue

    # The two pages indent the same span differently, so the anchor is
    # built from the file rather than typed twice.
    m = re.search(r'([ \t]*)<span class="status-badge\n'
                  r'[ \t]*\{% if project\.get_calculated_status == '
                  r"'Completed' %\}status-completed\n"
                  r'[ \t]*\{% elif project\.get_calculated_status == '
                  r"'In Progress' %\}status-in-progress\n"
                  r'[ \t]*\{% else %\}status-pending\{% endif %\}">',
                  t.replace('\r\n', '\n'))
    if not m:
        raise SystemExit('P4: %s does not carry the span this round was '
                         'written for' % shown)
    old = eol(PATH, m.group(0))
    if t.count(old) != 1:
        raise SystemExit('P4: %s - the span matches %d times, not once'
                         % (shown, t.count(old)))
    t = t.replace(old, eol(PATH, '%s<span class="alv-pill %s">'
                           % (m.group(1), STATUS)))

    # the four rules, in whichever of the two shapes this page wrote them
    css_a = t.find('<style')
    css_z = t.find('</style>', css_a)
    if css_a < 0 or css_z < 0:
        raise SystemExit('P4: %s has no style block' % shown)
    css = t[css_a:css_z]
    before = len(css)
    for pat in (r'(?m)^[ \t]*\.status-badge\s*\{[^}]*\}\n?',
                r'(?m)^[ \t]*\.status-completed\s*\{[^}]*\}\n?',
                r'(?m)^[ \t]*\.status-in-progress\s*\{[^}]*\}\n?',
                r'(?m)^[ \t]*\.status-pending\s*\{[^}]*\}\n?'):
        hits = re.findall(pat, css)
        if len(hits) != 1:
            raise SystemExit('P4: %s - %s matches %d times, not once'
                             % (shown, pat[:28], len(hits)))
        css = re.sub(pat, '', css, count=1)
    t = t[:css_a] + css + t[css_z:]
    print('  %-34s 1 pill, 4 rules, %d bytes of CSS out'
          % (shown, before - len(css)))

    # ---- GATES, per page ------------------------------------------
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->|\{#.*?#\}', '', t, flags=re.S),
                  flags=re.S)
    cssn = re.sub(r'/\*.*?\*/', ' ', t[css_a:t.find('</style>', css_a)],
                  flags=re.S)
    for gone in ('.status-badge', '.status-completed', '.status-in-progress',
                 '.status-pending'):
        if re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', cssn):
            raise SystemExit('P4: %s - %s is still styled' % (shown, gone))
    if 'status-badge' in body:
        raise SystemExit('P4: %s - status-badge is still in the markup with '
                         'nothing to style it' % shown)
    if body.count('alv-pill ') != 1:
        raise SystemExit('P4: %s - %d alv-pill spans, not 1'
                         % (shown, body.count('alv-pill ')))
    for tone in ('alv-pill-good', 'alv-pill-info', 'alv-pill-attn',
                 'alv-pill-neutral'):
        if body.count(tone) != 1:
            raise SystemExit('P4: %s - %s appears %d times, not 1'
                             % (shown, tone, body.count(tone)))

    NOTE = ("{%% endblock %%}\n\n"
            "{# P4, 1 Oct 2026 - the Status pill was this page's own: #}\n"
            "{# .status-badge plus three literals, Pending among them at #}\n"
            "{# #f8d7da. It is base's .alv-pill now, on the tone map #}\n"
            "{# agreed for P2.                 [%s] #}" % SENTINEL)
    cut = t.rfind('{% endblock %}')
    if cut < 0:
        raise SystemExit('P4: %s has no {%% endblock %%} to sign' % shown)
    t = t[:cut] + eol(PATH, NOTE) + t[cut + len('{% endblock %}'):]
    for mm in re.finditer(r'\{#(.*?)#\}', t, re.S):
        if '\n' in mm.group(1):
            raise SystemExit('P4: %s - a {# #} outlives its line' % shown)

    EDITED[alv_tree.rel(PATH)] = t
    if not CHECK:
        back_up(PATH, raw)
        write(PATH, t)
    done += 1

print('-' * 74)
print('  %d page(s) changed' % done)

# ---- and nowhere in Projects still carries the private colours ---------
# The EDITED text, not the file: with --check nothing has been written,
# and reading disk would find the rules this round has just removed.
left = {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q)
    if 'projects' not in rel.replace(os.sep, '/'):
        continue
    src = EDITED.get(rel) or read(q)[0]
    cssn = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', src, re.S)), flags=re.S)
    hit = [g for g in ('.status-completed', '.status-in-progress',
                       '.status-pending')
           if re.search(re.escape(g) + r'(?![\w-])[^{}]*\{', cssn)]
    if hit:
        left[rel] = hit
if left:
    raise SystemExit('P4: the Projects module still carries private status '
                     'colours: %s' % left)
print('  and no page in the Projects module carries its own status colours')

print('-' * 74)
print('  Pending is the house neutral on every Projects screen now.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
