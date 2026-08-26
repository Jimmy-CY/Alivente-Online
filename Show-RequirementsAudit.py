"""Show-RequirementsAudit - four requirements files. Which one matters, and
what is actually in use?

    python Show-RequirementsAudit.py

READ-ONLY. Writes nothing. Run it from the project root, inside the venv you
actually use, because half the answer comes from the installed metadata in
that environment rather than from the text files.

WHAT IT ANSWERS
---------------
1. WHICH FILE DEPLOYS. Parses railway.json, the Dockerfile and any Procfile to
   find the install command that actually runs. Three of the four files may be
   decoration; this says which.

2. WHERE THEY DIFFER. All four are near-copies. It prints the packages that
   are not in all of them, so drift is visible rather than assumed.

3. WHAT IS ACTUALLY IMPORTED, and by whom. Every .py in the project is scanned
   for imports, split into:
       APP      - pages/, mysite/, crs/, manage.py: runs on the server
       TOOLING  - the apply_*/test_*/Show-* scripts in the root: never deployed
   That distinction is the whole question for a package like beautifulsoup4 -
   if only TOOLING imports it, it does not belong in a deployed file.

4. WHAT IS UNUSED. A requirement that is neither imported directly nor pulled
   in as a dependency of something that is, is a candidate for removal. It is
   a CANDIDATE, not a verdict - see the caveats.

CAVEATS, HONESTLY
-----------------
Static import scanning cannot see:
  - packages loaded by name at runtime (Django DB backends are the big one:
    nothing imports `mysqlclient`, settings.py names it as a string)
  - Django apps listed in INSTALLED_APPS
  - build-only or CLI-only tools (gunicorn is invoked, never imported)
  - plugins that register themselves on install
So anything flagged UNUSED needs a human look. The script marks the known
runtime-named ones rather than pretending they are orphans.
"""

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

WHY = None
if '--why' in sys.argv:
    i = sys.argv.index('--why')
    if i + 1 < len(sys.argv):
        WHY = sys.argv[i + 1]

# --------------------------------------------------------------- helpers
def norm(name):
    """PEP 503 normalisation: case, and - _ . are all the same character."""
    return re.sub(r'[-_.]+', '-', name).strip().lower()


def load_req(path):
    raw = open(path, 'rb').read()
    enc = None
    for e in ('utf-16', 'utf-8-sig', 'utf-8', 'latin-1'):
        try:
            text = raw.decode(e)
            # utf-16 will "succeed" on some utf-8 files and produce CJK soup;
            # a sane requirements file is nearly all ASCII.
            printable = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
            if printable > 0.9:
                enc = e
                break
        except Exception:
            continue
    if enc is None:
        return 'unknown', []
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        out.append(line)
    return enc, out


def req_name(spec):
    return norm(re.split(r'[<>=!~\[; ]', spec, 1)[0])


APP_DIRS = ('pages', 'mysite', 'crs')
SKIP_DIRS = {'code', 'venv', 'env', 'staticfiles', '__pycache__', '.git',
             'media', 'node_modules', 'cron-service'}


def walk_py():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = os.path.relpath(dirpath, ROOT).replace('\\', '/')
        for f in filenames:
            if not f.endswith('.py') or '.bak' in f:
                continue
            top = rel_dir.split('/')[0]
            is_app = (top in APP_DIRS) or (rel_dir == '.' and f == 'manage.py')
            yield os.path.join(dirpath, f), is_app


