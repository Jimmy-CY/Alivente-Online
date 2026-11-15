# -*- coding: utf-8 -*-
"""PDF417 encoder - vendored from pdf417gen 0.8.1 (TR-3, 15 Nov 2026).

Copyright (c) 2016 Ivan Habunek. MIT License (the "PDF417-Py License"):
permission is granted, free of charge, to use, copy, modify, merge,
publish, distribute, sublicense and/or sell copies, provided this notice
is kept. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

Only the encoder is kept (no Pillow rendering, no command line); its
imports were made relative. travel/barcodes/__init__.py draws the SVG.
"""
from .encoding import encode

__all__ = ['encode']
