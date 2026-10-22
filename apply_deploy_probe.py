# -*- coding: utf-8 -*-
"""apply_deploy_probe.py - round DP-1, 22 Oct 2026.

THE PUSH SCRIPT ENDS BY SAYING 'RAILWAY WILL BUILD AND DEPLOY FROM THIS
PUSH', AND THEN NOBODY FINDS OUT WHETHER IT DID.

Push 4 landed on 21 October into a Railway with builds paused. Push 5
landed on 22 October into the same thing. Both runs ended with the
cheerful line above, both printed their post-deploy checks, and in both
cases the live site went on running 3245f19 for days. The checks were
checks of a deploy that had not happened.

THE SITE TELLS THE SCRIPT WHAT IT IS RUNNING. /version/ answers seven
hexadecimal characters and nothing else - the short SHA of the commit
the running process was built from, read off RAILWAY_GIT_COMMIT_SHA.
After a push, the script asks that URL every fifteen seconds until it
answers the SHA that was just pushed, or until the wait runs out.

AND IT TAKES NO CREDENTIALS TO DO IT. Railway has an API that would
answer this directly and it needs a token. A token on his laptop, in a
script, in a repository, is a thing that can leak and a thing that must
be rotated; the live site answering a public question about itself is
neither. The probe is unauthenticated BY DESIGN, and what it can tell
an unauthenticated caller is seven characters of hex.

WHAT THE ENDPOINT MAY RETURN IS WHITELISTED, NOT ESCAPED. The value
comes from the environment, and an environment variable is somebody
else's string. Every character that is not [0-9a-f] is dropped before
anything is sent, so the worst a hostile RAILWAY_GIT_COMMIT_SHA can
produce is a shorter hex string or the word unknown. That is the same
discipline as testing a line's SHAPE rather than regexing a secret out
of it.

IT IS EXEMPT FROM THE MODULE GATE, DELIBERATELY AND BY NAME.
ModuleAccessMiddleware redirects anonymous callers to the login page,
and a probe that must work from a laptop with no session cannot have
that. 'api/' is already in that exempt list and would have hidden this
change inside somebody else's prefix - but nothing is mounted under
api/ at all, so relying on it would be relying on dead configuration
that the next person to read the list may well delete. 'version/' goes
in on its own line with its own reason.

THE TIMEOUT IS NOT A FAILURE. The push is already in by the time the
wait starts, so running out of patience costs nothing and the script
says so: what the live site is still running, and the one line that
asks again. Exit code 0 either way.

AND THE PHOTO COMMAND SAYS WHAT IT WROTE. Demetri ran
convert_recipe_photos --write on 22 October and got back the same table
the dry run printed, with the 'DRY RUN. Nothing was written' line
simply absent. Absence is not a report. The write path now reads every
row back out of the database, measures the file on disk, and says how
many landed and what they weigh - or names the ones that did not.

Idempotent. Every file backed up to .bak_deployprobe.
"""
import os
import re
import sys

SUFFIX = '.bak_deployprobe'
URLS = os.path.join('mysite', 'urls.py')
MID = os.path.join('pages', 'middleware.py')
CMD = os.path.join('pages', 'management', 'commands',
                   'convert_recipe_photos.py')
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_deploy_probe.py'
PATCHER = 'apply_deploy_probe.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'DP-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE ENDPOINT
# ==========================================================================
URL_WAS = """def robots_txt(request):
    content = "User-agent: *\\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")"""

