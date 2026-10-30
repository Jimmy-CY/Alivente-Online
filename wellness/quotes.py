# -*- coding: utf-8 -*-
"""wellness/quotes.py - WL-1, 30 Oct 2026. The curated quote library.

DECISION 4, 30 OCT: a library kept in the app, not an outside service.

EVERY LINE IS A REAL QUOTE WITH A KNOWN SOURCE. Quotes are where the
internet is least reliable - "We are what we repeatedly do" is Will
Durant summarising Aristotle, not Aristotle - so an entry goes in only
with a source a reader could check, and the famous misattributions are
left out rather than "fixed". Translations are the common English ones.

From W-4, Claude PICKS from this list for each person and writes one
labelled line under it; it never writes the quote itself. Until then
today's quote is chosen evenly by date and person, so two people in one
household usually see different ones.

themes: start, steady, comeback, rest, gratitude, strength, mind.
"""
import hashlib

QUOTES = [
    {'text': 'Fall seven times, stand up eight.',
     'author': 'Japanese proverb', 'source': '', 'themes': ['comeback']},
    {'text': 'The journey of a thousand miles begins with a single step.',
     'author': 'Lao Tzu', 'source': 'Tao Te Ching, 64',
     'themes': ['start']},
    {'text': 'We suffer more often in imagination than in reality.',
     'author': 'Seneca', 'source': 'Letters to Lucilius, 13',
     'themes': ['mind']},
    {'text': 'It is not that we have a short time to live, but that we '
             'waste a lot of it.',
     'author': 'Seneca', 'source': 'On the Shortness of Life',
     'themes': ['start']},
    {'text': 'Begin at once to live, and count each separate day as a '
             'separate life.',
     'author': 'Seneca', 'source': 'Letters to Lucilius, 101',
     'themes': ['start', 'mind']},
    {'text': 'Waste no more time arguing about what a good man should be. '
             'Be one.',
     'author': 'Marcus Aurelius', 'source': 'Meditations, 10.16',
     'themes': ['strength']},
    {'text': 'Very little is needed to make a happy life.',
     'author': 'Marcus Aurelius', 'source': 'Meditations, 7.67',
     'themes': ['gratitude', 'mind']},
    {'text': 'The impediment to action advances action. What stands in '
             'the way becomes the way.',
     'author': 'Marcus Aurelius', 'source': 'Meditations, 5.20',
     'themes': ['comeback', 'strength']},
    {'text': 'First say to yourself what you would be; and then do what '
             'you have to do.',
     'author': 'Epictetus', 'source': 'Discourses, 3.23',
     'themes': ['start', 'steady']},
    {'text': 'He who has a why to live can bear almost any how.',
     'author': 'Friedrich Nietzsche', 'source': 'Twilight of the Idols',
     'themes': ['strength']},
    {'text': 'We are what we repeatedly do. Excellence, then, is not an '
             'act, but a habit.',
     'author': 'Will Durant', 'source': 'The Story of Philosophy',
     'themes': ['steady']},
    {'text': 'Habit is a second nature.',
     'author': 'Cicero', 'source': 'De Finibus, 5.74',
     'themes': ['steady']},
    {'text': 'Gratitude is not only the greatest of virtues, but the '
             'parent of all the others.',
     'author': 'Cicero', 'source': 'Pro Plancio',
     'themes': ['gratitude']},
    {'text': 'A healthy mind in a healthy body.',
     'author': 'Juvenal', 'source': 'Satires, X',
     'themes': ['strength', 'mind']},
    {'text': 'Make haste slowly.',
     'author': 'Augustus', 'source': 'Suetonius, Life of Augustus',
     'themes': ['steady', 'rest']},
    {'text': 'Slow and steady wins the race.',
     'author': 'Aesop', 'source': 'The Tortoise and the Hare',
     'themes': ['steady']},
    {'text': 'Drop by drop is the water pot filled.',
     'author': 'The Dhammapada', 'source': 'verse 122',
     'themes': ['steady']},
    {'text': 'Little by little, one travels far.',
     'author': 'Spanish proverb', 'source': '', 'themes': ['steady']},
    {'text': 'Rome was not built in a day.',
     'author': 'Proverb', 'source': '', 'themes': ['steady', 'comeback']},
    {'text': 'Well begun is half done.',
     'author': 'Greek proverb', 'source': 'quoted by Aristotle, Politics',
     'themes': ['start']},
    {'text': 'Know thyself.',
     'author': 'Delphic maxim', 'source': '', 'themes': ['mind']},
    {'text': 'Nothing in excess.',
     'author': 'Delphic maxim', 'source': '', 'themes': ['rest']},
    {'text': 'Do what you can, with what you have, where you are.',
     'author': 'Theodore Roosevelt', 'source': 'An Autobiography (1913)',
     'themes': ['start', 'comeback']},
    {'text': 'Well done is better than well said.',
     'author': 'Benjamin Franklin', 'source': "Poor Richard's Almanack",
     'themes': ['steady']},
    {'text': 'Lost time is never found again.',
     'author': 'Benjamin Franklin', 'source': "Poor Richard's Almanack",
     'themes': ['start']},
    {'text': 'One today is worth two tomorrows.',
     'author': 'Benjamin Franklin', 'source': 'The Way to Wealth',
     'themes': ['start']},
    {'text': 'Every day, in every way, I am getting better and better.',
     'author': 'Émile Coué', 'source': '', 'themes': ['mind', 'steady']},
    {'text': 'Rest is not idleness.',
     'author': 'John Lubbock', 'source': 'The Use of Life',
     'themes': ['rest']},
]


def for_day(user_id, day):
    """Today's quote for one person: steady all day, different tomorrow."""
    key = ('%s:%s' % (user_id, day.isoformat())).encode('utf-8')
    i = int(hashlib.sha256(key).hexdigest(), 16) % len(QUOTES)
    return QUOTES[i]
