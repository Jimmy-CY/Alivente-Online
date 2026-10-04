# -*- coding: utf-8 -*-
"""TL-1 - THE GREEK TASK LIST RAISED A 500, AND THE DOCSTRING KNEW

Demetri, 4 Oct 2026, from Live: "When I press Generate Task List now
(with Greek selected), I get the following error. The English Task List
works 100%."

    Server Error (500)
    alivente.online/projects/2/task-list/?language=greek

==========================================================================
TWO ARGUMENTS DECLARED, THREE PASSED, SIX TIMES
==========================================================================
    pages/views/projects.py:60    def get_translated_text(text,
                                                          target_language='en')

    pages/views/projects.py:1217  get_translated_text(
                                      project.project_name,
                                      getattr(project, 'project_name_greek', None),
                                      language)

TypeError, raised before the template is ever reached. And the reason
English works 100% is not luck - it is the shape of the call. All six
sites are written

    'name_greek': get_translated_text(...) if language == 'greek'
                  else project.project_name

so English never EVALUATES one of them. The defect could only ever fire
on Greek, which is exactly how it was reported.

==========================================================================
THE MODULE DOCSTRING RECORDED IT - AND WAS WRONG ABOUT WHEN
==========================================================================
Verbatim, from the top of pages/views/projects.py:

    Known latent issues (preserved verbatim - only manifest when the
    disabled persistent-translation path is re-enabled with
    language='greek'):
      - get_translated_text stub signature takes 2 args but
        project_task_list calls it with 3.

It did not wait to be re-enabled. Disabling the translation service
emptied the function BODIES. It never touched the CALL SITES, and the
call sites are what raise. The condition the note was waiting for -
"re-enabled with language='greek'" - was really just "language='greek'",
and that has been one radio button away the whole time.

A DEFECT WRITTEN INTO A DOCSTRING IS A DEFECT THAT SHIPS. This round
does not move the note to a better place; it removes the defect and
leaves the account of it.

==========================================================================
THE THIRD ARGUMENT WAS NEVER SPARE
==========================================================================
It is the translation RECORDED ON THE MODEL. All four fields exist:

    Project.project_name_greek          CharField(blank=True)
    Project.project_description_greek   TextField(blank=True)
    ProjectTask.task_name_greek         CharField(blank=True)
    ProjectTask.task_description_greek  TextField(blank=True)

and the Edit Task form already writes them - there are English and Greek
tabs on that page today. So the stored text is real, typed by hand, and
was being handed to a function that had no parameter to catch it.

The signature says so now:

    get_translated_text(text, stored='', language='english')

Stored, non-blank, and Greek asked for: the stored text. Otherwise the
original, because a blank cell is worse than an untranslated one - and
the template already agrees, writing {{ item.name_greek|default:item.name }}.

==========================================================================
AND IT IS DEFINED ONCE NOW
==========================================================================
There were two copies: pages/translation_service.py and a verbatim pair
re-declared inside pages/views/projects.py, with the import commented
out above them. Two copies of one definition is the PA-1 defect in
another costume - the one where a list written out twice drifts and the
second copy is the one that runs. translation_service.py is the
definition; projects.py imports it.

Backups: .bak_greekarity. Idempotent. --check writes nothing.
"""
import os
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_greekarity'
ROOT = os.getcwd()
CRLF = {}