URL_NOW = '''def robots_txt(request):
    content = "User-agent: *\\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")


def deploy_version(request):
    """What commit this process is running. DP-1, 22 Oct 2026.

    Seven characters of hex and a newline. Nothing else - not the
    branch, not the host, not the Django version, not whether DEBUG is
    on. The question this answers is 'has the thing I just pushed
    arrived', and nothing else is needed to answer it.

    WHY THIS EXISTS AT ALL. Push 4 and push 5 both landed into a
    Railway with builds paused, both printed their post-deploy checks,
    and the live site ran 3245f19 for three days. The push script now
    asks this URL until it answers the SHA that was just pushed.

    AND WHY IT IS NOT THE RAILWAY API. That would answer the same
    question and it needs a token - on a laptop, in a script, in a
    repository, a thing that can leak and must be rotated. A site
    answering a public question about itself is none of those.

    WHITELISTED, NOT ESCAPED. The value is an environment variable,
    which is somebody else string. Every character that is not a
    lowercase hex digit is dropped before anything is sent, so the
    worst a hostile value can produce is a shorter string or the word
    unknown. Nothing is interpolated, nothing is trusted.

    unknown MEANS THE BUILD DID NOT SUPPLY A SHA, not that the deploy
    failed. Railway sets RAILWAY_GIT_COMMIT_SHA on its own; a platform
    that does not can set GIT_COMMIT_SHA instead.
    """
    raw = (os.environ.get('RAILWAY_GIT_COMMIT_SHA')
           or os.environ.get('GIT_COMMIT_SHA')
           or '')
    sha = ''.join(c for c in raw.lower() if c in '0123456789abcdef')
    response = HttpResponse((sha[:7] or 'unknown') + "\\n",
                            content_type="text/plain")
    # NOT CACHEABLE, by anything, ever. A cached answer to this
    # question is a wrong answer by definition - it is the one thing
    # on this site guaranteed to change on every deploy.
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response'''

URL_ROUTE_WAS = """    path('robots.txt', robots_txt),"""

URL_ROUTE_NOW = """    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
    # matching line in ModuleAccessMiddleware.EXEMPT_URL_PATTERNS.
    path('version/', deploy_version, name='deploy_version'),"""

URL_IMPORT_WAS = """from django.contrib import admin
from django.urls import path, include, re_path"""

URL_IMPORT_NOW = """import os

from django.contrib import admin
from django.urls import path, include, re_path"""

# ==========================================================================
# THE MIDDLEWARE - one line, with its reason on it
# ==========================================================================
MID_WAS = """            'api/',  # If you have API endpoints
            'media/',  # Media files"""

MID_NOW = """            'api/',  # If you have API endpoints
            # DP-1, 22 Oct 2026 - THE DEPLOY PROBE.
            #
            # /version/ answers seven characters of hex and nothing
            # else, and the push script asks it from a laptop with no
            # session at all. Without this line the middleware would
            # bounce it to the login page and the probe would read a
            # login form as the running version for ever.
            #
            # ON ITS OWN LINE RATHER THAN UNDER 'api/'. That prefix is
            # already exempt and would have carried this for free - but
            # nothing is mounted under api/ anywhere in the tree, so it
            # is dead configuration, and hiding a deliberate public
            # endpoint inside dead configuration is how the reason gets
            # lost. This one says what it is.
            'version/',
            'media/',  # Media files"""

# ==========================================================================
# THE PUSH SCRIPT
# ==========================================================================
PS_PARAM_WAS = """    [switch]$Resume
)"""

PS_PARAM_NOW = """    [switch]$Resume,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT.
    # Push 4 and push 5 both ended by saying Railway would build and
    # deploy, and in both cases it did not. -Site is where to ask,
    # -WaitMinutes is how long to care, -NoWait skips it entirely.
    [string]$Site = 'https://alivente.online',
    [int]$WaitMinutes = 8,
    [switch]$NoWait
)"""

PS_TAIL_WAS = """Write-Host ''
Write-Host 'Railway will build and deploy from this push.' -ForegroundColor Cyan
Write-Host 'Migrations run automatically on deploy; this batch adds none.' -ForegroundColor Cyan
Write-Host ''
if ($Checks.Count -gt 0) {"""

