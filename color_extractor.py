"""
color_extractor.py — Multi-strategy website color extraction
Tries CSS files, meta tags, CSS variables — much more reliable than raw HTML
"""

import requests, re
from collections import Counter
from urllib.parse import urljoin


def _to_rgb(h: str):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)

def _brightness(h):
    r,g,b = _to_rgb(h); return r*.299 + g*.587 + b*.114

def _saturation(h):
    r,g,b = _to_rgb(h); return max(r,g,b) - min(r,g,b)

def _is_brand_color(h):
    """True if color is colorful enough to be a brand color"""
    return 25 < _brightness(h) < 220 and _saturation(h) > 35

def _dist(h1, h2):
    r1,g1,b1 = _to_rgb(h1); r2,g2,b2 = _to_rgb(h2)
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** .5


def extract_website_colors(url: str):
    """
    Multi-strategy color extraction:
    Priority 1 — meta theme-color tag (explicitly set by web designer)
    Priority 2 — CSS custom properties (--primary, --brand, --color)
    Priority 3 — background colors in header/nav CSS selectors
    Priority 4 — External CSS files parsed for same
    Priority 5 — Frequency analysis of all hex colors

    Returns (primary_hex, accent_hex) as 6-char uppercase strings without #
    """
    DEFAULT = ('1B3A6B', 'C8A951')

    try:
        UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        hdrs = {'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.8'}

        resp = requests.get(url, timeout=14, headers=hdrs, allow_redirects=True)
        html = resp.text

        scored = []   # list of (score, hex)

        # ── Priority 1: meta theme-color ──────────────────────
        for pattern in [
            r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']#?([0-9a-fA-F]{6})',
            r'<meta[^>]+content=["\']#?([0-9a-fA-F]{6})["\'][^>]+name=["\']theme-color',
        ]:
            m = re.search(pattern, html, re.I)
            if m: scored.append((100, m.group(1).upper()))

        # ── Priority 2+3: parse inline <style> tags ────────────
        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.I | re.DOTALL)
        full_css = '\n'.join(style_blocks)
        _parse_css(full_css, scored)

        # ── Priority 4: linked CSS files ──────────────────────
        css_urls = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', html, re.I)
        css_urls += re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet', html, re.I)
        for cu in css_urls[:6]:
            if not cu.startswith('http'): cu = urljoin(url, cu)
            try:
                cr = requests.get(cu, timeout=8, headers=hdrs)
                _parse_css(cr.text, scored)
            except Exception:
                pass

        # ── Priority 5: frequency of all hex colors in HTML ───
        all_hex = [c.upper() for c in re.findall(r'#([0-9a-fA-F]{6})\b', html)]
        all_hex += [c[0].upper()*2 + c[1].upper()*2 + c[2].upper()*2
                    for c in re.findall(r'#([0-9a-fA-F]{3})\b', html)]
        for color, cnt in Counter(all_hex).most_common(30):
            if _is_brand_color(color):
                scored.append((cnt // 5, color))

        if not scored:
            return DEFAULT

        # Sort by score descending, deduplicate, filter
        scored.sort(key=lambda x: -x[0])
        seen = set(); valid = []
        for _, c in scored:
            if c not in seen and _is_brand_color(c):
                seen.add(c); valid.append(c)

        if not valid:
            return DEFAULT

        primary = valid[0]
        accent  = DEFAULT[1]
        for c in valid[1:]:
            if _dist(primary, c) > 75:
                accent = c; break

        return primary, accent

    except Exception:
        return DEFAULT


def _parse_css(css: str, scored: list):
    """Parse CSS text and add found colors to scored list."""
    # CSS custom properties with primary/brand/color/theme names
    for m in re.finditer(
        r'--(?:primary|brand|main|color|theme|accent)[^:;\n]*:\s*#([0-9a-fA-F]{6})',
        css, re.I
    ):
        scored.append((90, m.group(1).upper()))

    # :root color variables
    root_blocks = re.findall(r':root\s*\{([^}]+)\}', css, re.I | re.DOTALL)
    for block in root_blocks:
        for m in re.finditer(r'#([0-9a-fA-F]{6})', block):
            scored.append((85, m.group(1).upper()))

    # Header/nav/button background colors
    for sel_pattern in [
        r'(?:header|\.header|\.navbar|\.nav-bar|nav)[^{]*\{([^}]*)\}',
        r'(?:\.btn-primary|\.button-primary|\.cta|a\.button)[^{]*\{([^}]*)\}',
        r'body\s*\{([^}]*)\}',
    ]:
        for m in re.finditer(sel_pattern, css, re.I | re.DOTALL):
            block = m.group(1)
            for cm in re.finditer(r'(?:background|background-color|color):\s*#([0-9a-fA-F]{6})', block, re.I):
                scored.append((75, cm.group(1).upper()))

    # All hex colors in CSS (lower score)
    for m in re.finditer(r'#([0-9a-fA-F]{6})\b', css):
        scored.append((5, m.group(1).upper()))
