"""
ppt_builder.py — 3 distinct PPT design styles, auto-selected by industry
Style A: Professional (Education, Finance, Legal)
Style B: Bold Split Panel (Technology, IT, Consulting)
Style C: Clean Cards (Retail, Manufacturing, Healthcare, Food)
"""

import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK  = RGBColor(0x1E, 0x2A, 0x3A)
GREY  = RGBColor(0x64, 0x74, 0x8B)
LGREY = RGBColor(0xE2, 0xE8, 0xF2)
IN    = Inches


# ── Theme ──────────────────────────────────────────────────────

class Theme:
    def __init__(self, primary_hex='1B3A6B', accent_hex='C8A951'):
        self.primary_hex = primary_hex.upper().lstrip('#')
        self.accent_hex  = accent_hex.upper().lstrip('#')
        self.primary  = self._rgb(self.primary_hex)
        self.accent   = self._rgb(self.accent_hex)
        self.light    = self._lighten(self.primary_hex, 0.91)
        self.dark_bg  = self._darken(self.primary_hex,  0.52)
        self.card_bg  = self._darken(self.primary_hex,  0.38)
        self.chrome   = self._lighten(self.primary_hex, 0.50)
        self.bg_warm  = self._lighten(self.primary_hex, 0.95)

    @staticmethod
    def _rgb(h):
        return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))
    @staticmethod
    def _lighten(h, f):
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return RGBColor(min(255,int(r+(255-r)*f)), min(255,int(g+(255-g)*f)), min(255,int(b+(255-b)*f)))
    @staticmethod
    def _darken(h, f):
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return RGBColor(int(r*f), int(g*f), int(b*f))


# ── Industry → Style mapping ───────────────────────────────────

def _pick_style(industry: str) -> str:
    i = (industry or '').lower().replace('_',' ')
    tech_kw = ('tech','software','it ','digital','data','cloud','ai ','saas','app',
               'internet','startup','cyber','media','telecom','ecomm','e-comm')
    card_kw = ('retail','food','health','medical','pharma','manufactur','real estate',
               'real estate','construction','fmcg','consumer','hotel','hospitality',
               'travel','restaurant','agriculture','textile','logistic','transport',
               'auto','fashion','beauty','sport')
    if any(k in i for k in tech_kw): return 'bold'
    if any(k in i for k in card_kw): return 'cards'
    return 'professional'


# ── Low-level drawing helpers ──────────────────────────────────

def _rect(sl, l, t, w, h, fill, line=None, lw=Pt(0)):
    sh = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = lw or Pt(1)
    else: sh.line.fill.background()
    return sh

def _rrect(sl, l, t, w, h, fill, line=None, lw=Pt(1.5)):
    sh = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = lw
    else: sh.line.fill.background()
    return sh

def _txt(sl, l, t, w, h, text, fs, color,
         bold=False, italic=False, align=PP_ALIGN.LEFT,
         fname='Calibri', wrap=True):
    tb = sl.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = wrap
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = str(text)
    r.font.size = Pt(fs); r.font.color.rgb = color
    r.font.bold = bold; r.font.italic = italic; r.font.name = fname
    return tb

def _bullets(sl, l, t, w, h, items, fs=13, color=None):
    color = color or DARK
    tb = sl.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after = Pt(4)
        r = p.add_run(); r.text = '\u25b8  ' + str(item)
        r.font.size = Pt(fs); r.font.color.rgb = color; r.font.name = 'Calibri'
    return tb

def _bg(sl, color):
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = color


# ══════════════════════════════════════════════════════════════
# STYLE A — PROFESSIONAL
# White background · Left accent bar · Stat cards row at bottom
# ══════════════════════════════════════════════════════════════

def _A_chrome(sl, t, cn, n, total, wu):
    _txt(sl, IN(.35), IN(.11), IN(6), IN(.22), cn.upper(), 7.5, t.chrome, bold=True)
    _txt(sl, IN(8.8), IN(.11), IN(1.1), IN(.22), f'{n}/{total}', 8, t.chrome, align=PP_ALIGN.RIGHT)
    _txt(sl, IN(.35), IN(5.38), IN(9.3), IN(.22), f'{wu}  |  {cn}', 7.5, t.chrome, align=PP_ALIGN.CENTER)

