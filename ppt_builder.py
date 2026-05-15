"""
ppt_builder.py — Professional PPT generator using python-pptx
Navy + Gold theme, 6 layout types, 22 slides
"""

import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── Colour palette ─────────────────────────────────────────────
NAVY  = RGBColor(0x1B, 0x3A, 0x6B)
DNAV  = RGBColor(0x0A, 0x1E, 0x3D)
GOLD  = RGBColor(0xC8, 0xA9, 0x51)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xEF, 0xF3, 0xFA)
DARK  = RGBColor(0x1E, 0x2A, 0x3A)
GREY  = RGBColor(0x64, 0x74, 0x8B)
LGREY = RGBColor(0xE2, 0xE8, 0xF2)
AABD4 = RGBColor(0xAA, 0xBB, 0xD4)

IN = Inches   # shorthand


# ── Low-level drawing helpers ──────────────────────────────────

def _rect(slide, l, t, w, h, fill, line_color=None, line_width=Pt(0)):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line_color:
        sh.line.color.rgb = line_color
        sh.line.width = line_width or Pt(1)
    else:
        sh.line.fill.background()
    return sh


def _rrect(slide, l, t, w, h, fill, line_color=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line_color:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(1.5)
    else:
        sh.line.fill.background()
    return sh


def _txt(slide, l, t, w, h, text, fs, color,
         bold=False, italic=False, align=PP_ALIGN.LEFT,
         fname='Calibri', wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = str(text)
    r.font.size = Pt(fs)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = fname
    return tb


def _bullets(slide, l, t, w, h, items, fs=13, color=None):
    color = color or DARK
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(3)
        r = p.add_run()
        r.text = '\u25b8  ' + str(item)
        r.font.size = Pt(fs)
        r.font.color.rgb = color
        r.font.name = 'Calibri'
    return tb


def _set_bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


# ── Reusable slide chrome ──────────────────────────────────────

def _chrome(slide, company_name, n, total, website):
    """Company tag + slide number + footer on every content slide"""
    _txt(slide, IN(0.35), IN(0.11), IN(6), IN(0.22),
         company_name.upper(), 7.5, AABD4, bold=True)
    _txt(slide, IN(8.8), IN(0.11), IN(1.1), IN(0.22),
         f'{n} / {total}', 8, AABD4, align=PP_ALIGN.RIGHT)
    _txt(slide, IN(0.35), IN(5.38), IN(9.3), IN(0.22),
         f'{website}  |  {company_name}', 7.5, AABD4, align=PP_ALIGN.CENTER)


def _stat_row(slide, stats_dict, y_in, left_in=0.35, total_w=9.3):
    """Row of Navy stat cards with Gold numbers"""
    if not stats_dict:
        return
    items = [(str(k), str(v)) for k, v in stats_dict.items()][:5]
    n = len(items)
    gap = 0.14
    cw = (total_w - gap * (n - 1)) / n
    ch = 0.82
    for i, (label, value) in enumerate(items):
        x = left_in + i * (cw + gap)
        _rrect(slide, IN(x), IN(y_in), IN(cw), IN(ch), DNAV, GOLD)
        _txt(slide, IN(x + 0.05), IN(y_in + 0.05),
             IN(cw - 0.1), IN(ch * 0.58),
             value, 18, GOLD, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        _txt(slide, IN(x + 0.05), IN(y_in + ch * 0.52),
             IN(cw - 0.1), IN(ch * 0.42),
             label, 8.5, WHITE, align=PP_ALIGN.CENTER)


# ── Layout A: Standard (title + description + bullets + stats) ─

def _layout_a(prs, layout, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _set_bg(sl, WHITE)
    _chrome(sl, cn, n, total, wu)

    title = sd.get('title', '')
    desc  = sd.get('description', '')
    pts   = sd.get('key_points', [])
    stats = sd.get('stats')

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, NAVY, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    cy = 1.60 if has_desc else 1.25
    has_stats = bool(stats and isinstance(stats, dict) and len(stats) > 0)
    ch = 2.28 if has_stats else 2.88

    # Content background
    bg = _rrect(sl, IN(0.35), IN(cy), IN(9.3), IN(ch), LIGHT)
    bg.line.color.rgb = LGREY
    bg.line.width = Pt(0.5)
    # Left accent bar
    _rect(sl, IN(0.35), IN(cy), IN(0.06), IN(ch), NAVY)

    if pts:
        _bullets(sl, IN(0.55), IN(cy + 0.12), IN(9.0), IN(ch - 0.24), pts, fs=13)

    if has_stats:
        _stat_row(sl, stats, cy + ch + 0.18)


# ── Layout B: Two-column ───────────────────────────────────────

def _layout_b(prs, layout, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _set_bg(sl, WHITE)
    _chrome(sl, cn, n, total, wu)

    title = sd.get('title', '')
    desc  = sd.get('description', '')
    pts   = sd.get('key_points', [])
    stats = sd.get('stats')

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, NAVY, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    cy  = 1.60 if has_desc else 1.25
    has_stats = bool(stats and isinstance(stats, dict) and len(stats) > 0)
    ch  = 2.28 if has_stats else 2.88
    cw  = 4.5
    gap = 0.30
    mid = len(pts) // 2 or 1

    # Left column
    lbg = _rrect(sl, IN(0.35), IN(cy), IN(cw), IN(ch), LIGHT)
    lbg.line.color.rgb = LGREY; lbg.line.width = Pt(0.5)
    _rect(sl, IN(0.35), IN(cy), IN(0.06), IN(ch), NAVY)
    if pts[:mid]:
        _bullets(sl, IN(0.55), IN(cy + 0.12), IN(cw - 0.26), IN(ch - 0.24),
                 pts[:mid], fs=12.5)

    # Right column
    rbg = _rrect(sl, IN(0.35 + cw + gap), IN(cy), IN(cw), IN(ch), LIGHT)
    rbg.line.color.rgb = LGREY; rbg.line.width = Pt(0.5)
    _rect(sl, IN(0.35 + cw + gap), IN(cy), IN(0.06), IN(ch), GOLD)
    if pts[mid:]:
        _bullets(sl, IN(0.55 + cw + gap), IN(cy + 0.12), IN(cw - 0.26), IN(ch - 0.24),
                 pts[mid:], fs=12.5)

    if has_stats:
        _stat_row(sl, stats, cy + ch + 0.18)


# ── Layout C: Timeline ─────────────────────────────────────────

def _layout_c(prs, layout, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _set_bg(sl, WHITE)
    _chrome(sl, cn, n, total, wu)

    title = sd.get('title', '')
    desc  = sd.get('description', '')
    pts   = sd.get('key_points', [])

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 27, NAVY, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    sy = 1.60 if has_desc else 1.30
    n_items = len(pts)
    if n_items == 0:
        return
    item_h = 3.55 / n_items

    for i, bullet in enumerate(pts):
        y = sy + i * item_h

        # Split "YEAR: content" if possible
        if ':' in bullet:
            parts = bullet.split(':', 1)
            year_text    = parts[0].strip()[:12]
            content_text = parts[1].strip()
        else:
            year_text    = str(1940 + i * 10)
            content_text = bullet

        badge_fill = NAVY if i % 2 == 0 else DNAV
        _rrect(sl, IN(0.35), IN(y + 0.04), IN(1.15), IN(item_h - 0.12),
               badge_fill, GOLD)
        _txt(sl, IN(0.35), IN(y + 0.04), IN(1.15), IN(item_h - 0.12),
             year_text, 12, GOLD, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')

        cb = _rrect(sl, IN(1.60), IN(y + 0.04), IN(8.05), IN(item_h - 0.12), LIGHT)
        cb.line.color.rgb = LGREY; cb.line.width = Pt(0.5)
        _txt(sl, IN(1.78), IN(y + 0.04), IN(7.70), IN(item_h - 0.12),
             content_text, 12, DARK, wrap=True)


# ── Layout E: Feature cards ────────────────────────────────────

def _layout_e(prs, layout, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout)
    _set_bg(sl, WHITE)
    _chrome(sl, cn, n, total, wu)

    title = sd.get('title', '')
    desc  = sd.get('description', '')
    pts   = sd.get('key_points', [])

    _txt(sl, IN(0.35), IN(0.36), IN(9.3), IN(0.72),
         title, 31, NAVY, bold=True, fname='Georgia', wrap=True)

    has_desc = bool(desc)
    if has_desc:
        _txt(sl, IN(0.35), IN(1.1), IN(9.3), IN(0.44),
             desc, 11.5, GREY, italic=True, wrap=True)

    sy = 1.60 if has_desc else 1.30

    # Parse "Name: body" or use whole bullet
    feats = []
    for b in pts:
        if ':' in b:
            p = b.split(':', 1)
            feats.append((p[0].strip(), p[1].strip()))
        else:
            feats.append((b[:35].strip(), b))

    cols = 3
    rows = (len(feats) + cols - 1) // cols
    cw   = (9.3 - 0.2 * (cols - 1)) / cols
    ch   = (3.6 - 0.18 * (rows - 1)) / max(rows, 1)

    for i, (hdr, bdy) in enumerate(feats[:cols * rows]):
        r = i // cols
        c = i %  cols
        x = 0.35 + c * (cw + 0.2)
        y = sy   + r * (ch + 0.18)

        card = _rrect(sl, IN(x), IN(y), IN(cw), IN(ch), LIGHT)
        card.line.color.rgb = LGREY; card.line.width = Pt(0.5)
        _rect(sl, IN(x), IN(y), IN(cw), IN(0.06), GOLD)
        _txt(sl, IN(x + 0.12), IN(y + 0.10), IN(cw - 0.24), IN(0.36),
             hdr, 11.5, NAVY, bold=True, wrap=True)
        _txt(sl, IN(x + 0.12), IN(y + 0.46), IN(cw - 0.24), IN(ch - 0.58),
             bdy, 10.5, DARK, wrap=True)


# ── Title slide ────────────────────────────────────────────────

def _title_slide(prs, layout, sd, data):
    sl  = prs.slides.add_slide(layout)
    cn  = data.get('company_name', '')
    wu  = data.get('website', '')

    _set_bg(sl, DNAV)

    # Subtle oval decorations
    for (ox, oy, r) in [(0, 0, 1.2), (9.5, 5.0, 2.5), (8, -0.5, 3), (0.5, 4.5, 1.8)]:
        ov = sl.shapes.add_shape(MSO_SHAPE.OVAL,
                                 IN(ox - r), IN(oy - r), IN(r * 2), IN(r * 2))
        ov.fill.solid()
        ov.fill.fore_color.rgb = GOLD
        ov.fill.fore_color.theme_color  # keep solid, set transparency via XML if needed
        ov.line.fill.background()
        # Make very transparent via XML
        sp_pr = ov._element.spPr
        from lxml import etree
        from pptx.oxml.ns import qn
        solid_fill = sp_pr.find(qn('a:solidFill'))
        if solid_fill is not None:
            srgb = solid_fill.find(qn('a:srgbClr'))
            if srgb is not None:
                alpha = etree.SubElement(srgb, qn('a:alpha'))
                alpha.set('val', '8000')   # ~5% opacity

    # "Since YEAR" tag
    _txt(sl, IN(0.5), IN(0.40), IN(9), IN(0.32),
         'EDUCATIONAL PUBLISHERS  ·  AGRA, INDIA',
         9, GOLD, bold=True, align=PP_ALIGN.CENTER)

    # Company name
    _txt(sl, IN(0.5), IN(0.80), IN(9), IN(1.40),
         cn, 44, GOLD, bold=True, align=PP_ALIGN.CENTER, fname='Georgia', wrap=True)

    # Tagline / description
    tagline = sd.get('description') or data.get('tagline', '')
    if tagline:
        _txt(sl, IN(0.8), IN(2.26), IN(8.4), IN(0.55),
             tagline, 15, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)

    # Dot separator
    _txt(sl, IN(2.5), IN(2.86), IN(5), IN(0.26),
         '\u00b7  ' * 11, 13, GOLD, align=PP_ALIGN.CENTER)

    # Stat cards
    stats = sd.get('stats')
    if stats and isinstance(stats, dict):
        items = list(stats.items())[:4]
        n_c   = len(items)
        gap   = 0.15
        cw    = (9.3 - gap * (n_c - 1)) / n_c
        ch    = 1.10
        cy    = 3.22
        for i, (label, value) in enumerate(items):
            x = 0.35 + i * (cw + gap)
            _rrect(sl, IN(x), IN(cy), IN(cw), IN(ch),
                   RGBColor(0x0A, 0x17, 0x26), GOLD)
            _txt(sl, IN(x + 0.05), IN(cy + 0.06), IN(cw - 0.1), IN(ch * 0.58),
                 str(value), 26, GOLD, bold=True,
                 align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(x + 0.05), IN(cy + ch * 0.52), IN(cw - 0.1), IN(ch * 0.42),
                 label, 9.5, WHITE, align=PP_ALIGN.CENTER)

    # Website
    _txt(sl, IN(0.5), IN(5.28), IN(9), IN(0.28),
         wu, 11, GOLD, italic=True, align=PP_ALIGN.CENTER)


# ── Closing slide ──────────────────────────────────────────────

def _closing_slide(prs, layout, sd, data):
    sl      = prs.slides.add_slide(layout)
    cn      = data.get('company_name', '')
    wu      = data.get('website', '')
    contact = data.get('contact', {})

    _set_bg(sl, NAVY)

    _txt(sl, IN(0.5), IN(0.45), IN(9), IN(1.0),
         'Thank You', 52, GOLD, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')

    desc = sd.get('description', 'Thank you for your time and interest in our company.')
    _txt(sl, IN(0.8), IN(1.55), IN(8.4), IN(0.5),
         desc, 14, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)

    contacts = [
        ('\U0001f310 Website', wu),
        ('\U0001f4cd Address', contact.get('address', 'India')),
        ('\U0001f4de Phone',   contact.get('phone',   'Contact via website')),
        ('\U0001f4e7 Email',   contact.get('email',   'Contact via website')),
    ]
    for i, (lbl, val) in enumerate(contacts):
        x = 0.5 if i < 2 else 5.3
        y = 2.18 + (i % 2) * 0.72
        _rrect(sl, IN(x), IN(y), IN(4.2), IN(0.62), DNAV, GOLD)
        _txt(sl, IN(x + 0.15), IN(y + 0.00), IN(4.0), IN(0.28),
             lbl, 9.5, GOLD, bold=True)
        _txt(sl, IN(x + 0.15), IN(y + 0.28), IN(4.0), IN(0.30),
             str(val), 11, WHITE)

    _txt(sl, IN(0.5), IN(4.00), IN(9), IN(0.35),
         f'{cn}  \u00b7  Quality · Trust · Excellence',
         12, GOLD, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')

    _txt(sl, IN(0.5), IN(5.28), IN(9), IN(0.28),
         wu, 11, GOLD, italic=True, align=PP_ALIGN.CENTER)


# ── Route each slide to correct layout ────────────────────────

def _pick_layout(slide_data: dict, idx: int, total: int) -> str:
    n     = slide_data.get('slide_number', idx + 1)
    title = slide_data.get('title', '').lower()
    pts   = slide_data.get('key_points', [])

    if n == 1:
        return 'title'
    if n == total:
        return 'closing'

    # History → timeline
    if 'history' in title or 'timeline' in title:
        return 'timeline'

    # Strengths / USP / Values / Vision → feature cards
    if any(kw in title for kw in ('strength', 'usp', 'value', 'vision', 'mission', 'overview of')):
        return 'cards'

    # More than 7 bullets and slide is even → two-column
    if len(pts) > 6 and n % 2 == 0:
        return 'twocol'

    return 'standard'


# ── Public entry point ─────────────────────────────────────────

def build_presentation(data: dict) -> bytes:
    """
    Build a full Navy+Gold PPTX from company data dict.
    Returns the raw PPTX bytes.
    """
    prs = Presentation()
    prs.slide_width  = IN(10)
    prs.slide_height = IN(5.625)

    blank = prs.slide_layouts[6]   # blank layout

    cn     = data.get('company_name', 'Company')
    wu     = data.get('website', '')
    slides = data.get('slides', [])
    total  = len(slides)

    for idx, sd in enumerate(slides):
        n      = sd.get('slide_number', idx + 1)
        layout = _pick_layout(sd, idx, total)

        if   layout == 'title':
            _title_slide(prs, blank, sd, data)
        elif layout == 'closing':
            _closing_slide(prs, blank, sd, data)
        elif layout == 'timeline':
            _layout_c(prs, blank, sd, cn, wu, n, total)
        elif layout == 'cards':
            _layout_e(prs, blank, sd, cn, wu, n, total)
        elif layout == 'twocol':
            _layout_b(prs, blank, sd, cn, wu, n, total)
        else:
            _layout_a(prs, blank, sd, cn, wu, n, total)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()
