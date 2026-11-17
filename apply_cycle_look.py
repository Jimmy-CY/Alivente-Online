# -*- coding: utf-8 -*-
"""apply_cycle_look.py - round CY-5, 17 Nov 2026.

RELEASE 98 - WELLNESS: THE CYCLE TRACKER REDESIGN.

    Demetri, 17 Nov: "I am happy with the Cycle Tracking changes,
    including sex tracking (as suggested) and Ovulation Days (as
    suggested). The rest of the Wellness app would keep our original
    colours."

    - Softer pinks on the cycle pages only (wellness.css, scoped to a page
      that carries <span class="cy-page">); the rest of Wellness keeps
      its sage and sand.
    - The overview: the cycle as a ring of days - the period in its
      logged shades, the fertile estimate, the likely ovulation day, PMS,
      the expected period - "16 days until your next period".
    - The calendar: a circle per day, darker red for a heavier flow, dots
      for what was logged; tap a logged day for its one-line summary.
    - Log a day: icon tiles grouped as Period, Feelings, Energy, Sleep,
      Sex, Pain and body, Discharge, Your tags, with a strip of the week.
      The same fields as before.
    - New: a fifth flow, Very heavy; Sex under More to log (off until
      switched on, never in a summary, the report or anything sent); the
      likely ovulation day with the fertile estimate (off by default, an
      estimate, not contraception); Cycle history - every cycle a bar,
      with three tiles.
    - Help and the guide say so; the phone app's version moves (wl26-1).

The suite, cycle_icons.py and _cy_tiles.html ship beside this patcher.
Stands on QL-1 (apply_quotes_one.py). Idempotent. Edits backed up to
.bak_cyclelook. No migration - everything lives in the locked record.
"""
import os
import sys

SUFFIX = '.bak_cyclelook'
MARK = 'CY-5, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_cycle_look.py',
    'wellness/cycle_icons.py',
    'wellness/templates/wellness/_cy_tiles.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_fifteen.py',
    # QL-1, 17 Nov 2026 - Release 97: 240 quotes, none twice in a round.
    'test_quotes.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_fifteen.py',
    # QL-1, 17 Nov 2026 - Release 97: 240 quotes, none twice in a round.
    'test_quotes.py',
    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    'test_cycle_look.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # QL-1, 17 Nov 2026 - Release 97: 240 quotes, none twice in a round.
    '.bak_quotes1',
]