PS_TAIL_NOW = """Write-Host ''
Write-Host 'Railway will build and deploy from this push.' -ForegroundColor Cyan
Write-Host 'Migrations run automatically on deploy; this batch adds none.' -ForegroundColor Cyan

# DP-1, 22 Oct 2026 - AND THEN FIND OUT WHETHER IT DID.
#
# The line above has been printed at the end of every push since this
# script was written, and twice in two days it was not true: Railway
# had builds paused, the push landed, the post-deploy checks printed,
# and the live site went on running 3245f19.
#
# THE SITE ANSWERS THE QUESTION ITSELF. /version/ returns seven
# characters of hex - the commit the running process was built from -
# and this asks it until it answers the SHA just pushed. No token, no
# API, nothing on this laptop to leak.
#
# A TIMEOUT IS NOT A FAILURE. The push is already in; running out of
# patience costs nothing, so this exits 0 either way and says what the
# live site is still running.
$deployed = $false
if (-not $NoWait) {
    Head 'Deploy'
    $sha  = [string](& git rev-parse HEAD)
    $want = $sha.Trim().Substring(0, 7)
    $probe = ($Site.TrimEnd('/') + '/version/')
    Say ('  asking ' + $probe + ' for ' + $want)
    Say ('  up to ' + $WaitMinutes + ' minute(s). Ctrl-C costs nothing - the push is already in.')
    $deadline = (Get-Date).AddMinutes($WaitMinutes)
    $seen = ''
    while ((Get-Date) -lt $deadline) {
        $got = ''
        try {
            $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 -Uri $probe
            $got = ([string]$resp.Content).Trim()
        } catch {
            $got = '(no answer)'
        }
        if ($got -eq $want) { $deployed = $true; break }
        if ($got -ne $seen) {
            $seen = $got
            Say ('  ' + (Get-Date -Format 'HH:mm:ss') + '   live says: ' + $seen)
        }
        Start-Sleep -Seconds 15
    }
    if ($deployed) {
        Good ('DEPLOYED - ' + $Site + ' is running ' + $want)
    } elseif ($seen -eq 'unknown') {
        Warn 'the probe answers, but the build supplied no commit SHA'
        Say  '        Railway normally sets RAILWAY_GIT_COMMIT_SHA on its own.'
        Say  '        Until it does, this cannot tell one deploy from another.'
    } elseif ($seen -eq '(no answer)' -or $seen -eq '') {
        Warn ('no answer from ' + $probe + ' in ' + $WaitMinutes + ' minute(s)')
        Say  '        Either the deploy has not landed yet, or this is the'
        Say  '        first push carrying the probe and the OLD build has no'
        Say  '        /version/ to answer with. Both look the same from here.'
    } else {
        Warn ('not deployed after ' + $WaitMinutes + ' minute(s) - live is still running ' + $seen)
        Say  '        The push is in. Watch Railway, or ask again:'
        Say  ('           (Invoke-WebRequest -UseBasicParsing ' + $probe + ').Content')
    }
}

Write-Host ''
if ($Checks.Count -gt 0) {"""

PS_CHECK_WAS = """    Write-Host 'Worth checking on Live once the deploy is green:' -ForegroundColor Cyan"""

PS_CHECK_NOW = """    if ($deployed) {
        Write-Host 'The deploy is green. Worth checking on Live:' -ForegroundColor Cyan
    } else {
        Write-Host 'Worth checking on Live ONCE THE DEPLOY IS GREEN - it is not yet:' -ForegroundColor Yellow
    }"""

# ==========================================================================
# THE PHOTO COMMAND - absence is not a report
# ==========================================================================
CMD_TRACK_WAS = """            if write:
                recipe.recipe_image_display.save(
                    display_name_for(recipe.recipe_image.name),
                    ContentFile(data), save=False)
                Recipe.objects.filter(pk=recipe.pk).update(
                    recipe_image_display=recipe.recipe_image_display.name)"""

CMD_TRACK_NOW = """            if write:
                recipe.recipe_image_display.save(
                    display_name_for(recipe.recipe_image.name),
                    ContentFile(data), save=False)
                Recipe.objects.filter(pk=recipe.pk).update(
                    recipe_image_display=recipe.recipe_image_display.name)
                # DP-1, 22 Oct 2026 - REMEMBER WHAT WAS CLAIMED, so it
                # can be read back below. The name and the byte count
                # are what this run says it wrote; the database and the
                # volume are asked afterwards whether that is true.
                written.append((recipe.recipe_id, recipe.recipe_name,
                                recipe.recipe_image_display.name,
                                len(data)))"""

CMD_INIT_WAS = """        done = skipped = failed = 0
        before = after = 0
        problems = []"""

