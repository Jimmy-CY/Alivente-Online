# -*- coding: utf-8 -*-
"""pages/activity.py - RA15, 23 Nov 2026. Who used Alivente, how and when.

Demetri, 23 Nov: "I want the sign-ins information. I want the changes to
the business records. I also want the Pages visited and time spent. For
the personal, I want to be able to see which modules/areas are used the
most ... I don't want access to the information they are saving in the
Personal side." - broken into the menu's own modules; kept 12 months; a
notice line; an email after 5 wrong passwords in a row; viewed by calendar
month, the last 30 days or the last 12 months.

Three records, all for a superuser only (User Administration > Activity):

  ActivityHit   a page opened: who, when, which module - and the page
                only in the business areas. In Personal (Passports,
                Travel, Recipes, Celebrations, Wellness, Household
                Members, CRS Reporting) the page is never kept: the
                module and the time, nothing else.
  SignIn        signed in, signed out, a wrong password: who, when, the
                device and the IP address.
  RecordChange  a business record added, changed or deleted: by whom,
                and the fields that changed, old and new. Nothing from
                Personal is ever watched; account numbers, ID numbers
                and the like say only "changed".

Time spent is worked out from the pages: a visit lasts until the next
page, at most 30 minutes; the last page of a sitting counts a minute.
Everything older than 12 months is deleted once a day.
"""
import contextvars
import datetime as dt
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)
KEEP_DAYS = 366
IDLE = dt.timedelta(minutes=30)     # a sitting ends after this long idle
LAST = dt.timedelta(minutes=1)      # the last page of a sitting
FAILS = 5                           # wrong passwords in a row: an email
_who = contextvars.ContextVar('alv_activity_user', default=None)

# ------------------------------------------------------------ the modules
AREAS = [('ops', 'Property Operations'), ('fin', 'Financial Management'),
         ('admin', 'Administration'), ('personal', 'Personal')]
# (key, label, area, sub-heading, URL prefixes). The longest prefix that
# matches wins (tenant_lease_agreement is Leases, not Tenants). A prefix
# matches the path itself or the path followed by '/' or '_' (as
# ModuleAccessMiddleware does).
MODULES = [
    # ---- Administration (before Tenants and Properties: narrower)
    ('signing', 'Manage Lease Signing', 'admin', 'Functional',
     ['lease-signing', 'tenant-lease-signing']),
    ('leases', 'Manage Lease Agreements', 'admin', 'Functional',
     ['tenant_lease_agreement', 'lease_agreements', 'upload_lease_agreement',
      'lease']),
    ('generate', 'Generate Lease Agreement', 'admin', 'Functional',
     ['generate-lease-agreement', 'get-property-tenant-data']),
    ('deeds', 'Manage Title Deeds', 'admin', 'Functional',
     ['title_deeds_management', 'title_deeds', 'upload_title_deed']),
    ('users', 'User Administration', 'admin', 'System',
     ['user-administration', 'workspace-management', 'setup-permissions']),
    ('menu', 'Menu Preference', 'admin', 'System', ['my-profile']),
    ('marks', 'Signature and Stamp', 'admin', 'System',
     ['administration/signature-and-stamp']),
    ('company', 'Company Details', 'admin', 'System',
     ['administration/company-details']),
    ('notifications', 'Notifications', 'admin', 'System',
     ['notifications']),
    # ---- Personal (usage only)
    ('household', 'Household Members', 'personal', 'Personal',
     ['personal/household-members']),
    ('passports', 'Passports / Documents', 'personal', 'Personal',
     ['passport-management']),
    ('travel', 'Travel', 'personal', 'Personal', ['travel']),
    ('recipes', 'Recipes', 'personal', 'Personal',
     ['recipe_management', 'recipes', 'recipe', 'view_recipe',
      'create_recipe', 'import_recipe', 'preview_imported_recipe',
      'meal_plans', 'unit_conversions', 'ingredient_base_units',
      'categories-management', 'measurement-units-management',
      'spell-check-instructions']),
    ('celebrations', 'Celebrations', 'personal', 'Personal',
     ['celebrations']),
    ('wellness', 'Wellness', 'personal', 'Personal', ['wellness']),
    ('crs', 'CRS Reporting', 'personal', 'Compliance', ['crs']),
    # ---- Property Operations
    ('properties', 'Properties', 'ops', '',
     ['properties', 'property', 'prop_rep', 'property_report', 'assets',
      'maintenance', 'ajax/category', 'ajax/subcategory']),
    ('tenants', 'Tenants', 'ops', '',
     ['tenant', 'tenant-payment-days', 'lease-timeline',
      'lease_renewal_report']),
    ('suppliers', 'Suppliers', 'ops', '',
     ['suppliers', 'supplier_report', 'ajax/supplier']),
    ('issues', 'Issues', 'ops', '',
     ['fsr', 'issues', 'issue-details', 'issues-analysis-data',
      'friday_status_report', 'resolved_issues_report', 'comments-report',
      'delete-comment']),
    ('projects', 'Projects', 'ops', '',
     ['projects', 'ajax/projects', 'ajax/tasks', 'translate']),
    ('dashboard', 'Dashboard', 'ops', '',
     ['property_management_dashboard', 'property_detail']),
    # ---- Financial Management
    ('invoices', 'Invoices', 'fin', '',
     ['invoices', 'physical-invoices', 'invoice-customers',
      'open_invoices_report']),
    ('receipts', 'Receipts', 'fin', '', ['receipts']),
    ('expenses', 'Expenses', 'fin', '',
     ['act_expense', 'mark_approved', 'mark_paid', 'mark_deleted']),
    ('petty_cash', 'Petty Cash', 'fin', '', ['petty_cash']),
    ('financials', 'Financials', 'fin', '',
     ['finance', 'dashboard_pl', 'occupancy-trends', 'vacancy-management',
      'forecast', 'revenue-details', 'budget-expense-details',
      'total-expense-details', 'financial-indicators']),
]
BY_KEY = {m[0]: m for m in MODULES}
PERSONAL = {m[0] for m in MODULES if m[2] == 'personal'}
# Never a page visit: the doors, the app shells, the files.
SKIP = ('static/', 'media/', 'alv-css/', 'admin/', 'login', 'logout',
        'version', 'sign/', 'forgot-password', 'set-password', 'accounts/',
        'travel/app/', 'wellness/app/', 'travel/inbound', 'favicon',
        'robots.txt', 'passkeys', 'webauthn')


