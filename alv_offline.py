# -*- coding: utf-8 -*-
"""alv_offline.py - E20, 17 Oct 2026.  NO RENDER REACHES THE NETWORK.

IMPORT IT AND IT IS DONE.  One line in a suite, beside the playwright
import:

    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline

WHY IT EXISTS.  base.html pulls FIVE files off content delivery
networks - Bootstrap's stylesheet, Font Awesome, jQuery, Popper and
Bootstrap's script.  170 of the 257 browser suites block that with a
route of their own.  87 did not.

IT IS A REPRODUCIBILITY PROBLEM, NOT A SPEED ONE.  A render that
reaches the internet measures whatever layout existed at the moment
the last stylesheet happened to arrive, and next time that is a
different moment.  Font Awesome decides the width of every icon button
on the page.  The fixtures exist precisely so that Bootstrap and
jQuery come from files on disk whose bytes are pinned - and six suites
were quietly fetching a newer Bootstrap over the top of them.

SIX, NOT EIGHTY-SEVEN - and the difference is the point of the tally
at the bottom of this file.  Across one whole sweep the guard turned
away 87 requests, all from six suites: test_zoom_guards (31),
test_required_promise (20), test_pd3 (16), test_card_wrap (10),
test_pd_tables (6), test_pd_palette (4).  The other 81 copy base's
<style> blocks and leave its <link> tags behind, so they ask for
nothing.  They are guarded anyway, because the next fixture written
from base's head would have joined the six silently.

The tally also turned up a fourth host nobody had listed -
stackpath.bootstrapcdn.com - which is the kind of thing a census finds
and a guess does not.

MEASURED, with and without: a fixture carrying three CDN links loads
in 0.95s guarded, and unguarded does not finish loading in eight
seconds at all, because the requests hang rather than refuse.

WHY A ROUTE AND NOT A CHROMIUM FLAG.  The obvious instrument is
`--host-resolver-rules=MAP * ~NOTFOUND`, and it is the wrong one.
Measured here, with HTTPS_PROXY set, the CDN request never reaches the
resolver at all - Chromium hands it to the proxy and the failure comes
back as ERR_TUNNEL_CONNECTION_FAILED whether the flag is present or
not.  A guard whose effect cannot be told apart from the environment's
is not a guard you can test.  The flag also silences loopback: `MAP *
~NOTFOUND` blocks a literal 127.0.0.1, which would have broken
test_lazy_images.py, and `EXCLUDE localhost` does not spare the
numeric form either.

A ROUTE IS TESTABLE.  It aborts the request itself, so the failure
reads net::ERR_FAILED and nothing else in the environment produces
that.  It is also what the 170 already do - this applies the same
instrument uniformly rather than inventing a second one.

LOOPBACK IS SPARED, deliberately.  test_lazy_images.py stands up a
real HTTP server on 127.0.0.1 and asks the browser to fetch images
from it; that is the suite measuring its own fixture, not the page
reaching the internet.

WHAT IT PATCHES.  Browser.new_page, Browser.new_context and
BrowserContext.new_page - the three ways a suite can end up with a
page.  Routing a context covers every page made from it; a page made
straight off the Browser gets its own route, because the implicit
context behind it is not handed to the caller.

DOUBLE GUARDING IS HARMLESS.  A suite that already routes gets two
handlers that both abort, and the answer is the same.  Nothing here
removes or overrides a suite's own route.
"""
import re

ABORTED = []          # every url this module turned away, in order
ALLOWED = []          # every url it let through (loopback only)
PATCHED = False

# WHAT COUNTS AS THE NETWORK.  http and https only.  file:// is how
# every fixture is loaded and data: is how images are inlined; neither
# goes anywhere.
NET = re.compile(r'^https?://')

# AND WHAT DOES NOT.  A suite's own HTTP server on loopback is the
# fixture, not the internet.  The numeric form is listed as well as the
# name because test_lazy_images.py uses the numeric form, and because a
# Chromium resolver rule excluding `localhost` does NOT spare
# 127.0.0.1 - measured, 17 Oct 2026.
LOOPBACK = re.compile(r'^https?://(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?(?:/|$)')