# ================================================================= --why mode
if WHY:
    want = {norm(WHY), norm(WHY).replace('-', '_')}
    print('')
    print('=' * 74)
    print(' Who imports %s, and is the import guarded?' % WHY)
    print('=' * 74)
    hits = 0
    for path, is_app in walk_py():
        try:
            src = open(path, encoding='utf-8-sig', errors='replace').read()
            tree = ast.parse(src)
        except Exception:
            continue
        lines = src.splitlines()

        # Record every try: block's line span, so an import inside one can be
        # reported as OPTIONAL rather than as a hard dependency. A guarded
        # import degrades a feature; an unguarded one takes the page down.
        # An `except Exception:` DOES catch ImportError - it is a subclass -
        # so matching on the literal word "ImportError" under-reports guards
        # and cries wolf about code that is deliberately optional. Resolve the
        # handler to actual names and check the inheritance chain instead.
        CATCHES_IMPORT = {'ImportError', 'ModuleNotFoundError', 'Exception',
                          'BaseException', 'OSError'}

        def handler_names(h):
            if h.type is None:            # bare `except:` catches everything
                return {'BaseException'}
            nodes = (h.type.elts if isinstance(h.type, ast.Tuple)
                     else [h.type])
            out = set()
            for n in nodes:
                if isinstance(n, ast.Name):
                    out.add(n.id)
                elif isinstance(n, ast.Attribute):
                    out.add(n.attr)
            return out

        guards = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                caught = set()
                for h in node.handlers:
                    caught |= handler_names(h)
                guards.append((node.lineno,
                               getattr(node, 'end_lineno', node.lineno),
                               bool(caught & CATCHES_IMPORT),
                               ', '.join(sorted(caught)) or 'bare except'))

        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split('.')[0]]
            if not any(norm(m) in want for m in mods):
                continue
            hits += 1
            ln = node.lineno
            guard = next((g for g in guards if g[0] <= ln <= g[1]), None)
            if guard and guard[2]:
                state = ('OPTIONAL - guarded by `except %s`, so a missing '
                         'package degrades the feature rather than breaking '
                         'the page' % guard[3])
            elif guard:
                state = ('inside a try that catches %s - which does NOT cover '
                         'ImportError' % guard[3])
            else:
                state = 'REQUIRED - unguarded; ImportError takes the page down'
            print('')
            print('  %s:%d   [%s]'
                  % (os.path.relpath(path, ROOT), ln,
                     'APP - deploys' if is_app else 'tooling - local only'))
            print('     %s' % lines[ln - 1].strip()[:78])
            print('     -> %s' % state)
    print('')
    print('  %d import site(s) found.' % hits)
    if not hits:
        print('  Nothing imports it. If it is in requirements, it is either a')
        print('  transitive dependency or dead weight.')
    print('')
    sys.exit(0)


# ============================================================ 1. WHAT DEPLOYS
print('')
print('=' * 74)
print(' 1. Which file does the deploy actually install?')
print('=' * 74)

installs = []
rj = os.path.join(ROOT, 'railway.json')
if os.path.exists(rj):
    try:
        j = json.load(open(rj, encoding='utf-8-sig'))
        cmd = (j.get('build') or {}).get('installCommand')
        if cmd:
            installs.append(('railway.json  installCommand', cmd))
        for c in (j.get('crons') or []):
            installs.append(('railway.json  cron: %s' % c.get('name', '?'),
                             c.get('command', '')))
    except Exception as e:
        print('  ! railway.json did not parse: %s' % e)

for f in ('Dockerfile',):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        for line in open(p, encoding='utf-8-sig', errors='replace'):
            if 'pip install' in line:
                installs.append((f, line.strip()))

for p in (os.path.join(ROOT, 'Procfile'),
          os.path.join(ROOT, 'mysite', 'Procfile')):
    if os.path.exists(p):
        installs.append((os.path.relpath(p, ROOT),
                         open(p, encoding='utf-8-sig',
                              errors='replace').read().strip()))

for where, cmd in installs:
    print('  %-34s %s' % (where, cmd[:80]))

deployed = set()
for _, cmd in installs:
    for m in re.finditer(r'-r\s+([^\s"\']+)', cmd):
        deployed.add(m.group(1).replace('\\', '/'))
print('')
if deployed:
    print('  => INSTALLED ON DEPLOY: %s' % ', '.join(sorted(deployed)))
else:
    print('  => no explicit -r found; the platform may be auto-detecting.')

