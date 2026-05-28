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
    """True if color is colorful enough to be a brand color (not near-white or near-black)"""
    return 18 < _brightness(h) < 235 and _saturation(h) > 18

def _is_structural_color(h):
    """
    Looser check for high-priority structural colors (header, nav, meta theme-color).
    Allows dark/near-black colors — e.g. a site with a black header should get black as primary.
    Excludes only pure white and colors with near-zero saturation that look like greys.
    """
    b = _brightness(h)
    s = _saturation(h)
    if b > 230:           return False  # near-white — skip
    if b < 20 and s < 10: return False  # pure grey-black with no saturation — skip
    return True

def _dist(h1, h2):
    r1,g1,b1 = _to_rgb(h1); r2,g2,b2 = _to_rgb(h2)
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** .5

def _rgb_to_hex(r, g, b) -> str:
    return f'{int(r):02X}{int(g):02X}{int(b):02X}'


def extract_website_colors(url: str):
    """
    Multi-strategy color extraction:
    Priority 1 — meta theme-color tag (explicitly set by web designer)
    Priority 2 — CSS custom properties (--primary, --brand, --color, etc.)
    Priority 3 — background colors in header/nav CSS selectors
    Priority 4 — External CSS files parsed for same
    Priority 5 — Frequency analysis of all hex and rgb colors

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

        # ── meta theme-color with rgb() ────────────────────────
        for pattern in [
            r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
            r'<meta[^>]+content=["\']rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)["\'][^>]+name=["\']theme-color',
        ]:
            m = re.search(pattern, html, re.I)
            if m: scored.append((100, _rgb_to_hex(m.group(1), m.group(2), m.group(3))))

        # ── Priority 2+3: parse inline <style> tags ────────────
        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.I | re.DOTALL)
        full_css = '\n'.join(style_blocks)
        _parse_css(full_css, scored)

        # ── Priority 4: linked CSS files ──────────────────────
        css_urls = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', html, re.I)
        css_urls += re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet', html, re.I)
        for cu in css_urls[:8]:
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

        # ── Priority 5b: rgb() colors in HTML (SVG, inline style) ─
        for m in re.finditer(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', html, re.I):
            h = _rgb_to_hex(m.group(1), m.group(2), m.group(3))
            if _is_brand_color(h):
                scored.append((1, h))

        if not scored:
            return DEFAULT

        # Sort by score descending, deduplicate, filter
        # High-priority sources (score >= 50): use looser structural check — allows dark/black header colors
        # Low-priority sources (score < 50): use strict brand color check — avoid noise
        scored.sort(key=lambda x: -x[0])
        seen = set(); valid = []
        for score, c in scored:
            if c in seen: continue
            seen.add(c)
            if score >= 50:
                if _is_structural_color(c): valid.append((score, c))
            else:
                if _is_brand_color(c): valid.append((score, c))

        if not valid:
            return DEFAULT

        primary = valid[0][1]
        accent  = DEFAULT[1]
        for _, c in valid[1:]:
            if _dist(primary, c) > 60:
                accent = c; break

        return primary, accent

    except Exception:
        return DEFAULT


def _parse_css(css: str, scored: list):
    """Parse CSS text and add found colors to scored list."""
    # CSS custom properties — broad name match for primary/brand/color/theme/accent/key/logo
    for m in re.finditer(
        r'--(?:[a-z-]*(?:primary|brand|main|color|theme|accent|key|corporate|header|logo|ui)[a-z-]*):\s*#([0-9a-fA-F]{6})',
        css, re.I
    ):
        scored.append((90, m.group(1).upper()))

    # CSS variables with rgb() values
    for m in re.finditer(
        r'--(?:[a-z-]*(?:primary|brand|main|color|theme|accent|key|corporate|header|logo)[a-z-]*):\s*rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
        css, re.I
    ):
        scored.append((90, _rgb_to_hex(m.group(1), m.group(2), m.group(3))))

    # :root color variables (all hex)
    root_blocks = re.findall(r':root\s*\{([^}]+)\}', css, re.I | re.DOTALL)
    for block in root_blocks:
        for m in re.finditer(r'#([0-9a-fA-F]{6})', block):
            scored.append((85, m.group(1).upper()))
        # :root rgb() values
        for m in re.finditer(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', block, re.I):
            scored.append((85, _rgb_to_hex(m.group(1), m.group(2), m.group(3))))

    # Header/nav/button background colors — hex
    for sel_pattern in [
        r'(?:header|\.header|\.navbar|\.nav-bar|nav)[^{]*\{([^}]*)\}',
        r'(?:\.btn-primary|\.button-primary|\.cta|a\.button)[^{]*\{([^}]*)\}',
        r'body\s*\{([^}]*)\}',
    ]:
        for m in re.finditer(sel_pattern, css, re.I | re.DOTALL):
            block = m.group(1)
            for cm in re.finditer(r'(?:background|background-color|color):\s*#([0-9a-fA-F]{6})', block, re.I):
                scored.append((75, cm.group(1).upper()))
            # same selectors but rgb()
            for cm in re.finditer(
                r'(?:background|background-color|color):\s*rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)',
                block, re.I
            ):
                scored.append((75, _rgb_to_hex(cm.group(1), cm.group(2), cm.group(3))))

    # All hex colors in CSS (lower score)
    for m in re.finditer(r'#([0-9a-fA-F]{6})\b', css):
        scored.append((5, m.group(1).upper()))

    # All rgb() in CSS (lower score)
    for m in re.finditer(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', css, re.I):
        scored.append((3, _rgb_to_hex(m.group(1), m.group(2), m.group(3))))