def module_of(path):
    """The module key for a path ('' when none: home, Help, landings)."""
    p = (path or '').lstrip('/').rstrip('/')
    best, size = '', 0
    for key, _l, _a, _s, prefixes in MODULES:
        for x in prefixes:
            if len(x) > size and (p == x or p.startswith(x + '/') or
                                  p.startswith(x + '_')):
                best, size = key, len(x)
    return best


def label(key):
    m = BY_KEY.get(key)
    return m[1] if m else 'Home and Help'


def is_personal(key):
    return key in PERSONAL


# --------------------------------------------------------------- recording
def current_user_id():
    return _who.get()


def device_of(ua):
    ua = ua or ''
    kind = 'Phone' if any(w in ua for w in ('iPhone', 'Android', 'Mobile')) \
        else 'Tablet' if 'iPad' in ua else 'Computer'
    for name, mark in (('Edge', 'Edg/'), ('Samsung', 'SamsungBrowser'),
                       ('Chrome', 'Chrome/'), ('Firefox', 'Firefox/'),
                       ('Safari', 'Safari/')):
        if mark in ua:
            return '%s · %s' % (kind, name)
    return kind


def ip_of(request):
    fwd = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0]
    return (fwd.strip() or request.META.get('REMOTE_ADDR') or '')[:45]


_purged = {'day': None}


def purge(today=None):
    """Older than 12 months: gone. Once a day a process - from the key
    watcher (pages/key_health.py), never inside a page."""
    from .models import ActivityHit, RecordChange, SignIn
    today = today or timezone.localdate()
    if _purged['day'] == today:
        return
    _purged['day'] = today
    cut = timezone.now() - dt.timedelta(days=KEEP_DAYS)
    try:
        ActivityHit.objects.filter(at__lt=cut).delete()
        SignIn.objects.filter(at__lt=cut).delete()
        RecordChange.objects.filter(at__lt=cut).delete()
    except Exception:                                   # noqa: BLE001
        logger.exception('activity purge')


