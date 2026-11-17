# -*- coding: utf-8 -*-
"""wellness/cycle_icons.py - CY-5, 17 Nov 2026. The icon tiles of Log a
day, from the approved redesign (canvas "Cycle Tracker before and after",
row 3; Demetri, 17 Nov: "I am happy with the Cycle Tracking changes").

Our own simple line drawings on a 34 x 34 grid, drawn in currentColor so
the tile decides the colour. Inspired by the idea of Clue's tiles, not
copied from them. Constants only - nothing here comes from a person, so
the template may mark them safe.
"""

_S = ' fill="none" stroke="currentColor" stroke-width="2"'
_R = _S + ' stroke-linecap="round" stroke-linejoin="round"'


def _face(mouth, eyes='dots'):
    e = ('<circle cx="13" cy="14" r="1.6" fill="currentColor"/>'
         '<circle cx="21" cy="14" r="1.6" fill="currentColor"/>'
         if eyes == 'dots' else
         '<path d="M11.5 14.5h3M19.5 14.5h3"%s/>' % _R)
    return '<circle cx="17" cy="17" r="12"%s/>%s<path d="%s"%s/>' % (
        _S, e, mouth, _R)


ICONS = {
    # Feelings
    'great': _face('M10.5 19c3 5 10 5 13 0') +
    '<path d="M27 6l1 2 2 1-2 1-1 2-1-2-2-1 2-1z" fill="currentColor"/>',
    'good': _face('M11.5 19.5c3 4 8 4 11 0'),
    'okay': _face('M12 21h10'),
    'low': _face('M12 23c3-3.5 7-3.5 10 0'),
    'very_low': _face('M12 24c3-4 7-4 10 0') +
    '<path d="M12 18v2"%s/>' % _R,
    'mood_swings': '<path d="M6 12c4-5 8-5 11 0s7 5 11 0M6 22c4 5 8 5 11 0'
    's7-5 11 0"%s/>' % _R,
    'irritable': _face('M12 22c3-2 7-2 10 0', eyes='lines') +
    '<path d="M11 10l4 2M23 10l-4 2"%s/>' % _R,
    'anxious': _face('M12 22q2.5-2 5 0t5 0'),
    'tearful': _face('M12 23c3-3 7-3 10 0') +
    '<path d="M24 17c1.5 2 1.5 3.5 0 4.2c-1.5-.7-1.5-2.2 0-4.2z"'
    ' fill="currentColor"/>',
    'focus': '<circle cx="17" cy="17" r="11"%s/><circle cx="17" cy="17"'
    ' r="5"%s/><path d="M17 3v4M17 27v4M3 17h4M27 17h4"%s/>' % (_S, _S, _R),
    # Energy
    'e_low': '<rect x="5" y="11" width="22" height="12" rx="3"%s/><path'
    ' d="M29 15v4"%s/><rect x="8" y="14" width="5" height="6" rx="1"'
    ' fill="currentColor"/>' % (_S, _R),
    'e_steady': '<rect x="5" y="11" width="22" height="12" rx="3"%s/><path'
    ' d="M29 15v4"%s/><rect x="8" y="14" width="10" height="6" rx="1"'
    ' fill="currentColor"/>' % (_S, _R),
    'e_high': '<path d="M19 4L8 19h8l-2 11 11-15h-8z"%s/>' % _R,
    # Sleep
    's_poor': '<path d="M18 8a9 9 0 1 0 8 13A7 7 0 0 1 18 8z"%s/><path'
    ' d="M22 5h5l-5 5h5"%s/>' % (_R, _R),
    's_okay': '<path d="M20 6a10 10 0 1 0 8 15A8 8 0 0 1 20 6z"%s/>' % _R,
    's_good': '<path d="M20 6a10 10 0 1 0 8 15A8 8 0 0 1 20 6z"%s/><path'
    ' d="M26 6l1 2 2 1-2 1-1 2-1-2-2-1 2-1z" fill="currentColor"/>' % _R,
    'poor_sleep': '<path d="M5 13c3-3 6 3 9 0s6 3 9 0 6 3 6 3M5 21c3-3 6 3'
    ' 9 0s6 3 9 0 6 3 6 3"%s/>' % _R,
    # Sex
    'protected': '<path d="M17 4l10 4v8c0 7-5 11-10 13C12 27 7 23 7 16V8z"'
    '%s/><path d="M12 16l4 4 6-7"%s/>' % (_R, _R),
    'unprotected': '<path d="M17 28s-11-6.5-11-14a6 6 0 0 1 11-3.3A6 6 0 0'
    ' 1 28 14c0 7.5-11 14-11 14z"%s stroke-dasharray="3 3"/>' % _R,
    'none': '<circle cx="17" cy="17" r="11"%s/><path d="M9 25L25 9"%s/>'
    % (_S, _R),
    'high_drive': '<path d="M17 4c2 5 8 8 8 15a8 8 0 0 1-16 0c0-4 2-6 4-8 0'
    ' 3 1 4 3 5-1-5 0-9 1-12z"%s/>' % _R,
    'low_drive': '<path d="M17 28s-11-6.5-11-14a6 6 0 0 1 11-3.3A6 6 0 0 1'
    ' 28 14c0 7.5-11 14-11 14z"%s/><path d="M12 16h10"%s/>' % (_R, _R),
    # Pain and body
    'cramps': '<path d="M7 17c0-6 4-10 10-10s10 4 10 10-4 10-10 10"%s/>'
    '<path d="M12 20l3-4 3 4 3-4"%s/>' % (_R, _R),
    'headache': '<circle cx="17" cy="15" r="9"%s/><path d="M13 27h8M20'
    ' 9l-3 5h4l-3 5"%s/>' % (_S, _R),
    'bloating': '<ellipse cx="17" cy="18" rx="10" ry="8"%s/><circle'
    ' cx="13" cy="17" r="1.6" fill="currentColor"/><circle cx="20" cy="20"'
    ' r="1.2" fill="currentColor"/>' % _S,
    'tender': '<path d="M6 14c0 5 4 8 7 8s5-3 5-6M28 14c0 5-4 8-7 8"%s/>'
    '<circle cx="12" cy="17" r="1.4" fill="currentColor"/><circle cx="22"'
    ' cy="17" r="1.4" fill="currentColor"/>' % _R,
    'back': '<path d="M17 4v26"%s/><path d="M13 8h8M12 13h10M12 18h10M13'
    ' 23h8"%s/>' % (_R, _R),
    'pelvic_pain': '<path d="M6 10c3 0 5 2 6 5l5 8 5-8c1-3 3-5 6-5"%s/>'
    '<path d="M17 23v6"%s/>' % (_R, _R),
    'tired': '<circle cx="17" cy="17" r="12"%s/><path d="M11 15c1.5 1.5 3'
    ' 1.5 4.5 0M18.5 15c1.5 1.5 3 1.5 4.5 0M14 22h6"%s/>' % (_S, _R),
    'acne': '<circle cx="17" cy="17" r="12"%s/><circle cx="12" cy="13"'
    ' r="1.4" fill="currentColor"/><circle cx="21" cy="11" r="1.1"'
    ' fill="currentColor"/><circle cx="22" cy="20" r="1.4"'
    ' fill="currentColor"/><circle cx="14" cy="22" r="1.1"'
    ' fill="currentColor"/>' % _S,
    'cravings': '<path d="M9 13h16l-2 15H11z"%s/><path d="M13 13c0-4 2-7'
    ' 4-7s4 3 4 7"%s/>' % (_R, _R),
    'hungry': '<path d="M11 5v24M8 5v7a3 3 0 0 0 6 0V5M23 5c-3 2-4 6-4 10h4'
    'v14"%s/>' % _R,
    'nausea': '<circle cx="17" cy="17" r="12"%s/><path d="M11 14h4M19'
    ' 14h4M11 22q3-3 6 0t6 0"%s/>' % (_S, _R),
    'dizzy': '<path d="M17 17m-2 0a2 2 0 1 0 4 0a5 5 0 1 0-10 0a8 8 0 1 0 16'
    ' 0a11 11 0 1 0-22 0"%s/>' % _R,
    'constipation': '<rect x="7" y="8" width="20" height="18" rx="6"%s/>'
    '<path d="M12 17h10"%s/>' % (_S, _R),
    'diarrhoea': '<path d="M5 12c3-3 6 3 9 0s6 3 9 0 6 3 6 3M5 18c3-3 6 3'
    ' 9 0s6 3 9 0 6 3 6 3M5 24c3-3 6 3 9 0s6 3 9 0 6 3 6 3"%s/>' % _R,
    'swelling': '<path d="M10 6v10c0 6 3 12 9 12h2c3 0 5-2 5-5v-6"%s/><path'
    ' d="M14 6v9M18 6v9M22 8v9"%s/>' % (_R, _R),
    'low_mood': '<path d="M9 18a8 8 0 0 1 16 0"%s/><path d="M11 22v4M17'
    ' 22v6M23 22v4"%s/>' % (_R, _R),
    # Perimenopause
    'hot_flush': '<path d="M17 4c2 5 8 8 8 15a8 8 0 0 1-16 0c0-4 2-6 4-8 0'
    ' 3 1 4 3 5-1-5 0-9 1-12z"%s/>' % _R,
    'night_sweats': '<path d="M18 8a9 9 0 1 0 8 13A7 7 0 0 1 18 8z"%s/><path'
    ' d="M25 5c1.5 2 1.5 3.5 0 4.2c-1.5-.7-1.5-2.2 0-4.2z"'
    ' fill="currentColor"/>' % _R,
    'brain_fog': '<path d="M9 22a5 5 0 0 1 1-10 7 7 0 0 1 13-1 5 5 0 0 1 2'
    ' 11z"%s/><path d="M10 27h14"%s/>' % (_R, _R),
    'joint_aches': '<circle cx="11" cy="11" r="4"%s/><circle cx="23"'
    ' cy="23" r="4"%s/><path d="M14 14l6 6"%s/>' % (_S, _S, _R),
    'dryness': '<path d="M17 4c-6 9-9 13-9 18a9 9 0 0 0 18 0c0-5-3-9-9-18z"'
    '%s/><path d="M8 26L26 8"%s/>' % (_R, _R),
    'palpitations': '<path d="M4 18h6l3-7 4 14 3-9 2 2h8"%s/>' % _R,
    # Discharge
    'dry': '<circle cx="17" cy="17" r="11"%s stroke-dasharray="2 4"/>' % _R,
    'sticky': '<path d="M9 23c2-6 4-12 8-12s6 6 8 12"%s/>' % _R,
    'creamy': '<path d="M8 20c0-5 4-9 9-9s9 4 9 9z"%s/>' % _R,
    'watery': '<path d="M17 6c-5 7-7 10-7 14a7 7 0 0 0 14 0c0-4-2-7-7-14z"'
    '%s/>' % _R,
    'clear': '<path d="M8 12c3 0 6 4 9 4s6-4 9-4M8 22c3 0 6-4 9-4s6 4 9 4"'
    '%s/>' % _R,
    # Fallback, and your own tags
    'tag': '<path d="M6 7h11l11 11-10 10L7 17z"%s/><circle cx="12" cy="12"'
    ' r="1.8" fill="currentColor"/>' % _R,
    'dot': '<circle cx="17" cy="17" r="5" fill="currentColor"/>',
}

# A drop, filled to show how heavy - the Period tiles.
_DROP = 'M17 4 C 11 13, 7 18, 7 23 a10 10 0 0 0 20 0 c0-5-4-10-10-19z'
FILL = {'spotting': 0.18, 'light': 0.38, 'medium': 0.6, 'heavy': 0.82,
        'very_heavy': 1.0}


def drop(key):
    """The Period tile: a drop outline, filled from the bottom."""
    frac = FILL[key]
    y = 34 - 32 * frac
    cid = 'cyd-' + key
    return ('<defs><clipPath id="%s"><rect x="0" y="%.1f" width="34"'
            ' height="34"/></clipPath></defs><path d="%s"%s/><path d="%s"'
            ' fill="currentColor" clip-path="url(#%s)"/>'
            % (cid, y, _DROP, _R, _DROP, cid))


def icon(key, family=''):
    """The drawing for a tile. family 'energy', 'sleep' tell apart the
    words they share ('low', 'okay')."""
    if family == 'flow':
        return drop(key)
    if family == 'tag':
        return ICONS['tag']
    if family in ('energy', 'sleep'):
        key = family[0] + '_' + key
    return ICONS.get(key, ICONS['dot'])
