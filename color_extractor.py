"""
color_extractor.py — Extract primary brand colors from a website
Returns hex colors to theme the PPT automatically
"""

import requests
import re
from collections import Counter


def _hex_to_rgb(h: str):
    h = h.strip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _brightness(h: str) -> float:
    r, g, b = _hex_to_rgb(h)
    return (r * 0.299 + g * 0.587 + b * 0.114)


def _saturation(h: str) -> float:
    r, g, b = _hex_to_rgb(h)
    mx, mn = max(r, g, b), min(r, g, b)
    return mx - mn


def _color_distance(h1: str, h2: str) -> float:
    r1, g1, b1 = _hex_to_rgb(h1)
    r2, g2, b2 = _hex_to_rgb(h2)
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def extract_website_colors(url: str):
    """
    Fetch website and extract the two most prominent brand colors.
    Returns (primary_hex, accent_hex) without # prefix.
    Falls back to Navy/Gold on any failure.
    """
    DEFAULT = ('1B3A6B', 'C8A951')

    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        resp = requests.get(url, timeout=12, headers=headers)
        html = resp.text

        # Extract all 6-digit hex colors
        raw_hex = re.findall(r'#([0-9a-fA-F]{6})\b', html)
        # Extract and expand 3-digit hex
        raw_hex += [c[0]*2 + c[1]*2 + c[2]*2
                    for c in re.findall(r'#([0-9a-fA-F]{3})\b', html)]

        # Normalise to uppercase
        raw_hex = [c.upper() for c in raw_hex]

        # Filter: keep colorful non-grey, non-white, non-black colors
        valid = []
        for c in raw_hex:
            br  = _brightness(c)
            sat = _saturation(c)
            if 20 < br < 210 and sat > 40:
                valid.append(c)

        if not valid:
            return DEFAULT

        # Rank by frequency
        counter = Counter(valid)
        ranked  = [color for color, _ in counter.most_common(20)]

        primary = ranked[0]

        # Accent = first color different enough from primary
        accent = DEFAULT[1]
        for candidate in ranked[1:]:
            if _color_distance(primary, candidate) > 70:
                accent = candidate
                break

        return primary, accent

    except Exception:
        return DEFAULT
