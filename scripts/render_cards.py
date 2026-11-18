#!/usr/bin/env python3
"""
Dessine les cartes du profil GitHub en SVG animés, dans cards/.

Direction : celle de altheisagency.com (noir chaud, crème, spectre violet du cristal,
Plus Jakarta Sans serré, étiquettes mono entre crochets, anneau lumineux en forme de
cristal). Chaque carte est un SVG autonome affiché dans une balise <img> : GitHub n'y
autorise ni JavaScript ni requête externe, donc animations CSS et SMIL seulement, polices
et images embarquées en data URI.

Les chiffres d'activité viennent de data/contributions.json (fetch_contributions.py).
Les chiffres de l'agence sont ceux affichés sur altheisagency.com, à tenir à jour à la main.

STATIC=1 dessine chaque animation dans son état final (aperçu, capture).
"""
import base64
import datetime
import json
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data", "contributions.json")
STATIC = bool(os.environ.get("STATIC"))

# ---- chiffres de l'agence (altheisagency.com, section L'agence) -------------
SITES, IDENTITES, VIDEOS = "40", "20", "30"

# ---- jetons de altheisagency.com ------------------------------------------------
BG = "#0d0c0b"
CARD = "#161514"
CARD2 = "#1e1d1b"
LINE = "#272522"
LINE2 = "#2f2d2a"
CREAM = "#f1eee8"
MUTE = "#8d8982"
DIM = "#4d4a45"
V_CORE = "#9868fc"
V_SOFT = "#bc9cfc"
V_DEEP = "#6820fc"
V_ORCHID = "#d87cfc"
V_PALE = "#e4a4fc"
W = 880

SANS = "'Plus Jakarta Sans', 'Helvetica Neue', Arial, sans-serif"
MONO = "'DM Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
FONT_FILES = {
    "800": ("Plus Jakarta Sans", 800, "jakarta-800.woff2"),
    "600": ("Plus Jakarta Sans", 600, "jakarta-600.woff2"),
    "400": ("Plus Jakarta Sans", 400, "jakarta-400.woff2"),
    "300": ("Plus Jakarta Sans", 300, "jakarta-300.woff2"),
    "mono": ("DM Mono", 400, "dmmono-400.woff2"),
}

# le cristal à huit facettes (assets/logo/favicon.svg de altheisagency.com, repère 257 259 485 485)
CRYSTAL = [
    ("#bd9dff", "356,593 358,590 433,486 439,478 543,478 544,479 544,482 543,488 513,640 512,642 511,643 504,641 413,614 356,597"),
    ("#9c6bff", "535,640 544,594 559,518 568,473 569,472 588,457 624,429 646,412 650,409 653,408 654,411 654,600 568,631 543,640 537,642 535,641"),
    ("#9b6bff", "521,268 522,264 526,266 640,374 642,376 647,382 647,384 615,409 579,437 566,447 564,445"),
    ("#dd7dfc", "351,383 366,368 441,297 459,280 475,265 477,265 477,268 475,276 463,320 452,360 428,447 427,447 415,437 353,385"),
    ("#e7a7fd", "449,453 451,445 457,423 487,314 492,296 496,282 499,276 509,310 512,322 538,429 543,450 543,454 537,455 453,455 450,454"),
    ("#6b22ff", "345,407 346,407 352,412 389,443 408,459 415,465 419,469 409,483 349,566 346,570 345,571"),
    ("#9d6cfe", "373,625 374,625 381,627 405,634 452,648 502,663 508,665 495,731 493,739 492,739 487,735 433,684 377,631 373,627"),
    ("#de7efc", "518,727 520,716 529,671 530,669 532,667 540,664 612,638 615,637 615,638 608,645 570,681 535,714 519,729 518,728"),
]

MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
MOIS_COURT = ["jan", "fév", "mar", "avr", "mai", "juin", "juil", "août", "sep", "oct", "nov", "déc"]

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.2)}70%{opacity:1;transform:scale(1.2)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes facet{from{opacity:0;transform:scale(.55) rotate(-14deg)}to{opacity:1;transform:none}}
@keyframes float{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-9px) rotate(2.4deg)}}
@keyframes breathe{0%,100%{opacity:.55}50%{opacity:.95}}
@keyframes tile{0%{opacity:0;transform:translateY(40px) scale(.94)}60%{opacity:1;transform:translateY(-4px) scale(1.01)}100%{opacity:1;transform:none}}
@keyframes sweep{0%{transform:translateX(-200px) skewX(-18deg)}30%,100%{transform:translateX(520px) skewX(-18deg)}}
@keyframes roll{from{transform:translateY(56px)}to{transform:none}}
.r{opacity:0;transform-box:fill-box;animation:rise .9s cubic-bezier(.2,.7,.1,1) both}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .9s cubic-bezier(.2,.7,.1,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .45s ease-out both}
.live{animation:pulse 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.dr{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.2s cubic-bezier(.65,.05,.36,1) both}
.fc{opacity:0;transform-box:fill-box;transform-origin:center;animation:facet .9s cubic-bezier(.16,1,.3,1) both}
.fl{transform-box:fill-box;transform-origin:center;animation:float 7s ease-in-out infinite}
.br{animation:breathe 5s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:tile 1s cubic-bezier(.2,.8,.2,1) both}
.sw{animation:sweep 6s ease-in-out infinite}
.ro{transform-box:fill-box;animation:roll .9s cubic-bezier(.15,.8,.2,1) both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.nu,.dr,.fc,.fl,.br,.ti,.ro{animation:none!important;opacity:1!important;transform:none!important;stroke-dashoffset:0!important}.sw{display:none}}
"""
STATIC_CSS = (".r,.f,.g,.p,.live,.nu,.dr,.fc,.fl,.br,.ti,.ro{animation:none!important;opacity:1!important;"
              "transform:none!important;stroke-dashoffset:0!important}.sw{display:none}")

GAP = 12
COL = W / 3


def font_face(keys):
    out = []
    for k in keys:
        fam, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "".join(out)


def svg(w, h, body, fonts, label, left=0, right=0, bottom=GAP):
    """Carte w x h posée en x=left sur un fond transparent, avec les marges qui font tomber les rangées juste."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + (STATIC_CSS if STATIC else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{css}</style>{body}</svg>')


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print(f"cards/{name} ({len(content) // 1024} Ko)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines))


def tag(x, y, text, color=MUTE, size=11.5):
    """Étiquette mono entre crochets, comme les [ SECTIONS ] du site."""
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" letter-spacing="1.6" fill="{color}">'
            f'[ {escape(text.upper())} ]</text>')


def grad(id_, stops, x1=0, y1=0, x2=1, y2=0, extra=""):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {extra}>{s}</linearGradient>'


TEXT_GRAD = [(0, V_PALE), (0.55, V_CORE), (1, V_DEEP)]


def hull(points):
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def crystal_points():
    return [tuple(map(int, p.split(","))) for _, poly in CRYSTAL for p in poly.split()]


# ---- 1 · en-tête ----------------------------------------------------------------
def hero():
    h = 440  # 318 + 2 lignes + lien
    # l'anneau lumineux : le contour du cristal, agrandi, comme sur la page d'accueil du site
    pts = crystal_points()
    hp = hull(pts)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ccx, ccy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cx, cy, ring_h = 686, 222, 352
    k = ring_h / (max(ys) - min(ys))
    ring = "M" + " L".join(f"{cx + (x - ccx) * k:.1f},{cy + (y - ccy) * k:.1f}" for x, y in hp) + " Z"
    gk = 128 / (max(ys) - min(ys))  # cristal intérieur, 128 px de haut
    gem_tf = f"translate({cx:.1f} {cy:.1f}) scale({gk:.4f}) translate({-ccx:.1f} {-ccy:.1f})"
    facets = "".join(f'<polygon class="fc" {d(0.5 + i * 0.07)} fill="{c}" points="{p}"/>' for i, (c, p) in enumerate(CRYSTAL))
    glow = "".join(f'<polygon fill="{c}" points="{p}"/>' for c, p in CRYSTAL)
    spin = ("" if STATIC else
            f'<animateTransform attributeName="gradientTransform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
            f'dur="14s" repeatCount="indefinite"/>')
    shine = ("" if STATIC else
             '<animateTransform attributeName="gradientTransform" type="translate" values="-520 0;520 0;520 0" '
             'keyTimes="0;.4;1" dur="7s" begin="1.8s" repeatCount="indefinite"/>')
    sub = ["Fondateur d'Altheis, agence digitale sur la Côte d'Azur.",
           "Je conçois des sites, des vidéos et des outils sur mesure",
           "qui font vendre, du premier appel à la mise en ligne."]
    link_y = 318 + (len(sub) - 1) * 25 + 40
    body = f"""
<defs>
  <clipPath id="c"><rect width="{W}" height="{h}" rx="20"/></clipPath>
  <linearGradient id="rg" gradientUnits="userSpaceOnUse" x1="{cx - 180}" y1="{cy}" x2="{cx + 180}" y2="{cy}">
    <stop offset="0" stop-color="{V_DEEP}"/><stop offset=".4" stop-color="{V_CORE}"/>
    <stop offset=".75" stop-color="{V_ORCHID}"/><stop offset="1" stop-color="{V_PALE}"/>{spin}
  </linearGradient>
  <radialGradient id="halo" cx="{cx}" cy="{cy}" r="230" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset=".55" stop-color="{V_DEEP}" stop-opacity=".22"/>
    <stop offset="1" stop-color="{V_DEEP}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="nm" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="520" y2="0">
    <stop offset="0" stop-color="{CREAM}"/><stop offset=".42" stop-color="{CREAM}"/><stop offset=".5" stop-color="{V_SOFT}"/>
    <stop offset=".58" stop-color="{CREAM}"/><stop offset="1" stop-color="{CREAM}"/>{shine}
  </linearGradient>
  {grad("dot", TEXT_GRAD, 0, 0, 1, 1)}
  <filter id="b1" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="b2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="b3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>
</defs>
<g clip-path="url(#c)">
  <rect width="{W}" height="{h}" fill="{BG}"/>
  <circle class="f br" {d(0.2)} cx="{cx}" cy="{cy}" r="240" fill="url(#halo)"/>
  <g class="f" {d(0.3)}>
    <path class="br" d="{ring}" fill="none" stroke="url(#rg)" stroke-width="34" stroke-linejoin="round" filter="url(#b1)"/>
    <path d="{ring}" fill="none" stroke="url(#rg)" stroke-width="7" stroke-linejoin="round" filter="url(#b2)" opacity=".9"/>
  </g>
  <path class="dr" {d(0.3)} pathLength="1" d="{ring}" fill="none" stroke="{CREAM}" stroke-opacity=".7" stroke-width="1.3" stroke-linejoin="round"/>
  <g class="fl" style="animation-delay:1.6s">
    <g class="f" {d(0.9)}><g transform="{gem_tf}" filter="url(#b3)" opacity=".75">{glow}</g></g>
    <g transform="{gem_tf}">{facets}</g>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="19.5" fill="none" stroke="{LINE}"/>
</g>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="50" width="8" height="8" rx="2" fill="url(#dot)"/>
  {tag(68, 58.5, "Altheis · Antibes")}
</g>
<text class="r" {d(0.15)} x="42" y="176" font-family="{SANS}" font-weight="800" font-size="104" letter-spacing="-5.5" fill="url(#nm)">Ethan</text>
<text class="r" {d(0.3)} x="42" y="268" font-family="{SANS}" font-weight="800" font-size="104" letter-spacing="-5.5" fill="url(#nm)">Cohen<tspan fill="{V_CORE}">.</tspan></text>
<g class="r" {d(0.55)}>{text_lines(48, 318, sub, 25, f'font-family="{SANS}" font-weight="300" font-size="16.5" fill="{CREAM}" fill-opacity=".72"')}</g>
<g class="f" {d(0.85)}>
  <text x="48" y="{link_y}" font-family="{MONO}" font-size="13" fill="{CREAM}">altheisagency.com</text>
  <text class="nu" x="190" y="{link_y}" font-family="{MONO}" font-size="13" fill="{V_CORE}">&#8599;</text>
</g>
"""
    write("hero.svg", svg(W, h, body, ["800", "300", "mono"],
                          "Ethan Cohen. Fondateur d'Altheis, agence digitale sur la Côte d'Azur : "
                          "sites, vidéos et outils sur mesure qui font vendre."))


# ---- 2 · les trois métiers ----------------------------------------------------------
TILE_W, TILE_H = COL - 8, 212


def count_up(num, word, x, y, attrs, begin, dur=1.2, frames=20):
    """Le chiffre monte de 0 à sa valeur par images SMIL <set> (seule méthode qui marche dans <img>)."""
    val = int(num)
    tail = f' <tspan font-weight="300" font-size="17" letter-spacing="0" fill="{CREAM}" fill-opacity=".8">{escape(word)}</tspan>'
    if STATIC:
        return f'<text x="{x}" y="{y}" {attrs}>{num}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else str(round(val * e))
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{txt}{tail}'
                   f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>')
    return "".join(out)


def metier(name, label, acc, num, word, blurb, delay, pos):
    lines = wrap(blurb, 36)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{156 + i * 20}" font-family="{SANS}" font-weight="300" '
        f'font-size="13.5" fill="{CREAM}" fill-opacity=".62">{escape(l)}</text>' for i, l in enumerate(lines))
    body = f"""
<defs>
  <clipPath id="c"><rect width="{TILE_W}" height="{TILE_H}" rx="20"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="64"/></clipPath>
  <radialGradient id="h" cx="1" cy="0" r="1"><stop offset="0" stop-color="{acc}" stop-opacity=".55"/>
    <stop offset=".6" stop-color="{acc}" stop-opacity=".06"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>
  {grad("n", [(0, V_PALE), (0.5, acc), (1, V_DEEP)], 0, 0, 1, 1)}
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#c)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{CARD}"/>
    <rect class="br" width="{TILE_W}" height="{TILE_H}" fill="url(#h)"/>
    <rect class="sw" style="animation-delay:{delay + 1.5:.2f}s" x="0" y="-20" width="80" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-200 0)"/>
    <rect x="0" y="0" width="{TILE_W}" height="2" fill="{acc}" opacity=".9"/>
  </g>
  <rect x=".5" y=".5" width="{TILE_W - 1}" height="{TILE_H - 1}" rx="19.5" fill="none" stroke="{LINE2}"/>
  <g class="f" {d(delay + 0.3)}>{tag(24, 40, label, V_SOFT, 11)}</g>
  <g class="f" {d(delay + 0.5)}><text class="nu" x="{TILE_W - 40}" y="41" font-family="{MONO}" font-size="14" fill="{CREAM}">&#8599;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.4)}>
    {count_up(num, word, 22, 116, f'font-family="{SANS}" font-weight="800" font-size="52" letter-spacing="-2.5" fill="url(#n)"', delay + 0.4)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(f"{name}.svg", svg(TILE_W, TILE_H, body, ["800", "300", "mono"],
                             f"{label} : {num} {word}. {blurb}", left=4 * pos, right=8 - 4 * pos))


# ---- 3 · graphe des contributions en violet ------------------------------------------
SCALE = [CARD2, "#2b1d4a", "#47279a", V_DEEP, V_CORE, V_PALE]


def levels(days):
    nz = sorted(x["count"] for x in days if x["count"])
    if not nz:
        return lambda c: 0
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75, 0.93)]
    return lambda c: 0 if c == 0 else 1 + sum(c > t for t in q)


def heatmap(data):
    days = data["days"]
    lvl = levels(days)
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # dimanche en haut, comme GitHub
    cell, step, gx, gy = 12, 15, 44, 118
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        col, row = divmod(i + lead, 7)
        date = datetime.date.fromisoformat(day["date"])
        if row == 0 and date.day <= 7 and (date.year, date.month) not in seen:
            seen.add((date.year, date.month))
            months.append((col, MOIS_COURT[date.month - 1]))
        c = day["count"]
        delay = 0.6 + col * 0.028 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{SCALE[lvl(c)]}">'
            f'<title>{date.day} {MOIS[date.month - 1]} : {c} contribution{"s" if c > 1 else ""}</title></rect>')
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" '
                     f'fill="{MUTE}">{m}</text>' for col, m in months if col < ncols - 1)
    lx = right - 28 - len(SCALE) * 14
    legend = "".join(f'<rect x="{lx + i * 14}" y="70" width="11" height="11" rx="2.5" fill="{c}"/>'
                     for i, c in enumerate(SCALE))
    h = gy + 7 * step + 44
    body = f"""