def _handler(route):
    url = route.request.url
    if LOOPBACK.match(url):
        ALLOWED.append(url)
        try:
            route.continue_()
        except Exception:
            pass
        return
    ABORTED.append(url)
    try:
        route.abort()
    except Exception:
        pass


def guard(obj):
    """Put the route on a page or a context.  Safe to call twice."""
    try:
        obj.route(NET, _handler)
    except Exception:
        # A closed context, or a Playwright that does not take a
        # pattern here.  A guard that raises would turn a network
        # question into a suite failure, which is worse than the
        # fetch it was trying to prevent.
        pass
    return obj


async def _ahandler(route):
    """The same decision, awaited.

    FIFTEEN OF THE 257 USE THE ASYNC API, and `async_playwright`
    contains the letters `sync_playwright`, which is how the first
    census of this round counted thirteen async suites as sync ones
    and the patcher refused on the first of them. They are a separate
    set of classes and they need their own patch."""
    url = route.request.url
    if LOOPBACK.match(url):
        ALLOWED.append(url)
        try:
            await route.continue_()
        except Exception:
            pass
        return
    ABORTED.append(url)
    try:
        await route.abort()
    except Exception:
        pass


def _install_async():
    try:
        from playwright.async_api import Browser, BrowserContext
    except Exception:
        return
    for cls, name in ((Browser, 'new_page'), (Browser, 'new_context'),
                      (BrowserContext, 'new_page')):
        real = getattr(cls, name)
        if getattr(real, '_alv_offline', False):
            continue

        def wrap(real=real):
            async def inner(self, *a, **kw):
                obj = await real(self, *a, **kw)
                try:
                    await obj.route(NET, _ahandler)
                except Exception:
                    pass
                return obj
            inner._alv_offline = True
            inner.__name__ = getattr(real, '__name__', 'wrapped')
            return inner

        setattr(cls, name, wrap())


def _install():
    """Patch the three ways a suite ends up holding a page.

    IT NEVER RAISES. This module is imported from inside the try that
    asks whether playwright is installed at all, so on a machine
    without it the import must be a no-op rather than the thing that
    turns a skipped render into a crashed suite. PATCHED says which
    happened, and the suite asks."""
    global PATCHED
    if PATCHED:
        return
    try:
        from playwright.sync_api import Browser, BrowserContext
    except Exception:
        _install_async()
        return

    for cls, name in ((Browser, 'new_page'), (Browser, 'new_context'),
                      (BrowserContext, 'new_page')):
        real = getattr(cls, name)
        if getattr(real, '_alv_offline', False):
            continue

        def wrap(real=real):
            def inner(self, *a, **kw):
                return guard(real(self, *a, **kw))
            inner._alv_offline = True
            inner.__name__ = getattr(real, '__name__', 'wrapped')
            return inner

        setattr(cls, name, wrap())
    _install_async()
    PATCHED = True


def _tally():
    """WHICH SUITES WERE ACTUALLY REACHING THE NETWORK - askable later.

    Set ALV_OFFLINE_TALLY to a path and every process that imports this
    module appends one JSON line to it when it exits: its argv[0], how
    many requests were turned away, and the hosts. Off by default and
    costs nothing; it exists because the honest answer to "how much was
    this costing" is a measurement, and the first guess at it was
    wrong - most fixtures carry only base's <style> blocks and ask for
    nothing at all.
    """
    import os
    path = os.environ.get('ALV_OFFLINE_TALLY')
    if not path:
        return
    import atexit, json, sys as _s

    def out():
        if not ABORTED and not ALLOWED:
            return
        try:
            row = {'who': os.path.basename(_s.argv[0] or '?'),
                   'aborted': len(ABORTED), 'allowed': len(ALLOWED),
                   'hosts': sorted(set(u.split('/')[2]
                                       for u in ABORTED))[:6]}
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(row) + '\n')
        except Exception:
            pass

    atexit.register(out)


_install()
_tally()
