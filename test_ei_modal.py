# -*- coding: utf-8 -*-
"""test_ei_modal.py - the Issue page's Edit Issue and Edit Comment pop-ups
are the house pop-up: a Bootstrap modal, base's header, base's fields.

    python test_ei_modal.py

Run from the repo root, after apply_ei_modal.py.

  1. The markup is the house shape, and nothing of the .ei-* dialect is
     left in markup, CSS or script. Every field is .form-group, a bold
     label, .alv-req exactly where the control is required, .form-control.
     Ids, names, form actions and the Django tags are what they were.
  2. The round changed only its six blocks (the file as it LEFT it,
     through alv_rounds.as_left_by).
  3. THE BROWSER, with the page's real jQuery 3.6.0 and Bootstrap 4.1.3
     from two fixture files (the Bootstrap one is the file base's SRI hash
     names). At 1280 and at 375: the Edit Issue button opens it; the
     field under the pop-up's centre is the field, not the backdrop; the
     header is the teal banner; fields are full width, 16px on a phone;
     Escape, the backdrop, Cancel and the close button each close it. Edit
     Comment opens filled with the comment's text and id.
     CONTROL: the same pop-up inside a parent with its own low z-index is
     covered by the backdrop - so the stacking check can fail.
  4. It is on the gate.
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

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
FD = os.path.join(T, 'fsr_details.html')
BASE = os.path.join(T, 'base.html')
SUFFIX = '.bak_eimodal'
BOOT = 'test_fixture_bootstrap413.css'
JQ = 'test_fixture_jquery360.js'
BSJS = 'test_fixture_bootstrap413.js'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_ei_modal.py'
MODALS = ('editIssueModal', 'editCommentModal')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def modal_block(text, mid):
    """From the modal's opening div to the {% endif %} that closes it."""
    m = re.search(r'<div[^>]*\bid="%s"' % mid, text)
    if not m:
        return ''
    i = text.rfind('\n', 0, m.start()) + 1
    # to the </div> that closes it - counted, because a {% endif %} sits
    # INSIDE Edit Issue, on the selected <option>
    depth = 0
    for t in re.finditer(r'<div\b|</div>', text[m.start():]):
        depth += 1 if t.group(0) == '<div' else -1
        if depth == 0:
            j = m.start() + t.end()
            return text[i:text.find('\n', j) + 1]
    return text[i:]


def fields(block):
    return [(m.group(1), m.group(2)) for m in re.finditer(
        r'<(input|select|textarea)\b([^>]*)>', block)
        if 'type="hidden"' not in m.group(2)]