<defs>{grad("t", TEXT_GRAD)}</defs>
<rect width="{W}" height="{h}" rx="20" fill="{BG}" stroke="{LINE}"/>
<g class="f" {d(0.2)}>{tag(44, 48, "Mis à jour chaque matin")}</g>
<text class="r" {d(0.3)} x="42" y="88" font-family="{SANS}" font-weight="800" font-size="34" letter-spacing="-1.6" fill="{CREAM}">Chaque jour, <tspan fill="url(#t)">en violet.</tspan></text>
{''.join(cells)}
<g class="f" {d(2.2)}>{labels}
<text x="{lx - 8}" y="80" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTE}">moins</text>
{legend}
<text x="{lx + len(SCALE) * 14 + 2}" y="80" font-family="{MONO}" font-size="11" fill="{MUTE}">plus</text></g>
"""
    write("heatmap.svg", svg(W, h, body, ["800", "mono"],
                             f"Graphe des contributions : {data['total']} contributions sur l'année"))


# ---- 4 · activité par mois -----------------------------------------------------------
def plural(n, word):
    return f"{n} {word}{'s' if n > 1 else ''}"


def activity(data):
    h = 340
    monthly = data["monthly"]
    start = next((i for i, m in enumerate(monthly) if m["total"] > 0), 0)
    monthly = monthly[max(0, min(start, len(monthly) - 6)):][-12:]  # depuis le premier mois actif, 6 mois au moins
    best = max(monthly, key=lambda m: m["total"])
    top = best["total"] or 1
    x0, x1, base, maxh = 40, 600, 292, 140
    n = len(monthly)
    gap = 12 if n > 8 else 18
    bw = min(56, (x1 - x0 - gap * (n - 1)) / n)
    bars = []
    for i, m in enumerate(monthly):
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        mm = int(m["month"][5:])
        fill = "url(#best)" if m is best else "url(#bar)"
        delay = 1.6 + i * 0.07
        bars.append(
            f'<rect class="g" style="animation-delay:{delay:.2f}s" x="{x:.1f}" y="{base - bh}" width="{bw:.1f}" '
            f'height="{bh}" rx="5" fill="{fill}"><title>{MOIS[mm - 1]} : {m["total"]}</title></rect>'
            f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="11" fill="{MUTE}">{MOIS_COURT[mm - 1]}</text>')
        if m is best:
            bars.append(f'<text class="p" style="animation-delay:2.6s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                        f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{V_PALE}">{m["total"]}</text>')
    cs, ls = data["current_streak"], data["longest_streak"]
    bd = datetime.date.fromisoformat(data["best_day"]["date"])
    stats = [
        (plural(cs, "jour"), "de suite, en ce moment" if cs >= ls else f"de suite (record : {ls})"),
        (plural(data["active_days"], "jour"), "avec au moins une contribution"),
        (str(data["best_day"]["count"]), f"le {'1er' if bd.day == 1 else bd.day} {MOIS[bd.month - 1]}, record d'une journée"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(f'<g class="r" {d(2.2 + i * 0.15)}>'
                    f'<text x="650" y="{y}" font-family="{SANS}" font-weight="800" font-size="36" letter-spacing="-1.5" fill="{CREAM}">{big}</text>'
                    f'<text x="650" y="{y + 24}" font-family="{SANS}" font-weight="300" font-size="13" fill="{MUTE}">{escape(small)}</text></g>')
        if i < 2:
            side.append(f'<rect class="f" {d(2.2)} x="650" y="{y + 44}" width="190" height="1" fill="{LINE2}"/>')
    first = monthly[0]["month"]
    since = f"Depuis {MOIS[int(first[5:]) - 1].rstrip('.')} {first[:4]}" if len(data["monthly"]) - start < 12 else "Les 12 derniers mois"
    body = f"""
