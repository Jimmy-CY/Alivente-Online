# -*- coding: utf-8 -*-
"""SP-1, 12 Nov 2026 - how many requests Alivente can answer at once.

Gunicorn reads this file by itself when it starts in this folder, so the
start command does not change. Before this file it ran ONE worker: a page,
its photos and any background call queued behind each other.

Three workers answer three requests at the same time. Each is a separate
process with its own database connection, so nothing is shared between
them. Railway's WEB_CONCURRENCY, if ever set, wins.
"""
import os

workers = int(os.environ.get('WEB_CONCURRENCY', '3'))
timeout = 30