def attr(tag, name):
    m = re.search(r'\b%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


if not os.path.isfile(FD):
    sys.exit('! %s not found' % FD)
NOW = read(FD)
HAVE_BAK = os.path.isfile(FD + SUFFIX)
WAS = read(FD + SUFFIX) if HAVE_BAK else None

# ==========================================================================
head('1. THE HOUSE SHAPE')
# ==========================================================================
for mid in MODALS:
    b = modal_block(NOW, mid)
    first = b.split('\n', 1)[0]
    ok(re.search(r'class="modal fade"', first) is not None,
       '%s is a Bootstrap .modal.fade' % mid, first.strip()[:90])
    for piece in ('class="modal-dialog"', 'class="modal-content"',
                  'class="modal-header alv-modal-head"',
                  'class="modal-title"', 'class="close" data-dismiss="modal"',
                  'class="modal-body"', 'class="modal-footer"'):
        ok(piece in b, '  it has %s' % piece)
    ok('danger' not in b, '  and its header is teal - it deletes nothing')
    cancel = re.search(r'<button[^>]*>\s*Cancel\s*</button>', b)
    ok(cancel is not None and 'data-dismiss="modal"' in cancel.group(0),
       '  Cancel is dismissed by Bootstrap, not by a page function')
    fs = fields(b)
    ok(len(fs) == (3 if mid == 'editIssueModal' else 1),
       '  %d field(s)' % len(fs))
    for kind, tag in fs:
        fid = attr(tag, 'id')
        cls = (attr(tag, 'class') or '').split()
        ok('form-control' in cls, '  #%s is .form-control' % fid, cls)
        lab = re.search(r'<label for="%s">(.*?)</label>' % fid, b, re.S)
        ok(lab is not None and re.match(r'\s*<strong>[^<]+</strong>',
                                        lab.group(1)),
           '  #%s has a label whose name is bold' % fid,
           lab.group(0) if lab else 'no label')
        req = ' required' in tag or tag.rstrip().endswith('required')
        star = bool(lab) and 'class="alv-req"' in lab.group(1)
        ok(req == star, '  #%s: asterisk %s, control %s' % (
            fid, 'yes' if star else 'no',
            'required' if req else 'optional'))
        grp = b.rfind('<div class="form-group">', 0, b.find(tag))
        ok(grp >= 0 and b.find('</div>', grp) > b.find(tag),
           '  #%s sits in a .form-group' % fid)
ok('<p class="form-text">' in modal_block(NOW, 'editCommentModal'),
   'the comment note is base\'s .form-text')

DIALECT = re.compile(r'\bei-(modal|label|input)|\bec-note')
ok(not DIALECT.search(NOW), 'no .ei-* / .ec-note name is left in the page',
   '\n'.join(sorted(set(m.group(0) for m in DIALECT.finditer(NOW)))))
ok(not re.search(r"getElementById\('edit(Issue|Comment)Modal'\)", NOW),
   'the script no longer shows and hides them by hand')
for fn in ('openEditIssueModal', 'closeEditIssueModal',
           'openEditCommentModal', 'closeEditCommentModal'):
    ok(re.search(r'function %s\b' % fn, NOW) is not None,
       'the script keeps %s - the buttons call it' % fn)
ok("$('#editIssueModal').modal('show')" in NOW and
   "$('#editCommentModal').modal('show')" in NOW,
   'opening is Bootstrap\'s')
ok('onclick="openEditIssueModal()"' in NOW and
   'onclick="openEditCommentModal(this)"' in NOW,
   'the page\'s Edit Issue and comment Edit buttons still call them')

if HAVE_BAK:
    for pat in ('id="ei_heading"', 'name="issues_heading"',
                'id="ei_description"', 'name="issues_description"',
                'id="ei_prop"', 'name="prop"', 'id="ec_text"',
                'name="issues_details_comment"', 'id="ec_comment_id"',
                'name="comment_id"', "{% url 'fsr_edit_commit'",
                "{% url 'fsr_comment_edit_commit'", '{% csrf_token %}',
                '{% if', '{% endif %}', '{% for', '{% endfor %}',
                'maxlength="255"', ' required'):
        ok(WAS.count(pat) == NOW.count(pat),
           'unchanged: %-34s x%d' % (pat, WAS.count(pat)),
           '%d -> %d' % (WAS.count(pat), NOW.count(pat)))
    ok(DIALECT.search(WAS) is not None and
       'form-control' not in modal_block(WAS, 'editIssueModal'),
       'CONTROL: before, it WAS the .ei-* dialect with no .form-control')
else:
    skip('the before-and-after checks', 'no fsr_details.html%s' % SUFFIX)

# ==========================================================================
head('2. ONLY ITS SIX BLOCKS CHANGED')
# ==========================================================================
REGIONS = [
    lambda t: modal_block(t, 'editIssueModal'),
    lambda t: modal_block(t, 'editCommentModal'),
    lambda t: (re.search(r'/\* ===== (Issue edit: button, modal, history|'
                         r'Edit history) \(added\) ===== \*/.*?(?=\.history-'
                         r'container)', t, re.S) or [''])[0],
    lambda t: (re.search(r'@media screen and \(max-width: 768px\) \{\n'
                         r'    \.ei-modal-dialog[^}]*\}\n[^}]*\}\n\}\n', t)
               or [''])[0],
    lambda t: (re.search(r'\.ec-note \{[^}]*\}\n', t) or [''])[0],
    # before: two scripts, Issue then Comment; after: one
    lambda t: (re.search(r'<script>\n// Edit Issue.*?</script>\n'
                         r'(?:\n<script>\n// Edit Comment.*?</script>\n)?',
                         t, re.S) or [''])[0],
]


def rest(t):
    for r in REGIONS:
        piece = r(t)
        if piece:
            t = t.replace(piece, '', 1)
    return t


if HAVE_BAK:
    sys.path.insert(0, ROOT)
    try:
        from alv_rounds import as_left_by
        left = as_left_by(FD, SUFFIX, read)
    except Exception:
        left = NOW
    ok(rest(WAS) == rest(left), 'outside the two pop-ups, their rules and '
       'their script, the page is byte-for-byte what it was')
    ok(rest(WAS) != WAS and rest(left) != left,
       'CONTROL: each side really had blocks to take out')
else:
    skip('the scope check', 'no backup')

# ==========================================================================
head('3. THE BROWSER - the real jQuery and Bootstrap')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def scripts_of(t):
    return [re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<script>(.*?)</script>', t, re.S)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def esc_script(s):
    return s.replace('</script', '<\\/script')


def page_html(t, trap=False):
    extra = ('<script>document.addEventListener("DOMContentLoaded",'
             'function(){var m=document.getElementById("editIssueModal");'
             'm.parentElement.style.position="relative";'
             'm.parentElement.style.zIndex="1";});</script>' if trap else '')
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><title>ei</title>'
            '<style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div><script>%s</script><script>%s</script>'
            '%s%s</body></html>'
            % (read(BOOT), '\n'.join(styles_of(read(BASE))),
               ''.join('<style>%s</style>' % c for c in styles_of(t)),
               body_markup(t), esc_script(read(JQ)), esc_script(read(BSJS)),
               ''.join('<script>%s</script>' % esc_script(s)
                       for s in scripts_of(t)), extra))


PROBE = r"""(id) => {
  const m = document.getElementById(id);
  const s = getComputedStyle(m);
  const r = {shown: m.classList.contains('show') && s.display === 'block'};
  if (!r.shown) return r;
  const f = m.querySelector('input:not([type=hidden]), select, textarea');
  const fr = f.getBoundingClientRect();
  const hit = document.elementFromPoint(fr.left + fr.width / 2,
                                        fr.top + fr.height / 2);
  const h = m.querySelector('.modal-header, .ei-modal-header');
  const body = m.querySelector('.modal-body, .ei-modal-body').getBoundingClientRect();
  r.hit = hit ? (hit.id || hit.className) : null;
  r.fieldOnTop = hit === f;
  r.headBg = getComputedStyle(h).backgroundImage;
  r.titleInk = getComputedStyle(h.querySelector('.modal-title, h2, h5')).color;
  r.size = getComputedStyle(f).fontSize;
  r.wide = fr.width >= body.width - 2 * 16 - 2;
  const lb = m.querySelector('label strong') || m.querySelector('label');
  r.bold = getComputedStyle(lb).fontWeight;
  r.backdrop = !!document.querySelector('.modal-backdrop.show');
  const dr = m.querySelector('.modal-dialog, .ei-modal-dialog').getBoundingClientRect();
  r.inside = dr.left >= 0 && dr.right <= window.innerWidth + 0.5;
  return r;
}"""

if sync_playwright is None:
    skip('3', 'playwright is not installed')
elif not all(os.path.isfile(f) for f in (BOOT, JQ, BSJS)):
    skip('3', 'a fixture is missing: %s' % ', '.join(
        f for f in (BOOT, JQ, BSJS) if not os.path.isfile(f)))
else:
    exe = '/opt/pw-browsers/chromium'
    fx = os.path.join(SCRATCH, '_ei_now.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(page_html(NOW))
    trapfx = os.path.join(SCRATCH, '_ei_trap.html')
    with open(trapfx, 'w', encoding='utf-8') as f:
        f.write(page_html(NOW, trap=True))

    def settle(pg, mid):
        """Bootstrap listens for Escape on the modal itself, and focuses it
        once the fade has finished - a real user's key arrives long after.
        Wait for that focus, as a person would without knowing it."""
        try:
            pg.wait_for_function(
                "(id) => document.getElementById(id).contains("
                "document.activeElement)", arg=mid, timeout=3000)
            return True
        except Exception:
            return False

    def press(pg, sel):
        """A click that fails as a check, not as a crash - on the old
        markup Cancel has no data-dismiss and would wait 30s, then raise."""
        try:
            pg.click(sel, timeout=3000)
            return True
        except Exception:
            return False

    def wait_state(pg, mid, shown):
        try:
            pg.wait_for_function(
                "([id, want]) => { const m = document.getElementById(id);"
                " const on = m.classList.contains('show') &&"
                " getComputedStyle(m).display === 'block';"
                " return on === want && !document.body.classList.contains("
                "'modal-open') === !want; }", arg=[mid, shown], timeout=3000)
            return True
        except Exception:
            return False

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for w in (1280, 375):
            print('\n  -- %dpx wide' % w)
            ctx = br.new_context(viewport={'width': w, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            _goto(pg, fx)
            ok(pg.evaluate("() => typeof jQuery === 'function' && "
                           "typeof jQuery.fn.modal === 'function'"),
               'jQuery and Bootstrap\'s modal plugin loaded from the fixtures')
            ok(not pg.evaluate(PROBE, 'editIssueModal')['shown'],
               'Edit Issue is closed when the page opens')
            press(pg, 'button[onclick="openEditIssueModal()"]')
            ok(wait_state(pg, 'editIssueModal', True),
               'the Edit Issue button opens it')
            r = pg.evaluate(PROBE, 'editIssueModal')
            if r.get('shown'):
                ok(r['fieldOnTop'], 'the field is on top - not under the '
                   'backdrop', r['hit'])
                ok(r['backdrop'], 'Bootstrap drew its backdrop')
                ok('linear-gradient' in r['headBg'],
                   'the header is base\'s banner', r['headBg'][:60])
                ok(r['titleInk'] == 'rgb(255, 255, 255)',
                   'its title is white', r['titleInk'])
                want = '16px' if w < 768 else '14px'
                ok(r['size'] == want, 'fields are %s' % want, r['size'])
                ok(r['wide'], 'fields fill the pop-up\'s width')
                ok(r['bold'] in ('700', 'bold', '600'),
                   'labels are bold', r['bold'])
                ok(r['inside'], 'the pop-up fits inside the window')
            ok(settle(pg, 'editIssueModal'), 'focus moves into the pop-up')
            pg.keyboard.press('Escape')
            ok(wait_state(pg, 'editIssueModal', False), 'Escape closes it')
            pg.evaluate('openEditIssueModal()')
            wait_state(pg, 'editIssueModal', True)
            settle(pg, 'editIssueModal')
            pg.mouse.click(3, 890)
            ok(wait_state(pg, 'editIssueModal', False),
               'a click on the backdrop closes it')
            for label, sel in (('Cancel', '#editIssueModal .modal-footer '
                                'button[data-dismiss]'),
                               ('the close button', '#editIssueModal .close')):
                pg.evaluate('openEditIssueModal()')
                wait_state(pg, 'editIssueModal', True)
                settle(pg, 'editIssueModal')
                ok(press(pg, sel) and wait_state(pg, 'editIssueModal', False),
                   '%s closes it' % label)
            pg.evaluate("""() => { const b = document.createElement('button');
                b.setAttribute('data-comment-id', '4711');
                b.setAttribute('data-comment-text', 'Leak under the sink');
                openEditCommentModal(b); }""")
            ok(wait_state(pg, 'editCommentModal', True),
               'Edit Comment opens')
            got = pg.evaluate("() => [document.getElementById('ec_text')"
                              ".value, document.getElementById("
                              "'ec_comment_id').value]")
            ok(got == ['Leak under the sink', '4711'],
               'with the comment\'s text and id filled in', got)
            r = pg.evaluate(PROBE, 'editCommentModal')
            if r.get('shown'):
                ok(r['fieldOnTop'], 'its field is on top', r['hit'])
            ok(settle(pg, 'editCommentModal'), 'focus moves into the pop-up')
            pg.keyboard.press('Escape')
            ok(wait_state(pg, 'editCommentModal', False), 'Escape closes it')
            mine = [e for e in errs if re.search(r'modal|ei-|ec_', e, re.I)]
            ok(not mine, 'no script error from the pop-ups', mine)
            ctx.close()

        # CONTROL - the check that the field is on top can fail.
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, trapfx)
        pg.evaluate('openEditIssueModal()')
        wait_state(pg, 'editIssueModal', True)
        r = pg.evaluate(PROBE, 'editIssueModal')
        ok(r.get('shown') and not r['fieldOnTop'],
           'CONTROL: inside a parent with z-index 1 the backdrop covers the '
           'field - so the check above can fail', r.get('hit'))
        ctx.close()
        br.close()

# ==========================================================================
head('4. IT IS ON THE GATE')
# ==========================================================================
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
