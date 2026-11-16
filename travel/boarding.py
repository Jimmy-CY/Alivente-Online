"""TR-8, 16 Nov 2026 - which boarding pass is Next, which are Coming up,
which are Used.

Demetri, 16 Nov:
  "Your Boarding Pass must always come first."
  "Always you pass first. Keep forever, but stamp them USED in red
   diagonally across (also grey out the QR Code)."
  "What happens if a flight is drastically delayed ... if the system
   assumes that you have used the pass and then deactivates it???"
  "if I fly to Greece (1hr40min) and then I connect within 2 hours to
   Dublin. The 8 hours will be an issue"

So:
  - nothing is ever switched off - a Used pass shows its barcode again on
    one tap;
  - the last flight of a run turns Used 6 h after its scheduled landing
    (8 h after it leaves when there is no landing time);
  - a flight with a later flight for the same person close behind it (a
    connection) hands Next over at its scheduled landing, and stays one tap
    away as "Earlier today" until the 6 h have passed;
  - "Done with this pass" and "Not flown yet" put a pass right by hand.
"""
import datetime as dt
import re

USED_AFTER_LANDING = dt.timedelta(hours=6)
USED_AFTER_LEAVING = dt.timedelta(hours=8)
CONNECTION = dt.timedelta(hours=24)      # a later flight this close = a run
NOT_YET_HOLDS = dt.timedelta(hours=24)   # "Not flown yet" holds this long
RECENT = dt.timedelta(hours=48)          # "Not flown yet" offered this long


def leaves(b):
    if not b.start_date:
        return None
    return dt.datetime.combine(b.start_date, b.start_time or dt.time(0))


def lands(b):
    """Scheduled landing, or None when the booking has no arrival time."""
    if not (b.start_date and b.end_time):
        return None
    end = dt.datetime.combine(b.end_date or b.start_date, b.end_time)
    if b.start_time and not b.end_date and b.end_time < b.start_time:
        end += dt.timedelta(days=1)                 # lands after midnight
    return end


def skeleton(word):
    """The consonants of a name: Demetri and Dimitrios both start DMTR."""
    return re.sub(r'[aeiouy]', '', word.lower())


def is_me(name, user):
    """Is this pass the signed-in person's? A pass says MANIAS/DIMITRIOS
    where the account says Demetri Manias - surname the same, first names
    alike by their consonants."""
    from .views import name_key
    words = name_key(name)
    if not words or user is None:
        return False
    first = (user.first_name or '').strip().lower()
    last = (user.last_name or '').strip().lower()
    if not (first and last):
        full = name_key(user.get_full_name() or user.username)
        return bool(full) and full <= words
    if last not in words:
        return False
    s = skeleton(first)[:3]
    return bool(s) and any(skeleton(w).startswith(s) for w in words
                           if w != last)


def flight_key(p):
    b = p.booking
    num = re.sub(r'\s+', '', (p.flight or '')).upper()
    return (b.start_date, num or 'booking-%s' % b.pk)


def sort_passes(cards, user):
    """By flight, the signed-in person's pass first on each flight."""
    return sorted(cards, key=lambda p: (leaves(p.booking) or dt.datetime.max,
                                        flight_key(p)[1],
                                        0 if p.mine else 1, p.name or ''))


def settle(cards, now, user=None):
    """Sets on each card: mine, connects (a later flight of the same
    person follows), handed (no longer Next), stamped (shows USED) and
    over (the airline's own links will no longer work). Returns
    (next, coming, used, earlier, then)."""
    from .views import name_key
    for p in cards:
        p.mine = is_me(p.name, user)
        p.person = name_key(p.name) or frozenset(['?%s' % p.pk])
        p.leaves_at = leaves(p.booking)
        p.lands_at = lands(p.booking)
    for p in cards:
        later = [q for q in cards if q.person == p.person and q is not p
                 and q.leaves_at and p.leaves_at and q.leaves_at > p.leaves_at
                 and q.leaves_at - (p.lands_at or p.leaves_at) <= CONNECTION]
        p.connects = bool(later)
        if p.lands_at:
            stamp_at = p.lands_at + USED_AFTER_LANDING
            hand_at = p.lands_at if p.connects else stamp_at
        elif p.leaves_at:
            stamp_at = p.leaves_at + USED_AFTER_LEAVING
            hand_at = (p.leaves_at + dt.timedelta(hours=3)
                       if p.connects else stamp_at)
        else:
            stamp_at = hand_at = None
        held = (p.marked == 'open' and p.marked_at is not None
                and now - p.marked_at.replace(tzinfo=None) < NOT_YET_HOLDS)
        if p.marked == 'used':
            p.stamped = p.handed = True
        elif held:
            p.stamped = p.handed = False
        else:
            p.stamped = bool(stamp_at and now >= stamp_at)
            p.handed = bool(hand_at and now >= hand_at) or p.stamped
        p.over = p.handed
        p.held = held
        # "Not flown yet" is offered only while a delay is believable:
        # within two days of the pass being stamped.
        p.recent = p.handed and (stamp_at is None or
                                 now - stamp_at < RECENT)
    ahead = sort_passes([p for p in cards if not p.handed], user)
    nxt, coming = [], []
    if ahead:
        k = flight_key(ahead[0])
        nxt = [p for p in ahead if flight_key(p) == k]
        coming = [p for p in ahead if flight_key(p) != k]
    used = sorted([p for p in cards if p.handed],
                  key=lambda p: (p.leaves_at or dt.datetime.min,
                                 0 if p.mine else 1), reverse=True)
    # Stable within a flight: own pass first even in the reversed list.
    used = _own_first_within(used)
    then = None
    if nxt and coming:
        first = coming[0]
        anchor = nxt[0].lands_at or nxt[0].leaves_at
        if (first.leaves_at and anchor
                and first.leaves_at - anchor <= CONNECTION):
            then = first
    earlier = None
    if nxt:
        lead = nxt[0]
        recent = [p for p in used if not p.stamped and p.person == lead.person]
        earlier = recent[0] if recent else None
    for p in nxt:
        p.is_next = True
    return nxt, coming, used, earlier, then


def _own_first_within(rows):
    out, i = [], 0
    while i < len(rows):
        k = flight_key(rows[i])
        j = i
        while j < len(rows) and flight_key(rows[j]) == k:
            j += 1
        out += sorted(rows[i:j], key=lambda p: (0 if p.mine else 1,
                                                p.name or ''))
        i = j
    return out


def boards_in(p, now):
    """'in 2 h', 'in 35 min', 'tomorrow', '' - for the Next pass."""
    if not p.leaves_at or not p.booking.start_time:
        return ''
    gap = p.leaves_at - now
    mins = int(gap.total_seconds() // 60)
    if mins < 0:
        return ''
    if mins < 60:
        return 'in %d min' % mins
    if mins < 24 * 60:
        return 'in %d h' % (mins // 60)
    days = (p.leaves_at.date() - now.date()).days
    return 'tomorrow' if days == 1 else 'in %d days' % days
