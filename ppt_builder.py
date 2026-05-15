"""
ppt_builder.py — Dynamic-theme PPT generator using python-pptx
Colors are extracted from the company website and applied throughout
"""

import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── Fixed neutral colors ───────────────────────────────────────
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK  = RGBColor(0x1E, 0x2A, 0x3A)
GREY  = RGBColor(0x64, 0x74, 0x8B)
LGREY = RGBColor(0xE2, 0xE8, 0xF2)

IN = Inches


# ── Theme — built from extracted website colors ────────────────

class Theme:
    """Holds all derived colors for a PPT theme."""

    def __init__(self, primary_hex: str = '1B3A6B', accent_hex: str = 'C8A951'):
        self.primary_hex = primary_hex.upper().lstrip('#')
        self.accent_hex  = accent_hex.upper().lstrip('#')

        self.primary = self._rgb(self.primary_hex)
        self.accent  = self._rgb(self.accent_hex)
        self.light   = self._lighten(self.primary_hex, 0.92)   # near-white tint
        self.dark_bg = self._darken(self.primary_hex,  0.55)   # deep title bg
        self.card_bg = self._darken(self.primary_hex,  0.40)   # stat card bg
        self.chrome  = self._lighten(self.primary_hex, 0.55)   # slide number / tag

    @staticmethod
    def _rgb(h: str) -> RGBColor:
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @staticmethod
    def _lighten(h: str, f: float) -> RGBColor:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return RGBColor(
            min(255, int(r + (255 - r) * f)),
            min(255, int(g + (255 - g) * f)),
            min(255, int(b + (255 - b) * f)),
        )

    @staticmethod
    def _darken(h: str, f: float) -> RGBColor:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return RGBColor(int(r * f), int(g * f), int(b * f))


# ── Drawing helpers (all take `t: Theme`) ─────────────────────

def _rect(slide, l, t, w, h, fill, line=None, lw=Pt(0)):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line; sh.line.width = lw or Pt(1)
    else:
        sh.line.fill.background()
    return sh