CMD_INIT_NOW = """        done = skipped = failed = 0
        before = after = 0
        problems = []
        written = []"""

CMD_SAY_WAS = """        self.stdout.write('')
        if not write:
            self.stdout.write('  DRY RUN. Nothing was written. '
                              'Pass --write to apply.')
        self.stdout.write('')"""

CMD_SAY_NOW = """        self.stdout.write('')
        if not write:
            self.stdout.write('  DRY RUN. Nothing was written. '
                              'Pass --write to apply.')
        else:
            self.report_what_landed(written)
        self.stdout.write('')

    # ----------------------------------------------------------------
    # DP-1, 22 Oct 2026 - ABSENCE IS NOT A REPORT.
    #
    # Demetri ran this with --write on 22 October and got back exactly
    # the table the dry run had printed, with the 'DRY RUN. Nothing was
    # written' line simply gone. Nothing said what had landed, nothing
    # said how big it was, and nothing would have said a word if the
    # save had silently failed.
    #
    # SO THE ROWS ARE READ BACK, not remembered. Each one is fetched
    # fresh from the database and its file measured on the volume. A
    # row whose display copy is not the name this run saved, or whose
    # file is not the size this run encoded, is named rather than
    # counted.
    # ----------------------------------------------------------------
    def report_what_landed(self, written):
        if not written:
            self.stdout.write('  WRITE RUN. Nothing needed writing - '
                              'every display copy was already current.')
            self.stdout.write('  Pass --rebuild to convert them anyway.')
            return

        confirmed = 0
        on_disk = 0
        wrong = []
        for rid, name, stored, claimed in written:
            row = Recipe.objects.filter(pk=rid).first()
            if row is None or row.recipe_image_display.name != stored:
                wrong.append((rid, name, 'the database does not point at '
                                         'the file this run saved'))
                continue
            try:
                size = row.recipe_image_display.size
            except Exception as exc:
                wrong.append((rid, name, 'not readable on the volume - %s'
                              % str(exc).split('\\n')[0][:48]))
                continue
            on_disk += size
            if size != claimed:
                wrong.append((rid, name, 'on disk as %d bytes, encoded as '
                                         '%d' % (size, claimed)))
            else:
                confirmed += 1

        self.stdout.write('  WRITTEN. %d display cop%s read back from the '
                          'database' % (confirmed,
                                        'y' if confirmed == 1 else 'ies'))
        self.stdout.write('           and measured on the volume - '
                          '%.1f MB.' % (on_disk / 1048576.0))
        if wrong:
            self.stdout.write('')
            self.stdout.write('  DID NOT LAND AS CLAIMED - named, not '
                              'swallowed:')
            for rid, name, why in wrong[:20]:
                self.stdout.write('    %-6s %-30s %s'
                                  % (rid, (name or '')[:30], why))"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('DP-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pu = os.path.join(root, URLS)
    u = read(pu)
    if MARK in u:
        print('DP-1  already applied - the site says what it is running.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    u = swap(u, URL_IMPORT_WAS, URL_IMPORT_NOW, '%s (the import)' % URLS)
    u = swap(u, URL_WAS, URL_NOW, '%s (the view)' % URLS)
    u = swap(u, URL_ROUTE_WAS, URL_ROUTE_NOW, '%s (the route)' % URLS)
    out[pu] = u

    pm = os.path.join(root, MID)
    out[pm] = swap(read(pm), MID_WAS, MID_NOW, '%s (the exempt list)' % MID)

    pc = os.path.join(root, CMD)
    c = read(pc)
    c = swap(c, CMD_INIT_WAS, CMD_INIT_NOW, '%s (the tally)' % CMD)
    c = swap(c, CMD_TRACK_WAS, CMD_TRACK_NOW, '%s (what was claimed)' % CMD)
    c = swap(c, CMD_SAY_WAS, CMD_SAY_NOW, '%s (what landed)' % CMD)
    out[pc] = c

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, PS_PARAM_WAS, PS_PARAM_NOW, '%s (the switches)' % PS1)
    s = swap(s, PS_TAIL_WAS, PS_TAIL_NOW, '%s (the wait)' % PS1)
    s = swap(s, PS_CHECK_WAS, PS_CHECK_NOW, '%s (the checks header)' % PS1)
    s = swap(s, """    'test_week_drag.py'
)""", """    'test_week_drag.py',
    # DP-1, 22 Oct 2026 - the site says what commit it is running.
    'test_deploy_probe.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'saveColumnOrder';""",
             """    @{ File = 'mysite/urls.py'; Text = 'def deploy_version'; What = 'DP-1: /version/ answers seven characters of hex - the commit the running process was built from - and this script asks it after a push until it answers the SHA just pushed. No Railway token anywhere' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'saveColumnOrder';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # WD-1, 22 Oct 2026 - the week drags too.
    'test_week_drag.py',
]""", """    # WD-1, 22 Oct 2026 - the week drags too.
    'test_week_drag.py',
    # DP-1, 22 Oct 2026 - and the push finds out whether it deployed.
    'test_deploy_probe.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # WD-1, 22 Oct 2026 - the week columns drag.
    '.bak_weekdrag',
]""", """    # WD-1, 22 Oct 2026 - the week columns drag.
    '.bak_weekdrag',
    # DP-1, 22 Oct 2026 - the site says what it is running.
    '.bak_deployprobe',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # DP-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nu = out[pu]
    code = T.python_code_only(nu, payloads=True)
    # NOTHING BUT HEX LEAVES. The whole point of the endpoint.
    if "if c in '0123456789abcdef'" not in code:
        refuse('%s: the version value is not whitelisted, and it comes '
               'from the environment' % URLS)
    # SLICED TO THE NEXT TOP-LEVEL def, not to a run of blank lines.
    # python_code_only blanks docstrings, so the function is full of
    # blank lines and the first draft of this slice ran straight on
    # into cached_media - which names settings.MEDIA_ROOT, and the gate
    # refused the round for a leak in somebody else's function.
    body = code[code.index('def deploy_version'):]
    nxt = re.search(r'\ndef \w+', body[1:])
    body = body[:nxt.start() + 1] if nxt else body
    for leak in ('DEBUG', 'SECRET', 'DATABASES', 'ALLOWED_HOSTS',
                 'settings.', 'request.META', 'platform', 'socket'):
        if leak in body:
            refuse('%s: deploy_version names %r, and it answers an '
                   'unauthenticated caller - seven characters of hex is '
                   'the whole budget' % (URLS, leak))
    if 'no-store' not in body:
        refuse('%s: the version answer is cacheable, and a cached answer '
               'to this question is wrong by definition' % URLS)
    if '[:7]' not in body:
        refuse('%s: the answer is not cut to a short SHA' % URLS)

    nm = out[pm]
    if "'version/'," not in nm:
        refuse('%s: /version/ is not exempt, so the probe would read the '
               'login page as the running version for ever' % MID)

    ns = out[pp]
    if '/version/' not in ns:
        refuse('%s: the push script does not ask the probe' % PS1)
    if 'git rev-parse HEAD' not in ns:
        refuse('%s: the wait has nothing to compare against' % PS1)
    # NO TOKEN. Not in the script, not in a variable, not in a comment
    # that somebody later fills in.
    for word in ('RAILWAY_TOKEN', 'RAILWAY_API', 'Authorization',
                 'Bearer ', 'api.railway'):
        if word in ns:
            refuse('%s: names %r - this round exists precisely so that '
                   'no credential is needed to answer this question'
                   % (PS1, word))
    if '$deployed' not in ns:
        refuse('%s: the post-deploy checks still print as though the '
               'deploy had happened' % PS1)

    nc = out[pc]
    if 'def report_what_landed' not in nc:
        refuse('%s: the write path still says nothing' % CMD)
    if 'recipe_image_display.size' not in nc:
        refuse('%s: it reports what it remembered rather than what is on '
               'the volume' % CMD)

    if CHECK:
        print('DP-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        a public endpoint answering seven hex characters, '
              'and no token anywhere')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('DP-1  applied - the push finds out whether it deployed.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