''',
         r'''    # QL-1, 17 Nov 2026 - Release 97: 240 quotes, none twice in a round.
    '.bak_quotes1',
    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    '.bak_cyclelook',
]

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-gr-text { min-height: 150px; resize: vertical; font-size: 16px; line-height: 1.5; padding: 12px 14px; }
.w-gr-send { display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
''',
         r'''.w-gr-text { min-height: 150px; resize: vertical; font-size: 16px; line-height: 1.5; padding: 12px 14px; }
.w-gr-send { display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }

/* CY-5, 17 Nov 2026 - the Cycle Tracker redesign (canvas "Cycle Tracker
   before and after", approved by Demetri on 17 Nov). Softer pinks on the
   cycle pages ONLY - the rest of Wellness keeps its sage and sand. A page
   carries <span class="cy-page" hidden> and the palette follows. Flow in
   five shades of red, the fertile estimate pale blue, the likely
   ovulation day dark blue, PMS lilac, the expected period dashed. */
:root {
  --cy-bg: #FFF6F7;
  --cy-pink: #F7D9E0;
  --cy-pink-soft: #FCEBEF;
  --cy-line: #F1D7DE;
  --cy-rose: #C2185B;
  --cy-rose-deep: #9C1249;
  --cy-ink: #3A2A30;
  --cy-quiet: #6E5A61;
  --cy-sp: #F6C9D0;
  --cy-li: #F08A9B;
  --cy-me: #E04F68;
  --cy-he: #B4233D;
  --cy-vh: #7E1328;
  --cy-fert: #5AA9C8;
  --cy-fert-soft: #E3F2F8;
  --cy-ov: #1F5F8B;
  --cy-pms: #B9A3D9;
  --cy-pred: #F3B6C2;
  --cy-feel: #C26A12;
  --cy-sleep: #5B6FB5;
  --cy-sex: #C2185B;
  --cy-pain: #8E5BB5;
  --cy-energy: #2E8B6F;
  --cy-dis: #2F7FA0;
  --cy-tag: #6E5A61;
  /* the help's swatches name Wellness colours (test_wellness_eight). */
  --w-cy-period: var(--cy-me);
  --w-cy-expected: var(--cy-pred);
  --w-cy-fertile: var(--cy-fert);
  --w-cy-ovulation: var(--cy-ov);
  --w-cy-pms: var(--cy-pms);
  --w-cy-logged: var(--cy-rose);
}
@media (prefers-color-scheme: dark) {
  :root {
    --cy-bg: #221A1D;
    --cy-pink: #4A2A35;
    --cy-pink-soft: #33242A;
    --cy-line: #46323A;
    --cy-rose: #F48FB1;
    --cy-rose-deep: #F8BBD0;
    --cy-ink: #F3E6EA;
    --cy-quiet: #C9B3BA;
    --cy-fert-soft: #1E3542;
    --cy-feel: #F0A75A;
    --cy-sleep: #9AAAE0;
    --cy-sex: #F48FB1;
    --cy-pain: #C3A0E0;
    --cy-energy: #6CC9A8;
    --cy-dis: #7FC4E0;
    --cy-tag: #C9B3BA;
  }
}
body:has(.cy-page) {
  --w-bg: var(--cy-bg);
  --w-tint-morning: var(--cy-bg);
  --w-tint-afternoon: var(--cy-bg);
  --w-tint-evening: var(--cy-bg);
  --w-soft: var(--cy-pink-soft);
  --w-sand: var(--cy-pink-soft);
  --w-sand-line: var(--cy-line);
  --w-sand-ink: var(--cy-rose-deep);
  --w-sage: var(--cy-me);
  --w-sage-deep: var(--cy-rose);
  --w-sage-track: var(--cy-pink-soft);
  --w-line: var(--cy-line);
  --w-empty: var(--cy-pink-soft);
  --w-ink: var(--cy-ink);
  --w-quiet: var(--cy-quiet);
  --w-rose: var(--cy-rose);
  --w-rose-deep: var(--cy-rose-deep);
  --w-rose-soft: var(--cy-pink);
  --w-rose-wash: var(--cy-pink-soft);
  background: var(--cy-bg);
}
@media (prefers-color-scheme: dark) {
  body:has(.cy-page) { --w-on-accent: #2A0F1A; --w-card: #2E2226; }
}

/* the ring */
.cy-wheel { display: flex; justify-content: center; }
.cy-wheel svg { max-width: 100%; height: auto; }
.cy-b { fill: none; stroke: var(--cy-pink-soft); }
.cy-b.rest { stroke: var(--cy-pink); }
.cy-b.f-spotting { stroke: var(--cy-sp); }
.cy-b.f-light { stroke: var(--cy-li); }
.cy-b.f-medium { stroke: var(--cy-me); }
.cy-b.f-heavy { stroke: var(--cy-he); }
.cy-b.f-very_heavy { stroke: var(--cy-vh); }
.cy-b.fert { stroke: var(--cy-fert); }
.cy-b.ov { stroke: var(--cy-ov); }
.cy-b.pms { stroke: var(--cy-pms); opacity: .8; }
.cy-b.pred { stroke: var(--cy-pred); }
.cy-mark { fill: var(--cy-rose); }
.cy-ovdot { fill: var(--cy-ov); stroke: var(--w-card); stroke-width: 3; }
.cy-now { fill: var(--w-card); stroke: var(--cy-ink); stroke-width: 3; }
.cy-now-n { font-size: 13px; font-weight: 700; fill: var(--cy-ink); }
.cy-t-when { font-size: 13px; fill: var(--cy-quiet); }
.cy-t-big { font-size: 27px; font-weight: 700; fill: var(--cy-ink); }
.cy-t-small { font-size: 15px; fill: var(--cy-ink); }
.cy-t-ov { font-size: 12.5px; font-weight: 600; fill: var(--cy-ov); }
@media (prefers-color-scheme: dark) { .cy-t-ov { fill: var(--cy-fert); } }
.cy-key, .cy-flowkey { display: flex; flex-wrap: wrap; gap: 8px 14px; justify-content: center; font-size: 12.5px; color: var(--cy-ink); }
.cy-key span, .cy-flowkey span { display: inline-flex; align-items: center; gap: 6px; }
.cy-key i, .cy-flowkey i { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.cy-flowkey { justify-content: flex-start; gap: 8px 12px; }
.cy-flowkey i { width: 26px; height: 12px; border-radius: 6px; }
.cy-flowkey.cy-small { justify-content: flex-start; font-size: 12px; }
.cy-flowkey.cy-small i { width: 12px; border-radius: 50%; }
:is(.cy-key, .cy-flowkey, .cy-hist-bar, .cy-week) .f-spotting { background: var(--cy-sp); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar, .cy-week) .f-light { background: var(--cy-li); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar, .cy-week) .f-medium { background: var(--cy-me); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar, .cy-week) .f-heavy { background: var(--cy-he); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar, .cy-week) .f-very_heavy { background: var(--cy-vh); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar) .fert { background: var(--cy-fert); }
:is(.cy-key, .cy-flowkey, .cy-hist-bar) .ov { background: var(--cy-ov); }
.cy-key .pms { background: var(--cy-pms); }
.cy-key .pred { border: 2px dashed var(--cy-pred); box-sizing: border-box; }
.cy-info { background: var(--cy-pink-soft); }
.cy-acts { display: flex; gap: 10px; }
.cy-acts form { display: flex; }
.cy-track { flex: 1; border-radius: 26px; min-height: 52px; }
.cy-quick { border-radius: 26px; min-height: 52px; white-space: nowrap; }

/* the calendar: a circle per day in its flow's shade */
.cy-monthbar { display: flex; justify-content: space-between; align-items: center; }
.cy-nav { width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--cy-line); background: var(--w-card); color: var(--cy-rose); font-size: 20px; display: flex; align-items: center; justify-content: center; text-decoration: none; }
span.cy-nav { border-color: transparent; background: none; }
.w-month.cy-month { gap: 2px; }
.w-month.cy-month a, .w-month.cy-month span.day { min-height: 50px; border-radius: 0; background: none; box-shadow: none; gap: 2px; justify-content: flex-start; padding-top: 2px; }
.cy-month a b, .cy-month span.day b { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; }
.cy-month .out b { font-weight: 400; }
.cy-month i { height: 6px; display: flex; gap: 2px; font-style: normal; }
.cy-month i s { width: 5px; height: 5px; border-radius: 50%; display: inline-block; background: var(--cy-rose); text-decoration: none; }
.cy-month i s.feel { background: var(--cy-feel); }
.cy-month i s.sleep { background: var(--cy-sleep); }
.cy-month i s.more { background: var(--cy-quiet); }
.w-month.cy-month .logged::after { content: none; }
.cy-month .f-spotting b { background: var(--cy-sp); color: var(--cy-ink); }
.cy-month .f-light b { background: var(--cy-li); color: #3A0E19; }
.cy-month .f-medium b { background: var(--cy-me); color: #FFFFFF; }
.cy-month .f-heavy b { background: var(--cy-he); color: #FFFFFF; }
.cy-month .f-very_heavy b { background: var(--cy-vh); color: #FFFFFF; }
.cy-month .fertile b { background: var(--cy-fert-soft); color: var(--cy-ov); }
.cy-month .ov b { background: var(--cy-ov); color: #FFFFFF; }
.cy-month .expected b { border: 2px dashed var(--cy-pred); }
.cy-month .pms b { background: color-mix(in srgb, var(--cy-pms) 35%, transparent); }
.cy-month .today b { box-shadow: inset 0 0 0 2.5px var(--cy-ink); }
.cy-month .picked b { outline: 2px solid var(--cy-rose); outline-offset: 2px; }
.cy-month .out { color: var(--cy-quiet); opacity: .7; }
.w-legend .ov { background: var(--cy-ov); border-radius: 50%; }
.w-legend .dotkey { width: 6px; height: 6px; border-radius: 50%; background: var(--cy-rose); }
body:has(.cy-page) .w-legend i { border-radius: 50%; }
body:has(.cy-page) .w-legend .fertile { background: var(--cy-fert-soft); box-shadow: inset 0 0 0 1px var(--cy-fert); }
body:has(.cy-page) .w-legend .expected { box-shadow: none; border: 2px dashed var(--cy-pred); box-sizing: border-box; }
body:has(.cy-page) .w-legend .pms { background: var(--cy-pms); }
.cy-picked { background: var(--cy-pink-soft); border-radius: 14px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.cy-picked .w-btn { align-self: flex-start; }

/* Log a day: icon tiles by group */
.cy-week { display: flex; gap: 6px; }
.cy-week a { flex: 1; min-height: 52px; border-radius: 12px; background: var(--w-card); color: var(--cy-ink); text-decoration: none; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; position: relative; }
.cy-week a b { font-size: 15px; }
.cy-week a[class*="f-"] { box-shadow: inset 0 -4px 0 0 var(--cy-me); background: var(--w-card); }
.cy-week a.on { background: var(--cy-rose); color: var(--w-on-accent); }
.cy-group-h { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.cy-tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); gap: 10px 8px; }
.cy-tile { display: flex; flex-direction: column; align-items: center; gap: 5px; cursor: pointer; position: relative; }
.cy-tile input { position: absolute; opacity: 0; pointer-events: none; }
.cy-ic { --g: var(--cy-rose); width: 58px; height: 58px; border-radius: 16px; display: flex; align-items: center; justify-content: center; background: var(--w-card); color: var(--g); border: 2px solid color-mix(in srgb, var(--g) 35%, transparent); box-sizing: border-box; }
.cy-lb { font-size: 11.5px; line-height: 1.2; text-align: center; color: var(--cy-ink); }
.cy-tile input:checked + .cy-ic { background: var(--g); border-color: var(--g); color: var(--w-card); }
.cy-tile input:checked ~ .cy-lb { font-weight: 600; }
.cy-tile input:focus-visible + .cy-ic { outline: 2px solid var(--cy-ink); outline-offset: 2px; }
.g-period .cy-ic { --g: var(--cy-rose); }
.g-period .cy-tile:nth-child(1) .cy-ic { color: var(--cy-li); }
.g-period .cy-tile:nth-child(2) .cy-ic { color: var(--cy-li); }
.g-period .cy-tile:nth-child(3) .cy-ic { color: var(--cy-me); }
.g-period .cy-tile:nth-child(4) .cy-ic { color: var(--cy-he); }
.g-period .cy-tile:nth-child(5) .cy-ic { color: var(--cy-vh); }
.g-period .cy-tile input:checked + .cy-ic { background: var(--cy-pink-soft); border-color: var(--cy-rose); border-width: 3px; }
.g-feel .cy-ic { --g: var(--cy-feel); }
.g-sleep .cy-ic { --g: var(--cy-sleep); }
.g-sex .cy-ic { --g: var(--cy-sex); }
.g-pain .cy-ic { --g: var(--cy-pain); }
.g-energy .cy-ic { --g: var(--cy-energy); }
.g-discharge .cy-ic { --g: var(--cy-dis); }
.g-tags .cy-ic { --g: var(--cy-tag); }

/* Cycle history */
.cy-stats { display: flex; gap: 8px; }
.cy-stats div { flex: 1; background: var(--cy-pink-soft); border-radius: 14px; padding: 10px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.cy-stats span { font-size: 11.5px; color: var(--cy-quiet); }
.cy-stats b { font-size: 19px; color: var(--cy-ink); white-space: nowrap; }
.cy-hist { display: flex; flex-direction: column; gap: 4px; }
.cy-hist-top { display: flex; justify-content: space-between; font-size: 12.5px; color: var(--cy-ink); }
.cy-hist-bar { display: flex; gap: 1px; height: 14px; border-radius: 7px; overflow: hidden; background: var(--cy-pink); }
.cy-hist-bar i { flex: 1; background: var(--cy-pink); }
@media print { body:has(.cy-page) { background: #FFFFFF; } }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    if (e.target.closest && e.target.closest('[data-print]')) window.print();
  });

  // ---- WL-4b, 30 Oct 2026 - turn on reminders on this phone. The phone
''',
         r'''    if (e.target.closest && e.target.closest('[data-print]')) window.print();
  });
  // CY-5, 17 Nov 2026 - an icon tile that is one of a kind (mood, sleep,
  // energy, discharge) clears when tapped again, so a wrong tap can be
  // undone. Without script the tiles still work as plain choices.
  var tiles = document.querySelector('[data-cy-tiles]');
  if (tiles) {
    var was = null;
    tiles.addEventListener('pointerdown', function (e) {
      var l = e.target.closest && e.target.closest('label.cy-tile');
      var r = l && l.querySelector('input[type=radio][data-untick]');
      was = r && r.checked ? r : null;
    });
    tiles.addEventListener('click', function (e) {
      var r = e.target.closest && e.target.closest('input[type=radio][data-untick]');
      if (r && r === was) { r.checked = false; was = null; }
    });
  }

  // ---- WL-4b, 30 Oct 2026 - turn on reminders on this phone. The phone
'''),
    ]),
    (os.path.join('wellness', 'cycle.py'), [
        (r'''    ('medium', 'Medium'),
    ('heavy', 'Heavy'),
]
FLOW_NAMES = dict(FLOWS)
# Spotting alone does not start a period.
BLEED = ('light', 'medium', 'heavy')
FLOW_RANK = {'spotting': 0, 'light': 1, 'medium': 2, 'heavy': 3}

SYMPTOMS = [
''',
         r'''    ('medium', 'Medium'),
    ('heavy', 'Heavy'),
    # CY-5, 17 Nov 2026 - a fifth, darkest shade (the approved redesign).
    ('very_heavy', 'Very heavy'),
]
FLOW_NAMES = dict(FLOWS)
# Spotting alone does not start a period.
BLEED = ('light', 'medium', 'heavy', 'very_heavy')
FLOW_RANK = {'spotting': 0, 'light': 1, 'medium': 2, 'heavy': 3,
             'very_heavy': 4}
HEAVY = ('heavy', 'very_heavy')

SYMPTOMS = [
'''),
        (r'''    ('sleep', 'Sleep'),
    ('discharge', 'Discharge'),
    ('tags', 'My own tags'),
]
''',
         r'''    ('sleep', 'Sleep'),
    ('discharge', 'Discharge'),
    # CY-5, 17 Nov 2026 - Demetri: "including sex tracking (as
    # suggested)". Off until switched on; never in the day's summary
    # line, the doctor report or anything sent.
    ('sex', 'Sex'),
    ('tags', 'My own tags'),
]
'''),
        (r'''DISCHARGE = [('dry', 'Dry'), ('sticky', 'Sticky'), ('creamy', 'Creamy'),
             ('watery', 'Watery'), ('clear', 'Clear and stretchy')]
CHOICES = {'mood': dict(MOODS), 'energy': dict(ENERGY),
           'sleep': dict(SLEEP), 'discharge': dict(DISCHARGE)}
''',
         r'''DISCHARGE = [('dry', 'Dry'), ('sticky', 'Sticky'), ('creamy', 'Creamy'),
             ('watery', 'Watery'), ('clear', 'Clear and stretchy')]
# CY-5 - more than one can be true of a day, so these are ticks.
SEX = [('protected', 'Protected'), ('unprotected', 'Unprotected'),
       ('none', 'No sex'), ('high_drive', 'High drive'),
       ('low_drive', 'Low drive')]
SEX_NAMES = dict(SEX)
CHOICES = {'mood': dict(MOODS), 'energy': dict(ENERGY),
           'sleep': dict(SLEEP), 'discharge': dict(DISCHARGE)}
'''),
        (r'''                    # reminder time and the logging nudge.
                    'track': (), 'tags': (), 'pill_at': '',
                    'nudge': False}

# A gap of one dry day inside a period does not end it.
''',
         r'''                    # reminder time and the logging nudge.
                    'track': (), 'tags': (), 'pill_at': '',
                    'nudge': False,
                    # CY-5 - the likely ovulation day, shown only with
                    # the fertile estimate. Off by default.
                    'ovulation': False}

# A gap of one dry day inside a period does not end it.
'''),
        (r'''    if mine:
        out['tags'] = mine
    return out

''',
         r'''    if mine:
        out['tags'] = mine
    sx = post_like.getlist('sex') if hasattr(post_like, 'getlist') \
        else post_like.get('sex', [])
    sx = [k for k, _n in SEX if k in set(sx or ())]
    if sx:
        out['sex'] = sx
    return out

'''),
        (r'''           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'flags': flags(cs, today, mode)}
    if not ps:
        if mode not in PREDICTING:
''',
         r'''           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'ovulation': None,
           'flags': flags(cs, today, mode)}
    if not ps:
        if mode not in PREDICTING:
