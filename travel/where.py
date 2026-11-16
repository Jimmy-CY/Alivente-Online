# -*- coding: utf-8 -*-
"""travel/where.py - TR-5, 16 Nov 2026. Which country a booking is in.

Demetri, 16 Nov, looking at "Greece, Cyprus, Paphos" on a Greece - Ireland
trip: the bookings that came in before Release 85 never recorded their
country, so Ireland was missing; and "Don't keep home countries in" -
Cyprus was only there because the flights leave from and come back to
Larnaca.

country_of(booking) answers from what the booking already says, with no
call out: its own country (read from the email since R85), else a country
named in its address or places, else the airport code in its destination
("Dublin (DUB)"), else a city it names. A flight is where it lands; every
other booking is where it is.

HOME is the family's own country - Cyprus unless TRAVEL_HOME_COUNTRY says
otherwise. It is left out of a trip's countries unless the trip has no
other (a weekend in Paphos is still in Cyprus).
"""
import os
import re

HOME = os.environ.get('TRAVEL_HOME_COUNTRY', 'Cyprus')

COUNTRIES = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Argentina',
    'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain',
    'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Bhutan',
    'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei',
    'Bulgaria', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Chile',
    'China', 'Colombia', 'Costa Rica', 'Croatia', 'Cuba', 'Cyprus',
    'Czech Republic', 'Denmark', 'Dominican Republic', 'Ecuador', 'Egypt',
    'Estonia', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Georgia',
    'Germany', 'Ghana', 'Greece', 'Guatemala', 'Hong Kong', 'Hungary',
    'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel',
    'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo',
    'Kuwait', 'Latvia', 'Lebanon', 'Liechtenstein', 'Lithuania',
    'Luxembourg', 'Madagascar', 'Malaysia', 'Maldives', 'Malta',
    'Mauritius', 'Mexico', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro',
    'Morocco', 'Mozambique', 'Namibia', 'Nepal', 'Netherlands',
    'New Zealand', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
    'Pakistan', 'Panama', 'Peru', 'Philippines', 'Poland', 'Portugal',
    'Qatar', 'Romania', 'Russia', 'Rwanda', 'San Marino', 'Saudi Arabia',
    'Senegal', 'Serbia', 'Seychelles', 'Singapore', 'Slovakia', 'Slovenia',
    'South Africa', 'South Korea', 'Spain', 'Sri Lanka', 'Sweden',
    'Switzerland', 'Taiwan', 'Tanzania', 'Thailand', 'Tunisia', 'Turkey',
    'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom',
    'United States', 'Uruguay', 'Uzbekistan', 'Vatican City', 'Venezuela',
    'Vietnam', 'Zambia', 'Zimbabwe',
]

# Other ways an address or an email writes a country.
ALIASES = {
    'uk': 'United Kingdom', 'great britain': 'United Kingdom',
    'england': 'United Kingdom', 'scotland': 'United Kingdom',
    'wales': 'United Kingdom', 'northern ireland': 'United Kingdom',
    'usa': 'United States', 'united states of america': 'United States',
    'uae': 'United Arab Emirates',
    'holland': 'Netherlands', 'the netherlands': 'Netherlands',
    'czechia': 'Czech Republic', 'republic of ireland': 'Ireland',
    'eire': 'Ireland', 'hellas': 'Greece', 'ελλάδα': 'Greece',
    'ελλαδα': 'Greece', 'κύπρος': 'Cyprus', 'κυπρος': 'Cyprus',
    'españa': 'Spain', 'espana': 'Spain', 'italia': 'Italy',
    'deutschland': 'Germany', 'österreich': 'Austria',
    'osterreich': 'Austria', 'schweiz': 'Switzerland', 'suisse': 'Switzerland',
    'türkiye': 'Turkey', 'turkiye': 'Turkey', 'korea': 'South Korea',
    'macedonia': 'North Macedonia', 'vatican': 'Vatican City',
}

