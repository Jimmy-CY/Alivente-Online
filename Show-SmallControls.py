# -*- coding: utf-8 -*-
"""Show-SmallControls.py - which text controls are under 16px on a phone,
and exactly which rule makes them so.

    python Show-SmallControls.py
    python Show-SmallControls.py --verbose     every control, not a summary

Run from the repo root. READ-ONLY - nothing is written.

WHY IT EXISTS

  iOS Safari zooms the whole page when a focused text control is under
  16px. base guards ONE thing: `.form-control { font-size: 16px }` below
  768px. Rendering the pages the zoom-guard round touched found 64 controls
  on 16 of them still under 16px at 375 wide. That count covered only the
  pages that round touched; this tool renders EVERY page.

  A count says which pages zoom. It does not say what to change, and there
  are at least three different answers:

    LOCAL   a rule on the page sets the control's own font-size below 16px
            (a filter select at 13px, a .line-input at 14px) and beats
            base because it is more specific or comes later.
    INHERIT the control has no font-size of its own. Bootstrap's reboot
            gives input/select/textarea `font-size: inherit`, so it takes
            whatever its container has - a 0.85rem table, a 13px card.
    BASE    base's own rule, or Bootstrap's, sets it (.form-control-sm).

  So for every small control this asks Chromium itself - DevTools'
  getMatchedStylesForNode, the same data the Styles pane shows - which
  declaration WON, and where it lives: the page (with its line number),
  base, or the Bootstrap fixture. Nothing here reasons about CSS by
  pattern; the browser does the cascade.

WHAT IT RENDERS

  The page's content block with Django stripped - every branch of every
  conditional kept, which can only ADD controls - inside the real base CSS,
  the Bootstrap 4.1.3 fixture and the page's own <style> blocks, at 375px
  with the sidebar class on the body. Controls built by script at runtime
  are not in the markup and are not seen; say so rather than miss it.
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
    print('     reason  : %s' % str(err).split('\n')[0][:150])
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
# ------------------------------------------------------------------------

import os
import re
import sys
from collections import Counter, defaultdict, OrderedDict

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
BOOT = 'test_fixture_bootstrap413.css'
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')
if not os.path.isfile(BOOT):
    sys.exit('! %s not found - it is the Bootstrap the pages load' % BOOT)
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sys.exit('! playwright is not installed - pip install playwright')

VERBOSE = '--verbose' in sys.argv
WIDTH = 375
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S | re.I)
    body = re.sub(r'\{#.*?#\}', '', body, flags=re.S)
    body = re.sub(r'\{%.*?%\}', '', body, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', body, flags=re.S)


def pages():
    out = []
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith('.html') or 'OLD DO NOT USE' in f:
                continue
            rel = os.path.relpath(os.path.join(d, f), ROOT).replace('\\', '/')
            if rel == 'base.html':
                continue
            t = read(os.path.join(d, f))
            if re.search(r'\{%\s*extends\s+["\']base\.html', t):
                out.append((rel, t))
    return sorted(out)


BASE = read(os.path.join(ROOT, 'base.html'))
BASE_CSS = '\n'.join(styles_of(BASE))
BOOT_CSS = read(BOOT)


def fixture(page_styles, markup):
    tags = ['<style id="s-boot">%s</style>' % BOOT_CSS,
            '<style id="s-base">%s</style>' % BASE_CSS]
    tags += ['<style id="s-page-%d">%s</style>' % (i, c)
             for i, c in enumerate(page_styles)]
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><title>s</title>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar"><div>%s</div></div></body></html>'
            % (''.join(tags), markup))


TEXTY = r"""() => {
  const skip = ['hidden','checkbox','radio','submit','button','reset','file',
                'image','range','color'];
  const out = [];
  document.querySelectorAll('input, select, textarea').forEach((e, i) => {
    const t = (e.getAttribute('type') || '').toLowerCase();
    if (skip.includes(t)) return;
    const px = parseFloat(getComputedStyle(e).fontSize);
    if (px < 16) { e.setAttribute('data-sc', String(i)); out.push([i, px]); }
  });
  return out;
}"""


def font_decl(style):
    """The font-size a CDP style object declares, and whether !important."""
    got = None
    for p in (style or {}).get('cssProperties', []):
        if p.get('name') == 'font-size' and not p.get('disabled') \
                and p.get('parsedOk', True) and p.get('value'):
            imp = bool(p.get('important'))
            if got is None or imp or not got[1]:
                got = (p['value'].strip(), imp)
    return got


def winner(rules, inline):
    """Last declaration wins, !important beats plain. rules come from CDP in
    cascade order, lowest first."""
    best = None
    for r in rules:
        d = font_decl(r['rule']['style'])
        if d is None:
            continue
        cand = (d[0], d[1], r['rule'])
        if best is None or d[1] or not best[1]:
            best = cand
    d = font_decl(inline)
    if d is not None and (best is None or not best[1] or d[1]):
        best = (d[0], d[1], {'selectorList': {'text': 'style="..."'},
                             'styleSheetId': None, 'origin': 'inline'})
    return best


def main():
    found = OrderedDict()
    total_pages = 0
    with sync_playwright() as pw:
        exe = '/opt/pw-browsers/chromium'
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        n = 0
        for rel, t in pages():
            total_pages += 1
            n += 1
            fx = os.path.join(SCRATCH, '_sc_%04d.html' % n)
            with open(fx, 'w', encoding='utf-8') as f:
                f.write(fixture(styles_of(t), body_markup(t)))
            ctx = br.new_context(viewport={'width': WIDTH, 'height': 900})
            # Nothing leaves the machine: the markup carries real image and
            # font URLs, and fetching them measures the network, not CSS.
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fx)
            small = pg.evaluate(TEXTY)
            if not small:
                ctx.close()
                continue
            cdp = ctx.new_cdp_session(pg)
            sheets = {}
            cdp.on('CSS.styleSheetAdded',
                   lambda e: sheets.__setitem__(e['header']['styleSheetId'],
                                                e['header']))
            cdp.send('DOM.enable')
            cdp.send('CSS.enable')
            doc = cdp.send('DOM.getDocument', {'depth': -1})
            owner = {}
            for sid, h in sheets.items():
                nd = h.get('ownerNode')
                if nd:
                    d = cdp.send('DOM.describeNode', {'backendNodeId': nd})
                    at = d['node'].get('attributes', [])
                    owner[sid] = dict(zip(at[::2], at[1::2])).get('id', '?')
            page_lines = t.split('\n')
            rows = []
            for idx, px in small:
                q = cdp.send('DOM.querySelector', {
                    'nodeId': doc['root']['nodeId'],
                    'selector': '[data-sc="%d"]' % idx})
                nid = q['nodeId']
                desc = cdp.send('DOM.describeNode', {'nodeId': nid})['node']
                at = desc.get('attributes', [])
                at = dict(zip(at[::2], at[1::2]))
                ms = cdp.send('CSS.getMatchedStylesForNode', {'nodeId': nid})
                w = winner(ms.get('matchedCSSRules', []), ms.get('inlineStyle'))
                how = 'LOCAL'
                if w is None or w[0] in ('inherit', 'unset'):
                    how = 'INHERIT'
                    w = None
                    for anc in ms.get('inheritedStyles', []):
                        w = winner(anc.get('matchedCSSRules', []),
                                   anc.get('inlineStyle'))
                        if w and w[0] not in ('inherit', 'unset'):
                            break
                        w = None
                if w is None:
                    src, sel, val = '?', '(browser default)', ''
                else:
                    val, rule = w[0], w[2]
                    sel = rule['selectorList']['text']
                    sid = rule.get('styleSheetId')
                    tag = owner.get(sid, 'inline' if sid is None else '?')
                    if tag == 's-boot':
                        src = 'bootstrap'
                    elif tag == 's-base':
                        src = 'base'
                    elif tag == 'inline':
                        src = 'inline style'
                    else:
                        src = 'page'
                        first = sel.split(',')[0].strip()
                        for ln, line in enumerate(page_lines, 1):
                            if first and first in line and '{' in \
                                    '\n'.join(page_lines[ln - 1:ln + 1]):
                                src = 'page:%d' % ln
                                break
                    if how == 'LOCAL' and src in ('base', 'bootstrap'):
                        how = 'BASE'
                ident = desc['nodeName'].lower()
                if at.get('type'):
                    ident += '[%s]' % at['type']
                ident += (' #' + at['id']) if at.get('id') else ''
                ident += (' name=' + at['name']) if at.get('name') else ''
                cls = at.get('class', '')
                rows.append((ident, cls, px, how, src, sel, val))
            found[rel] = rows
            ctx.close()
        br.close()

    ctls = sum(len(r) for r in found.values())
    print('=' * 74)
    print('SMALL TEXT CONTROLS AT %dpx - under 16px, so iOS zooms on tap'
          % WIDTH)
    print('=' * 74)
    print('pages rendered : %d (every template that extends base)'
          % total_pages)
    print('pages affected : %d' % len(found))
    print('controls       : %d' % ctls)
    how = Counter(r[3] for rs in found.values() for r in rs)
    print('by cause       : ' + ', '.join('%s %d' % kv
                                           for kv in how.most_common()))
    fc = Counter(bool(re.search(r'\bform-control\b', r[1]))
                 for rs in found.values() for r in rs)
    print('.form-control  : %d carry it, %d do not' % (fc[True], fc[False]))

    for rel, rows in found.items():
        print('\n' + '-' * 74)
        print('%s  - %d control(s)' % (rel, len(rows)))
        groups = defaultdict(list)
        for r in rows:
            groups[(r[3], r[4], r[5], r[6])].append(r)
        for (h, src, sel, val), rs in sorted(groups.items(),
                                             key=lambda kv: -len(kv[1])):
            print('  %-7s %2d x %-5s  %s  { font-size: %s }  [%s]'
                  % (h, len(rs), '%gpx' % rs[0][2], sel[:60], val, src))
            kinds = Counter('%s .%s' % (r[0].split(' ')[0],
                                        '.'.join(r[1].split()[:2]) or '-')
                            for r in rs)
            print('           ' + '; '.join('%d %s' % (c, k)
                                            for k, c in kinds.most_common(4)))
            if VERBOSE:
                for r in rs:
                    print('             %s  class="%s"' % (r[0], r[1][:40]))
    print('\n' + '=' * 74)
    print('READ-ONLY. Nothing was written.')


if __name__ == '__main__':
    main()