<defs>
  {grad("t", TEXT_GRAD)}
  {grad("bar", [(0, "#5a3fb0"), (1, "#2a1f4a")], 0, 0, 0, 1)}
  {grad("best", [(0, V_PALE), (0.5, V_CORE), (1, V_DEEP)], 0, 0, 0, 1)}
</defs>
<rect width="{W}" height="{h}" rx="20" fill="{BG}" stroke="{LINE}"/>
<g class="f" {d(1.3)}>{tag(40, 58, since + " sur GitHub")}</g>
<text class="r" {d(1.4)} x="38" y="114" font-family="{SANS}" font-weight="800" font-size="50" letter-spacing="-2.4" fill="url(#t)">{data["total"]:,}<tspan fill="{CREAM}" font-weight="300" font-size="30" letter-spacing="-.8"> contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write("activity.svg", svg(W, h, body, ["800", "300", "mono"],
                              f"{data['total']} contributions, {plural(cs, 'jour')} de suite"))


# ---- 5 · en ligne en ce moment ------------------------------------------------------------
REPO_W, REPO_H = COL - 8, 300
SITES_EN_LIGNE = [
    ("altheis", "altheisagency.com", "https://altheisagency.com",
     "Le site de l'agence en 16 langues, pages de ville et guide des prix.", "Agence · 16 langues", V_CORE),
    ("politique", "Politique, simplement", "https://politique.altheisagency.com",
     "La politique française expliquée depuis le début, sans parti pris.", "Pédagogie · 2027", V_ORCHID),
    ("offbyriviera", "Off By Riviera", "https://offbyriviera.com",
     "Conciergerie privée de Cannes à Monaco, un site en quatre langues.", "Client · FR EN IT DE", V_DEEP),
]


