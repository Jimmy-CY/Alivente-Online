# -*- coding: utf-8 -*-
"""E-2b - THE 403 PAGE BECOMES A TEMPLATE.

E-2 added the gate that compiles every template and resolves every name.
The first thing it asked that nobody had asked before was "does every
template a Python module names actually exist", and the answer was no,
once:

    pages/middleware.py:1044   render(request, 'access_denied.html', ...)

That template had never been written. The call sat inside a BARE
`except:`, which caught the TemplateDoesNotExist it could not name and
fell through to `_render_simple_access_denied` - eighty lines of HTML in
an f-string. So nobody ever saw a 500, and nobody ever saw the custom
page either. What they saw was the fallback, and the fallback was the
live product:

    linear-gradient(135deg, #667eea 0%, #764ba2 100%)   full bleed
    h1 { color: #e74c3c }                               two emoji
    no {% extends %}, no nav, no base, no tokens

ModuleAccessMiddleware is third in MIDDLEWARE and its url_permission_map
guards 172 URL prefixes. Every person without can_access_financials and
the rest of them lands there.

AND BECAUSE IT WAS A STRING AND NOT A FILE, NO ROUND HAS EVER SEEN IT.
The twelve standalone templates are at least templates; the colour
rounds, the table and card standards, every A round - none of them can
reach a page that lives inside a Python method. This round makes it a
file, which is most of the point.

WHAT THIS ROUND DOES

  1. Writes pages/templates/access_denied.html, extending base, built
     entirely from base's own classes and carrying no <style> block and
     no hex literal of its own.
  2. Replaces _render_access_denied with one that renders it, keeping
     the OUTER try/except so a failure to render is still a 403 and not
     a 500.
  3. Deletes _render_simple_access_denied and the bare `except:` with it.
  4. Keeps the one thing the f-string did that a template cannot - the
     permission name read as English - as _permission_label, and passes
     it in.

DEMETRI LOOKED FIRST, at 1280 and 390, 6 Oct 2026.

FILES: pages/middleware.py, and one new template.
                                              [test_access_denied.py]
"""
import os
import re
import sys

SUFFIX = '.bak_denied'
MARK = 'E-2b, 6 Oct 2026'

ROOT = os.path.dirname(os.path.abspath(__file__))
MIDDLEWARE = os.path.join(ROOT, 'pages', 'middleware.py')
TEMPLATE_REL = 'pages/templates/access_denied.html'

CHECK = False

# ==========================================================================
# THE PAGE
# ==========================================================================
ACCESS_DENIED_HTML = '''{% extends 'base.html' %}

{% block title %}Access Denied{% endblock %}

{% block content %}
{# E-2b, 6 Oct 2026. THIS PAGE EXISTED AS AN f-STRING FOR THE LIFE OF    #}
{# THE PROJECT. pages/middleware.py tried to render 'access_denied.html' #}
{# inside a bare `except:`, the template had never been written, and so  #}
{# what 172 guarded URL prefixes actually answered with was eighty lines #}
{# of HTML inside a Python method - a purple gradient, two emoji, no     #}
{# base, no nav, no tokens. Because it was a string and not a file, no   #}
{# standards round we have ever run could see it.                        #}
{#                                                                       #}
{# NOT A STANDALONE TEMPLATE. The twelve exempt pages are exempt because #}
{# base cannot reach them - a PDF body, an email. This one is served to  #}
{# a logged-in person in a browser while the database is up, so it       #}
{# extends base like every other page and inherits the nav that is the   #}
{# whole point: somebody who has been stopped needs a way onward.        #}
{#                                                                       #}
{# AND IT CARRIES NO <style> BLOCK AND NO HEX LITERAL. Every colour here #}
{# comes from base. B-1, B-2 and B-2b would each have to re-measure the  #}
{# tree if this page arrived with literals in it, and a page added after #}
{# the colour rounds has no excuse for needing any.                      #}
<div style="max-width: 560px; margin: 0 auto;">

  <h2 class="page-title-h2">ACCESS DENIED</h2>
  <br/>

  {# THE BAR AT THE TOP, which is the house rule, and the Back control   #}
  {# built the house way - the arrow always, the word only where there   #}
  {# is room for it.                           [test_bar_top, D7]        #}
  <div class="page-action-buttons">
    <a href="{% url 'home' %}" class="btn action-primary" role="button">
      <i class="fas fa-home"></i> Home
    </a>
    {# history.back(), not a {% url %}. The house Back means "the screen #}
    {# you came from", and on this page that screen is whichever one     #}
    {# carried the link - there is no single URL to name.                #}
    <a href="javascript:history.back()" class="btn action-back" role="button" aria-label="Back">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>

  <div class="form-card">
    <h3 class="form-section-title"><i class="fas fa-lock"></i> You do not have access to this module</h3>

    <p>Your account is signed in, but it has not been given the permission
       this screen requires. Nothing has gone wrong and nothing was
       changed.</p>

    <p><strong>Signed in as</strong><br/>
       {{ request.user.get_full_name|default:request.user.username }}</p>

    <p><strong>Permission required</strong><br/>
       {{ permission_label }}</p>

    <p><strong>Page requested</strong><br/>
       {{ requested_path }}</p>

    <p>Ask whoever administers your account to add this permission, and
       quote the two lines above - they are what the change needs.</p>
  </div>

</div>
{% endblock %}
'''