class ActivityMiddleware:
    """After the login: who is asking (for the change log) and, for a
    page actually shown, a visit."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        uid = user.pk if user is not None and user.is_authenticated else None
        tok = _who.set(uid)
        try:
            response = self.get_response(request)
        finally:
            _who.reset(tok)
        if uid:
            try:
                self.hit(request, response, uid)
            except Exception:                           # noqa: BLE001
                logger.exception('activity hit')
        return response

    @staticmethod
    def hit(request, response, uid):
        if request.method != 'GET' or response.status_code != 200:
            return
        if 'text/html' not in (response.get('Content-Type') or ''):
            return
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return
        if (request.headers.get('sec-fetch-dest') or 'document') not in (
                'document', 'iframe'):
            return
        path = request.path_info.lstrip('/')
        if any(path.startswith(s) for s in SKIP):
            return
        from .models import ActivityHit
        key = module_of(path)
        now = timezone.now()
        ActivityHit.objects.create(
            user_id=uid, at=now, day=timezone.localdate(now), module=key,
            # In Personal the page is never kept - the module only.
            path='' if is_personal(key) else ('/' + path)[:200])


# ------------------------------------------------------------- sign-ins
def signed_in(sender, request, user, **kw):
    _sign(request, user, user.username, 'in')


def signed_out(sender, request, user, **kw):
    if user is not None:
        _sign(request, user, user.username, 'out')


def sign_failed(sender, credentials, request=None, **kw):
    name = str((credentials or {}).get('username') or '')[:150]
    from django.contrib.auth.models import User
    u = User.objects.filter(username__iexact=name).first() if name else None
    row = _sign(request, u, name, 'failed')
    if row is not None:
        try:
            alert(row)
        except Exception:                               # noqa: BLE001
            logger.exception('activity alert')


def _sign(request, user, name, kind):
    from .models import SignIn
    try:
        ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
        return SignIn.objects.create(
            at=timezone.now(), user=user, username=(name or '')[:150],
            kind=kind, ip=ip_of(request) if request else '',
            device=device_of(ua)[:60])
    except Exception:                                   # noqa: BLE001
        logger.exception('activity sign-in')
        return None


def in_a_row(name):
    """Wrong passwords for this name since its last good sign-in."""
    from .models import SignIn
    last = SignIn.objects.filter(username__iexact=name, kind='in') \
        .order_by('-at').values_list('at', flat=True).first()
    qs = SignIn.objects.filter(username__iexact=name, kind='failed')
    if last:
        qs = qs.filter(at__gt=last)
    return qs.count()


def alert(row, send=None):
    """The 5th wrong password in a row for a name: one email. True if
    sent."""
    if not row.username or in_a_row(row.username) != FAILS:
        return False
    from django.core.mail import EmailMessage
    from . import key_health
    to = key_health.recipient()
    if not to:
        return False
    t = timezone.localtime(row.at)
    who = row.user.get_full_name() if row.user_id else ''
    body = [
        'Someone has typed the wrong password %d times in a row for the '
        'Alivente Online sign-in "%s"%s.' % (
            FAILS, row.username, ' (%s)' % who if who else ''),
        '',
        'Last try: %s %d %s at %s, from %s (IP %s).' % (
            t.strftime('%a'), t.day, t.strftime('%b'), t.strftime('%H:%M'),
            row.device or 'an unknown device', row.ip or 'unknown'),
        '',
        'If it was not one of you, change that password (User '
        'Administration > the key button) and look at Activity > Sign-ins.',
        '', 'Alivente Online']
    msg = EmailMessage(subject='Alivente Online - %d wrong passwords for %s'
                       % (FAILS, row.username), body='\n'.join(body),
                       to=[to])
    (send or (lambda m: m.send(fail_silently=False)))(msg)
    return True


# ------------------------------------------------------ business records
# (app label, model, module key, what it is called)
WATCHED = [
    ('pages', 'props', 'properties', 'Property'),
    ('pages', 'PropertyAsset', 'properties', 'Asset'),
    ('pages', 'AssetMaintenance', 'properties', 'Maintenance'),
    ('pages', 'tenant', 'tenants', 'Tenant'),
    ('pages', 'supplier', 'suppliers', 'Supplier'),
    ('pages', 'issues', 'issues', 'Issue'),
    ('pages', 'Project', 'projects', 'Project'),
    ('pages', 'ProjectTask', 'projects', 'Task'),
    ('pages', 'invoices', 'invoices', 'Invoice'),
    ('pages', 'InvoiceCustomer', 'invoices', 'Invoice customer'),
    ('pages', 'PhysicalInvoice', 'invoices', 'Invoice'),
    ('pages', 'CashReceipt', 'receipts', 'Receipt'),
    ('pages', 'act_expense', 'expenses', 'Expense'),
    ('pages', 'petty', 'petty_cash', 'Petty cash'),
    ('pages', 'revenue', 'financials', 'Revenue'),
    ('pages', 'expense', 'financials', 'Budget expense'),
    ('pages', 'prop_values', 'financials', 'Valuation'),
    ('pages', 'LeaseSigning', 'signing', 'Lease signing'),
    ('pages', 'GeneratedLease', 'generate', 'Generated lease'),
    ('pages', 'CompanyDetails', 'company', 'Company details'),
    ('pages', 'HouseMark', 'marks', 'Signature or stamp'),
    ('pages', 'Workspace', 'users', 'Workspace'),
    ('auth', 'User', 'users', 'User'),
]
# Never the value - only that it changed.
SECRET = ('password', 'iban', 'account', 'passport', 'id_number', 'idno',
          'id_no', 'identity', 'tax', 'tic', 'arc', 'card', 'pin', 'token',
          'secret', 'swift', 'bic', 'signature', 'image', 'stamp', 'key')
NOT_SHOWN = {'last_login', 'updated_at', 'modified', 'date_modified',
             'last_updated', 'modified_at', 'updated'}


def _fields(obj):
    for f in obj._meta.concrete_fields:
        if f.primary_key or f.name in NOT_SHOWN or \
                getattr(f, 'auto_now', False):
            continue
        yield f


def _val(obj, f):
    try:
        v = getattr(obj, f.attname)
    except Exception:                                   # noqa: BLE001
        return ''
    if v is None or v == '':
        return ''
    if hasattr(v, 'name') and f.get_internal_type() in ('FileField',
                                                          'ImageField'):
        return (v.name or '').rsplit('/', 1)[-1]
    if isinstance(v, (bytes, bytearray, memoryview)):
        return '(file)'
    s = str(v)
    return s if len(s) <= 120 else s[:117] + '...'


def _secret(f):
    n = f.name.lower()
    return any(w in n for w in SECRET)


def _before(sender, instance, raw=False, **kw):
    if raw or not instance.pk:
        instance._alv_before = None
        return
    try:
        old = sender._base_manager.filter(pk=instance.pk).first()
    except Exception:                                   # noqa: BLE001
        old = None
    instance._alv_before = {f.name: _val(old, f) for f in _fields(old)} \
        if old is not None else None


def _after(sender, instance, created, raw=False, module='', what='', **kw):
    if raw:
        return
    before = getattr(instance, '_alv_before', None)
    changes = []
    if created or before is None:
        action = 'added'
    else:
        action = 'changed'
        for f in _fields(instance):
            a, b = before.get(f.name, ''), _val(instance, f)
            if a != b:
                name = str(f.verbose_name or f.name)
                changes.append([name[:1].upper() + name[1:]] + (
                    ['', ''] if _secret(f) else [a, b]))
        if not changes:
            return
    _log(instance, module, what, action, changes)


def _deleted(sender, instance, module='', what='', **kw):
    _log(instance, module, what, 'deleted', [])


def _log(instance, module, what, action, changes):
    from .models import RecordChange
    try:
        name = str(instance)
    except Exception:                                   # noqa: BLE001
        name = '#%s' % instance.pk
    try:
        RecordChange.objects.create(
            at=timezone.now(), user_id=_who.get(), module=module,
            what=what[:40], object_id=str(instance.pk or '')[:40],
            name=name[:200], action=action, changes=changes[:40])
    except Exception:                                   # noqa: BLE001
        logger.exception('activity change')


def _receivers(module, what):
    """Named functions, not functools.partial: a receiver row is read by
    other suites (test_project_rollup) that call anything without a
    __name__ as a weak reference."""
    def after_save(sender, instance, created=False, raw=False, **kw):
        _after(sender, instance, created, raw=raw, module=module, what=what)

    def after_delete(sender, instance, **kw):
        _deleted(sender, instance, module=module, what=what)
    return after_save, after_delete


def connect():
    """Wire the sign-ins and the watched records (pages/apps.py)."""
    from django.apps import apps
    from django.contrib.auth import signals as auth
    from django.db.models import signals
    auth.user_logged_in.connect(signed_in, dispatch_uid='alv_act_in')
    auth.user_logged_out.connect(signed_out, dispatch_uid='alv_act_out')
    auth.user_login_failed.connect(sign_failed, dispatch_uid='alv_act_fail')
    for app, model, module, what in WATCHED:
        try:
            m = apps.get_model(app, model)
        except LookupError:
            continue
        uid = 'alv_act_%s_%s' % (app, model)
        after_save, after_delete = _receivers(module, what)
        signals.pre_save.connect(_before, sender=m, weak=False,
                                 dispatch_uid=uid + '_pre')
        signals.post_save.connect(after_save, sender=m, weak=False,
                                  dispatch_uid=uid + '_post')
        signals.post_delete.connect(after_delete, sender=m, weak=False,
                                    dispatch_uid=uid + '_del')


# --------------------------------------------------------------- looking
def period(p='', month='', today=None):
    """(start, end, words, key): a calendar month (month='2026-11'), the
    last 30 days (p='30') or the last 12 months (p='12')."""
    today = today or timezone.localdate()
    if p == '30':
        return today - dt.timedelta(days=29), today, 'Last 30 days', '30'
    if p == '12':
        start = (today.replace(day=1) - dt.timedelta(days=330)).replace(day=1)
        return start, today, 'Last 12 months', '12'
    try:
        y, m = (int(x) for x in (month or '').split('-'))
        first = dt.date(y, m, 1)
    except (ValueError, TypeError):
        first = today.replace(day=1)
    nxt = (first + dt.timedelta(days=32)).replace(day=1)
    return (first, min(nxt - dt.timedelta(days=1), today) if first <= today
            else nxt - dt.timedelta(days=1), first.strftime('%B %Y'),
            first.strftime('%Y-%m'))


def months(today=None, n=12):
    today = today or timezone.localdate()
    out, d = [], today.replace(day=1)
    for _ in range(n):
        out.append((d.strftime('%Y-%m'), d.strftime('%B %Y')))
        d = (d - dt.timedelta(days=1)).replace(day=1)
    return out


def sittings(hits):
    """Hits of one person, oldest first -> sittings: [{start, end, hits}],
    each hit given .spent (a timedelta)."""
    out, cur = [], None
    for i, h in enumerate(hits):
        nxt = hits[i + 1] if i + 1 < len(hits) else None
        gap = (nxt.at - h.at) if nxt is not None else None
        h.spent = gap if gap is not None and gap <= IDLE else LAST
        if cur is None or h.at - cur['end'] > IDLE:
            cur = {'start': h.at, 'end': h.at, 'hits': []}
            out.append(cur)
        cur['hits'].append(h)
        cur['end'] = h.at
    for s in out:
        s['spent'] = sum((h.spent for h in s['hits']), dt.timedelta())
    return out


def words(td):
    m = int(round(td.total_seconds() / 60))
    if m < 1:
        return '<1m'
    if m < 60:
        return '%dm' % m
    h, m = divmod(m, 60)
    return '%dh' % h if not m or h >= 10 else '%dh %02dm' % (h, m)


def _hits(start, end, user=None):
    from .models import ActivityHit
    qs = ActivityHit.objects.filter(day__gte=start, day__lte=end)
    if user is not None:
        qs = qs.filter(user=user)
    return list(qs.order_by('user_id', 'at'))


def usage(start, end):
    """The grid: users (columns) x modules (rows, by area), with visits
    and time; area totals."""
    from django.contrib.auth.models import User
    hits = _hits(start, end)
    by_user = {}
    for h in hits:
        by_user.setdefault(h.user_id, []).append(h)
    cell = {}
    for uid, hs in by_user.items():
        sittings(hs)
        for h in hs:
            if not h.module:
                continue
            c = cell.setdefault((h.module, uid), [0, dt.timedelta()])
            c[0] += 1
            c[1] += h.spent
    users = list(User.objects.filter(is_active=True).order_by(
        '-is_superuser', 'first_name', 'last_name', 'username'))
    most = max([c[0] for c in cell.values()] or [1])

    def shade(n):
        if not n:
            return 'z'
        f = n / float(most)
        return 'd' if f > .5 else 'b' if f > .15 else 'a'
    areas = []
    for akey, aname in AREAS:
        rows, tot = [], {u.pk: [0, dt.timedelta()] for u in users}
        sub = None
        for key, lab, area, subhead, _p in MODULES:
            if area != akey:
                continue
            cells = []
            for u in users:
                n, t = cell.get((key, u.pk), [0, dt.timedelta()])
                tot[u.pk][0] += n
                tot[u.pk][1] += t
                cells.append({'n': n, 't': words(t) if n else '',
                              'shade': shade(n),
                              'title': '%s · %s: %d visit%s, %s' % (
                                  u.get_full_name() or u.username, lab, n,
                                  '' if n == 1 else 's', words(t))})
            rows.append({'key': key, 'label': lab, 'cells': cells,
                         'sub': subhead if subhead and subhead != sub and
                         akey in ('admin', 'personal') else ''})
            sub = subhead
        # The menu's order: Property Operations as in the menu.
        if akey in ('ops', 'fin'):
            order = [m[0] for m in MODULES if m[2] == akey]
            rows.sort(key=lambda r: order.index(r['key']))
        areas.append({'key': akey, 'name': aname, 'rows': rows,
                      'personal': akey == 'personal',
                      'totals': [{'n': tot[u.pk][0],
                                  't': words(tot[u.pk][1])
                                  if tot[u.pk][0] else ''} for u in users]})
    return {'users': users, 'areas': areas}


def visits(start, end, user=None):
    """Sittings, newest first: who, when, how long, and the business pages
    (Personal: the module and the count only)."""
    from django.contrib.auth.models import User
    hits = _hits(start, end, user)
    names = {u.pk: u.get_full_name() or u.username
             for u in User.objects.all()}
    by_user, out = {}, []
    for h in hits:
        by_user.setdefault(h.user_id, []).append(h)
    for uid, hs in by_user.items():
        for s in sittings(hs):
            mods = {}
            for h in s['hits']:
                k = h.module
                m = mods.setdefault(k, {'label': label(k), 'n': 0,
                                        'spent': dt.timedelta(),
                                        'personal': is_personal(k),
                                        'pages': []})
                m['n'] += 1
                m['spent'] += h.spent
                if h.path and not m['personal']:
                    m['pages'].append({'at': h.at, 'path': h.path})
            for m in mods.values():
                m['t'] = words(m['spent'])
            out.append({'who': names.get(uid, '?'), 'uid': uid,
                        'start': s['start'], 'end': s['end'],
                        'spent': words(s['spent']), 'n': len(s['hits']),
                        'mods': sorted(mods.values(),
                                       key=lambda m: -m['spent'])})
    out.sort(key=lambda s: s['start'], reverse=True)
    return out[:300]


def _span(start, end):
    """[start 00:00, the day after end 00:00) in Cyprus time. Not
    at__date: on MySQL with USE_TZ that needs the server's time-zone
    tables, and without them it matches nothing (the RA15 push)."""
    z = timezone.get_current_timezone()
    return (timezone.make_aware(dt.datetime.combine(start, dt.time()), z),
            timezone.make_aware(dt.datetime.combine(
                end + dt.timedelta(days=1), dt.time()), z))


def changes(start, end, user=None):
    from .models import RecordChange
    a, b = _span(start, end)
    qs = RecordChange.objects.filter(at__gte=a, at__lt=b).select_related('user')
    if user is not None:
        qs = qs.filter(user=user)
    rows = list(qs.order_by('-at')[:500])
    for r in rows:
        r.module_label = label(r.module)
    return rows


def signins(start, end, user=None):
    from .models import SignIn
    a, b = _span(start, end)
    qs = SignIn.objects.filter(at__gte=a, at__lt=b).select_related('user')
    if user is not None:
        qs = qs.filter(user=user)
    return list(qs.order_by('-at')[:500])