def site_card(i, key, name, url, desc, meta, acc):
    delay = 0.6 + i * 0.14
    img = base64.b64encode(open(os.path.join(ASSETS, f"{key}.jpg"), "rb").read()).decode()
    iw = REPO_W - 24
    ih = round(iw * 10 / 16)
    body = f"""
<defs>
  <clipPath id="c"><rect width="{REPO_W}" height="{REPO_H}" rx="20"/></clipPath>
  <clipPath id="im"><rect x="12" y="12" width="{iw}" height="{ih}" rx="12"/></clipPath>
  <linearGradient id="fd" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="{CARD}" stop-opacity="0"/><stop offset="1" stop-color="{CARD}" stop-opacity=".55"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <rect width="{REPO_W}" height="{REPO_H}" rx="20" fill="{CARD}" stroke="{LINE2}"/>
  <g clip-path="url(#im)">
    <image href="data:image/jpeg;base64,{img}" x="12" y="12" width="{iw}" height="{ih}" preserveAspectRatio="xMidYMin slice"/>
    <rect x="12" y="12" width="{iw}" height="{ih}" fill="url(#fd)"/>
  </g>
  <rect x="12.5" y="12.5" width="{iw - 1}" height="{ih - 1}" rx="11.5" fill="none" stroke="{CREAM}" stroke-opacity=".08"/>
  <g class="r" {d(delay + 0.35)}>
    <rect x="24" y="{ih + 33}" width="8" height="8" rx="2" fill="{acc}"/>
    <text x="40" y="{ih + 42}" font-family="{SANS}" font-weight="600" font-size="17" letter-spacing="-.3" fill="{CREAM}">{escape(name)}</text>
    <text class="nu" x="{REPO_W - 38}" y="{ih + 42}" font-family="{MONO}" font-size="13" fill="{V_CORE}">&#8599;</text>
    {text_lines(24, ih + 70, wrap(desc, 35), 19, f'font-family="{SANS}" font-weight="300" font-size="13" fill="{CREAM}" fill-opacity=".62"')}
    <text x="24" y="{REPO_H - 20}" font-family="{MONO}" font-size="11" letter-spacing=".6" fill="{MUTE}">{escape(meta)}</text>
  </g>
</g>
"""
    write(f"site-{key}.svg", svg(REPO_W, REPO_H, body, ["600", "300", "mono"], f"{name} : {desc}",
                                 left=4 * i, right=8 - 4 * i))