# ==========================================================================
# THE REPLACEMENT
# ==========================================================================
# The whole of _render_access_denied AND _render_simple_access_denied,
# from the first def to the return of html_content, becomes this.
NEW_METHODS = '''    @staticmethod
    def _permission_label(required_permission):
        """'auth.can_access_financials' -> 'Can Access Financials'.

        THE ONE THING THE f-STRING DID THAT A TEMPLATE CANNOT. Django's
        template language has no split-then-title, and inventing a filter
        for one page would be a worse trade than four lines here. The
        wording is byte-for-byte what the old page produced, so nobody
        reads a different sentence after this round than before it.
        """
        return required_permission.split('.')[-1].replace('_', ' ').title()

    def _render_access_denied(self, request, required_permission):
        """Render the house access-denied page.   [E-2b, 6 Oct 2026]

        This used to try access_denied.html inside a BARE `except:`,
        catch the TemplateDoesNotExist it could not name, and fall
        through to eighty lines of HTML in an f-string. The template had
        never been written, so the fallback WAS the page - a purple
        gradient with two emoji on it, the only screen in the app that
        was not a template and therefore the only one no standards round
        could ever see. 172 URL prefixes land here.

        THE OUTER except STAYS, and is not the same thing. A bare
        `except:` around a render hides a missing template for years; an
        `except Exception` around the whole method, logging what it
        caught, is the difference between a 403 and a 500 on the day
        base itself breaks.            [test_access_denied.py]
        """
        try:
            return render(request, 'access_denied.html', {
                'required_permission': required_permission,
                'permission_label':
                    self._permission_label(required_permission),
                'requested_path': request.path,
            }, status=403)
        except Exception as e:
            logger.error(f"Error rendering access denied page: {e}")
            return HttpResponseForbidden(
                "Access Denied: Insufficient permissions")
'''

HEAD = ('    def _render_access_denied(self, request, '
        'required_permission):')
TAIL = '        return HttpResponseForbidden(html_content)'


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    """Match the file's own line endings, whatever they are."""
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def new_file(rel, body, what):
    """Create a file this round introduces.

    No backup: there is nothing to back up, and a .bak_ of a file that
    did not exist would be a lie about what was there before. Idempotent
    by MARK, and it refuses a file of the same name it did not write -
    that file would be somebody else's work.
    """
    path = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.isfile(path):
        have = read(path)
        if MARK in have:
            print('  %-44s already there' % rel)
            return path
        raise SystemExit('E-2b: %s exists and this round did not write it'
                         % rel)
    if not CHECK:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        write(path, body)
    print('  %-44s NEW  %s' % (rel, what))
    return path