'''),
        (r'''        out['fertile'] = (ov - dt.timedelta(days=5),
                          ov + dt.timedelta(days=1))
    return out

''',
         r'''        out['fertile'] = (ov - dt.timedelta(days=5),
                          ov + dt.timedelta(days=1))
        # CY-5 - the likely day itself, only if asked for as well.
        if settings.get('ovulation'):
            out['ovulation'] = ov
    return out

'''),
        (r'''            e = days.get(d.isoformat(), {})
            kind = ''
            if e.get('flow') in BLEED:
                kind = 'period'
''',
         r'''            e = days.get(d.isoformat(), {})
            kind = ''
            ov = s.get('ovulation')
            if e.get('flow') in BLEED:
                kind = 'period'
'''),
        (r'''            week.append({'n': d.day, 'date': d, 'in': d.month == month,
                         'kind': kind, 'today': d == today,
                         'logged': bool(e), 'future': d > today})
            d += dt.timedelta(days=1)
        weeks.append(week)
        if d.month != month and d > first:
            break
    return weeks


''',
         r'''            week.append({'n': d.day, 'date': d, 'in': d.month == month,
                         'kind': kind, 'today': d == today,
                         'logged': bool(e), 'future': d > today,
                         # CY-5 - the flow's own shade, the ovulation
                         # day, and a dot for each kind of thing logged.
                         'flow': e.get('flow', ''),
                         'ov': bool(ov and d == ov and not e.get('flow')),
                         'dots': dots(e)})
            d += dt.timedelta(days=1)
        weeks.append(week)
        if d.month != month and d > first:
            break
    return weeks


DOTS = (('body', ('sym', 'pain', 'relief')),
        ('feel', ('mood', 'energy')),
        ('sleep', ('sleep',)),
        ('more', ('note', 'discharge', 'tags', 'sex')))


def dots(e):
    """CY-5 - which small dots a calendar day shows: body (symptoms or
    pain), feelings, sleep, and one for anything else."""
    return [k for k, keys in DOTS if any(e.get(x) for x in keys)]


def day_words(e):
    """CY-5 - one line for a day: 'Medium flow · Cramps · Tired · Slept
    poorly'. Never mentions sex - it stays inside Log a day."""
    out = []
    if e.get('flow'):
        out.append('%s flow' % FLOW_NAMES[e['flow']] if e['flow'] !=
                   'spotting' else 'Spotting')
    out += [SYMPTOM_NAMES[k] for k in e.get('sym', []) if k in
            SYMPTOM_NAMES]
    if e.get('pain'):
        out.append('Pain %d of 10' % e['pain'])
    if e.get('mood'):
        out.append('Mood: %s' % CHOICES['mood'][e['mood']].lower())
    if e.get('energy'):
        out.append('Energy: %s' % CHOICES['energy'][e['energy']].lower())
    if e.get('sleep'):
        out.append('Slept %s' % {'poor': 'poorly', 'okay': 'okay',
                                 'good': 'well'}[e['sleep']])
    if e.get('discharge'):
        out.append('Discharge: %s'
                   % CHOICES['discharge'][e['discharge']].lower())
    out += e.get('tags', [])
    if e.get('note'):
        out.append('A note')
    return ' · '.join(out)


def _when(d):
    """'Tue 17 Nov' without %-d."""
    return '%s %d %s' % (d.strftime('%a'), d.day, d.strftime('%b'))


def _arc(c, r, a0, a1):
    import math
    x0, y0 = c + r * math.sin(a0), c - r * math.cos(a0)
    x1, y1 = c + r * math.sin(a1), c - r * math.cos(a1)
    large = 1 if a1 - a0 > math.pi else 0
    return 'M%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f' % (x0, y0, r, r, large,
                                                       x1, y1)


def wheel(s, days, today, pms_days=None, size=280):
    """CY-5 - the big ring of the approved redesign (17 Nov): one bead
    per day of the cycle - the period in its logged shades, the fertile
    estimate, the likely ovulation day, the PMS days, the expected next
    period - with today marked and a dot outside each logged day. None
    without a cycle day."""
    import math
    n_today = s.get('cycle_day')
    if not n_today or not s['cycles']:
        return None
    start = s['cycles'][-1]['start']
    usual = s.get('avg_cycle') or 28
    L = max(usual, n_today if n_today <= PREDICT_MAX else usual)
    c = size / 2.0
    sw = 20
    r = c - sw / 2.0 - 12
    gap = min(0.035, math.pi / L / 4)
    fer, ov, win = s.get('fertile'), s.get('ovulation'), s.get('window')
    pms_from = L - pms_days + 1 if pms_days else None
    beads, marks = [], []
    for n in range(1, L + 1):
        d = start + dt.timedelta(days=n - 1)
        e = days.get(d.isoformat(), {})
        f = e.get('flow')
        if f:
            cls = 'f-' + f
        elif ov and d == ov:
            cls = 'ov'
        elif fer and fer[0] <= d <= fer[1]:
            cls = 'fert'
        elif win and d > today and win[0] <= d <= win[1]:
            cls = 'pred'
        elif pms_from and n >= pms_from and d > today:
            cls = 'pms'
        else:
            cls = 'rest'
        a0 = 2 * math.pi * (n - 1) / L + gap
        a1 = 2 * math.pi * n / L - gap
        beads.append({'d': _arc(c, r, a0, a1), 'cls': cls})
        if e:
            am = 2 * math.pi * (n - 0.5) / L
            ro = r + sw / 2.0 + 7
            marks.append({'x': '%.1f' % (c + ro * math.sin(am)),
                          'y': '%.1f' % (c - ro * math.cos(am))})
    out = {'size': size, 'c': '%.1f' % c, 'r': '%.1f' % r, 'sw': sw,
           'beads': beads, 'marks': marks, 'of': L, 'day': n_today,
           'when': 'Today, ' + _when(today)}
    if n_today <= L:
        at = 2 * math.pi * (n_today - 0.5) / L
        out['tx'] = '%.1f' % (c + r * math.sin(at))
        out['ty'] = '%.1f' % (c - r * math.cos(at))
    if ov and start <= ov < start + dt.timedelta(days=L):
        ao = 2 * math.pi * ((ov - start).days + 0.5) / L
        out['ox'] = '%.1f' % (c + r * math.sin(ao))
        out['oy'] = '%.1f' % (c - r * math.cos(ao))
    # The words in the middle.
    big, small, line = 'Day %d' % n_today, 'of your cycle', ''
    if s.get('in_period'):
        big, small = 'Day %d' % s['period_day'], 'of your period'
    elif win and s['state'] in ('predicted', 'first_guess'):
        to = (win[0] - today).days
        if to > 1:
            big, small = '%d days' % to, 'until your next period'
        elif to == 1:
            big, small = '1 day', 'until your next period'
        elif win[0] <= today <= win[1]:
            big, small = 'Any day now', 'your period is due'
    if ov and s['state'] in ('predicted', 'first_guess'):
        k = (ov - today).days
        if k > 1:
            line = 'Ovulation likely in %d days' % k
        elif k == 1:
            line = 'Ovulation likely tomorrow'
        elif k == 0:
            line = 'Ovulation likely today'
    out.update({'big': big, 'small': small, 'line': line})
    return out


def history(days, cs, s, n=RECENT, fertile=False):
    """CY-5 - Cycle history: the current cycle and the last n before
    it, newest first, each a row of day cells in the period's shades
    (and, with the estimate on, the fertile days and the likely
    ovulation day, counted back 14 days from the next start)."""
    rows = []
    top = max([c['length'] or 0 for c in cs[-n - 1:]] +
              [s.get('cycle_day') or 0, 28])
    top = min(top, PREDICT_MAX)
    for c in cs[-n - 1:][::-1]:
        length = c['length'] or (s.get('cycle_day') or 1)
        if length > PREDICT_MAX:
            continue
        ov_n = length - 14 if fertile and c['length'] else None
        cells = []
        for i in range(length):
            d = c['start'] + dt.timedelta(days=i)
            f = days.get(d.isoformat(), {}).get('flow')
            if f:
                cls = 'f-' + f
            elif ov_n and i + 1 == ov_n:
                cls = 'ov'
            elif ov_n and ov_n - 5 <= i + 1 <= ov_n + 1:
                cls = 'fert'
            else:
                cls = 'rest'
            cells.append(cls)
        if c['length']:
            last = c['start'] + dt.timedelta(days=c['length'] - 1)
            label = '%d %s – %d %s' % (c['start'].day,
                                       c['start'].strftime('%b'),
                                       last.day, last.strftime('%b'))
            side = '%d days' % c['length']
        else:
            label = 'Now · from %d %s' % (c['start'].day,
                                          c['start'].strftime('%b'))
            side = 'day %d' % length
        rows.append({'label': label, 'side': side, 'cells': cells,
                     'w': '%.2f' % (100.0 * length / top)})
    return rows


