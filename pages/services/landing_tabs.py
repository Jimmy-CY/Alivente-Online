# -*- coding: utf-8 -*-
"""Which tab a landing page opens on.               TB-1b, 15 Oct 2026

THREE PAGES, TWO VIEW MODULES, ONE RULE. admin_apms and personal_page
live in pages/views/administration.py and finance lives in
pages/views/finance.py, so the alternative to a module of its own is one
view module importing a helper out of another for no reason but
proximity.

WHAT TRAVELS IS A KEY, NOT A TAB. ?tab=/anything/ read back at face
value is how a URL parameter becomes a way to put arbitrary text into a
class attribute. The key is checked against THAT PAGE'S OWN LIST, which
the view passes in, and anything else falls to the page's default - so a
stale bookmark opens the page it always did rather than a blank one.

WHY THE VIEW AND NOT A HASH READ ON LOAD. #setup would work, and the
reader would see the wrong tab painted and then jump. The server knows
the answer before the first frame, so it says so in the markup.
"""


def landing_tab(request, tabs, default):
    """The tab key this landing page should open on.

    `tabs` is the page's own tuple of keys and `default` is the one it
    arrives on when nothing asks. An unrecognised key - a typo, an old
    bookmark, or something forged - is not an error: it is the default,
    silently, because a landing page that refuses to render is worse
    than one that opens where it always did.
    """
    key = request.GET.get('tab', '')
    return key if key in tabs else default