# Airports by IATA code - where a flight lands.
AIRPORTS = {
    'LCA': ('Larnaca', 'Cyprus'), 'PFO': ('Paphos', 'Cyprus'),
    'ATH': ('Athens', 'Greece'), 'SKG': ('Thessaloniki', 'Greece'),
    'HER': ('Heraklion', 'Greece'), 'CHQ': ('Chania', 'Greece'),
    'RHO': ('Rhodes', 'Greece'), 'JMK': ('Mykonos', 'Greece'),
    'JTR': ('Santorini', 'Greece'), 'CFU': ('Corfu', 'Greece'),
    'KGS': ('Kos', 'Greece'), 'ZTH': ('Zakynthos', 'Greece'),
    'DUB': ('Dublin', 'Ireland'), 'SNN': ('Shannon', 'Ireland'),
    'ORK': ('Cork', 'Ireland'), 'NOC': ('Knock', 'Ireland'),
    'LHR': ('London', 'United Kingdom'), 'LGW': ('London', 'United Kingdom'),
    'STN': ('London', 'United Kingdom'), 'LTN': ('London', 'United Kingdom'),
    'LCY': ('London', 'United Kingdom'), 'MAN': ('Manchester',
                                                  'United Kingdom'),
    'EDI': ('Edinburgh', 'United Kingdom'), 'BHX': ('Birmingham',
                                                     'United Kingdom'),
    'BFS': ('Belfast', 'United Kingdom'), 'GLA': ('Glasgow',
                                                   'United Kingdom'),
    'BRS': ('Bristol', 'United Kingdom'),
    'CDG': ('Paris', 'France'), 'ORY': ('Paris', 'France'),
    'NCE': ('Nice', 'France'), 'LYS': ('Lyon', 'France'),
    'MRS': ('Marseille', 'France'), 'BOD': ('Bordeaux', 'France'),
    'FRA': ('Frankfurt', 'Germany'), 'MUC': ('Munich', 'Germany'),
    'BER': ('Berlin', 'Germany'), 'DUS': ('Dusseldorf', 'Germany'),
    'HAM': ('Hamburg', 'Germany'), 'CGN': ('Cologne', 'Germany'),
    'STR': ('Stuttgart', 'Germany'),
    'AMS': ('Amsterdam', 'Netherlands'), 'EIN': ('Eindhoven', 'Netherlands'),
    'BRU': ('Brussels', 'Belgium'), 'CRL': ('Charleroi', 'Belgium'),
    'LUX': ('Luxembourg', 'Luxembourg'),
    'ZRH': ('Zurich', 'Switzerland'), 'GVA': ('Geneva', 'Switzerland'),
    'BSL': ('Basel', 'Switzerland'),
    'VIE': ('Vienna', 'Austria'), 'SZG': ('Salzburg', 'Austria'),
    'INN': ('Innsbruck', 'Austria'),
    'FCO': ('Rome', 'Italy'), 'CIA': ('Rome', 'Italy'),
    'MXP': ('Milan', 'Italy'), 'LIN': ('Milan', 'Italy'),
    'BGY': ('Bergamo', 'Italy'), 'VCE': ('Venice', 'Italy'),
    'NAP': ('Naples', 'Italy'), 'FLR': ('Florence', 'Italy'),
    'PSA': ('Pisa', 'Italy'), 'BLQ': ('Bologna', 'Italy'),
    'CTA': ('Catania', 'Italy'), 'PMO': ('Palermo', 'Italy'),
    'BRI': ('Bari', 'Italy'), 'CAG': ('Cagliari', 'Italy'),
    'MAD': ('Madrid', 'Spain'), 'BCN': ('Barcelona', 'Spain'),
    'AGP': ('Malaga', 'Spain'), 'PMI': ('Palma', 'Spain'),
    'ALC': ('Alicante', 'Spain'), 'VLC': ('Valencia', 'Spain'),
    'SVQ': ('Seville', 'Spain'), 'BIO': ('Bilbao', 'Spain'),
    'IBZ': ('Ibiza', 'Spain'), 'TFS': ('Tenerife', 'Spain'),
    'LPA': ('Gran Canaria', 'Spain'),
    'LIS': ('Lisbon', 'Portugal'), 'OPO': ('Porto', 'Portugal'),
    'FAO': ('Faro', 'Portugal'), 'FNC': ('Funchal', 'Portugal'),
    'CPH': ('Copenhagen', 'Denmark'), 'ARN': ('Stockholm', 'Sweden'),
    'OSL': ('Oslo', 'Norway'), 'HEL': ('Helsinki', 'Finland'),
    'KEF': ('Reykjavik', 'Iceland'),
    'WAW': ('Warsaw', 'Poland'), 'KRK': ('Krakow', 'Poland'),
    'PRG': ('Prague', 'Czech Republic'), 'BUD': ('Budapest', 'Hungary'),
    'OTP': ('Bucharest', 'Romania'), 'SOF': ('Sofia', 'Bulgaria'),
    'BEG': ('Belgrade', 'Serbia'), 'ZAG': ('Zagreb', 'Croatia'),
    'SPU': ('Split', 'Croatia'), 'DBV': ('Dubrovnik', 'Croatia'),
    'LJU': ('Ljubljana', 'Slovenia'), 'TIA': ('Tirana', 'Albania'),
    'TGD': ('Podgorica', 'Montenegro'), 'TIV': ('Tivat', 'Montenegro'),
    'MLA': ('Malta', 'Malta'), 'RIX': ('Riga', 'Latvia'),
    'TLL': ('Tallinn', 'Estonia'), 'VNO': ('Vilnius', 'Lithuania'),
    'IST': ('Istanbul', 'Turkey'), 'SAW': ('Istanbul', 'Turkey'),
    'AYT': ('Antalya', 'Turkey'), 'ESB': ('Ankara', 'Turkey'),
    'TLV': ('Tel Aviv', 'Israel'), 'BEY': ('Beirut', 'Lebanon'),
    'AMM': ('Amman', 'Jordan'), 'CAI': ('Cairo', 'Egypt'),
    'HRG': ('Hurghada', 'Egypt'), 'SSH': ('Sharm el-Sheikh', 'Egypt'),
    'DXB': ('Dubai', 'United Arab Emirates'),
    'AUH': ('Abu Dhabi', 'United Arab Emirates'), 'DOH': ('Doha', 'Qatar'),
    'JNB': ('Johannesburg', 'South Africa'),
    'CPT': ('Cape Town', 'South Africa'), 'DUR': ('Durban', 'South Africa'),
    'JFK': ('New York', 'United States'), 'EWR': ('New York',
                                                   'United States'),
    'BOS': ('Boston', 'United States'), 'MIA': ('Miami', 'United States'),
    'LAX': ('Los Angeles', 'United States'),
    'SFO': ('San Francisco', 'United States'),
    'ORD': ('Chicago', 'United States'), 'YYZ': ('Toronto', 'Canada'),
    'YUL': ('Montreal', 'Canada'), 'BKK': ('Bangkok', 'Thailand'),
    'SIN': ('Singapore', 'Singapore'), 'HKG': ('Hong Kong', 'Hong Kong'),
    'NRT': ('Tokyo', 'Japan'), 'HND': ('Tokyo', 'Japan'),
    'SYD': ('Sydney', 'Australia'), 'MEL': ('Melbourne', 'Australia'),
    'MLE': ('Male', 'Maldives'), 'MRU': ('Mauritius', 'Mauritius'),
}