def _rrect(slide, l, t, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line; sh.line.width = Pt(1.5)
    else:
        sh.line.fill.background()
    return sh


def _txt(slide, l, t, w, h, text, fs, color,
         bold=False, italic=False, align=PP_ALIGN.LEFT,
         fname='Calibri', wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = wrap
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = str(text)
    r.font.size = Pt(fs); r.font.color.rgb = color
    r.font.bold = bold;   r.font.italic = italic
    r.font.name = fname
    return tb


def _bullets(slide, l, t, w, h, items, fs=13, color=None):
    color = color or DARK
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(3)
        r = p.add_run()
        r.text = '\u25b8  ' + str(item)
        r.font.size = Pt(fs); r.font.color.rgb = color
        r.font.name = 'Calibri'
    return tb


def _bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def _chrome(slide, t, cn, n, total, wu):
    _txt(slide, IN(0.35), IN(0.11), IN(6),   IN(0.22),
         cn.upper(), 7.5, t.chrome, bold=True)
    _txt(slide, IN(8.8),  IN(0.11), IN(1.1), IN(0.22),
         f'{n} / {total}', 8, t.chrome, align=PP_ALIGN.RIGHT)
    _txt(slide, IN(0.35), IN(5.38), IN(9.3), IN(0.22),
         f'{wu}  |  {cn}', 7.5, t.chrome, align=PP_ALIGN.CENTER)


def _stat_row(slide, t, stats_dict, y_in):
    if not stats_dict: return
    items = [(str(k), str(v)) for k, v in stats_dict.items()][:5]
    n = len(items); gap = 0.14
    cw = (9.3 - gap * (n - 1)) / n; ch = 0.82
    for i, (label, value) in enumerate(items):
        x = 0.35 + i * (cw + gap)
        _rrect(slide, IN(x), IN(y_in), IN(cw), IN(ch), t.card_bg, t.accent)
        _txt(slide, IN(x+0.05), IN(y_in+0.05), IN(cw-0.1), IN(ch*0.58),
             value, 18, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        _txt(slide, IN(x+0.05), IN(y_in+ch*0.52), IN(cw-0.1), IN(ch*0.42),
             label, 8.5, WHITE, align=PP_ALIGN.CENTER)


# ── Layout A: Standard ─────────────────────────────────────────

def _layout_a(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _bg(sl, WHITE); _chrome(sl, t, cn, n, total, wu)

    title = sd.get('title', ''); desc = sd.get('description', '')
    pts   = sd.get('key_points', []); stats = sd.get('stats')

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, t.primary, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    cy = 1.60 if has_desc else 1.25
    has_stats = bool(stats and isinstance(stats, dict) and stats)
    ch = 2.28 if has_stats else 2.88

    bg = _rrect(sl, IN(0.35), IN(cy), IN(9.3), IN(ch), t.light)
    bg.line.color.rgb = LGREY; bg.line.width = Pt(0.5)
    _rect(sl, IN(0.35), IN(cy), IN(0.06), IN(ch), t.primary)

    if pts:
        _bullets(sl, IN(0.55), IN(cy+0.12), IN(9.0), IN(ch-0.24), pts)

    if has_stats:
        _stat_row(sl, t, stats, cy + ch + 0.18)


# ── Layout B: Two-column ───────────────────────────────────────

def _layout_b(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _bg(sl, WHITE); _chrome(sl, t, cn, n, total, wu)

    title = sd.get('title', ''); desc = sd.get('description', '')
    pts   = sd.get('key_points', []); stats = sd.get('stats')

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, t.primary, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    cy = 1.60 if has_desc else 1.25
    has_stats = bool(stats and isinstance(stats, dict) and stats)
    ch = 2.28 if has_stats else 2.88
    cw = 4.5; gap = 0.30; mid = max(1, len(pts) // 2)

    lbg = _rrect(sl, IN(0.35), IN(cy), IN(cw), IN(ch), t.light)
    lbg.line.color.rgb = LGREY; lbg.line.width = Pt(0.5)
    _rect(sl, IN(0.35), IN(cy), IN(0.06), IN(ch), t.primary)
    if pts[:mid]:
        _bullets(sl, IN(0.55), IN(cy+0.12), IN(cw-0.26), IN(ch-0.24), pts[:mid], fs=12.5)

    rbg = _rrect(sl, IN(0.35+cw+gap), IN(cy), IN(cw), IN(ch), t.light)
    rbg.line.color.rgb = LGREY; rbg.line.width = Pt(0.5)
    _rect(sl, IN(0.35+cw+gap), IN(cy), IN(0.06), IN(ch), t.accent)
    if pts[mid:]:
        _bullets(sl, IN(0.55+cw+gap), IN(cy+0.12), IN(cw-0.26), IN(ch-0.24), pts[mid:], fs=12.5)

    if has_stats:
        _stat_row(sl, t, stats, cy + ch + 0.18)


# ── Layout C: Timeline ─────────────────────────────────────────

def _layout_c(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _bg(sl, WHITE); _chrome(sl, t, cn, n, total, wu)

    title = sd.get('title', ''); desc = sd.get('description', '')
    pts   = sd.get('key_points', [])

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 27, t.primary, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    sy = 1.60 if has_desc else 1.30
    n_items = len(pts)
    if not n_items: return
    item_h = 3.55 / n_items

    for i, bullet in enumerate(pts):
        y = sy + i * item_h
        if ':' in bullet:
            parts = bullet.split(':', 1)
            yr = parts[0].strip()[:12]; content = parts[1].strip()
        else:
            yr = str(1940 + i * 10); content = bullet

        badge = t.primary if i % 2 == 0 else t.dark_bg
        _rrect(sl, IN(0.35), IN(y+0.04), IN(1.15), IN(item_h-0.12), badge, t.accent)
        _txt(sl, IN(0.35), IN(y+0.04), IN(1.15), IN(item_h-0.12),
             yr, 12, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')

        cb = _rrect(sl, IN(1.60), IN(y+0.04), IN(8.05), IN(item_h-0.12), t.light)
        cb.line.color.rgb = LGREY; cb.line.width = Pt(0.5)
        _txt(sl, IN(1.78), IN(y+0.04), IN(7.70), IN(item_h-0.12),
             content, 12, DARK, wrap=True)


# ── Layout E: Feature cards ────────────────────────────────────

def _layout_e(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _bg(sl, WHITE); _chrome(sl, t, cn, n, total, wu)

    title = sd.get('title', ''); desc = sd.get('description', '')
    pts   = sd.get('key_points', [])

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, t.primary, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    sy = 1.60 if has_desc else 1.30
    feats = []
    for b in pts:
        if ':' in b:
            p = b.split(':', 1); feats.append((p[0].strip(), p[1].strip()))
        else:
            feats.append((b[:35].strip(), b))

    cols = 3; rows = (len(feats) + cols - 1) // cols
    cw = (9.3 - 0.2 * (cols-1)) / cols
    ch = (3.6 - 0.18 * (rows-1)) / max(rows, 1)

    for i, (hdr, bdy) in enumerate(feats[:cols*rows]):
        r = i // cols; c = i % cols
        x = 0.35 + c * (cw + 0.2); y = sy + r * (ch + 0.18)

        card = _rrect(sl, IN(x), IN(y), IN(cw), IN(ch), t.light)
        card.line.color.rgb = LGREY; card.line.width = Pt(0.5)
        _rect(sl, IN(x), IN(y), IN(cw), IN(0.06), t.accent)
        _txt(sl, IN(x+0.12), IN(y+0.10), IN(cw-0.24), IN(0.36),
             hdr, 11.5, t.primary, bold=True, wrap=True)
        _txt(sl, IN(x+0.12), IN(y+0.46), IN(cw-0.24), IN(ch-0.58),
             bdy, 10.5, DARK, wrap=True)


# ── Title slide ────────────────────────────────────────────────

def _title_slide(prs, layout, t, sd, data):
    sl = prs.slides.add_slide(layout)
    cn = data.get('company_name', ''); wu = data.get('website', '')
    _bg(sl, t.dark_bg)

    # Decorative ovals
    from lxml import etree
    from pptx.oxml.ns import qn
    for (ox, oy, r) in [(0,0,1.2),(9.5,5,2.5),(8,-0.5,3),(0.5,4.5,1.8)]:
        ov = sl.shapes.add_shape(MSO_SHAPE.OVAL,
                                 IN(ox-r), IN(oy-r), IN(r*2), IN(r*2))
        ov.fill.solid(); ov.fill.fore_color.rgb = t.accent
        ov.line.fill.background()
        sp_pr = ov._element.spPr
        sf = sp_pr.find(qn('a:solidFill'))
        if sf is not None:
            srgb = sf.find(qn('a:srgbClr'))
            if srgb is not None:
                alpha = etree.SubElement(srgb, qn('a:alpha'))
                alpha.set('val', '8000')

    _txt(sl, IN(0.5), IN(0.40), IN(9), IN(0.32),
         cn.upper(), 9, t.accent, bold=True, align=PP_ALIGN.CENTER)

    _txt(sl, IN(0.5), IN(0.78), IN(9), IN(1.40),
         cn, 44, t.accent, bold=True, align=PP_ALIGN.CENTER,
         fname='Georgia', wrap=True)

    tagline = sd.get('description') or data.get('tagline', '')
    if tagline:
        _txt(sl, IN(0.8), IN(2.26), IN(8.4), IN(0.55),
             tagline, 15, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)

    _txt(sl, IN(2.5), IN(2.86), IN(5), IN(0.26),
         '\u00b7  ' * 11, 13, t.accent, align=PP_ALIGN.CENTER)

    stats = sd.get('stats')
    if stats and isinstance(stats, dict):
        items = list(stats.items())[:4]
        n_c = len(items); gap = 0.15
        cw = (9.3 - gap * (n_c-1)) / n_c; ch = 1.10; cy = 3.22
        for i, (label, value) in enumerate(items):
            x = 0.35 + i * (cw + gap)
            _rrect(sl, IN(x), IN(cy), IN(cw), IN(ch), t.card_bg, t.accent)
            _txt(sl, IN(x+0.05), IN(cy+0.06), IN(cw-0.1), IN(ch*0.58),
                 str(value), 26, t.accent, bold=True,
                 align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(x+0.05), IN(cy+ch*0.52), IN(cw-0.1), IN(ch*0.42),
                 label, 9.5, WHITE, align=PP_ALIGN.CENTER)

    _txt(sl, IN(0.5), IN(5.28), IN(9), IN(0.28),
         wu, 11, t.accent, italic=True, align=PP_ALIGN.CENTER)


# ── Closing slide ──────────────────────────────────────────────

def _closing_slide(prs, layout, t, sd, data):
    sl = prs.slides.add_slide(layout)
    cn = data.get('company_name', ''); wu = data.get('website', '')
    contact = data.get('contact', {})
    _bg(sl, t.primary)

    _txt(sl, IN(0.5), IN(0.45), IN(9), IN(1.0),
         'Thank You', 52, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')

    desc = sd.get('description', 'Thank you for your time and interest.')
    _txt(sl, IN(0.8), IN(1.55), IN(8.4), IN(0.5),
         desc, 14, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)

    contacts = [
        ('\U0001f310 Website', wu),
        ('\U0001f4cd Address', contact.get('address', 'India')),
        ('\U0001f4de Phone',   contact.get('phone',   'Contact via website')),
        ('\U0001f4e7 Email',   contact.get('email',   'Contact via website')),
    ]
    for i, (lbl, val) in enumerate(contacts):
        x = 0.5 if i < 2 else 5.3; y = 2.18 + (i % 2) * 0.72
        _rrect(sl, IN(x), IN(y), IN(4.2), IN(0.62), t.dark_bg, t.accent)
        _txt(sl, IN(x+0.15), IN(y),      IN(4.0), IN(0.28), lbl, 9.5, t.accent, bold=True)
        _txt(sl, IN(x+0.15), IN(y+0.28), IN(4.0), IN(0.30), str(val), 11, WHITE)

    _txt(sl, IN(0.5), IN(4.0), IN(9), IN(0.35),
         cn, 12, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
    _txt(sl, IN(0.5), IN(5.28), IN(9), IN(0.28),
         wu, 11, t.accent, italic=True, align=PP_ALIGN.CENTER)


# ── Layout picker ──────────────────────────────────────────────

def _pick_layout(sd, idx, total):
    n     = sd.get('slide_number', idx + 1)
    title = sd.get('title', '').lower()
    pts   = sd.get('key_points', [])

    if n == 1:           return 'title'
    if n == total:       return 'closing'
    if any(kw in title for kw in ('history', 'timeline', 'journey')):
        return 'timeline'
    if any(kw in title for kw in ('strength', 'usp', 'value', 'vision', 'mission', 'why')):
        return 'cards'
    if len(pts) > 6 and n % 2 == 0:
        return 'twocol'
    return 'standard'


# ── Public entry point ─────────────────────────────────────────

def build_presentation(data: dict,
                       primary_hex: str = '1B3A6B',
                       accent_hex:  str = 'C8A951') -> bytes:
    """
    Build a full PPTX from company data using website-extracted colors.
    primary_hex / accent_hex are 6-digit hex strings WITHOUT #
    """
    t = Theme(primary_hex, accent_hex)

    prs = Presentation()
    prs.slide_width  = IN(10)
    prs.slide_height = IN(5.625)

    blank  = prs.slide_layouts[6]
    cn     = data.get('company_name', 'Company')
    wu     = data.get('website', '')
    slides = data.get('slides', [])
    total  = len(slides)

    for idx, sd in enumerate(slides):
        n      = sd.get('slide_number', idx + 1)
        layout = _pick_layout(sd, idx, total)

        if   layout == 'title':
            _title_slide(prs, blank, t, sd, data)
        elif layout == 'closing':
            _closing_slide(prs, blank, t, sd, data)
        elif layout == 'timeline':
            _layout_c(prs, blank, t, sd, cn, wu, n, total)
        elif layout == 'cards':
            _layout_e(prs, blank, t, sd, cn, wu, n, total)
        elif layout == 'twocol':
            _layout_b(prs, blank, t, sd, cn, wu, n, total)
        else:
            _layout_a(prs, blank, t, sd, cn, wu, n, total)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()