# ==========================================================================
# THE COUNTS THIS ROUND MOVES
# ==========================================================================
# A ROUND THAT ADDS A TEMPLATE OWNS EVERY NUMBER THAT COUNTS TEMPLATES,
# or the number quietly becomes a statement about last week. A1 learned
# this when it added four pages; the comment it left is the rule.
#
# ANCHORS ARE WHOLE LINES, NOT DIGITS. '142' already appears in
# test_subtree_tones as rgb(142, 98, 7), and a bare '121' would match
# inside any longer number. An anchor that can hit prose or another
# number is how a patcher edits something nobody meant.
#
#   test_tree_roots      MAIN_N 142 -> 143, docstring 150 -> 151
#   test_subtree_tones   walk 142 -> 143, flat 124 -> 125, docstring too
#   test_house_title     121 -> 122 wearers, AND base's own note with it
#   apply_settings_env   BOOT_COUNT 9 -> 11, because this round adds two
#                        suites that boot Django and SE-1's tripwire is
#                        an exact number on purpose
WHY = ('# 143 since 6 Oct: Section E round E-2b added access_denied.html,'
       '\n# the 403 page, which until then lived in an f-string.\n')

COUNTS = [
    ('test_tree_roots.py', [
        ('# 142 since 1 Oct: Section A round A1 added the four public\n'
         '# set-password pages. CRS_N is untouched.\n'
         'MAIN_N = 142\n',
         '# 142 since 1 Oct: Section A round A1 added the four public\n'
         '# set-password pages. CRS_N is untouched.\n'
         + WHY + 'MAIN_N = 143\n',
         'MAIN_N'),
        ('SECTION 1 IS THE TREE ITSELF - both roots, 150 templates, and '
         'the zero\n',
         'SECTION 1 IS THE TREE ITSELF - both roots, 151 templates, and '
         'the zero\n',
         "test_tree_roots' docstring total"),
    ]),
    ('test_subtree_tones.py', [
        ("ok(len(tree) == 142, 'a WALK finds 142 templates', len(tree))\n",
         "ok(len(tree) == 143, 'a WALK finds 143 templates', len(tree))\n",
         'the walk'),
        ("ok(len(top) == 124, '  a flat listing finds 124 - 120 was what "
         "H7 counted',\n",
         "ok(len(top) == 125, '  a flat listing finds 125 - 120 was what "
         "H7 counted',\n",
         'the flat listing'),
        ('every one of the 142 and fails if any page declares a rule for '
         'one of\n',
         'every one of the 143 and fails if any page declares a rule for '
         'one of\n',
         "test_subtree_tones' docstring"),
    ]),
    ('test_house_title.py', [
        ("ok(len(wearers) == 121,\n"
         "   '121 templates now wear the class, which is the number base\\'s "
         "note '\n",
         "# 122 since 6 Oct 2026. Section E round E-2b made the 403 page a\n"
         "# template, and it wears the house title like every other page.\n"
         "ok(len(wearers) == 122,\n"
         "   '122 templates now wear the class, which is the number base\\'s "
         "note '\n",
         'the wearer count'),
    ]),
    # BASE'S OWN NOTE MOVES WITH IT. The suite's assertion is that the two
    # agree; changing one and not the other makes the suite pass while
    # base tells a reader the wrong number.
    ('pages/templates/base.html', [
        ('h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 121 '
         'pages\n',
         'h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 122 '
         'pages\n',
         "base's note"),
    ]),
    ('apply_settings_env.py', [
        ('BOOT_COUNT = 9\n',
         '# 11 since 6 Oct 2026: Section E added test_url_names.py, which\n'
         '# boots Django to resolve names and compile templates, and\n'
         '# test_access_denied.py, which boots it to render one. Both were\n'
         '# written carrying their own setdefault - this number is the\n'
         '# tripwire that proves it rather than assuming it.\n'
         'BOOT_COUNT = 11\n',
         'SE-1\'s boot count'),
    ]),
]


