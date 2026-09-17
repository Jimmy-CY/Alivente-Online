"""apply_admin_headings.py - Administration and Personal, stage B: the
   module heading.

    python apply_admin_headings.py --check     survey, write nothing
    python apply_admin_headings.py             apply

Run from the repo root, after apply_admin_repair.py.

WHERE THE SYSTEM ACTUALLY STANDS

  Across the 90 property-management templates:

      46   on base's standard, .page-title-h2
      17   an h2 with a <center> and no class
      15   an h2 in some other shape
       6   an h1
       3   an h2 with an icon in it
       3   no heading at all

  So base's standard is the plurality and 44 pages are not on it. Seven of
  those are these two modules. I nearly reported the opposite: the first
  four list screens I looked at - Tenants, Properties, Suppliers,
  Expenses - are all in the 17, and from that sample it looked as though
  the standard covered entry screens only. Four pages is not a survey.

THE MODULE NAME IS DERIVED WHERE THERE IS ONE TO DERIVE

  Same rule as the entry-screen round: follow the Back link to the screen
  it returns to and read its heading. user_permissions returns to
  user_administration, so it becomes USER ADMINISTRATION over PERMISSIONS.

  A LANDING SCREEN IS ITS OWN MODULE. user_administration, workspace
  management, help and my_profile have no Back at all - they ARE the top
  of their module, so their own heading becomes the module line and there
  is no mode line to invent.

  admin_apms has a Back, and it goes to `home`. THAT IS NOT A MODULE. It
  is the system root, and deriving from it would head the Administration
  dashboard with whatever the home page calls itself. Named, with the
  reason, and treated as a landing screen.

  AND A MODE LABEL DOES NOT REPEAT ITS MODULE. notification_settings
  calls itself "Administration Notification Settings" and returns to
  ADMINISTRATION, which would give ADMINISTRATION over ADMINISTRATION
  NOTIFICATION SETTINGS. Where the mode begins with the module name, that
  prefix is dropped.

A SIXTH CLASS NAME FOR ONE HEADING

  admin_apms heads itself with .admin-page-title, declared on that page
  and nowhere else. That is the sixth name this system has had for one
  heading - after page-title-h2, page-title-center, the bare centred h2,
  the h1, and the icon'd h2. It goes with this round.

THE ICON GOES TOO. base's standards block says a heading carries no icon;
  six of these seven start with one.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_adminhead'
SUITE = 'test_admin_headings.py'

ADMIN = re.compile(r'(^|/)(user_|workspace_|admin_|permission)|'
                   r'(^|/)(notification_settings|help_page|database_error)')
PERSONAL = re.compile(r'(^|/)(my_profile|personal_)')

H2, H4 = 'page-title-h2', 'page-subtitle-h4'
SIXTH = 'admin-page-title'

# A Back target that is not a module. NAMED, with the reason.
NOT_A_MODULE = {
    'home': 'the system root, not a module - deriving from it would head '
            'the Administration dashboard with the home page\'s name',
}

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}
DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if ADMIN.search(rel) or PERSONAL.search(rel):
                out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def resolve(url_name):
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n == url_name + '.html':
                return os.path.join(dirpath, n)
    return None


def django_balance(text):
    d = 0
    for m in re.finditer(r'\{%\s*(\w+)', text):
        w = m.group(1)
        if w in DJANGO_OPEN:
            d += 1
        elif w.startswith('end'):
            d -= 1
            if d < 0:
                return False
    return d == 0


def mismatches(scan):
    stack, n = [], 0
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, _a, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if close:
            if not stack or stack[-1] != name:
                n += 1
            if stack:
                stack.pop()
        else:
            stack.append(name)
    return n + len(stack)


def upper_literal(s):
    """Upper-case the text, and NOTHING that is not text.

    Django tags, because {{ WORKSPACE.NAME }} is a variable that does not
    exist. And HTML ENTITIES: help_page's heading contains &amp;, which
    upper-cased becomes &AMP; - browsers mostly forgive it, the standard
    does not, and it is the kind of thing that survives for years because
    it renders. The first version of this protected the Django tags and
    not the entities.
    """
    out, i = [], 0
    for m in re.finditer(r'\{\{.*?\}\}|\{%.*?%\}|&[A-Za-z][A-Za-z0-9]*;'
                         r'|&#[0-9]+;', s, re.S):
        out.append(s[i:m.start()].upper())
        out.append(m.group(0))
        i = m.end()
    out.append(s[i:].upper())
    return ''.join(out)


def clean(inner):
    out = re.sub(r'</?center>', '', inner)
    out = re.sub(r'<i\b[^>]*>\s*</i>', '', out)     # the icon the standard forbids
    return ' '.join(out.split())


def first_heading(text):
    m = re.search(r'<(h[1-4])\b([^>]*)>(.*?)</\1>', inert(text), re.S)
    if not m:
        return None
    return (m.start(), m.end(), text[m.start(3):m.end(3)])


def back_url(text):
    m = re.search(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>',
                  inert(text))
    if not m:
        return None
    u = re.search(r"\{%\s*url\s*'([^']+)'", m.group(0))
    return u.group(1) if u else None


def plan(rel, path, reports):
    text, nl, raw = read(path)
    if re.search(r'class="[^"]*\b%s\b' % H2, inert(text)):
        return None
    h = first_heading(text)
    if not h:
        reports.append((rel, 'it has no heading to work from'))
        return None
    start, end, inner = h
    own = upper_literal(clean(inner))

    url = back_url(text)
    mod, mode, why = own, None, 'a landing screen - it is its own module'
    if url and url in NOT_A_MODULE:
        why = 'Back goes to %s: %s' % (url, NOT_A_MODULE[url])
    elif url:
        p = resolve(url)
        theirs = first_heading(read(p)[0]) if p else None
        if theirs:
            mod = upper_literal(clean(theirs[2]))
            mode = own
            # A MODE DOES NOT REPEAT ITS MODULE.
            if mode.startswith(mod + ' '):
                mode = mode[len(mod) + 1:]
            why = "module read from '%s'" % url
        else:
            why = "Back goes to '%s', which has no heading to read" % url

    indent = re.search(r'[ \t]*$', text[:start]).group(0)
    block = '<h2 class="%s">%s</h2>' % (H2, mod)
    if mode:
        block += '\n%s<h4 class="%s">%s</h4>' % (indent, H4, mode)
    new = text[:start] + block + text[end:]
    # the sixth class name, wherever it is
    new = re.sub(r'\n[ \t]*\.%s\s*\{[^{}]*\}[ \t]*(?=\n)' % SIXTH, '', new)
    new = re.sub(r'\s*(?<![-\w])%s(?![-\w])' % SIXTH, '', new)
    return dict(rel=rel, path=path, text=text, new=new, nl=nl, raw=raw,
                mod=mod, mode=mode, why=why)


def check_page(p, problems):
    bad = []
    if not django_balance(p['new']):
        bad.append('the Django block tags no longer balance')
    if mismatches(inert(p['new'])) > mismatches(inert(p['text'])):
        bad.append('the tag mismatches got worse')
    for want in (p['mod'], p['mode']):
        if want and ''.join(re.sub(r'<[^>]+>', '', want).split()).upper() \
                not in ''.join(re.sub(r'<[^>]+>', '', p['new']).split()).upper():
            bad.append('"%s" is not in the page it was written into'
                       % want[:30])
    if SIXTH in p['new']:
        bad.append('the sixth class name survived')
    for b in bad:
        problems.append('%s: %s' % (p['rel'], b))
    return not bad


NOTE = ("    # Administration and Personal, stage B: the module heading. Its\n"
        "    # section 2 re-derives every module name from the screen Back\n"
        "    # returns to, so renaming a module reports its sub-screens the\n"
        "    # same day. Newest, so most likely to be what breaks.\n")


def wire_gate(check_only, problems):
    if not os.path.exists(PS1):
        return 'gate: %s not found, skipped' % os.path.basename(PS1)
    text, nl, raw = read(PS1)
    if SUITE in text:
        return 'gate: already listed.'
    a = text.find('$suites = @(')
    b = text.find('\n)\n', a) if a >= 0 else -1
    if a < 0 or b < 0:
        problems.append('gate: the suite list was not found. NOT wired.')
        return 'gate: NOT wired'
    last = None
    for m in re.finditer(r"'test_[A-Za-z0-9_]+\.py'", text[a:b]):
        last = m
    if last is None:
        problems.append('gate: the list holds no suite to follow.')
        return 'gate: NOT wired'
    at = a + last.end()
    new = text[:at] + ",\n" + NOTE + "    '%s'" % SUITE + text[at:]
    before = re.findall(r"'test_[A-Za-z0-9_]+\.py'", text[a:b])
    nb = new.find('\n)\n', a)
    if re.findall(r"'test_[A-Za-z0-9_]+\.py'", new[a:nb]) != \
            before + ["'%s'" % SUITE] or new[:a] != text[:a] \
            or new[nb:] != text[b:]:
        problems.append('gate: the list did not come out as expected.')
        return 'gate: NOT wired'
    if not check_only:
        bak = PS1 + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(PS1, new, nl)
    return 'gate: %s goes on the end of %d suite(s).' % (SUITE, len(before))


def main():
    check_only = '--check' in sys.argv
    if not os.path.isdir(T):
        print('! %s not found - run from the repo root' % T)
        sys.exit(1)

    problems, planned, reports = [], [], []
    for rel, path in pages():
        p = plan(rel, path, reports)
        if p is None or p['new'] == p['text']:
            continue
        if check_page(p, problems):
            planned.append(p)

    gate_line = wire_gate(check_only, problems)

    for p in planned:
        ctrl = [hex(ord(c)) for c in p['new']
                if ord(c) < 32 and c not in '\t\n\r']
        if ctrl:
            problems.append('%s: control character(s) %s'
                            % (p['rel'], ', '.join(sorted(set(ctrl)))))

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  HEADINGS WRITTEN (%d):' % len(planned))
    for p in planned:
        print('    %-30s %s' % (p['rel'][:30], p['why']))
        print('        %s' % p['mod'][:66])
        if p['mode']:
            print('        %s' % p['mode'][:66])
    if reports:
        print('')
        print('  LEFT ALONE, and named rather than guessed at:')
        for rel, why in reports:
            print('    %-30s %s' % (rel[:30], why))
    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for p in planned:
        bak = p['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(p['raw'])
        write(p['path'], p['new'], p['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.' % SUFFIX)


if __name__ == '__main__':
    main()