SERVICE = os.path.join(ROOT, 'pages', 'translation_service.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'projects.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('TL1: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('TL1: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('TL-1 - THE GREEK TASK LIST 500%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE DEFINITION. ONE COPY, THREE ARGUMENTS.
# ==========================================================================
SERVICE_NEW = '''# -*- coding: utf-8 -*-
"""The persistent translation stubs - THE ONLY COPY.

Translation itself is still disabled: googletrans was removed and
nothing has replaced it, so neither function calls out to anything. What
they do is serve the Greek text an editor has already TYPED, through the
English/Greek tabs on the Edit Task form.

TL-1, 4 Oct 2026 - get_translated_text declared two arguments and
project_task_list passed three, six times, every one of them behind
`if language == 'greek'`. English skipped all six and worked perfectly;
Greek raised TypeError before the template was reached and Live answered
Server Error (500). The third argument was never spare - it is the
translation stored on the model, and the signature says so now.

These were also DECLARED TWICE: here, and again inside
pages/views/projects.py with the import commented out above them. The
view imports this module now. Two copies of one definition is how a
definition drifts.

TODO: replace googletrans with deep-translator and translate on demand
when `stored` comes back blank.
"""


def ensure_project_translations(project):
    """Fill in a Project's *_greek fields. Disabled: does nothing.

    The parameter is a Project - project_task_list has always called it
    with one. It was declared as `request`, which is harmless while the
    body is `pass` and a false lead for whoever writes the body.
    """
    pass


def get_translated_text(text, stored='', language='english'):
    """The text to show for `language`.

    `stored` is the translation recorded on the model - project_name_greek
    and its three siblings, every one blank=True, so it is routinely
    empty and may arrive as None from a getattr default.

    Greek asked for and a non-blank translation on file: that. Anything
    else: the original, because a blank cell is worse than an
    untranslated one - which is the same call the template makes when it
    writes {{ item.name_greek|default:item.name }}.
    """
    if language == 'greek' and stored and stored.strip():
        return stored
    return text
'''

s, sraw = read(SERVICE)
if 'TL-1, 4 Oct 2026' in s:
    print('  translation_service.py     already the only copy')
else:
    if 'def get_translated_text(text, target_language=' not in s.replace('\r\n', '\n'):
        raise SystemExit('TL1: translation_service.py is not the file this round read')
    if not CHECK:
        back_up(SERVICE, sraw)
        write(SERVICE, SERVICE_NEW)
    print('  translation_service.py     three arguments, one copy')

# ==========================================================================
# 2. THE VIEW IMPORTS IT AND DROPS ITS OWN PAIR.
# ==========================================================================
v, vraw = read(VIEW)
vnl = v.replace('\r\n', '\n')

OLD_STUBS = """# --------------------------------------------------------------------------- #
# Translation service stubs (translation temporarily disabled)
# --------------------------------------------------------------------------- #
# from ..translation_service import ensure_project_translations, get_translated_text

def ensure_project_translations(request):
    pass


def get_translated_text(text, target_language='en'):
    return text
"""

NEW_STUBS = """# --------------------------------------------------------------------------- #
# Translation service stubs (translation itself is still disabled)
# --------------------------------------------------------------------------- #
# TL-1, 4 Oct 2026 - THE IMPORT IS BACK AND THE LOCAL PAIR IS GONE. These
# two were declared here as well, with this line commented out above
# them, so one definition existed in two places and the copy that ran was
# the one nobody was reading. The signature that raised the 500 -
# (text, target_language) against a three-argument call - was this copy's.
from ..translation_service import ensure_project_translations, get_translated_text
"""

OLD_DOC = """Known latent issues (preserved verbatim - only manifest when the
disabled persistent-translation path is re-enabled with language='greek'):
  - get_translated_text stub signature takes 2 args but project_task_list
    calls it with 3.
  - ensure_project_translations stub parameter is named 'request' but it
    is called with a project in project_task_list (harmless while the
    body is a no-op; matters once implemented).
"""

NEW_DOC = """TL-1, 4 Oct 2026 - THE TWO "KNOWN LATENT ISSUES" THIS DOCSTRING USED TO
CARRY WERE NEITHER LATENT NOR PRESERVED FOR A REASON. They were, verbatim:

    - get_translated_text stub signature takes 2 args but
      project_task_list calls it with 3.
    - ensure_project_translations stub parameter is named 'request' but
      it is called with a project in project_task_list.

and the note said they would "only manifest when the disabled
persistent-translation path is re-enabled with language='greek'".

The first one did not wait. Disabling translation emptied the function
BODIES; it never touched the CALL SITES, and the call sites are what
raise. Six of them pass three arguments, each behind `if language ==
'greek'`, so English skipped every one and ran clean while Greek raised
TypeError and Live answered Server Error (500) - reported from the
Projects page with the English list working beside it.

The stubs live in ..translation_service now, declared once, and
get_translated_text takes the stored translation as its second argument
because that is what was always being passed to it. test_greek_arity
holds the signature, the six call sites and the single definition.
"""

if 'TL-1, 4 Oct 2026' in vnl:
    print('  views/projects.py          already imports the stubs')
else:
    vnl = swap(vnl, OLD_STUBS, NEW_STUBS, 'the local stub pair')
    vnl = swap(vnl, OLD_DOC, NEW_DOC, 'the latent-issues note')
    vnl = swap(
        vnl,
        """  - Translation utilities - both the temporarily-disabled persistent
    translation stubs (ensure_project_translations, get_translated_text)
    and the on-demand Google Translate AJAX endpoint (translate_text +
    translate_to_greek_service helper).
""",
        """  - Translation utilities - the on-demand Google Translate AJAX
    endpoint (translate_text + translate_to_greek_service helper). The
    persistent stubs are imported from ..translation_service; they used
    to be re-declared here as well.
""",
        'the utilities bullet')
    out = vnl.replace('\n', '\r\n') if CRLF.get(VIEW) else vnl
    if not CHECK:
        back_up(VIEW, vraw)
        write(VIEW, out)
    print('  views/projects.py          imports the stubs, note replaced')

# ==========================================================================
# 3. THIS ROUND'S SUITE WALKS pages/, AND THE TREE KEEPS A REGISTER OF THAT.
# ==========================================================================
# test_greek_arity reads every .py under pages/ to bind every call
# against the signature it reaches. X0 keeps five lists of every suite
# that walks a root of its own, and test_tree_roots section 3 finds them
# with a deliberately crude `'os.walk(' in text`. A suite that walks and
# is on none of the lists fails that gate.
#
# FOURTH TIME. LZ-1, BK-1 and PJ-6 each shipped a suite that walked
# without registering, and each one landed on this same register.
#
# ALREADY_WIDE is the right list, and for the reason test_ai_models is on
# it: this walks the repo for PYTHON, not a template root. Pointing it at
# pages/templates would blind it - a view can be written in any file.
REPAIRS = [
    ('alv_tree.py',
     """                # any file. Pointing it at the template
                # tree would blind it. [R1]
                'test_ai_models.py']""",
     """                # any file. Pointing it at the template
                # tree would blind it. [R1]
                'test_ai_models.py',
                # TL-1, 4 Oct 2026 - same shape, same reason. It binds
                # every call made by bare name under pages/ against the
                # signature it reaches, so what it needs is every .py
                # there is. A template root would hide the views.
                'test_greek_arity.py']"""),
]

for name, old_t, new_t in REPAIRS:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print('  %-26s not on disk - skipped' % name)
        continue
    t2, raw2 = read(path)
    n2 = t2.replace('\r\n', '\n')
    if 'test_greek_arity.py' in n2:
        print('  %-26s already registered' % name)
        continue
    c = n2.count(old_t)
    if c != 1:
        raise SystemExit('TL1: %s - the anchor appears %d times, not once'
                         % (name, c))
    n2 = n2.replace(old_t, new_t)
    out2 = n2.replace('\n', '\r\n') if CRLF.get(path) else n2
    if not CHECK:
        back_up(path, raw2)
        write(path, out2)
    print('  %-26s the suite is on the walking register' % name)

print('=' * 74)
print('TL-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