def _A_stat_row(sl, t, stats, y):
    if not stats: return
    items = [(str(k),str(v)) for k,v in stats.items()][:5]
    n=len(items); gap=.14; cw=(9.3-gap*(n-1))/n; ch=.82
    for i,(lbl,val) in enumerate(items):
        x=.35+i*(cw+gap)
        _rrect(sl, IN(x), IN(y), IN(cw), IN(ch), t.card_bg, t.accent)
        _txt(sl, IN(x+.05), IN(y+.05), IN(cw-.1), IN(ch*.58), val, 18, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        _txt(sl, IN(x+.05), IN(y+ch*.52), IN(cw-.1), IN(ch*.42), lbl, 8.5, WHITE, align=PP_ALIGN.CENTER)

def _A_content(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout); _bg(sl, WHITE); _A_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description','')
    pts=sd.get('key_points',[]); stats=sd.get('stats')
    _txt(sl, IN(.35), IN(.36), IN(9.3), IN(.72), title, 31, t.primary, bold=True, fname='Georgia', wrap=True)
    has_desc=bool(desc)
    if has_desc: _txt(sl, IN(.35), IN(1.1), IN(9.3), IN(.44), desc, 11.5, GREY, italic=True, wrap=True)
    cy=1.60 if has_desc else 1.25
    hs=bool(stats and isinstance(stats,dict) and stats)
    ch=2.28 if hs else 2.88
    bg=_rrect(sl, IN(.35), IN(cy), IN(9.3), IN(ch), t.light)
    bg.line.color.rgb=LGREY; bg.line.width=Pt(.5)
    _rect(sl, IN(.35), IN(cy), IN(.06), IN(ch), t.primary)
    if pts: _bullets(sl, IN(.55), IN(cy+.12), IN(9.0), IN(ch-.24), pts)
    if hs: _A_stat_row(sl, t, stats, cy+ch+.18)

def _A_twocol(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout); _bg(sl, WHITE); _A_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description','')
    pts=sd.get('key_points',[]); stats=sd.get('stats')
    _txt(sl, IN(.35), IN(.36), IN(9.3), IN(.72), title, 31, t.primary, bold=True, fname='Georgia', wrap=True)
    has_desc=bool(desc)
    if has_desc: _txt(sl, IN(.35), IN(1.1), IN(9.3), IN(.44), desc, 11.5, GREY, italic=True, wrap=True)
    cy=1.60 if has_desc else 1.25
    hs=bool(stats and isinstance(stats,dict) and stats)
    ch=2.28 if hs else 2.88; cw=4.5; gap=.30; mid=max(1,len(pts)//2)
    lb=_rrect(sl, IN(.35), IN(cy), IN(cw), IN(ch), t.light); lb.line.color.rgb=LGREY; lb.line.width=Pt(.5)
    _rect(sl, IN(.35), IN(cy), IN(.06), IN(ch), t.primary)
    if pts[:mid]: _bullets(sl, IN(.55), IN(cy+.12), IN(cw-.26), IN(ch-.24), pts[:mid], fs=12.5)
    rb=_rrect(sl, IN(.35+cw+gap), IN(cy), IN(cw), IN(ch), t.light); rb.line.color.rgb=LGREY; rb.line.width=Pt(.5)
    _rect(sl, IN(.35+cw+gap), IN(cy), IN(.06), IN(ch), t.accent)
    if pts[mid:]: _bullets(sl, IN(.55+cw+gap), IN(cy+.12), IN(cw-.26), IN(ch-.24), pts[mid:], fs=12.5)
    if hs: _A_stat_row(sl, t, stats, cy+ch+.18)

def _A_timeline(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout); _bg(sl, WHITE); _A_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    _txt(sl, IN(.35), IN(.36), IN(9.3), IN(.72), title, 27, t.primary, bold=True, fname='Georgia', wrap=True)
    has_desc=bool(desc)
    if has_desc: _txt(sl, IN(.35), IN(1.1), IN(9.3), IN(.44), desc, 11.5, GREY, italic=True, wrap=True)
    sy=1.60 if has_desc else 1.30
    if not pts: return
    ih=3.55/len(pts)
    for i,b in enumerate(pts):
        y=sy+i*ih
        yr,ct = (b.split(':',1)[0].strip()[:12], b.split(':',1)[1].strip()) if ':' in b else (str(1940+i*10), b)
        badge=t.primary if i%2==0 else t.dark_bg
        _rrect(sl, IN(.35), IN(y+.04), IN(1.15), IN(ih-.12), badge, t.accent)
        _txt(sl, IN(.35), IN(y+.04), IN(1.15), IN(ih-.12), yr, 12, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        cb=_rrect(sl, IN(1.6), IN(y+.04), IN(8.05), IN(ih-.12), t.light); cb.line.color.rgb=LGREY; cb.line.width=Pt(.5)
        _txt(sl, IN(1.78), IN(y+.04), IN(7.7), IN(ih-.12), ct, 12, DARK, wrap=True)

def _A_cards(prs, layout, t, sd, cn, wu, n, total):
    sl = prs.slides.add_slide(layout); _bg(sl, WHITE); _A_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    _txt(sl, IN(.35), IN(.36), IN(9.3), IN(.72), title, 31, t.primary, bold=True, fname='Georgia', wrap=True)
    has_desc=bool(desc)
    if has_desc: _txt(sl, IN(.35), IN(1.1), IN(9.3), IN(.44), desc, 11.5, GREY, italic=True, wrap=True)
    sy=1.60 if has_desc else 1.30
    feats=[(b.split(':',1)[0].strip(), b.split(':',1)[1].strip()) if ':' in b else (b[:35], b) for b in pts]
    cols=3; rows=(len(feats)+cols-1)//cols
    cw=(9.3-.2*(cols-1))/cols; ch=(3.6-.18*(rows-1))/max(rows,1)
    for i,(hdr,bdy) in enumerate(feats[:cols*rows]):
        r=i//cols; c=i%cols; x=.35+c*(cw+.2); y=sy+r*(ch+.18)
        card=_rrect(sl, IN(x), IN(y), IN(cw), IN(ch), t.light); card.line.color.rgb=LGREY; card.line.width=Pt(.5)
        _rect(sl, IN(x), IN(y), IN(cw), IN(.06), t.accent)
        _txt(sl, IN(x+.12), IN(y+.10), IN(cw-.24), IN(.36), hdr, 11.5, t.primary, bold=True, wrap=True)
        _txt(sl, IN(x+.12), IN(y+.46), IN(cw-.24), IN(ch-.58), bdy, 10.5, DARK, wrap=True)

def _A_title(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website','')
    _bg(sl, t.dark_bg)
    from lxml import etree
    from pptx.oxml.ns import qn
    for ox,oy,r in [(0,0,1.2),(9.5,5,2.5),(8,-.5,3),(.5,4.5,1.8)]:
        ov=sl.shapes.add_shape(MSO_SHAPE.OVAL, IN(ox-r), IN(oy-r), IN(r*2), IN(r*2))
        ov.fill.solid(); ov.fill.fore_color.rgb=t.accent; ov.line.fill.background()
        sf=ov._element.spPr.find(qn('a:solidFill'))
        if sf is not None:
            srgb=sf.find(qn('a:srgbClr'))
            if srgb is not None:
                a=etree.SubElement(srgb,qn('a:alpha')); a.set('val','7000')
    _txt(sl, IN(.5), IN(.4), IN(9), IN(.32), cn.upper(), 9, t.accent, bold=True, align=PP_ALIGN.CENTER)
    _txt(sl, IN(.5), IN(.78), IN(9), IN(1.4), cn, 44, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia', wrap=True)
    tag=sd.get('description') or data.get('tagline','')
    if tag: _txt(sl, IN(.8), IN(2.26), IN(8.4), IN(.55), tag, 15, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)
    _txt(sl, IN(2.5), IN(2.86), IN(5), IN(.26), '\u00b7  '*11, 13, t.accent, align=PP_ALIGN.CENTER)
    stats=sd.get('stats')
    if stats and isinstance(stats,dict):
        items=list(stats.items())[:4]; nc=len(items); gap=.15
        cw=(9.3-gap*(nc-1))/nc; ch=1.10; cy=3.22
        for i,(lbl,val) in enumerate(items):
            x=.35+i*(cw+gap)
            _rrect(sl, IN(x), IN(cy), IN(cw), IN(ch), t.card_bg, t.accent)
            _txt(sl, IN(x+.05), IN(cy+.06), IN(cw-.1), IN(ch*.58), str(val), 26, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(x+.05), IN(cy+ch*.52), IN(cw-.1), IN(ch*.42), lbl, 9.5, WHITE, align=PP_ALIGN.CENTER)
    _txt(sl, IN(.5), IN(5.28), IN(9), IN(.28), wu, 11, t.accent, italic=True, align=PP_ALIGN.CENTER)

def _A_closing(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website',''); contact=data.get('contact',{})
    _bg(sl, t.primary)
    _txt(sl, IN(.5), IN(.45), IN(9), IN(1.0), 'Thank You', 52, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
    desc=sd.get('description','Thank you for your time.')
    _txt(sl, IN(.8), IN(1.55), IN(8.4), IN(.5), desc, 14, WHITE, italic=True, align=PP_ALIGN.CENTER, wrap=True)
    for i,(lbl,val) in enumerate([('\U0001f310 Website',wu),('\U0001f4cd Address',contact.get('address','India')),('\U0001f4de Phone',contact.get('phone','Contact via website')),('\U0001f4e7 Email',contact.get('email','Contact via website'))]):
        x=.5 if i<2 else 5.3; y=2.18+(i%2)*.72
        _rrect(sl, IN(x), IN(y), IN(4.2), IN(.62), t.dark_bg, t.accent)
        _txt(sl, IN(x+.15), IN(y), IN(4.0), IN(.28), lbl, 9.5, t.accent, bold=True)
        _txt(sl, IN(x+.15), IN(y+.28), IN(4.0), IN(.3), str(val), 11, WHITE)
    _txt(sl, IN(.5), IN(4.0), IN(9), IN(.35), cn, 12, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
    _txt(sl, IN(.5), IN(5.28), IN(9), IN(.28), wu, 11, t.accent, italic=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════
# STYLE B — BOLD SPLIT PANEL
# Left 3.2" solid color panel with white title
# Right white area with content
# ══════════════════════════════════════════════════════════════

PW = 3.2   # panel width inches
CX = 3.35  # content start x
CW = 6.4   # content width

def _B_content(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, WHITE)
    title=sd.get('title',''); desc=sd.get('description','')
    pts=sd.get('key_points',[]); stats=sd.get('stats')

    # Left panel
    _rect(sl, IN(0), IN(0), IN(PW), IN(5.625), t.primary)
    _txt(sl, IN(.15), IN(.1), IN(PW-.2), IN(.22), f'{n}/{total}', 8, t.light, align=PP_ALIGN.RIGHT)
    _txt(sl, IN(.15), IN(.35), IN(PW-.2), IN(.22), cn.upper(), 7.5, t.light, bold=True)
    # Slide title in panel
    _txt(sl, IN(.15), IN(1.0), IN(PW-.25), IN(2.0), title, 22, WHITE, bold=True, fname='Georgia', wrap=True)
    # Accent line under title
    _rect(sl, IN(.15), IN(3.1), IN(PW-.3), IN(.04), t.accent)
    # Stats in panel
    has_stats=bool(stats and isinstance(stats,dict) and stats)
    if has_stats:
        items=list(stats.items())[:3]
        for i,(lbl,val) in enumerate(items):
            y=3.3+i*.72
            _txt(sl, IN(.15), IN(y), IN(PW-.2), IN(.38), str(val), 20, t.accent, bold=True, fname='Georgia')
            _txt(sl, IN(.15), IN(y+.36), IN(PW-.2), IN(.28), lbl, 8, t.light)
    _txt(sl, IN(.1), IN(5.35), IN(PW-.1), IN(.2), wu, 7, t.light, italic=True)

    # Right side
    content_y = .25
    if desc:
        _txt(sl, IN(CX), IN(content_y), IN(CW), IN(.55), desc, 11, GREY, italic=True, wrap=True)
        content_y += .6

    bullet_h = 5.0 - content_y - .35
    if pts: _bullets(sl, IN(CX), IN(content_y), IN(CW), IN(bullet_h), pts, fs=12.5)
    _txt(sl, IN(CX), IN(5.38), IN(CW), IN(.2), cn, 7.5, t.chrome)

def _B_timeline(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, WHITE)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    _rect(sl, IN(0), IN(0), IN(PW), IN(5.625), t.primary)
    _txt(sl, IN(.15), IN(.1), IN(PW-.2), IN(.22), f'{n}/{total}', 8, t.light, align=PP_ALIGN.RIGHT)
    _txt(sl, IN(.15), IN(.35), IN(PW-.2), IN(.22), cn.upper(), 7.5, t.light, bold=True)
    _txt(sl, IN(.15), IN(.8), IN(PW-.25), IN(2.0), title, 22, WHITE, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.15), IN(2.9), IN(PW-.25), IN(1.0), desc, 9.5, t.light, italic=True, wrap=True)
    _txt(sl, IN(.1), IN(5.35), IN(PW-.1), IN(.2), wu, 7, t.light, italic=True)
    if not pts: return
    ih=5.3/len(pts); sy=.15
    for i,b in enumerate(pts):
        y=sy+i*ih
        yr,ct=(b.split(':',1)[0].strip()[:10], b.split(':',1)[1].strip()) if ':' in b else (str(1940+i*10), b)
        # Year pill
        pill=_rrect(sl, IN(CX), IN(y+.04), IN(1.0), IN(ih-.1), t.dark_bg, t.accent, lw=Pt(1.2))
        _txt(sl, IN(CX), IN(y+.04), IN(1.0), IN(ih-.1), yr, 11, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        # Content
        cb=_rrect(sl, IN(CX+1.1), IN(y+.04), IN(5.2), IN(ih-.1), t.light); cb.line.color.rgb=LGREY; cb.line.width=Pt(.5)
        _txt(sl, IN(CX+1.2), IN(y+.04), IN(5.0), IN(ih-.1), ct, 11.5, DARK, wrap=True)

def _B_cards(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, WHITE)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    _rect(sl, IN(0), IN(0), IN(PW), IN(5.625), t.primary)
    _txt(sl, IN(.15), IN(.1), IN(PW-.2), IN(.22), f'{n}/{total}', 8, t.light, align=PP_ALIGN.RIGHT)
    _txt(sl, IN(.15), IN(.35), IN(PW-.2), IN(.22), cn.upper(), 7.5, t.light, bold=True)
    _txt(sl, IN(.15), IN(.8), IN(PW-.25), IN(2.0), title, 22, WHITE, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.15), IN(2.9), IN(PW-.25), IN(1.5), desc, 9.5, t.light, italic=True, wrap=True)
    _txt(sl, IN(.1), IN(5.35), IN(PW-.1), IN(.2), wu, 7, t.light, italic=True)
    feats=[(b.split(':',1)[0].strip(), b.split(':',1)[1].strip()) if ':' in b else (b[:28], b) for b in pts]
    cols=2; rows=(len(feats)+cols-1)//cols
    cw=(CW-.15*(cols-1))/cols; ch=(5.4-.18*(rows-1))/max(rows,1)
    for i,(hdr,bdy) in enumerate(feats[:cols*rows]):
        r=i//cols; c=i%cols; x=CX+c*(cw+.15); y=.15+r*(ch+.18)
        card=_rrect(sl, IN(x), IN(y), IN(cw), IN(ch), t.light); card.line.color.rgb=LGREY; card.line.width=Pt(.5)
        _rect(sl, IN(x), IN(y), IN(cw), IN(.06), t.accent)
        _txt(sl, IN(x+.1), IN(y+.1), IN(cw-.2), IN(.35), hdr, 11, t.primary, bold=True, wrap=True)
        _txt(sl, IN(x+.1), IN(y+.46), IN(cw-.2), IN(ch-.58), bdy, 10, DARK, wrap=True)

def _B_title(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website','')
    _bg(sl, WHITE)
    # Left half solid
    _rect(sl, IN(0), IN(0), IN(5.2), IN(5.625), t.primary)
    # Decorative rectangles
    _rect(sl, IN(0), IN(4.5), IN(5.2), IN(.6), t.dark_bg)
    _rect(sl, IN(5.2), IN(0), IN(.08), IN(5.625), t.accent)
    # Company name in left panel
    _txt(sl, IN(.3), IN(.4), IN(4.6), IN(.3), 'EST. 1940', 9, t.light, bold=True, fname='Calibri')
    _txt(sl, IN(.3), IN(.8), IN(4.6), IN(2.2), cn, 38, t.accent, bold=True, fname='Georgia', wrap=True)
    tag=sd.get('description') or data.get('tagline','')
    if tag: _txt(sl, IN(.3), IN(3.2), IN(4.6), IN(.8), tag, 14, WHITE, italic=True, wrap=True)
    _txt(sl, IN(.3), IN(4.55), IN(4.6), IN(.3), wu, 10, t.light, italic=True)
    # Right side content
    _txt(sl, IN(5.5), IN(.5), IN(4.1), IN(.3), data.get('tagline',''), 13, GREY, italic=True, wrap=True)
    stats=sd.get('stats')
    if stats and isinstance(stats,dict):
        items=list(stats.items())[:4]; nc=len(items)
        cw=(4.1-.1*(nc-1))/nc; ch=1.1; gap=.1
        for i,(lbl,val) in enumerate(items):
            x=5.5+i*(cw+gap); y=1.5
            _rrect(sl, IN(x), IN(y), IN(cw), IN(ch), t.light); 
            _txt(sl, IN(x+.05), IN(y+.06), IN(cw-.1), IN(ch*.55), str(val), 24, t.primary, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(x+.05), IN(y+ch*.54), IN(cw-.1), IN(ch*.4), lbl, 9, GREY, align=PP_ALIGN.CENTER)
    # Feature points right side
    pts=sd.get('key_points',[])
    if pts: _bullets(sl, IN(5.5), IN(2.9), IN(4.1), IN(2.4), pts[:5], fs=11, color=DARK)

def _B_closing(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website',''); contact=data.get('contact',{})
    _bg(sl, WHITE)
    _rect(sl, IN(0), IN(0), IN(5.2), IN(5.625), t.primary)
    _rect(sl, IN(0), IN(3.8), IN(5.2), IN(1.0), t.dark_bg)
    _rect(sl, IN(5.2), IN(0), IN(.08), IN(5.625), t.accent)
    _txt(sl, IN(.3), IN(.5), IN(4.6), IN(1.2), 'Thank\nYou', 46, t.accent, bold=True, fname='Georgia')
    desc=sd.get('description','Thank you for your time.')
    _txt(sl, IN(.3), IN(1.9), IN(4.6), IN(1.2), desc, 12, WHITE, italic=True, wrap=True)
    _txt(sl, IN(.3), IN(3.88), IN(4.6), IN(.3), cn, 11, t.light, bold=True, fname='Georgia')
    _txt(sl, IN(.3), IN(4.25), IN(4.6), IN(.25), wu, 10, t.light, italic=True)
    for i,(lbl,val) in enumerate([('\U0001f310',wu),('\U0001f4cd',contact.get('address','India')),('\U0001f4de',contact.get('phone','—')),('\U0001f4e7',contact.get('email','—'))]):
        y=.4+i*1.15
        _txt(sl, IN(5.5), IN(y), IN(.4), IN(.4), lbl, 18, t.primary)
        _txt(sl, IN(5.95), IN(y), IN(3.7), IN(.3), lbl.split()[-1] if len(lbl.split())>1 else '', 9, GREY, bold=True)
        _txt(sl, IN(5.95), IN(y+.28), IN(3.7), IN(.35), str(val), 12, DARK, wrap=True)
        _rect(sl, IN(5.5), IN(y+.72), IN(4.2), IN(.02), LGREY)


# ══════════════════════════════════════════════════════════════
# STYLE C — CLEAN CARDS
# Very light background · White floating cards · Pill stats
# ══════════════════════════════════════════════════════════════

def _C_chrome(sl, t, cn, n, total, wu):
    _txt(sl, IN(.25), IN(.07), IN(6), IN(.2), cn.upper(), 7.5, t.chrome, bold=True)
    _txt(sl, IN(8.8), IN(.07), IN(1.1), IN(.2), f'{n}/{total}', 7.5, t.chrome, align=PP_ALIGN.RIGHT)
    _txt(sl, IN(.25), IN(5.38), IN(9.5), IN(.2), f'{wu}  |  {cn}', 7.5, t.chrome, align=PP_ALIGN.CENTER)

def _C_content(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, t.bg_warm); _C_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description','')
    pts=sd.get('key_points',[]); stats=sd.get('stats')

    # Title card
    tc=_rrect(sl, IN(.22), IN(.3), IN(9.56), IN(.9), WHITE); tc.line.color.rgb=LGREY; tc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(.3), IN(.1), IN(.9), t.primary)
    _txt(sl, IN(.45), IN(.34), IN(9.0), IN(.5), title, 26, t.primary, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.45), IN(.75), IN(9.0), IN(.4), desc, 10.5, GREY, italic=True, wrap=True)

    has_stats=bool(stats and isinstance(stats,dict) and stats)
    content_end=4.55 if has_stats else 5.1

    # Content card
    cc=_rrect(sl, IN(.22), IN(1.28), IN(9.56), IN(content_end-1.28), WHITE); cc.line.color.rgb=LGREY; cc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(1.28), IN(9.56), IN(.06), t.accent)
    if pts:
        if len(pts)>5:
            mid=len(pts)//2
            _bullets(sl, IN(.35), IN(1.38), IN(4.55), IN(content_end-1.45), pts[:mid], fs=12)
            _bullets(sl, IN(5.0), IN(1.38), IN(4.55), IN(content_end-1.45), pts[mid:], fs=12)
        else:
            _bullets(sl, IN(.35), IN(1.38), IN(9.3), IN(content_end-1.45), pts, fs=12.5)

    # Stat pills
    if has_stats:
        items=list(stats.items())[:5]; ns=len(items); gap=.1
        pw=(9.56-gap*(ns-1))/ns; ph=.65
        for i,(lbl,val) in enumerate(items):
            px=.22+i*(pw+gap)
            _rrect(sl, IN(px), IN(4.7), IN(pw), IN(ph), t.primary)
            _txt(sl, IN(px+.04), IN(4.72), IN(pw-.08), IN(ph*.55), str(val), 16, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(px+.04), IN(4.72+ph*.52), IN(pw-.08), IN(ph*.42), lbl, 7.5, WHITE, align=PP_ALIGN.CENTER)

def _C_twocol(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, t.bg_warm); _C_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[]); stats=sd.get('stats')
    tc=_rrect(sl, IN(.22), IN(.3), IN(9.56), IN(.9), WHITE); tc.line.color.rgb=LGREY; tc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(.3), IN(.1), IN(.9), t.primary)
    _txt(sl, IN(.45), IN(.34), IN(9.0), IN(.5), title, 26, t.primary, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.45), IN(.75), IN(9.0), IN(.4), desc, 10.5, GREY, italic=True, wrap=True)
    has_stats=bool(stats and isinstance(stats,dict) and stats)
    content_end=4.55 if has_stats else 5.1; cw=4.65; mid=max(1,len(pts)//2)
    lc=_rrect(sl, IN(.22), IN(1.28), IN(cw), IN(content_end-1.28), WHITE); lc.line.color.rgb=LGREY; lc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(1.28), IN(cw), IN(.06), t.primary)
    if pts[:mid]: _bullets(sl, IN(.35), IN(1.38), IN(cw-.2), IN(content_end-1.45), pts[:mid], fs=12)
    rc=_rrect(sl, IN(.22+cw+.13), IN(1.28), IN(cw), IN(content_end-1.28), WHITE); rc.line.color.rgb=LGREY; rc.line.width=Pt(.5)
    _rect(sl, IN(.22+cw+.13), IN(1.28), IN(cw), IN(.06), t.accent)
    if pts[mid:]: _bullets(sl, IN(.35+cw+.13), IN(1.38), IN(cw-.2), IN(content_end-1.45), pts[mid:], fs=12)
    if has_stats:
        items=list(stats.items())[:5]; ns=len(items); gap=.1
        pw=(9.56-gap*(ns-1))/ns; ph=.65
        for i,(lbl,val) in enumerate(items):
            px=.22+i*(pw+gap)
            _rrect(sl, IN(px), IN(4.7), IN(pw), IN(ph), t.primary)
            _txt(sl, IN(px+.04), IN(4.72), IN(pw-.08), IN(ph*.55), str(val), 16, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(px+.04), IN(4.72+ph*.52), IN(pw-.08), IN(ph*.42), lbl, 7.5, WHITE, align=PP_ALIGN.CENTER)

def _C_timeline(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, t.bg_warm); _C_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    tc=_rrect(sl, IN(.22), IN(.3), IN(9.56), IN(.9), WHITE); tc.line.color.rgb=LGREY; tc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(.3), IN(.1), IN(.9), t.primary)
    _txt(sl, IN(.45), IN(.34), IN(9.0), IN(.5), title, 26, t.primary, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.45), IN(.75), IN(9.0), IN(.4), desc, 10.5, GREY, italic=True, wrap=True)
    if not pts: return
    ih=3.95/len(pts); sy=1.3
    for i,b in enumerate(pts):
        y=sy+i*ih
        yr,ct=(b.split(':',1)[0].strip()[:12], b.split(':',1)[1].strip()) if ':' in b else (str(1940+i*10), b)
        _rrect(sl, IN(.22), IN(y+.04), IN(1.1), IN(ih-.1), t.primary)
        _txt(sl, IN(.22), IN(y+.04), IN(1.1), IN(ih-.1), yr, 11, t.accent, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
        cb=_rrect(sl, IN(1.42), IN(y+.04), IN(8.36), IN(ih-.1), WHITE); cb.line.color.rgb=LGREY; cb.line.width=Pt(.5)
        _txt(sl, IN(1.56), IN(y+.04), IN(8.1), IN(ih-.1), ct, 11.5, DARK, wrap=True)

def _C_feature_cards(prs, layout, t, sd, cn, wu, n, total):
    sl=prs.slides.add_slide(layout); _bg(sl, t.bg_warm); _C_chrome(sl, t, cn, n, total, wu)
    title=sd.get('title',''); desc=sd.get('description',''); pts=sd.get('key_points',[])
    tc=_rrect(sl, IN(.22), IN(.3), IN(9.56), IN(.9), WHITE); tc.line.color.rgb=LGREY; tc.line.width=Pt(.5)
    _rect(sl, IN(.22), IN(.3), IN(.1), IN(.9), t.primary)
    _txt(sl, IN(.45), IN(.34), IN(9.0), IN(.5), title, 26, t.primary, bold=True, fname='Georgia', wrap=True)
    if desc: _txt(sl, IN(.45), IN(.75), IN(9.0), IN(.4), desc, 10.5, GREY, italic=True, wrap=True)
    feats=[(b.split(':',1)[0].strip(), b.split(':',1)[1].strip()) if ':' in b else (b[:28], b) for b in pts]
    cols=3; rows=(len(feats)+cols-1)//cols
    cw=(9.56-.18*(cols-1))/cols; ch=(3.78-.18*(rows-1))/max(rows,1)
    for i,(hdr,bdy) in enumerate(feats[:cols*rows]):
        r=i//cols; c=i%cols; x=.22+c*(cw+.18); y=1.32+r*(ch+.18)
        card=_rrect(sl, IN(x), IN(y), IN(cw), IN(ch), WHITE); card.line.color.rgb=LGREY; card.line.width=Pt(.5)
        _rect(sl, IN(x), IN(y), IN(cw), IN(.07), t.primary if i%3==0 else t.accent if i%3==1 else t.dark_bg)
        _txt(sl, IN(x+.1), IN(y+.11), IN(cw-.2), IN(.35), hdr, 11.5, t.primary, bold=True, wrap=True)
        _txt(sl, IN(x+.1), IN(y+.47), IN(cw-.2), IN(ch-.58), bdy, 10.5, DARK, wrap=True)

def _C_title(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website','')
    _bg(sl, WHITE)
    # Top color stripe
    _rect(sl, IN(0), IN(0), IN(10), IN(.18), t.primary)
    _rect(sl, IN(0), IN(.18), IN(10), IN(.06), t.accent)
    # Company name big centered
    _txt(sl, IN(.5), IN(.4), IN(9), IN(1.6), cn, 46, t.primary, bold=True, align=PP_ALIGN.CENTER, fname='Georgia', wrap=True)
    # Accent underline
    _rect(sl, IN(3.0), IN(2.1), IN(4.0), IN(.06), t.accent)
    tag=sd.get('description') or data.get('tagline','')
    if tag: _txt(sl, IN(.8), IN(2.25), IN(8.4), IN(.55), tag, 15, GREY, italic=True, align=PP_ALIGN.CENTER, wrap=True)
    # Stats cards row
    stats=sd.get('stats')
    if stats and isinstance(stats,dict):
        items=list(stats.items())[:4]; nc=len(items); gap=.2
        cw=(9.5-gap*(nc-1))/nc; ch=1.25; cy=3.1
        for i,(lbl,val) in enumerate(items):
            x=.25+i*(cw+gap)
            card=_rrect(sl, IN(x), IN(cy), IN(cw), IN(ch), t.light); card.line.color.rgb=t.chrome; card.line.width=Pt(.8)
            _rect(sl, IN(x), IN(cy), IN(cw), IN(.07), t.primary)
            _txt(sl, IN(x+.05), IN(cy+.1), IN(cw-.1), IN(ch*.55), str(val), 26, t.primary, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
            _txt(sl, IN(x+.05), IN(cy+ch*.56), IN(cw-.1), IN(ch*.38), lbl, 9.5, GREY, align=PP_ALIGN.CENTER)
    _txt(sl, IN(.5), IN(4.6), IN(9), IN(.25), wu, 11, GREY, italic=True, align=PP_ALIGN.CENTER)
    # Bottom stripe
    _rect(sl, IN(0), IN(5.45), IN(10), IN(.18), t.primary)

def _C_closing(prs, layout, t, sd, data):
    sl=prs.slides.add_slide(layout); cn=data.get('company_name',''); wu=data.get('website',''); contact=data.get('contact',{})
    _bg(sl, t.bg_warm)
    _rect(sl, IN(0), IN(0), IN(10), IN(.18), t.primary)
    _rect(sl, IN(0), IN(.18), IN(10), IN(.06), t.accent)
    _txt(sl, IN(.5), IN(.4), IN(9), IN(1.1), 'Thank You', 52, t.primary, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
    _rect(sl, IN(3.5), IN(1.55), IN(3.0), IN(.06), t.accent)
    desc=sd.get('description','Thank you for your time.')
    _txt(sl, IN(.8), IN(1.72), IN(8.4), IN(.5), desc, 14, GREY, italic=True, align=PP_ALIGN.CENTER, wrap=True)
    cards=[('\U0001f310 Website',wu),('\U0001f4cd Address',contact.get('address','India')),('\U0001f4de Phone',contact.get('phone','—')),('\U0001f4e7 Email',contact.get('email','—'))]
    for i,(lbl,val) in enumerate(cards):
        x=.25 if i<2 else 5.12; y=2.55+(i%2)*.8
        cc=_rrect(sl, IN(x), IN(y), IN(4.63), IN(.68), WHITE); cc.line.color.rgb=LGREY; cc.line.width=Pt(.5)
        _rect(sl, IN(x), IN(y), IN(4.63), IN(.07), t.primary if i<2 else t.accent)
        _txt(sl, IN(x+.12), IN(y+.1), IN(4.4), IN(.26), lbl, 9.5, t.primary, bold=True)
        _txt(sl, IN(x+.12), IN(y+.34), IN(4.4), IN(.28), str(val), 11, DARK)
    _txt(sl, IN(.5), IN(4.38), IN(9), IN(.25), cn, 12, t.primary, bold=True, align=PP_ALIGN.CENTER, fname='Georgia')
    _rect(sl, IN(0), IN(5.45), IN(10), IN(.18), t.primary)


# ══════════════════════════════════════════════════════════════
# DISPATCHER
# ══════════════════════════════════════════════════════════════

def _pick_layout(sd, idx, total):
    n     = sd.get('slide_number', idx + 1)
    title = sd.get('title', '').lower()
    pts   = sd.get('key_points', [])
    stats = sd.get('stats')
    has_stats = bool(stats and isinstance(stats, dict) and len(stats) >= 3)

    if n == 1:     return 'title'
    if n == total: return 'closing'

    # Timeline: history / journey slides
    if any(k in title for k in ('history','timeline','journey','milestone','evolution')):
        return 'timeline'

    # Feature cards: strengths, USP, values, vision slides
    if any(k in title for k in ('strength','usp','unique','value','vision','mission',
                                  'advantage','differenti','why choose','why us')):
        return 'cards'

    # Two-column: any slide with 6+ bullets
    if len(pts) >= 6:
        return 'twocol'

    # Feature cards: product, team, award slides with 4+ bullets
    if any(k in title for k in ('product','service','offering','team','director',
                                  'audience','target','award','recogni','certif','roadmap')):
        if len(pts) >= 4:
            return 'cards'

    # Two-column: every 3rd content slide for variety
    if 3 <= n <= total - 2 and n % 3 == 0 and len(pts) >= 3:
        return 'twocol'

    return 'content'


def build_presentation(data: dict,
                       primary_hex: str = '1B3A6B',
                       accent_hex:  str = 'C8A951') -> bytes:
    t       = Theme(primary_hex, accent_hex)
    industry = data.get('industry_type', '')
    style    = _pick_style(industry)

    prs = Presentation()
    prs.slide_width  = IN(10)
    prs.slide_height = IN(5.625)
    blank  = prs.slide_layouts[6]

    cn     = data.get('company_name', 'Company')
    wu     = data.get('website', '')
    slides = data.get('slides', [])
    total  = len(slides)

    # Style dispatch table
    dispatch = {
        'professional': {
            'title':'_A_title','closing':'_A_closing','content':'_A_content',
            'twocol':'_A_twocol','timeline':'_A_timeline','cards':'_A_cards',
        },
        'bold': {
            'title':'_B_title','closing':'_B_closing','content':'_B_content',
            'twocol':'_B_content','timeline':'_B_timeline','cards':'_B_cards',
        },
        'cards': {
            'title':'_C_title','closing':'_C_closing','content':'_C_content',
            'twocol':'_C_twocol','timeline':'_C_timeline','cards':'_C_feature_cards',
        },
    }
    fn_map = dispatch.get(style, dispatch['professional'])
    fns = {
        '_A_title':_A_title,'_A_closing':_A_closing,'_A_content':_A_content,
        '_A_twocol':_A_twocol,'_A_timeline':_A_timeline,'_A_cards':_A_cards,
        '_B_title':_B_title,'_B_closing':_B_closing,'_B_content':_B_content,
        '_B_timeline':_B_timeline,'_B_cards':_B_cards,
        '_C_title':_C_title,'_C_closing':_C_closing,'_C_content':_C_content,
        '_C_twocol':_C_twocol,'_C_timeline':_C_timeline,'_C_feature_cards':_C_feature_cards,
    }

    for idx, sd in enumerate(slides):
        n      = sd.get('slide_number', idx+1)
        layout = _pick_layout(sd, idx, total)
        fn     = fns[fn_map[layout]]

        if layout in ('title','closing'):
            fn(prs, blank, t, sd, data)
        else:
            fn(prs, blank, t, sd, cn, wu, n, total)

    buf = io.BytesIO()
    prs.save(buf); buf.seek(0)
    return buf.getvalue(), style