def patch(rel, edits):
    """Apply whole-line edits to a file this round does not own.

    Each anchor must match EXACTLY ONCE, and the file is written only
    when every one of them does. A patcher that does half the edits
    leaves a tree nobody measured.
    """
    path = os.path.join(ROOT, rel.replace('/', os.sep))
    text = read(path)
    if all(new in text for _old, new, _what in edits):
        print('  %-44s already done' % rel)
        return
    for old, new, what in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit('E-2b: %s - the anchor for %s matched %d '
                             'time(s), not once' % (rel, what, n))
    for old, new, _what in edits:
        text = text.replace(old, fit(text, new), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-44s %d count(s) moved' % (rel, len(edits)))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    src = read(MIDDLEWARE)

    # ------------------------------------------------------------------
    # THE ANCHORS, EACH MATCHED EXACTLY ONCE, before anything is written.
    # ------------------------------------------------------------------
    done = MARK in src

    if not done:
        for anchor, what in ((HEAD, 'the renderer'),
                             (TAIL, 'the end of the f-string')):
            n = src.count(anchor)
            if n != 1:
                raise SystemExit(
                    'E-2b: %s matched %d time(s), not once - '
                    'pages/middleware.py is not the file this round was '
                    'measured against' % (what, n))

        a = src.index(HEAD)
        b = src.index(TAIL, a) + len(TAIL)
        b = src.index('\n', b) + 1
        block = src[a:b]

        # AND THE BLOCK REALLY IS THE ONE WE MEAN. Two anchors can both
        # match and still bracket the wrong thing if somebody moved a
        # method between them.
        for must, why in (
                ('_render_simple_access_denied', 'the fallback method'),
                ('#667eea', 'the purple the fallback draws'),
                ('html_content = f"""', 'the f-string itself'),
                ("render(request, 'access_denied.html'", 'the render call')):
            if must not in block:
                raise SystemExit('E-2b: the block between the anchors does '
                                 'not contain %s - refusing to cut it' % why)

        # Nothing outside this block may mention the fallback, or
        # deleting it would break a call site this round cannot see.
        outside = src[:a] + src[b:]
        hits = [m.start() for m in
                re.finditer(r'_render_simple_access_denied', outside)]
        if hits:
            raise SystemExit('E-2b: _render_simple_access_denied is called '
                             'from %d place(s) outside the block this round '
                             'removes' % len(hits))

    print('')
    print('  NEW FILES')
    print('  ' + '-' * 70)
    new_file(TEMPLATE_REL, ACCESS_DENIED_HTML,
             'the 403 page, on base')

    print('')
    print('  CHANGED FILES')
    print('  ' + '-' * 70)
    if done:
        print('  %-44s already carries %s' % ('pages/middleware.py', MARK))
    else:
        text = src[:a] + fit(src, NEW_METHODS) + src[b:]

        if 'html_content' in text:
            raise SystemExit('E-2b: html_content survives the rewrite')
        # BY COUNT, NOT BY PRESENCE. #667eea appears FOUR times in this
        # module: twice in the fallback this round removes and twice in
        # _render_connectivity_error, which is a different page with a
        # real reason to be an f-string - the database is down, so it
        # cannot render a template that extends base. A check that asked
        # whether the purple is gone from the file would be asking this
        # round to delete somebody else's page.
        if text.count('#667eea') != src.count('#667eea') - 2:
            raise SystemExit('E-2b: the fallback\'s two gradients did not '
                             'both go - %d before, %d after'
                             % (src.count('#667eea'), text.count('#667eea')))
        if text.count("render(request, 'access_denied.html'") != 1:
            raise SystemExit('E-2b: the render call is not there exactly '
                             'once after the rewrite')
        try:
            import ast
            ast.parse(text)
        except SyntaxError as e:
            raise SystemExit('E-2b: the rewritten middleware does not '
                             'parse - %s' % e)

        if not CHECK:
            backup(MIDDLEWARE)
            write(MIDDLEWARE, text)
        print('  %-44s %d lines of f-string removed'
              % ('pages/middleware.py', block.count('\n')))

    print('')
    print('  COUNTS THIS ROUND MOVES')
    print('  ' + '-' * 70)
    for rel, edits in COUNTS:
        patch(rel, edits)

    print('')
    if CHECK:
        print('E-2b  NOT APPLIED')
        return 1
    print('E-2b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