def stats(cs):
    """CY-5 - the three tiles over Cycle history: cycle length, period
    length and how much the cycles vary. None until one cycle is done."""
    lengths = recent_lengths(cs)
    if not lengths:
        return None
    pers = [c['period'] for c in cs[-RECENT:]]
    spread = max(lengths) - min(lengths)
    return {'cycle': int(round(median(lengths))),
            'cycle_usual': span_words(min(lengths), max(lengths), ' – '),
            'period': int(round(median(pers))),
            'period_usual': span_words(min(pers), max(pers), ' – '),
            'vary': (spread + 1) // 2,
            'vary_word': 'regular' if spread <= 7 else 'varies more'}


'''),
        (r'''                for i in range(c['period'])]
        flows = [days.get(d.isoformat(), {}).get('flow') for d in span]
        heavy = sum(1 for f in flows if f == 'heavy')
        top = max((FLOW_RANK.get(f, -1) for f in flows), default=-1)
        sym = {}
''',
         r'''                for i in range(c['period'])]
        flows = [days.get(d.isoformat(), {}).get('flow') for d in span]
        heavy = sum(1 for f in flows if f in HEAVY)
        top = max((FLOW_RANK.get(f, -1) for f in flows), default=-1)
        sym = {}
'''),
        (r'''                     'heaviest': [k for k, v in FLOW_RANK.items()
                                  if v == top][0] if top >= 0 else '',
                     'pain': max(pains) if pains else None,
                     'common': common})
''',
         r'''                     'heaviest': [k for k, v in FLOW_RANK.items()
                                  if v == top][0] if top >= 0 else '',
                     'heaviest_name': FLOW_NAMES[[k for k, v in
                                                  FLOW_RANK.items()
                                                  if v == top][0]]
                     if top >= 0 else '',
                     'pain': max(pains) if pains else None,
                     'common': common})
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
     'a': 'Yes. In Cycle settings, under More to log, switch on mood, '
          'energy, sleep, discharge or your own tags (type them, separated '
          'by commas). They appear in Log today, and Patterns shows how '
          'they follow your cycle. All of it is locked like the rest.'},
    {'q': 'What are PMS days?',
     'a': 'After three periods with symptoms logged, the calendar shades '
          'the days before each expected period when your symptoms usually '
          'begin - faint rose. The calendar looks six months ahead.'},
    {'q': 'Can Wellness remind me to take my pill?',
     'a': 'Yes. In Cycle settings set a daily pill reminder time. Like '
''',
         r'''    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
     'a': 'Yes. In Cycle settings, under More to log, switch on mood, '
          'energy, sleep, sex, discharge or your own tags (type them, '
          'separated '
          'by commas). They appear in Log today, and Patterns shows how '
          'they follow your cycle. All of it is locked like the rest.'},
    {'q': 'What are PMS days?',
     'a': 'After three periods with symptoms logged, the calendar shades '
          'the days before each expected period when your symptoms usually '
          'begin - lilac. The calendar looks six months ahead.'},
    # CY-5, 17 Nov 2026 - the Cycle Tracker redesign.
    {'q': 'What do the colours on the cycle pages mean?',
     'a': 'Red is your period, darker for a heavier flow - spotting, '
          'light, medium, heavy and very heavy. Dashed pink is when the '
          'next one is expected, lilac the PMS days, blue the fertile '
          'estimate and dark blue the likely ovulation day (both only if '
          'you turned them on). The ring shows the same for this cycle, '
          'one bead a day. The softer pinks are on the cycle pages only.'},
    {'q': 'Can I see the likely ovulation day?',
     'a': 'Yes. In Cycle settings turn on the fertile estimate, then "Also '
          'show the likely ovulation day". It is counted about 14 days '
          'back from your next expected period and shown in dark blue. It '
          'is an estimate, not contraception - never rely on it to prevent '
          'a pregnancy.'},
    {'q': 'Can I track sex, and who sees it?',
     'a': 'Yes, if you switch Sex on under More to log: protected, '
          'unprotected, none, and how your drive is. Only you see it, only '
          'in Log a day - it never shows in a day\'s summary, the doctor '
          'report, a reminder or an email, and it is locked like the '
          'rest.'},
    {'q': 'Can Wellness remind me to take my pill?',
     'a': 'Yes. In Cycle settings set a daily pill reminder time. Like '
'''),
        (r'''         'Optional: a day-before reminder, a nudge to log, a daily pill '
         'time. Each only ever says "A Wellness reminder".',
         'Optional: More to log - mood, energy, sleep, discharge or your '
         'own tags.']},
    # ---- When something is not working
    {'q': 'Reminders do not arrive',
''',
         r'''         'Optional: a day-before reminder, a nudge to log, a daily pill '
         'time. Each only ever says "A Wellness reminder".',
         'Optional: More to log - mood, energy, sleep, sex, discharge or '
         'your own tags.']},
    # ---- When something is not working
    {'q': 'Reminders do not arrive',
'''),
        (r'''               'turn the sounds off', 'time zone', 'At home today')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight', 'progress photos')),
