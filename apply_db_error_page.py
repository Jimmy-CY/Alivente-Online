#!/usr/bin/env python3
"""
apply_db_error_page.py
======================

Two fixes to the database error page in pages/middleware.py.

1. Mojibake
-----------
The response is built with `content_type='text/html'`. Passing content_type
explicitly makes Django use it verbatim - no charset is appended - so the
browser falls back to latin-1 and the UTF-8 emoji bytes shatter into
"âš ï¸ Connection Issue". Adding `; charset=utf-8` fixes it. (Django only
appends DEFAULT_CHARSET when content_type is omitted entirely.)

2. The page names the wrong cause
---------------------------------
Every database exception rendered as "We're experiencing temporary
connectivity issues. This usually resolves quickly. Please try refreshing."

That is true for a dropped connection and actively misleading for anything
else. A missing column after an un-run migration produced exactly that page:
it invited a wait-and-retry, when refreshing could never work and the fix was
one `manage.py migrate`. The log had the answer instantly; the screen pointed
away from it.

So the exception is now classified and the page says which of the two it is:

  connectivity  server gone away, too many connections, lost connection,
                InterfaceError            -> unchanged wording, DB_CONNECTION_503
  schema        unknown column, no such table, bad SQL, ProgrammingError
                                          -> "the database is out of date",
                                             no refresh prompt, DB_SCHEMA_503

Classification uses the MySQL error number first and the exception class as a
fallback - drivers disagree about which class wraps which code, so the number
is the more reliable signal. **Anything unrecognised keeps the existing
connectivity wording**, so no current behaviour changes except where we are
confident.

When settings.DEBUG is on, the schema page also prints the actual exception.
Locally that turns a mystery into a one-line diagnosis. It is never shown when
DEBUG is off.

Idempotent; backs up to .bak_dberrorpage. Run from the project root:

    python apply_db_error_page.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'middleware.py')

SENTINEL = 'DB_SCHEMA_503'


# --- 1. pass the exception through to the renderer -------------------------

# Anchored on the line above rather than the one below: the blank line that
# follows this call carries trailing whitespace, and matching on it fails
# invisibly. "Error type:" appears at this call site only.
CALL1_OLD = """                f"Error type: {type(e).__name__}"
            )
            self._emergency_cleanup()
            return self._render_connectivity_error(request)"""

CALL1_NEW = """                f"Error type: {type(e).__name__}"
            )
            self._emergency_cleanup()
            return self._render_connectivity_error(request, e)"""

CALL2_OLD = """        except (DatabaseError, InterfaceError):
            connections.close_all()
            return self._render_connectivity_error(request)

    def process_exception(self, request, exception):"""

CALL2_NEW = """        except (DatabaseError, InterfaceError) as e:
            connections.close_all()
            return self._render_connectivity_error(request, e)

    def process_exception(self, request, exception):"""

CALL3_OLD = """            self._emergency_cleanup()
            return self._render_connectivity_error(request)
        return None"""

CALL3_NEW = """            self._emergency_cleanup()
            return self._render_connectivity_error(request, exception)
        return None"""


# --- 2. classification helper, inserted before the renderer ----------------

HELPER_ANCHOR = "    def _render_connectivity_error(self, request):"

HELPER = '''    # MySQL error numbers that genuinely mean "cannot reach or use the server".
    # These keep the reassuring, retry-friendly wording.
    _CONNECTIVITY_ERRNOS = frozenset({
        1040,   # too many connections
        1042,   # unable to connect to any of the specified hosts
        1043,   # bad handshake
        1045,   # access denied - not connectivity as such, but nothing the
                # user can do, and retrying is the least-wrong advice
        1049,   # unknown database
        2002,   # can't connect through socket
        2003,   # can't connect to server
        2005,   # unknown server host
        2006,   # server has gone away
        2013,   # lost connection during query
        2055,   # lost connection, system error
    })

    # Error numbers that mean the SQL does not match the schema. Refreshing
    # cannot fix any of these; a migration or a deployment usually can.
    _SCHEMA_ERRNOS = frozenset({
        1051,   # unknown table
        1054,   # unknown column      <- the un-run migration case
        1064,   # SQL syntax error
        1091,   # can't drop; check that it exists
        1109,   # unknown table in the field list
        1146,   # table doesn't exist
        1364,   # field has no default value
    })

    @classmethod
    def _classify_db_exception(cls, exception):
        """'connectivity' or 'schema'.

        The MySQL error number is checked before the exception class because
        drivers disagree about which class wraps which code - mysqlclient and
        PyMySQL do not map ER_BAD_FIELD_ERROR the same way. The number is
        unambiguous where it is available.

        Unrecognised exceptions fall back to 'connectivity', which is the
        wording this page has always used. Nothing changes except where the
        classification is confident.
        """
        if exception is None:
            return 'connectivity'

        errno = None
        args = getattr(exception, 'args', None) or ()
        if args and isinstance(args[0], int):
            errno = args[0]
        else:
            # Django wraps the driver error; the original carries the number.
            cause = getattr(exception, '__cause__', None)
            cause_args = getattr(cause, 'args', None) or ()
            if cause_args and isinstance(cause_args[0], int):
                errno = cause_args[0]

        if errno is not None:
            if errno in cls._CONNECTIVITY_ERRNOS:
                return 'connectivity'
            if errno in cls._SCHEMA_ERRNOS:
                return 'schema'

        # No usable number - fall back to the exception class.
        if isinstance(exception, InterfaceError):
            return 'connectivity'
        try:
            from django.db import OperationalError, ProgrammingError
            if isinstance(exception, ProgrammingError):
                return 'schema'
            if isinstance(exception, OperationalError):
                return 'connectivity'
        except Exception:
            pass

        return 'connectivity'

'''


# --- 3. the renderer itself ------------------------------------------------

RENDER_OLD_HEAD = """    def _render_connectivity_error(self, request):
        \"\"\"Render user-friendly connectivity error page\"\"\"
        # Always return the HTML fallback to avoid template issues
        return HttpResponse(
            \"\"\""""

RENDER_NEW_HEAD = """    def _render_connectivity_error(self, request, exception=None):
        \"\"\"Render the database error page, worded for the kind of failure.

        `exception` is optional so any older call site still works; without it
        the page reads exactly as it always did.
        \"\"\"
        kind = self._classify_db_exception(exception)

        if kind == 'schema':
            heading = 'Database Out Of Date'
            # No "try refreshing" here on purpose. Refreshing cannot fix a
            # schema mismatch, and saying so sends people looking in the wrong
            # place - which is precisely what happened.
            body = (
                \"<p>The application has been updated but the database has not \"
                \"caught up, so a table or column it expects is missing.</p>\"
                \"<p>Refreshing will not help. This needs a database migration \"
                \"to be applied.</p>\"
            )
            code = 'DB_SCHEMA_503'
        else:
            heading = 'Connection Issue'
            body = (
                \"<p>We're experiencing temporary connectivity issues. This \"
                \"usually resolves quickly.</p>\"
                \"<p>Please try refreshing the page or check back in a few \"
                \"moments.</p>\"
            )
            code = 'DB_CONNECTION_503'

        # Only ever in DEBUG. Locally this turns a mystery into a diagnosis;
        # in production it would leak schema detail to whoever hit the page.
        detail = ''
        try:
            from django.conf import settings
            from django.utils.html import escape
            if settings.DEBUG and exception is not None:
                detail = ('<pre class="detail">%s: %s</pre>'
                          % (escape(type(exception).__name__), escape(str(exception))))
        except Exception:
            detail = ''

        # Buttons differ: refreshing is worth offering only when it might work.
        buttons = '<a href="/" class="btn">Go Home</a>'
        if kind != 'schema':
            buttons = ('<a href="javascript:location.reload()" class="btn">Refresh Page</a>'
                       + buttons)

        return HttpResponse(
            \"\"\""""

# The body of the HTML: replace the hardcoded block with placeholders.
HTML_OLD = """            <body>
                <div class="error-container">
                    <h1>⚠️ Connection Issue</h1>
                    <p>We're experiencing temporary connectivity issues. This usually resolves quickly.</p>
                    <p>Please try refreshing the page or check back in a few moments.</p>
                    <a href="javascript:location.reload()" class="btn">\U0001f504 Refresh Page</a>
                    <a href="/" class="btn">\U0001f3e0 Go Home</a>
                    <div class="error-code">Error Code: DB_CONNECTION_503</div>
                </div>
            </body>
            </html>
            \"\"\",
            status=503,
            content_type='text/html'
        )"""

HTML_NEW = """            <body>
                <div class="error-container">
                    <h1>__HEADING__</h1>
                    __BODY__
                    __BUTTONS__
                    <div class="error-code">Error Code: __CODE__</div>
                    __DETAIL__
                </div>
            </body>
            </html>
            \"\"\"
            # Token replacement rather than %-formatting or .format(): the CSS
            # above is full of percentages ("0%, #764ba2 100%") and braces,
            # both of which those two would try to interpret.
            .replace('__HEADING__', heading)
            .replace('__BODY__', body)
            .replace('__BUTTONS__', buttons)
            .replace('__CODE__', code)
            .replace('__DETAIL__', detail),
            status=503,
            # The charset MUST be spelled out. Django appends DEFAULT_CHARSET
            # only when content_type is omitted; passing it bare left the
            # browser to guess latin-1, which is what turned the heading into
            # "âš ï¸ Connection Issue".
            content_type='text/html; charset=utf-8'
        )"""

# The title and one style rule need adjusting too.
TITLE_OLD = "                <title>Connection Issue</title>"
TITLE_NEW = "                <title>Database Unavailable</title>"

STYLE_OLD = """                    .error-code {
                        color: #999;
                        font-size: 0.9em;
                        margin-top: 20px;
                    }"""

STYLE_NEW = """                    .error-code {
                        color: #999;
                        font-size: 0.9em;
                        margin-top: 20px;
                    }
                    .detail {
                        text-align: left;
                        background: #f6f7f8;
                        border: 1px solid #e1e5e9;
                        border-radius: 6px;
                        padding: 10px 12px;
                        margin-top: 16px;
                        font-size: 0.8em;
                        color: #c0392b;
                        white-space: pre-wrap;
                        word-break: break-word;
                    }"""


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


EDITS = (
    ('call site 1', CALL1_OLD, CALL1_NEW),
    ('call site 2', CALL2_OLD, CALL2_NEW),
    ('call site 3', CALL3_OLD, CALL3_NEW),
    ('renderer head', RENDER_OLD_HEAD, RENDER_NEW_HEAD),
    ('page title', TITLE_OLD, TITLE_NEW),
    ('style block', STYLE_OLD, STYLE_NEW),
    ('page body', HTML_OLD, HTML_NEW),
)


def main():
    if not os.path.exists(TARGET):
        print('! pages/middleware.py not found - run from the project root')
        return 1

    src, enc, nl = sniff(TARGET)

    if SENTINEL in src:
        print('= already patched - nothing to do')
        return 0

    for name, old, _ in EDITS:
        n = src.count(old)
        if n != 1:
            print('! %s anchor matched %d times, expected 1 - aborting, nothing written'
                  % (name, n))
            return 1
    if src.count(HELPER_ANCHOR) != 1:
        print('! helper anchor matched %d times, expected 1 - aborting'
              % src.count(HELPER_ANCHOR))
        return 1

    for _, old, new in EDITS:
        src = src.replace(old, new, 1)
    src = src.replace(RENDER_NEW_HEAD, HELPER + RENDER_NEW_HEAD, 1)

    try:
        compile(src, 'middleware.py', 'exec')
    except SyntaxError as exc:
        print('! the patched file does not compile: %s (line %s)' % (exc.msg, exc.lineno))
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched and the result compiles, nothing written')
        return 0

    bak = TARGET + '.bak_dberrorpage'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/middleware.py patched (backup: .bak_dberrorpage)')
    print('  - charset=utf-8 declared, so the page stops rendering as mojibake')
    print('  - schema errors say so, and do not suggest refreshing')
    print('  - connectivity errors read exactly as before')
    print('  - the exception itself is shown when DEBUG is on')
    print('')
    print('Verify:  python -m py_compile pages/middleware.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
