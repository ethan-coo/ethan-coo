#!/usr/bin/env python3
"""Sous-ensembles WOFF2 de Plus Jakarta Sans (la police de altheisagency.com) et DM Mono, SIL OFL 1.1.

À relancer seulement si un texte des cartes utilise un caractère absent du jeu ci-dessous.
Usage : python scripts/make_fonts.py <dossier contenant les .ttf de Google Fonts>
"""
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "àâäçéèêëîïôöùûüÿœæÀÂÇÉÈÊÎÔÙÛŒ«»’‘“”…·•–→↗↘←★✦°€×"


def build(src, out, axes=None):
    font = TTFont(os.path.join(SRC, src))
    if axes:
        font = instancer.instantiateVariableFont(font, axes, updateFontNames=False)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = ["*"]
    s = subset.Subsetter(opts)
    s.populate(text=CHARS)
    s.subset(font)
    font.flavor = "woff2"
    font.save(os.path.join(OUT, out))
    print(out, os.path.getsize(os.path.join(OUT, out)) // 1024, "Ko")


build("pjs.ttf", "jakarta-800.woff2", {"wght": 800})
build("pjs.ttf", "jakarta-600.woff2", {"wght": 600})
build("pjs.ttf", "jakarta-400.woff2", {"wght": 400})
build("pjs.ttf", "jakarta-300.woff2", {"wght": 300})
build("dmmono.ttf", "dmmono-400.woff2")