''',
         r'''               'turn the sounds off', 'time zone', 'At home today')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile', 'ovulation', 'track sex')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight', 'progress photos')),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''                   'next period is likely.',
        'steps': [
            'The card at the top shows the day of your cycle and its phase '
            'on a soft wave. Tomorrow shows the next day.',
            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: general wellbeing ideas, loosely matched to '
            'the phase. Tap one for why and how; hide any you do not want.',
            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
            'A first guess at the next period appears after one full cycle, '
            'as a window of a few days; it gets steadier from two.',
''',
         r'''                   'next period is likely.',
        'steps': [
            'The ring is your cycle, one bead a day: where you are, how many '
            'days until the next period and, if you turned it on, when '
            'ovulation is likely.',
            'The phase card shows the day of your cycle and its phase on a '
            'soft wave. Tomorrow shows the next day.',
            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: general wellbeing ideas, loosely matched to '
            'the phase. Tap one for why and how; hide any you do not want.',
            'Or tap + Log today to add flow, feelings, sleep, symptoms and '
            'a note.',
            'Tap a day you logged on the calendar to see a one-line summary '
            'and change it; tap an empty past day to fill it in.',
            'A first guess at the next period appears after one full cycle, '
            'as a window of a few days; it gets steadier from two.',
'''),
        (r'''                              'phases are estimates from your own '
                              'averages.'),
            ('--w-rose-soft', 'Rose days: your period.'),
            ('--w-rose', 'Outlined days: when the next one is expected.'),
            ('--w-sky-soft', 'Pale blue: the fertile estimate, only if you '
                             'turned it on. An estimate, not contraception.'),
            ('--w-rose-wash', 'Faint rose: PMS days - when symptoms usually '
                              'come before a period, from what you logged. '
                              'The calendar looks six months ahead.'),
        ],
    },
    'cycle_log': {
        'title': 'Log a day',
        'purpose': 'How today is - everything is optional.',
        'steps': [
            'Pick the flow, or leave No bleeding.',
            'Tick anything you notice - from cramps to mood swings, with '
            'more in perimenopause mode - and move the pain slider if you '
            'like.',
            'Mood, energy, sleep, discharge and your own tags appear here '
            'when you switch them on in Cycle settings.',
            'A private note is only for you.',
        ],
''',
         r'''                              'phases are estimates from your own '
                              'averages.'),
            ('--w-cy-period', 'Red: your period, darker for a heavier '
                              'flow - spotting, light, medium, heavy, '
                              'very heavy.'),
            ('--w-cy-expected', 'Dashed pink: when the next one is '
                                'expected.'),
            ('--w-cy-fertile', 'Blue: the fertile estimate, only if you '
                               'turned it on. An estimate, not '
                               'contraception.'),
            ('--w-cy-ovulation', 'Dark blue: the likely ovulation day, if '
                                 'you turned that on as well.'),
            ('--w-cy-pms', 'Lilac: PMS days - when symptoms usually come '
                           'before a period, from what you logged. The '
                           'calendar looks six months ahead.'),
            ('--w-cy-logged', 'Small dots: something logged that day - '
                              'red for body, orange for feelings, blue for '
                              'sleep, grey for anything else.'),
        ],
    },
    'cycle_log': {
        'title': 'Log a day',
        'purpose': 'How today is - everything is optional.',
        'steps': [
            'The strip at the top is this week - tap a day to log it.',
            'Tap a drop for the flow - the fuller, the heavier - or leave '
            'No bleeding.',
            'Tap the tiles for anything you notice: feelings, sleep, pain '
            'and body, with more in perimenopause mode. Tap a tile again '
            'to clear it. Move the pain slider if you like.',
            'Mood, energy, sleep, sex, discharge and your own tags appear '
            'here when you switch them on in Cycle settings. Sex is only '
            'ever seen here.',
            'A private note is only for you.',
        ],
'''),
        (r'''            'Reminders - a day before, a nudge to log, a daily pill time - '
            'only ever say "A Wellness reminder".',
            'More to log adds mood, energy, sleep, discharge or your own '
            'tags to Log today, and to Patterns.',
            'Download my log saves everything as a file.',
            'Turning it off keeps your log, locked. Delete everything '
''',
         r'''            'Reminders - a day before, a nudge to log, a daily pill time - '
            'only ever say "A Wellness reminder".',
            'The fertile estimate can show the likely ovulation day too, '
            'in dark blue. Both are estimates, not contraception.',
            'More to log adds mood, energy, sleep, sex, discharge or your '
            'own tags to Log today, and to Patterns.',
            'Download my log saves everything as a file.',
            'Turning it off keeps your log, locked. Delete everything '
'''),
        (r'''                   'period.',
        'steps': [
            'Patterns appear after three periods with symptoms logged. '
            'Mood, sleep, energy and your own tags count too.',
''',
         r'''                   'period.',
        'steps': [
            'The three tiles: your usual cycle, your usual period and how '
            'much your cycles vary.',
            'Cycle history draws each cycle as a bar of its days, newest '
            'first, with the period in its shades.',
            'Patterns appear after three periods with symptoms logged. '
            'Mood, sleep, energy and your own tags count too.',
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl25-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl26-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl25-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl26-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle.html'), [
        (r'''{% extends "wellness/base.html" %}
{% comment %} CY-1, 30 Oct 2026 - the cycle overview, as approved on the design canvas (row 2). {% endcomment %}
{% block title %}Cycle · Wellness{% endblock %}
{% block content %}
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
  <h1 class="w-title">Cycle</h1>
  <a class="w-icon-btn" href="{% url 'wellness:cycle_settings' %}" aria-label="Cycle tracker settings">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M11 2.5v2.2M11 17.3v2.2M2.5 11h2.2M17.3 11h2.2M5 5l1.6 1.6M15.4 15.4L17 17M5 17l1.6-1.6M15.4 6.6L17 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
''',
         r'''{% extends "wellness/base.html" %}
{% comment %} CY-1, 30 Oct 2026 - the cycle overview, as approved on the design canvas (row 2). CY-5, 17 Nov 2026 - redesigned. {% endcomment %}
{% block title %}Cycle · Wellness{% endblock %}
{% block content %}
{% comment %} CY-5, 17 Nov 2026 - the approved redesign (canvas "Cycle Tracker before and after"): softer pinks on the cycle pages only, the cycle as a ring of days, the calendar in shades of red by flow. The marker below switches the palette on for this page. {% endcomment %}
<span class="cy-page" hidden></span>
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
  <h1 class="w-title">Your cycle</h1>
  <a class="w-icon-btn" href="{% url 'wellness:cycle_settings' %}" aria-label="Cycle tracker settings">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M11 2.5v2.2M11 17.3v2.2M2.5 11h2.2M17.3 11h2.2M5 5l1.6 1.6M15.4 15.4L17 17M5 17l1.6-1.6M15.4 6.6L17 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
'''),
        (r'''{% endif %}

<section class="w-card">
  <div class="w-cy-head">
    {% if s.cycle_day %}
    <svg class="w-cy-ring" width="112" height="112" viewBox="0 0 112 112" role="img" aria-label="Cycle day {{ s.cycle_day }} of about {{ ring.of }}" style="flex:none">
      <circle class="track" cx="56" cy="56" r="46" fill="none" stroke-width="10"/>
      <circle class="per" cx="56" cy="56" r="46" fill="none" stroke-width="10" stroke-linecap="round" stroke-dasharray="{{ ring.period }}" transform="rotate(-90 56 56)"/>
      <circle class="now" cx="56" cy="56" r="46" fill="none" stroke-width="3" stroke-dasharray="{{ ring.today }}" transform="rotate(-90 56 56)" opacity="0.7"/>
      <text x="56" y="54" text-anchor="middle" font-size="26" font-weight="600">{{ s.cycle_day }}</text>
      <text class="sub" x="56" y="73" text-anchor="middle" font-size="12">cycle day</text>
    </svg>
    {% endif %}
    <div style="display:flex;flex-direction:column;gap:6px;min-width:0">
      <div class="w-cy-big" data-cycle-headline>{{ big }}</div>
      <div class="w-small w-quiet">{{ small }}</div>
    </div>
  </div>
</section>

{% comment %}
''',
         r'''{% endif %}

{% if wheel %}
<div class="cy-wheel" data-cycle-ring>
  <svg width="{{ wheel.size }}" height="{{ wheel.size }}" viewBox="0 0 {{ wheel.size }} {{ wheel.size }}" role="img" aria-label="Cycle day {{ wheel.day }} of about {{ wheel.of }}. {{ wheel.big }} {{ wheel.small }}.{% if wheel.line %} {{ wheel.line }}.{% endif %}">
    {% for b in wheel.beads %}<path class="cy-b {{ b.cls }}" d="{{ b.d }}" stroke-width="{{ wheel.sw }}"/>{% endfor %}
    {% for m in wheel.marks %}<circle class="cy-mark" cx="{{ m.x }}" cy="{{ m.y }}" r="3"/>{% endfor %}
    {% if wheel.ox %}<circle class="cy-ovdot" cx="{{ wheel.ox }}" cy="{{ wheel.oy }}" r="11"/>{% endif %}
    {% if wheel.tx %}<circle class="cy-now" cx="{{ wheel.tx }}" cy="{{ wheel.ty }}" r="15"/><text class="cy-now-n" x="{{ wheel.tx }}" y="{{ wheel.ty }}" dy="4.5" text-anchor="middle">{{ wheel.day }}</text>{% endif %}
    <text class="cy-t-when" x="{{ wheel.c }}" y="{{ wheel.c }}" dy="-36" text-anchor="middle">{{ wheel.when }}</text>
    <text class="cy-t-big" x="{{ wheel.c }}" y="{{ wheel.c }}" dy="-4" text-anchor="middle">{{ wheel.big }}</text>
    <text class="cy-t-small" x="{{ wheel.c }}" y="{{ wheel.c }}" dy="20" text-anchor="middle">{{ wheel.small }}</text>
    {% if wheel.line %}<text class="cy-t-ov" x="{{ wheel.c }}" y="{{ wheel.c }}" dy="46" text-anchor="middle">{{ wheel.line }}</text>{% endif %}
  </svg>
</div>
<div class="cy-key">
  <span><i class="f-medium"></i>Period</span>
  {% if s.fertile %}<span><i class="fert"></i>Fertile estimate</span>{% endif %}
  {% if s.ovulation %}<span><i class="ov"></i>Ovulation</span>{% endif %}
  {% if ring_pms %}<span><i class="pms"></i>PMS</span>{% endif %}
  {% if s.window %}<span><i class="pred"></i>Expected</span>{% endif %}
</div>
{% endif %}

<section class="w-card cy-info">
  <div class="w-cy-big" data-cycle-headline>{{ big }}</div>
  <div class="w-small w-quiet">{{ small }}</div>
</section>

{% if not locked %}
<div class="cy-acts">
  <a class="w-btn cy-track" href="{% url 'wellness:cycle_log' %}">{% if logged_today %}Change today{% else %}+ Log today{% endif %}</a>
  {% if open_from %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}">{% csrf_token %}<input type="hidden" name="do" value="end"><button type="submit" class="w-btn ghost cy-quick">My period ended</button></form>
  {% elif can_start %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}">{% csrf_token %}<input type="hidden" name="do" value="start"><button type="submit" class="w-btn ghost cy-quick">My period started</button></form>
  {% endif %}
</div>
{% if open_from %}<form method="post" action="{% url 'wellness:cycle_quick' %}" style="text-align:center;margin-top:-6px">{% csrf_token %}<input type="hidden" name="do" value="end"><input type="hidden" name="on" value="yesterday"><button type="submit" class="w-linkbtn w-small">It ended yesterday</button></form>{% endif %}
{% endif %}

{% comment %}
'''),
        (r'''  {% else %}
  <p class="w-small w-quiet" style="margin:0;text-align:center">{{ card.why_none }}</p>
  {% endif %}
  {% if when == 'today' and not locked %}
  {% if open_from %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}" class="w-btn-row">{% csrf_token %}<input type="hidden" name="do" value="end"><button type="submit" class="w-btn w-sand-btn" style="flex:1">My period ended</button></form>
  <form method="post" action="{% url 'wellness:cycle_quick' %}" style="text-align:center">{% csrf_token %}<input type="hidden" name="do" value="end"><input type="hidden" name="on" value="yesterday"><button type="submit" class="w-linkbtn w-small">It ended yesterday</button></form>
  {% elif can_start %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}" class="w-btn-row">{% csrf_token %}<input type="hidden" name="do" value="start"><button type="submit" class="w-btn w-sand-btn" style="flex:1">My period started</button></form>
  {% endif %}
  {% endif %}
</section>
''',
         r'''  {% else %}
  <p class="w-small w-quiet" style="margin:0;text-align:center">{{ card.why_none }}</p>
  {% endif %}
</section>
'''),
        (r'''{% endif %}

<a class="w-btn full" href="{% url 'wellness:cycle_log' %}">{% if logged_today %}Change today{% else %}Log today{% endif %}</a>

<section class="w-card" aria-labelledby="cal-h">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <a class="w-small" href="?m={{ prev_m|date:'Y-m' }}" aria-label="Previous month" style="min-width:44px;min-height:44px;display:flex;align-items:center">‹ {{ prev_m|date:'M' }}</a>
    <h2 class="w-h2" id="cal-h">{{ month|date:'F Y' }}</h2>
    {% if show_next %}<a class="w-small" href="?m={{ next_m|date:'Y-m' }}" aria-label="Next month" style="min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:flex-end">{{ next_m|date:'M' }} ›</a>{% else %}<span style="min-width:44px"></span>{% endif %}
  </div>
  <div class="w-month">
    <span class="dow">M</span><span class="dow">T</span><span class="dow">W</span><span class="dow">T</span><span class="dow">F</span><span class="dow">S</span><span class="dow">S</span>
    {% for week in weeks %}{% for c in week %}{% if c.future %}<span class="day{% if not c.in %} out{% endif %}{% if c.kind %} {{ c.kind }}{% endif %}">{{ c.n }}</span>{% else %}<a href="{% url 'wellness:cycle_log' %}?date={{ c.date|date:'Y-m-d' }}" class="{% if not c.in %}out{% endif %}{% if c.kind %} {{ c.kind }}{% endif %}{% if c.today %} today{% endif %}{% if c.logged %} logged{% endif %}" aria-label="{{ c.date|date:'j F' }}{% if c.kind == 'period' %}, period{% endif %}{% if c.logged %}, logged{% endif %}">{{ c.n }}</a>{% endif %}{% endfor %}{% endfor %}
  </div>
  <div class="w-legend">
    <span><i class="period"></i>Period</span>
    {% if s.window %}<span><i class="expected"></i>Expected</span>{% endif %}
    {% if s.fertile %}<span><i class="fertile"></i>Fertile estimate</span>{% endif %}
    {% if pms_days %}<span><i class="pms"></i>PMS days</span>{% endif %}
  </div>
  {% if pms_days %}<div class="w-small w-quiet" data-pms-line>From what you have logged, the days before a period often bring symptoms - about {{ pms_days }} day{{ pms_days|pluralize }} before.</div>{% endif %}
  {% if s.fertile %}<div class="w-small w-quiet">The fertile estimate is shown because you turned it on. {{ fertile_label }}</div>{% endif %}
  <div class="w-small w-quiet">Tap any past day to fill it in or change it.</div>
</section>

{% if s.avg_cycle or s.avg_period %}
<div class="w-list">
  {% if s.avg_cycle %}<div class="w-row"><span class="w-row-name">Average cycle</span><span class="w-row-side">{{ s.avg_cycle }} days</span></div>{% endif %}
  {% if s.avg_period %}<div class="w-row"><span class="w-row-name">Average period</span><span class="w-row-side">{{ s.avg_period }} days</span></div>{% endif %}
  <a class="w-row" href="{% url 'wellness:cycle_patterns' %}" style="text-decoration:none;color:inherit"><span class="w-row-name">Patterns and doctor report</span><span class="w-row-side" aria-hidden="true">›</span></a>
</div>
{% endif %}
''',
         r'''{% endif %}

<section class="w-card" aria-labelledby="cal-h" id="calendar">
  <div class="cy-monthbar">
    <a class="cy-nav" href="?m={{ prev_m|date:'Y-m' }}#calendar" aria-label="{{ prev_m|date:'F' }}">‹</a>
    <h2 class="w-h2" id="cal-h">{{ month|date:'F Y' }}</h2>
    {% if show_next %}<a class="cy-nav" href="?m={{ next_m|date:'Y-m' }}#calendar" aria-label="{{ next_m|date:'F' }}">›</a>{% else %}<span class="cy-nav" aria-hidden="true"></span>{% endif %}
  </div>
  <div class="w-month cy-month">
    <span class="dow">M</span><span class="dow">T</span><span class="dow">W</span><span class="dow">T</span><span class="dow">F</span><span class="dow">S</span><span class="dow">S</span>
    {% for week in weeks %}{% for c in week %}{% if c.future %}<span class="day{% if not c.in %} out{% endif %}{% if c.kind %} {{ c.kind }}{% endif %}{% if c.ov %} ov{% endif %}"{% if c.ov %} aria-label="{{ c.date|date:'j F' }}, likely ovulation"{% endif %}><b>{{ c.n }}</b><i></i></span>{% else %}<a href="{% if c.logged %}?m={{ month|date:'Y-m' }}&amp;d={{ c.date|date:'Y-m-d' }}#day{% else %}{% url 'wellness:cycle_log' %}?date={{ c.date|date:'Y-m-d' }}{% endif %}" class="{% if not c.in %}out{% endif %}{% if c.kind %} {{ c.kind }}{% endif %}{% if c.flow %} f-{{ c.flow }}{% endif %}{% if c.ov %} ov{% endif %}{% if c.today %} today{% endif %}{% if c.logged %} logged{% endif %}{% if picked and picked.date == c.date %} picked{% endif %}" aria-label="{{ c.date|date:'j F' }}{% if c.kind == 'period' %}, period{% endif %}{% if c.ov %}, likely ovulation{% endif %}{% if c.logged %}, logged{% endif %}"><b>{{ c.n }}</b><i>{% for d in c.dots %}<s class="{{ d }}"></s>{% endfor %}</i></a>{% endif %}{% endfor %}{% endfor %}
  </div>
  <div class="cy-flowkey" aria-label="Flow, lightest to heaviest">
    <span><i class="f-spotting"></i>Spotting</span><span><i class="f-light"></i>Light</span><span><i class="f-medium"></i>Medium</span><span><i class="f-heavy"></i>Heavy</span><span><i class="f-very_heavy"></i>Very heavy</span>
  </div>
  <div class="w-legend">
    {% if s.window %}<span><i class="expected"></i>Expected</span>{% endif %}
    {% if s.fertile %}<span><i class="fertile"></i>Fertile estimate</span>{% endif %}
    {% if s.ovulation %}<span><i class="ov"></i>Ovulation</span>{% endif %}
    {% if pms_days %}<span><i class="pms"></i>PMS days</span>{% endif %}
    <span><i class="dotkey"></i>Something logged</span>
  </div>
  {% if picked %}
  <div class="cy-picked" id="day" data-day-summary>
    <b>{{ picked.when }}{% if picked.day %} · day {{ picked.day }}{% endif %}</b>
    <span class="w-small w-quiet">{{ picked.words }}</span>
    <a class="w-btn ghost" href="{% url 'wellness:cycle_log' %}?date={{ picked.date|date:'Y-m-d' }}">Change this day</a>
  </div>
  {% endif %}
  {% if pms_days %}<div class="w-small w-quiet" data-pms-line>From what you have logged, the days before a period often bring symptoms - about {{ pms_days }} day{{ pms_days|pluralize }} before.</div>{% endif %}
  {% if s.fertile %}<div class="w-small w-quiet">The fertile estimate is shown because you turned it on{% if s.ovulation %}, with the likely ovulation day{% endif %}. {{ fertile_label }}</div>{% endif %}
  <div class="w-small w-quiet">Tap a day to see what you logged, or an empty past day to fill it in.</div>
</section>

{% if s.avg_cycle or s.avg_period %}
<div class="w-list">
  {% if s.avg_cycle %}<div class="w-row"><span class="w-row-name">Average cycle</span><span class="w-row-side">{{ s.avg_cycle }} days</span></div>{% endif %}
  {% if s.avg_period %}<div class="w-row"><span class="w-row-name">Average period</span><span class="w-row-side">{{ s.avg_period }} days</span></div>{% endif %}
  <a class="w-row" href="{% url 'wellness:cycle_patterns' %}" style="text-decoration:none;color:inherit"><span class="w-row-name">Cycle history, patterns and doctor report</span><span class="w-row-side" aria-hidden="true">›</span></a>
</div>
{% endif %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_intro.html'), [
        (r'''{% block title %}Cycle tracker · Wellness{% endblock %}
{% block content %}
<h1 class="w-title">Cycle tracker</h1>
<span class="w-private"><svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="7" width="9" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" fill="none" stroke="currentColor" stroke-width="1.4"/></svg> Optional and private</span>
''',
         r'''{% block title %}Cycle tracker · Wellness{% endblock %}
{% block content %}
<span class="cy-page" hidden></span>
<h1 class="w-title">Cycle tracker</h1>
<span class="w-private"><svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="7" width="9" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" fill="none" stroke="currentColor" stroke-width="1.4"/></svg> Optional and private</span>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_log.html'), [
        (r'''{% extends "wellness/base.html" %}
{% comment %} CY-1, 30 Oct 2026 - log a day: flow, symptoms, pain, a private note. Everything optional; an empty day is removed. {% endcomment %}
{% block title %}Log a day · Cycle · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:cycle' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Cycle</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
<form method="post" style="display:flex;flex-direction:column;gap:16px">
  {% csrf_token %}
  <input type="hidden" name="date" value="{{ day|date:'Y-m-d' }}">
  <div style="display:flex;flex-direction:column;gap:2px">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
      <a class="w-small" href="?date={{ yesterday }}" aria-label="The day before" style="min-width:44px;min-height:44px;display:flex;align-items:center">‹ Day before</a>
''',
         r'''{% extends "wellness/base.html" %}
{% comment %} CY-1, 30 Oct 2026 - log a day: flow, symptoms, pain, a private note. Everything optional; an empty day is removed. CY-5, 17 Nov 2026 - icon tiles by group (the approved redesign); the same fields as before. {% endcomment %}
{% block title %}Log a day · Cycle · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:cycle' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Cycle</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
<span class="cy-page" hidden></span>
<form method="post" style="display:flex;flex-direction:column;gap:16px" data-cy-tiles>
  {% csrf_token %}
  <input type="hidden" name="date" value="{{ day|date:'Y-m-d' }}">
  <div style="display:flex;flex-direction:column;gap:4px">
    {% comment %} CY-5, 17 Nov 2026 - the week's days as a strip; tap one to log it. {% endcomment %}
    <nav class="cy-week" aria-label="Days this week">
      {% for w in week %}<a href="?date={{ w.date }}" class="{% if w.on %}on{% endif %}{% if w.flow %} f-{{ w.flow }}{% endif %}{% if w.logged %} logged{% endif %}"{% if w.on %} aria-current="date"{% endif %}><span>{{ w.dow }}</span><b>{{ w.n }}</b></a>{% endfor %}
    </nav>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
      <a class="w-small" href="?date={{ yesterday }}" aria-label="The day before" style="min-width:44px;min-height:44px;display:flex;align-items:center">‹ Day before</a>
'''),
        (r'''  </div>

  <section class="w-card" aria-labelledby="flow-h">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <h2 class="w-h2" id="flow-h">Period</h2>
      {% if starting %}<span class="w-small w-quiet">Started this day</span>{% endif %}
    </div>
    <div class="w-flow" role="radiogroup" aria-labelledby="flow-h">
      {% for key, label in flows %}
      <label><input type="radio" name="flow" value="{{ key }}"{% if e.flow == key %} checked{% endif %}><span><i>{% if key == 'spotting' %}<b style="width:6px;height:6px"></b>{% elif key == 'light' %}<b></b>{% elif key == 'medium' %}<b></b><b></b>{% else %}<b></b><b></b><b></b>{% endif %}</i>{{ label }}</span></label>
      {% endfor %}
    </div>
    <label class="w-small w-quiet" style="display:flex;align-items:center;gap:8px;min-height:44px"><input class="w-radio" type="radio" name="flow" value=""{% if not e.flow %} checked{% endif %}> No bleeding</label>
  </section>

  <section class="w-card" aria-labelledby="sym-h">
    <h2 class="w-h2" id="sym-h">Anything else? <span class="w-small w-quiet" style="font-weight:400">Optional</span></h2>
    <div class="w-chips w-sym">
      {% for key, label in symptoms %}
      <label class="w-chip"><input type="checkbox" name="sym" value="{{ key }}"{% if key in e.sym %} checked{% endif %}><span>{{ label }}</span></label>
      {% endfor %}
    </div>
  </section>

  {% comment %} CY-3, 31 Oct 2026 - only what is switched on in the tracker's settings. {% endcomment %}
  {% if 'mood' in track %}
  <section class="w-card" aria-labelledby="mood-h"><h2 class="w-h2" id="mood-h">Mood</h2>
    <div class="w-chips">{% for k, label in moods %}<label class="w-chip"><input type="radio" name="mood" value="{{ k }}"{% if e.mood == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'energy' in track %}
  <section class="w-card" aria-labelledby="energy-h"><h2 class="w-h2" id="energy-h">Energy</h2>
    <div class="w-chips">{% for k, label in energy %}<label class="w-chip"><input type="radio" name="energy" value="{{ k }}"{% if e.energy == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'sleep' in track %}
  <section class="w-card" aria-labelledby="sleep-h"><h2 class="w-h2" id="sleep-h">Sleep last night</h2>
    <div class="w-chips">{% for k, label in sleep %}<label class="w-chip"><input type="radio" name="sleep" value="{{ k }}"{% if e.sleep == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'discharge' in track %}
  <section class="w-card" aria-labelledby="dis-h"><h2 class="w-h2" id="dis-h">Discharge</h2>
    <div class="w-chips">{% for k, label in discharge %}<label class="w-chip"><input type="radio" name="discharge" value="{{ k }}"{% if e.discharge == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'tags' in track and my_tags %}
  <section class="w-card" aria-labelledby="tags-h"><h2 class="w-h2" id="tags-h">Your tags</h2>
    <div class="w-chips">{% for tg in my_tags %}<label class="w-chip"><input type="checkbox" name="tag" value="{{ tg }}"{% if tg in e.tags %} checked{% endif %}><span>{{ tg }}</span></label>{% endfor %}</div></section>
  {% endif %}

''',
         r'''  </div>

  <section class="w-card cy-group g-period" aria-labelledby="flow-h">
    <div class="cy-group-h">
      <h2 class="w-h2" id="flow-h">Period</h2>
      {% if starting %}<span class="w-small w-quiet">Started this day</span>{% endif %}
    </div>
    <div class="cy-tiles" role="radiogroup" aria-labelledby="flow-h">{% include "wellness/_cy_tiles.html" with tiles=T.flow name="flow" kind="radio" %}</div>
    <label class="w-small w-quiet" style="display:flex;align-items:center;gap:8px;min-height:44px"><input class="w-radio" type="radio" name="flow" value=""{% if not e.flow %} checked{% endif %}> No bleeding</label>
  </section>

  <section class="w-card cy-group g-feel" aria-labelledby="feel-h">
    <h2 class="w-h2" id="feel-h">Feelings</h2>
    {% if 'mood' in track %}<div class="cy-tiles" role="radiogroup" aria-label="Mood">{% include "wellness/_cy_tiles.html" with tiles=T.mood name="mood" kind="radio" %}</div>{% endif %}
    <div class="cy-tiles">{% include "wellness/_cy_tiles.html" with tiles=T.feel_sym name="sym" %}</div>
  </section>

  {% if 'energy' in track %}
  <section class="w-card cy-group g-energy" aria-labelledby="energy-h"><h2 class="w-h2" id="energy-h">Energy</h2>
    <div class="cy-tiles" role="radiogroup" aria-labelledby="energy-h">{% include "wellness/_cy_tiles.html" with tiles=T.energy name="energy" kind="radio" %}</div></section>
  {% endif %}

  <section class="w-card cy-group g-sleep" aria-labelledby="sleep-h">
    <h2 class="w-h2" id="sleep-h">{% if 'sleep' in track %}Sleep last night{% else %}Sleep{% endif %}</h2>
    {% if 'sleep' in track %}<div class="cy-tiles" role="radiogroup" aria-labelledby="sleep-h">{% include "wellness/_cy_tiles.html" with tiles=T.sleep name="sleep" kind="radio" %}</div>{% endif %}
    <div class="cy-tiles">{% include "wellness/_cy_tiles.html" with tiles=T.sleep_sym name="sym" %}</div>
  </section>

  {% if 'sex' in track %}
  <section class="w-card cy-group g-sex" aria-labelledby="sex-h">
    <div class="cy-group-h"><h2 class="w-h2" id="sex-h">Sex</h2><span class="w-small w-quiet">Only you</span></div>
    <div class="cy-tiles">{% include "wellness/_cy_tiles.html" with tiles=T.sex name="sex" %}</div>
  </section>
  {% endif %}

  <section class="w-card cy-group g-pain" aria-labelledby="sym-h">
    <div class="cy-group-h"><h2 class="w-h2" id="sym-h">Pain and body</h2><span class="w-small w-quiet">Optional</span></div>
    <div class="cy-tiles">{% include "wellness/_cy_tiles.html" with tiles=T.body_sym name="sym" %}</div>
  </section>

  {% if 'discharge' in track %}
  <section class="w-card cy-group g-discharge" aria-labelledby="dis-h"><h2 class="w-h2" id="dis-h">Discharge</h2>
    <div class="cy-tiles" role="radiogroup" aria-labelledby="dis-h">{% include "wellness/_cy_tiles.html" with tiles=T.discharge name="discharge" kind="radio" %}</div></section>
  {% endif %}
  {% if 'tags' in track and my_tags %}
  <section class="w-card cy-group g-tags" aria-labelledby="tags-h"><h2 class="w-h2" id="tags-h">Your tags</h2>
    <div class="cy-tiles">{% include "wellness/_cy_tiles.html" with tiles=T.tags name="tag" %}</div></section>
  {% endif %}

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_patterns.html'), [
        (r'''{% block top_left %}<a class="w-home" href="{% url 'wellness:cycle' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Cycle</a>{% endblock %}
{% block content %}
<h1 class="w-title">Your patterns</h1>

<section class="w-card" aria-labelledby="bars-h">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <h2 class="w-h2" id="bars-h">Last {{ bars|length|default:6 }} cycle{{ bars|length|pluralize }}</h2>
    <span class="w-small w-quiet">days</span>
  </div>
  {% if bars %}
  <div class="w-bars" role="img" aria-label="{{ bar_words }}">
    {% for b in bars %}
    <div>
      <span style="font-size:13px;font-weight:600">{{ b.len }}</span>
      <span class="bar" style="height:{{ b.h }}px"><i style="height:{{ b.p }}px"></i></span>
      <span class="w-small w-quiet" style="font-size:11px">{{ b.m }}</span>
    </div>
    {% endfor %}
  </div>
  <div class="w-legend"><span><i class="period"></i>Period days</span><span><i style="background:var(--w-sage-track)"></i>Rest of the cycle</span></div>
  <p class="w-small" style="margin:0">{{ bar_words }}</p>
  {% else %}
  <p class="w-quiet" style="margin:0">Your first full cycle appears here once your next period starts.</p>
  {% endif %}
</section>

<section class="w-card" aria-labelledby="around-h">
''',
         r'''{% block top_left %}<a class="w-home" href="{% url 'wellness:cycle' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Cycle</a>{% endblock %}
{% block content %}
<span class="cy-page" hidden></span>
<h1 class="w-title">Your patterns</h1>

{% comment %} CY-5, 17 Nov 2026 - Cycle history (the approved redesign, row 4): three tiles, then every cycle as a bar of its days. {% endcomment %}
{% if stats %}
<div class="cy-stats">
  <div><span>Cycle length</span><b>{{ stats.cycle }} days</b><span>usual: {{ stats.cycle_usual }}</span></div>
  <div><span>Period</span><b>{{ stats.period }} days</b><span>usual: {{ stats.period_usual }}</span></div>
  <div><span>Variation</span><b>± {{ stats.vary }} day{{ stats.vary|pluralize }}</b><span>{{ stats.vary_word }}</span></div>
</div>
{% endif %}
{% if history %}
<section class="w-card" aria-labelledby="hist-h" data-cycle-history>
  <h2 class="w-h2" id="hist-h">Cycle history</h2>
  {% for h in history %}
  <div class="cy-hist">
    <div class="cy-hist-top"><span>{{ h.label }}</span><b>{{ h.side }}</b></div>
    <div class="cy-hist-bar" style="width:{{ h.w }}%" role="img" aria-label="{{ h.label }}, {{ h.side }}">{% for c in h.cells %}<i class="{{ c }}"></i>{% endfor %}</div>
  </div>
  {% endfor %}
  {% if bar_words %}<p class="w-small" style="margin:0">{{ bar_words }}</p>{% else %}<p class="w-small w-quiet" style="margin:0">Your first full cycle appears here once your next period starts.</p>{% endif %}
  <div class="cy-flowkey cy-small"><span><i class="f-medium"></i>Period, in its shades</span>{% if s.fertile %}<span><i class="fert"></i>Fertile estimate</span><span><i class="ov"></i>Likely ovulation</span>{% endif %}</div>
</section>
{% endif %}

<section class="w-card" aria-labelledby="around-h">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_report.html'), [
        (r'''    <tbody>
    {% for row in r.rows %}
    <tr><td>{{ row.start|date:"j M Y" }}</td><td>{% if row.length %}{{ row.length }} d{% else %}current{% endif %}</td><td>{{ row.period }} d</td><td>{% if row.heaviest %}{{ row.heaviest|capfirst }}{% else %}-{% endif %}</td><td>{{ row.heavy }}</td><td>{% if row.pain %}{{ row.pain }}/10{% else %}-{% endif %}</td><td>{{ row.common|join:", "|default:"-" }}</td></tr>
    {% endfor %}
    </tbody>
''',
         r'''    <tbody>
    {% for row in r.rows %}
    <tr><td>{{ row.start|date:"j M Y" }}</td><td>{% if row.length %}{{ row.length }} d{% else %}current{% endif %}</td><td>{{ row.period }} d</td><td>{% if row.heaviest %}{{ row.heaviest_name }}{% else %}-{% endif %}</td><td>{{ row.heavy }}</td><td>{% if row.pain %}{{ row.pain }}/10{% else %}-{% endif %}</td><td>{{ row.common|join:", "|default:"-" }}</td></tr>
    {% endfor %}
    </tbody>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_settings.html'), [
        (r'''{% block tabs %}{% endblock %}
{% block content %}
<h1 class="w-title">Cycle settings</h1>

''',
         r'''{% block tabs %}{% endblock %}
{% block content %}
<span class="cy-page" hidden></span>
<h1 class="w-title">Cycle settings</h1>

'''),
        (r'''  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="remind" value="1"{% if prefs.remind %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Remind me a day before it is expected<br><span class="w-small w-quiet">The reminder only says "A Wellness reminder", on the phones you turned reminders on for.</span></span></label>
  {% comment %} CY-3, 31 Oct 2026 - a nudge to log, a daily pill reminder, more to log, your own tags. {% endcomment %}
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="nudge" value="1"{% if prefs.nudge %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Nudge me to log once it is due<br><span class="w-small w-quiet">If the expected days have begun and nothing is logged, one gentle "A Wellness reminder" in the morning.</span></span></label>
  <label style="display:flex;flex-direction:column;gap:6px;font-size:15px"><span>A daily pill reminder at <span class="w-small w-quiet">(optional)</span></span><input class="w-input" type="time" name="pill_at" value="{{ prefs.pill_at }}" style="max-width:160px"><span class="w-small w-quiet">It says only "A Wellness reminder". Leave it empty for none.</span></label>
  <fieldset style="border:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px">
    <legend class="w-h2" style="margin-bottom:8px">More to log <span class="w-small w-quiet" style="font-weight:400">optional</span></legend>
    <p class="w-small w-quiet" style="margin:0 0 4px">Each one adds a short question to Log today, and shows in Patterns.</p>
    {% for key, label in track_opts %}
    <label class="w-toggle"><span>{{ label }}</span><input type="checkbox" name="track" value="{{ key }}"{% if key in tracked %} checked{% endif %}></label>
''',
         r'''  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
  {% comment %} CY-5, 17 Nov 2026 - the likely ovulation day, with the fertile estimate (Demetri: "Ovulation Days (as suggested)"). {% endcomment %}
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px;padding-left:32px"><input type="checkbox" name="ovulation" value="1"{% if prefs.ovulation %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Also show the likely ovulation day<br><span class="w-small w-quiet">A dark blue day inside the fertile estimate, about 14 days before the next expected period. Only with the fertile estimate on. {{ fertile_label }}</span></span></label>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="remind" value="1"{% if prefs.remind %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Remind me a day before it is expected<br><span class="w-small w-quiet">The reminder only says "A Wellness reminder", on the phones you turned reminders on for.</span></span></label>
  {% comment %} CY-3, 31 Oct 2026 - a nudge to log, a daily pill reminder, more to log, your own tags. {% endcomment %}
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="nudge" value="1"{% if prefs.nudge %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Nudge me to log once it is due<br><span class="w-small w-quiet">If the expected days have begun and nothing is logged, one gentle "A Wellness reminder" in the morning.</span></span></label>
  <label style="display:flex;flex-direction:column;gap:6px;font-size:15px"><span>A daily pill reminder at <span class="w-small w-quiet">(optional)</span></span><input class="w-input" type="time" name="pill_at" value="{{ prefs.pill_at }}" style="max-width:160px"><span class="w-small w-quiet">It says only "A Wellness reminder". Leave it empty for none.</span></label>
  <fieldset style="border:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px">
    <legend class="w-h2" style="margin-bottom:8px">More to log <span class="w-small w-quiet" style="font-weight:400">optional</span></legend>
    <p class="w-small w-quiet" style="margin:0 0 4px">Each one adds a short question to Log today, and shows in Patterns. Sex stays inside Log today: it is never in a day's summary, the doctor report or anything sent.</p>
    {% for key, label in track_opts %}
    <label class="w-toggle"><span>{{ label }}</span><input type="checkbox" name="track" value="{{ key }}"{% if key in tracked %} checked{% endif %}></label>
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# PT-2, 12 Nov 2026 - the card's lines and the recipe page.
# PT-4, 13 Nov 2026 - the greeting page.
SW_VERSION = 'wl25-1'


''',
         r'''# PT-2, 12 Nov 2026 - the card's lines and the recipe page.
# PT-4, 13 Nov 2026 - the greeting page.
# CY-5, 17 Nov 2026 - the Cycle Tracker redesign.
SW_VERSION = 'wl26-1'


'''),
    ]),
    (os.path.join('wellness', 'views_cycle.py'), [
        (r'''    next_m = (first + dt.timedelta(days=32)).replace(day=1)
    big, small = C.headline(s)
    return render(request, 'wellness/cycle.html', {
        'tab': 'cycle',
        's': s,
''',
         r'''    next_m = (first + dt.timedelta(days=32)).replace(day=1)
    big, small = C.headline(s)
    # CY-5, 17 Nov 2026 - the big ring, and a tapped day's summary.
    picked = None
    raw = request.GET.get('d', '')
    try:
        pd = dt.date.fromisoformat(raw) if raw else None
    except ValueError:
        pd = None
    if pd and pd <= today and pd.isoformat() in days:
        ps = [p[0] for p in C.periods(days) if p[0] <= pd]
        picked = {'date': pd, 'when': C._when(pd),
                  'day': (pd - ps[-1]).days + 1 if ps else None,
                  'words': C.day_words(days[pd.isoformat()]) or
                  'Something private logged'}
    ring_pms = C.pms(days, s['cycles']) if s.get('window') else None
    return render(request, 'wellness/cycle.html', {
        'wheel': C.wheel(s, days, today, ring_pms),
        'ring_pms': ring_pms,
        'picked': picked,
        'tab': 'cycle',
        's': s,
'''),
        (r'''        'moods': C.MOODS, 'energy': C.ENERGY, 'sleep': C.SLEEP,
        'discharge': C.DISCHARGE, 'my_tags': list(prefs.get('tags') or ()),
    })


''',
         r'''        'moods': C.MOODS, 'energy': C.ENERGY, 'sleep': C.SLEEP,
        'discharge': C.DISCHARGE, 'my_tags': list(prefs.get('tags') or ()),
        # CY-5 - the icon tiles and the week strip.
        'T': _groups(e, prefs),
        'week': _week(day, today, days),
    })


# CY-5, 17 Nov 2026 - Log a day as icon tiles, grouped (the approved
# redesign, row 3). The same fields and names as before - only the look
# changes - so nothing already logged moves.
FEEL_SYM = ('mood_swings', 'irritable', 'anxious', 'tearful', 'focus')
SLEEP_SYM = ('poor_sleep',)


def _tile(value, label, picked, family=''):
    from . import cycle_icons as IC
    return {'value': value, 'label': label, 'on': picked,
            'svg': IC.icon(value, family)}


def _groups(e, prefs):
    """The tiles for each field, by the name the form posts. Every
    symptom is always offered (so nothing logged before is dropped on
    save), the perimenopause ones in that mode or once logged."""
    sym = set(e.get('sym') or ())
    names = dict(C.SYMPTOMS + C.PERI_SYMPTOMS)
    body = [k for k, _n in C.SYMPTOMS if k not in FEEL_SYM + SLEEP_SYM +
            ('low_mood',)]
    body += [k for k, _n in C.PERI_SYMPTOMS
             if prefs.get('mode') == 'perimenopause' or k in sym]
    one = lambda field, opts, fam='': [            # noqa: E731
        _tile(k, n, e.get(field) == k, fam) for k, n in opts]
    return {
        'flow': one('flow', C.FLOWS, 'flow'),
        'mood': one('mood', C.MOODS),
        'feel_sym': [_tile(k, names[k], k in sym)
                     for k in ('low_mood',) + FEEL_SYM],
        'energy': one('energy', C.ENERGY, 'energy'),
        'sleep': one('sleep', C.SLEEP, 'sleep'),
        'sleep_sym': [_tile(k, names[k], k in sym) for k in SLEEP_SYM],
        'sex': [_tile(k, n, k in (e.get('sex') or ())) for k, n in C.SEX],
        'body_sym': [_tile(k, names[k], k in sym) for k in body],
        'discharge': one('discharge', C.DISCHARGE),
        'tags': [_tile(t, t, t in (e.get('tags') or ()), 'tag')
                 for t in (prefs.get('tags') or ())],
    }


def _week(day, today, days):
    """Seven days around the one being logged, none after today."""
    last = min(today, day + dt.timedelta(days=3))
    first = last - dt.timedelta(days=6)
    out = []
    d = first
    while d <= last:
        out.append({'date': d.isoformat(), 'dow': d.strftime('%a')[0],
                    'n': d.day, 'on': d == day,
                    'logged': d.isoformat() in days,
                    'flow': (days.get(d.isoformat()) or {}).get('flow', '')})
        d += dt.timedelta(days=1)
    return out


'''),
        (r'''            return redirect('wellness:cycle')
        prefs['fertile'] = bool(request.POST.get('fertile'))
        # CY-3 - more to log, your own tags, the pill time, the nudge.
        prefs['track'] = [k for k in request.POST.getlist('track')
''',
         r'''            return redirect('wellness:cycle')
        prefs['fertile'] = bool(request.POST.get('fertile'))
        # CY-5 - the likely ovulation day goes with the fertile estimate.
        prefs['ovulation'] = prefs['fertile'] and \
            bool(request.POST.get('ovulation'))
        # CY-3 - more to log, your own tags, the pill time, the nudge.
        prefs['track'] = [k for k in request.POST.getlist('track')
'''),
        (r'''        'tab': 'cycle',
        's': s,
        'bars': bars,
        'bar_words': ('Your cycles run %s days and your periods %s.'
''',
         r'''        'tab': 'cycle',
        's': s,
        # CY-5, 17 Nov 2026 - Cycle history: three tiles, every cycle a bar.
        'stats': C.stats(s['cycles']),
        'history': C.history(days, s['cycles'], s,
                             fertile=bool(prefs.get('fertile')) and
                             prefs['mode'] == 'normal'),
        'bars': bars,
        'bar_words': ('Your cycles run %s days and your periods %s.'
'''),
    ]),
]


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
    raise SystemExit('CY-5 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_cycle_look.py'" in read(pq):
        print('CY-5 already applied.')
        return 0
    if "'test_quotes.py'" not in read(pq):
        refuse('QL-1 (apply_quotes_one.py, Release 97) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('CY-5 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CY-5 applied - the Cycle Tracker redesign.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
