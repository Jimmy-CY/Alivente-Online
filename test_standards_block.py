"""test_standards_block.py - the standards block is there, is accurate, and
   never reaches a browser.

    python test_standards_block.py

Run from the repo root, after apply_standards_block.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 IS THE ONE THAT MATTERS. The block is 17KB of prose sitting in
    a template that renders on every page. It must be stripped by Django, not
    merely believed to be. The suite compiles base.html with Django itself
    and asserts the rendered output contains no word of it - and then proves
    the check can fail, by rendering the same text as an HTML comment and
    watching it come straight through.

  * SECTION 3 IS WHY THIS SUITE EXISTS AT ALL. A standards document that has
    drifted from the code is worse than none, because people trust it. So
    every claim it makes that CAN be checked, is: every token it names must
    be declared in base, every component it names must be defined in base,
    every suite it cites must exist in the repo, and every [CONVENTION] entry
    must NOT name a suite - that marker is a promise that nothing enforces
    the rule, and it is a lie if a suite is sitting right beside it.

  * SECTION 4 checks the block's own structure: one copy, outside <html>,
    never inside a <style> or <script>, and no stray closing tag inside it -
    which would end the comment early and render the rest into the page.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot check whether the standards
are GOOD, or whether the system obeys the ones marked [CONVENTION] - by
definition nothing does. It checks that the document describes a base.html
that exists, and that it costs the visitor nothing.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BAK = BASE + '.bak_std'
MARK = 'ALIVENTE ONLINE - THE SYSTEM STANDARD'

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


if not os.path.exists(BASE):
    sys.exit('! base.html not found - run from the repo root')
B = read(BASE)
WAS = read(BAK) if os.path.exists(BAK) else None

_m = re.search(r'\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}', B, re.S)
BODY = _m.group(1) if _m else ''
CSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', B, re.S))

# ===========================================================================
head('1. the block is there, once, and in the right place')
# ===========================================================================
check('base carries the standards block', MARK in B)
check('  exactly once', B.count(MARK) == 1, str(B.count(MARK)))
check('  inside a Django comment tag', MARK in BODY)
check('  and there is exactly one such tag',
      len(re.findall(r'\{%\s*comment\s*%\}', B)) == 1)
check('  which is closed exactly once',
      len(re.findall(r'\{%\s*endcomment\s*%\}', B)) == 1)
check('the block sits before <html>, so it is outside the document',
      B.index(MARK) < B.find('<html'))
for tag in ('<style', '<script', '<!--'):
    check('  and not inside a %s, where it WOULD ship' % tag,
          B.rfind(tag, 0, B.index(MARK)) == -1)

# ===========================================================================
head('2. it never reaches a browser')
# ===========================================================================
try:
    import django
    from django.conf import settings
    from django.template import Engine, Context
    if not settings.configured:
        settings.configure(TEMPLATES=[], USE_TZ=True,
                           INSTALLED_APPS=['django.contrib.staticfiles'])
        django.setup()
    # ONLY THE LIBRARIES THIS SLICE ACTUALLY LOADS.
    #
    # A first version walked the repo for every templatetags module and
    # registered them all, and failed with "Invalid template library
    # specified. ImportError raised..." - because a project tag library can
    # import models, and this minimal settings.configure() has no app
    # registry to import them against. That is a fact about the suite's
    # settings, not about base.html, and it failed the ONE check in this
    # file that matters.
    #
    # The slice rendered below is everything before <html>: a doctype, a
    # load tag, and the comment block. It needs whatever that slice loads
    # and nothing else. Anything that will not import is SKIPPED loudly
    # rather than taking the check down.
    import importlib
    src = B.split('<html')[0]
    KNOWN = {'static': 'django.templatetags.static',
             'i18n': 'django.templatetags.i18n',
             'l10n': 'django.templatetags.l10n',
             'tz': 'django.templatetags.tz',
             'humanize': 'django.contrib.humanize.templatetags.humanize'}
    libs, skipped = {}, []
    for name in set(re.findall(r'\{%\s*load\s+([^%]+?)\s*%\}', src)):
        for one in name.split():
            path = KNOWN.get(one)
            if path is None:
                for _d, _s2, _fs in os.walk(ROOT):
                    if os.path.basename(_d) == 'templatetags' and \
                            one + '.py' in _fs:
                        path = '%s.templatetags.%s' % (
                            os.path.basename(os.path.dirname(_d)), one)
                        break
            if not path:
                skipped.append(one)
                continue
            try:
                importlib.import_module(path)
                libs[one] = path
            except Exception as e:
                skipped.append('%s (%s)' % (one, type(e).__name__))
    if skipped:
        print('  NOTE  tag librar(ies) not importable here, skipped: %s'
              % ', '.join(sorted(skipped)))

    eng = Engine(dirs=[T], libraries=libs)

    # The head of the file is enough and needs no context to render.
    out = eng.from_string(src).render(Context({}))
    check('Django renders the block to nothing', MARK not in out,
          '%d byte(s) of output' % len(out.encode('utf-8')))
    for phrase in ('CONVENTION', 'SURVEY', 'push gate', 'Demetri'):
        check('  no trace of %-12s in the rendered output' % repr(phrase),
              phrase not in out)
    check('  what IS rendered is just the doctype and whitespace',
          out.strip() in ('<!doctype html>', '<!DOCTYPE html>'),
          repr(out.strip()[:40]))

    # THE CONTROL. Prove the check above can fail: the same text as an HTML
    # comment goes straight through to the browser.
    leak = eng.from_string('<!doctype html>\n<!-- %s -->' % MARK) \
        .render(Context({}))
    check('  CONTROL: as an HTML comment the same text DOES ship',
          MARK in leak, '%d bytes' % len(leak.encode('utf-8')))
    check('  CONTROL: .. so the assertion above is measuring something',
          MARK not in out and MARK in leak)
except ImportError:
    print('  SKIP  django not importable - section 2 needs it')
except Exception as e:
    check('Django renders the block to nothing', False, str(e)[:70])

# The bytes that DO ship are unchanged by this block.
if WAS is not None:
    def strip(t):
        t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}\n?', '', t,
                   flags=re.S)
        return re.sub(r'\n{3,}', '\n\n', t)
    check('everything outside the block is byte-identical to before',
          strip(B) == strip(WAS))
    check('  CONTROL: the block really did add something',
          len(B) > len(WAS) + 5000, '+%d bytes on disk' % (len(B) - len(WAS)))
else:
    print('  SKIP  no base.html.bak_std to compare against')

# ===========================================================================
head('3. it describes a base.html that exists')
# ===========================================================================
# A DOCUMENT THAT HAS DRIFTED IS WORSE THAN NONE, because people trust it.
_tokens = set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', CSS))
_named = set(re.findall(r'--alv-[a-z0-9-]+', BODY))
_families = ('--alv-age-', '--alv-grade-', '--alv-tag-')
_ghost = sorted(t for t in _named
                if t not in _tokens and not t.startswith(_families))
check('every token it names is declared in base', not _ghost, str(_ghost[:5]))
check('  CONTROL: it names a useful number of them', len(_named) >= 20,
      '%d named, %d declared in base' % (len(_named), len(_tokens)))

_defined = set()
for m in re.finditer(r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{',
                     re.sub(r'/\*.*?\*/', '', CSS, flags=re.S)):
    _defined.update(re.findall(r'\.([a-zA-Z][\w-]*)', m.group(1)))
_names = set(re.findall(
    r'\.(alv-[a-z0-9-]+|action-[a-z0-9-]+|page-action-buttons|icon-[a-z0-9-]+|'
    r'ui-menu[\w-]*|row-actions|cell-actions|table-container|'
    r'mobile-action-[a-z0-9-]+|status-btn|back-button|disabled-btn|'
    r'desktop-action-cell)\b', BODY))
_ghostc = sorted(c for c in _names if c not in _defined)
check('every component it names is defined in base', not _ghostc,
      str(_ghostc[:5]))
check('  CONTROL: it names a useful number of them', len(_names) >= 25,
      '%d named, %d defined in base' % (len(_names), len(_defined)))

_cited = sorted(set(re.findall(r'test_[a-z_]+\.py', BODY)))
_cited = [c for c in _cited if '<' not in c]
_absent = [c for c in _cited if not os.path.exists(os.path.join(ROOT, c))]
check('every suite it cites exists in the repo', not _absent, str(_absent))
check('  and it cites enough of them to be a map', len(_cited) >= 6,
      '%d: %s' % (len(_cited), ', '.join(c.replace('test_', '')[:12]
                                         for c in _cited[:5])))

# THE [CONVENTION] MARKER IS A PROMISE. It says nothing enforces this rule.
# If a suite is named on the same line, the marker is a lie and somebody
# will trust the wrong half.
_lies = [ln.strip()[:52] for ln in BODY.split('\n')
         if '[CONVENTION]' in ln and re.search(r'test_[a-z_]+\.py', ln)]
check('no [CONVENTION] line also cites a suite - the marker means '
      'nothing enforces it', not _lies, str(_lies[:2]))
check('  CONTROL: there ARE convention entries to get wrong',
      BODY.count('[CONVENTION]') >= 3, str(BODY.count('[CONVENTION]')))
check('  and enforced entries too', len(_cited) >= 6)

# ===========================================================================
head('4. the block cannot break the template')
# ===========================================================================
# NOTHING IN THE BODY MAY LOOK LIKE AN HTML TAG.
#
# 41 suites parse base.html with regular expressions, and several find a
# stylesheet by matching an opening style tag, then anything, then a closing
# one. A literal style tag written in PROSE inside this block opens such a
# match at the sentence and closes it at base's first real closing tag,
# swallowing an entire stylesheet. That is not hypothetical: the first push
# of this block took seven checks in test_table_standard.py down exactly
# that way - and that suite's own notes already warned "English prose inside
# a comment has impersonated markup".
_taglike = sorted(set(re.findall(r'<[a-zA-Z!/][^\s>]{0,24}', BODY)))
check('nothing in the document is shaped like an HTML tag - 41 suites parse '
      'this file with regexes', not _taglike, str(_taglike[:4]))
check('  CONTROL: the check can see one', bool(re.findall(
    r'<[a-zA-Z!/][^\s>]{0,24}', 'a sentence with a <style> in it')))

check('no closing comment tag inside the body - it would end the block early '
      'and render the rest into the page',
      not re.search(r'\{%\s*endcomment\s*%\}', BODY))
# NOT "no <style> in the body" - the document legitimately talks ABOUT
# <style> blocks, and that check failed correct work. Inside a Django
# comment tag nothing is parsed as HTML at all: the tag's render() returns
# an empty string, so a <style> written in prose can never become an
# element. The real invariant is that the block did not SWALLOW one of
# base's own tags, or introduce one outside itself.
_out = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', B, flags=re.S)
if WAS is not None:
    for _t in ('<style', '<script'):
        check('base still has all %d of its %s tags outside the block'
              % (WAS.count(_t), _t),
              _out.count(_t) == WAS.count(_t),
              '%d vs %d' % (_out.count(_t), WAS.count(_t)))
check('  and the block itself contributes no element to the page',
      '<style' not in _out[:_out.find('<html')])
_stack, _fault = [], None
OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock', 'with': 'endwith'}
CLOSE = {v: k for k, v in OPEN.items()}
_outside = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', B,
                  flags=re.S)
for m in re.finditer(r'\{%\s*(\w+)', _outside):
    t = m.group(1)
    if t in OPEN:
        _stack.append(t)
    elif t in CLOSE and (not _stack or OPEN[_stack.pop()] != t):
        _fault = t
        break
check('base\'s own Django tags still balance', _fault is None and not _stack,
      _fault or ','.join(_stack))
for blk in re.findall(r'<style[^>]*>(.*?)</style>', B, re.S):
    check('  and its stylesheet braces do',
          blk.count('{') == blk.count('}'),
          '%d/%d' % (blk.count('{'), blk.count('}')))

# ===========================================================================
head('5. it says the things it is for')
# ===========================================================================
for section in ('HOW A CHANGE IS MADE', 'WHAT base OWNS', 'THE STANDARDS',
                'THE RULES THAT KEEP BEING RELEARNED', 'WHERE THE PLAN LIVES',
                'CHANGING A STANDARD'):
    check('it has a section on %s' % section, section in BODY)
for claim in ('PAGE HEADINGS', 'ACTION BARS', 'TABLES', 'PRINT', 'MOBILE',
              'COLOUR MEANS SOMETHING'):
    check('  and covers %-22s' % claim, claim in BODY)
check('it says where the plan lives, rather than trying to be the plan',
      'running_list' in BODY)
check('it warns that Administration and Personal are untested',
      'NEVER BEEN REVIEWED OR TESTED' in BODY)

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that the standards are the right ones, or that')
print('  the system obeys the [CONVENTION] entries - by definition nothing')
print('  enforces those. Only that the document describes a base that')
print('  exists, and costs the visitor nothing.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