# ========================================================= 2. THE FOUR FILES
print('')
print('=' * 74)
print(' 2. The requirements files, and how they differ')
print('=' * 74)

CANDIDATES = ['requirements.txt', 'cron-requirements.txt',
              'requirements-dev.txt',
              os.path.join('mysite', 'requirements.txt'),
              os.path.join('mysite', 'cron-requirements.txt')]

files = {}
for rel in CANDIDATES:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        continue
    enc, specs = load_req(p)
    files[rel.replace('\\', '/')] = (enc, specs)

print('  %-32s %-10s %5s  %s' % ('FILE', 'ENCODING', 'PKGS', 'deployed?'))
print('  ' + '-' * 68)
for rel, (enc, specs) in files.items():
    mark = 'YES  <-- this one' if rel in deployed else 'no'
    print('  %-32s %-10s %5d  %s' % (rel, enc, len(specs), mark))

# treat requirements-dev.txt separately - it is meant to differ
core = {k: v for k, v in files.items() if 'dev' not in k}
sets = {k: {req_name(s) for s in v[1]} for k, v in core.items()}
if len(sets) > 1:
    everywhere = set.intersection(*sets.values())
    anywhere = set.union(*sets.values())
    drift = sorted(anywhere - everywhere)
    print('')
    print('  %d package(s) common to all %d core files, %d that differ:'
          % (len(everywhere), len(sets), len(drift)))
    keys = list(sets)
    for d in drift:
        print('     %-34s %s' % (d, ' '.join(
            ('X' if d in sets[k] else '.') for k in keys)))
    print('     %-34s %s' % ('', ' '.join(str(i + 1) for i in range(len(keys)))))
    for i, k in enumerate(keys):
        print('       %d = %s' % (i + 1, k))

    # Same package, different PIN. More dangerous than a missing package,
    # because nothing looks wrong: the file you edit and the file that
    # deploys both list it, at versions years apart.
    specs_by = {k: {req_name(s): s for s in v[1]} for k, v in core.items()}
    pinned_drift = []
    for pkg in sorted(everywhere):
        vals = {k: specs_by[k].get(pkg, '') for k in keys}
        if len(set(vals.values())) > 1:
            pinned_drift.append((pkg, vals))
    print('')
    if pinned_drift:
        print('  !! %d package(s) present in every file at DIFFERENT versions:'
              % len(pinned_drift))
        for pkg, vals in pinned_drift:
            print('     %s' % pkg)
            for k in keys:
                tag = '  <-- deploys' if k in deployed else ''
                print('        %-34s %s%s' % (vals[k], k, tag))
    else:
        print('  Every shared package is pinned identically across the files.')

# ==================================================== 3. WHAT IS IMPORTED
print('')
print('=' * 74)
print(' 3. What the code actually imports')
print('=' * 74)

app_imports, tool_imports = set(), set()
app_files = tool_files = 0

for path, is_app in walk_py():
    try:
        tree = ast.parse(open(path, encoding='utf-8-sig',
                              errors='replace').read())
    except Exception:
        continue
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(node.module.split('.')[0])
    if is_app:
        app_imports |= mods
        app_files += 1
    else:
        tool_imports |= mods
        tool_files += 1

print('  scanned %d app file(s) and %d tooling file(s)'
      % (app_files, tool_files))

# --------------------------------------------- map import name -> distribution
dist_of = {}
try:
    from importlib.metadata import packages_distributions, requires, distributions
    pd = packages_distributions()
    for mod, dists in pd.items():
        for d in dists:
            dist_of.setdefault(mod, set()).add(norm(d))
    META = True
except Exception as e:
    print('  ! installed metadata unavailable (%s) - name mapping will be'
          ' approximate' % type(e).__name__)
    META = False


def to_dists(mods):
    out = set()
    for m in mods:
        if m in dist_of:
            out |= dist_of[m]
        else:
            out.add(norm(m))          # best guess: import name == dist name
    return out


app_dists = to_dists(app_imports)
tool_dists = to_dists(tool_imports)