def section_title(text, accent, theme, name):
    fg = "#e6edf3" if theme == "dark" else "#1f2328"
    body = (f'<defs>{grad("t", TEXT_GRAD)}</defs>'
            f'<text class="r" {d(0.2)} x="2" y="44" font-family="{SANS}" font-weight="800" font-size="34" '
            f'letter-spacing="-1.6" fill="{fg}">{escape(text)} <tspan fill="url(#t)">{escape(accent)}</tspan></text>')
    write(f"titre-{name}-{theme}.svg", svg(W, 62, body, ["800"], f"{text} {accent}", bottom=0))


if __name__ == "__main__":
    data = json.load(open(DATA))
    hero()
    metier("sites", "Sites web", V_CORE, SITES, "sites livrés",
           "Vitrines, cartes de restaurant, espaces de gestion. Pensés pour vendre, pas pour décorer.", 0.9, 0)
    metier("videos", "Vidéos", V_ORCHID, VIDEOS, "vidéos produites",
           "Films de marque, publicités verticales, logos animés, production assistée par IA.", 1.1, 1)
    metier("identites", "Identité", V_DEEP, IDENTITES, "identités de marque",
           "Nom, logo, palette et charte, jusqu'à l'enseigne et aux supports imprimés.", 1.3, 2)
    heatmap(data)
    activity(data)
    for theme in ("dark", "light"):
        section_title("En ligne,", "en ce moment.", theme, "en-ligne")
    for i, s in enumerate(SITES_EN_LIGNE):
        site_card(i, *s)