# Cities a booking may name without a country.
CITIES = {}
for _code, (_city, _country) in AIRPORTS.items():
    CITIES.setdefault(_city.lower(), _country)
CITIES.update({
    'galway': 'Ireland', 'limerick': 'Ireland', 'killarney': 'Ireland',
    'kilkenny': 'Ireland', 'nicosia': 'Cyprus', 'limassol': 'Cyprus',
    'ayia napa': 'Cyprus', 'protaras': 'Cyprus', 'piraeus': 'Greece',
    'nafplio': 'Greece', 'kalamata': 'Greece', 'delphi': 'Greece',
    'meteora': 'Greece', 'patras': 'Greece', 'oxford': 'United Kingdom',
    'cambridge': 'United Kingdom', 'windsor': 'United Kingdom',
    'ascot': 'United Kingdom', 'bath': 'United Kingdom',
    'york': 'United Kingdom', 'liverpool': 'United Kingdom',
    'lucerne': 'Switzerland', 'luzern': 'Switzerland',
    'interlaken': 'Switzerland', 'zermatt': 'Switzerland',
    'bern': 'Switzerland', 'lausanne': 'Switzerland',
    'granada': 'Spain', 'cordoba': 'Spain', 'toledo': 'Spain',
    'san sebastian': 'Spain', 'sintra': 'Portugal', 'cascais': 'Portugal',
    'verona': 'Italy', 'como': 'Italy', 'siena': 'Italy',
    'amalfi': 'Italy', 'sorrento': 'Italy', 'monaco': 'Monaco',
    'monte carlo': 'Monaco', 'cannes': 'France', 'avignon': 'France',
    'strasbourg': 'France', 'bruges': 'Belgium', 'ghent': 'Belgium',
    'antwerp': 'Belgium', 'rotterdam': 'Netherlands',
    'the hague': 'Netherlands', 'edinburgh': 'United Kingdom',
})

_NAMES = {c.lower(): c for c in COUNTRIES}
_NAMES.update(ALIASES)


def _words(text):
    return ' %s ' % ' '.join(re.findall(r'[^\W\d_]+', (text or '').lower()))


def named_country(text):
    """The country a piece of text names - the LAST one it names, as an
    address ends with its country ("..., Galway, Ireland")."""
    w = _words(text)
    best, at = '', -1
    for name, country in _NAMES.items():
        if len(name) < 3 and name != 'uk':
            continue
        i = w.rfind(' %s ' % name)
        if i > at:
            best, at = country, i
    return best


def named_city(text):
    w = _words(text)
    best, at = '', -1
    for name, country in CITIES.items():
        i = w.rfind(' %s ' % name)
        if i > at:
            best, at = country, i
    return best


def airport_country(text):
    """ "Dublin (DUB)" -> Ireland."""
    for code in re.findall(r'\b([A-Z]{3})\b', text or ''):
        if code in AIRPORTS:
            return AIRPORTS[code][1]
    return ''


def country_of(b):
    """The booking's country, from what it already says ('' if none)."""
    if (getattr(b, 'country', '') or '').strip():
        return _NAMES.get(b.country.strip().lower(), b.country.strip())
    flight = getattr(b, 'kind', '') in ('flight', 'train', 'ferry')
    dest = getattr(b, 'to_place', '') or ''
    places = [getattr(b, 'address', ''), getattr(b, 'city', ''), dest]
    if not flight:
        places.append(getattr(b, 'from_place', ''))
    for text in places:
        c = named_country(text)
        if c:
            return c
    c = airport_country(dest)
    if c:
        return c
    if not flight:
        c = airport_country(getattr(b, 'from_place', ''))
        if c:
            return c
    for text in [getattr(b, 'city', ''), dest, getattr(b, 'address', ''),
                 getattr(b, 'title', '')] + (
                     [] if flight else [getattr(b, 'from_place', '')]):
        c = named_city(text)
        if c:
            return c
    return ''


def is_home(country):
    return (country or '').strip().lower() == HOME.lower()