# ------------------------------------------------------ transitive closure
def closure(roots):
    seen, stack = set(), list(roots)
    while stack:
        d = stack.pop()
        if d in seen:
            continue
        seen.add(d)
        if not META:
            continue
        try:
            reqs = requires(d) or []
        except Exception:
            continue
        for r in reqs:
            # skip optional extras: 'pytest; extra == "test"'
            if ';' in r and 'extra' in r.split(';', 1)[1]:
                continue
            stack.append(req_name(r))
    return seen


app_closed = closure(app_dists)

# =============================================== 4. CLASSIFY THE DEPLOYED FILE
target = sorted(deployed)[0] if deployed else None
if target and target in files:
    print('')
    print('=' * 74)
    print(' 4. %s - what is each line for?' % target)
    print('=' * 74)

    # Django and friends are named as STRINGS in settings, never imported.
    RUNTIME_NAMED = {
        'gunicorn': 'invoked by Procfile, never imported',
        'mysqlclient': 'Django DB backend, named in settings as a string',
        'mysql-connector': 'legacy DB driver, python-2 era',
        'mysql-connector-python': 'DB driver, may be named in settings',
        'pymysql': 'DB driver, usually install_as_MySQLdb() in __init__',
        'whitenoise': 'middleware, named in settings as a string',
        'psycopg2-binary': 'DB driver, named in settings',
        'setuptools': 'build tooling',
        'wheel': 'build tooling',
        'pip': 'build tooling',
    }

    direct, transitive, tooling_only, unknown = [], [], [], []
    for spec in files[target][1]:
        n = req_name(spec)
        if n in app_dists:
            direct.append((spec, ''))
        elif n in RUNTIME_NAMED:
            direct.append((spec, RUNTIME_NAMED[n]))
        elif n in app_closed:
            transitive.append(spec)
        elif n in tool_dists:
            tooling_only.append(spec)
        else:
            unknown.append(spec)

    def block(title, items, note=''):
        print('')
        print('  %s  (%d)' % (title, len(items)))
        if note:
            print('  %s' % note)
        for it in items:
            if isinstance(it, tuple):
                print('     %-34s %s' % (it[0], it[1]))
            else:
                print('     %s' % it)

    block('IMPORTED BY THE APP, or named at runtime', direct)
    block('PULLED IN as a dependency of the above', transitive,
          '(remove only the top-level ones; pip resolves these)')
    block('USED ONLY BY TOOLING - never runs on the server', tooling_only,
          '(candidates for requirements-dev.txt instead)')
    block('NO EVIDENCE OF USE - look before removing', unknown,
          '(static scanning misses runtime-named packages; see caveats)')

    # ---- and the reverse: imported but NOT declared
    declared = {req_name(s) for s in files[target][1]}
    # Normalised stdlib names, because norm() turns __future__ into -future-
    STDLIB = {norm(m) for m in getattr(sys, 'stdlib_module_names', ())}
    # Modules that are just .py files sitting in the project root - fsr.py,
    # issues.py, print_tenant.py and friends. They are local code, not
    # packages, and reporting them as undeclared dependencies is noise.
    LOCAL = {norm(f[:-3]) for f in os.listdir(ROOT) if f.endswith('.py')}
    LOCAL |= {norm(d) for d in os.listdir(ROOT)
              if os.path.isdir(os.path.join(ROOT, d))}

    missing = sorted(d for d in app_dists
                     if d not in declared and d not in STDLIB
                     and d not in LOCAL)
    print('')
    print('  IMPORTED BY THE APP BUT NOT DECLARED  (%d)' % len(missing))
    print('  (installed in your venv, so it works here; absent on a clean'
          ' build)')
    for m in missing:
        print('     %-28s   python Show-RequirementsAudit.py --why %s'
              % (m, m))
    if not missing:
        print('     (none)')

print('')
print('=' * 74)
print('  Read-only. Nothing was written.')
print('=' * 74)
