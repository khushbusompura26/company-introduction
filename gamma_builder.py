"""
gamma_builder.py — Gamma AI presentation generation
Converts company research data into beautifully designed Gamma presentations.

Gamma API key: get yours at https://gamma.app/settings/api
"""

import requests, re

GAMMA_API_BASE = "https://gamma.app/api/v1"

# ── Theme catalogue ─────────────────────────────────────────────
# Carefully curated theme recommendations per industry
INDUSTRY_THEMES = {
    'technology':    ['stratos', 'nebulae', 'founder', 'electric', 'borealis'],
    'software':      ['founder', 'stratos', 'electric', 'borealis', 'aurora'],
    'it':            ['borealis', 'stratos', 'blue-steel', 'marine', 'founder'],
    'digital':       ['aurora', 'electric', 'stratos', 'borealis', 'gamma-dark'],
    'ai':            ['stratos', 'nebulae', 'aurora', 'electric', 'founder'],
    'saas':          ['founder', 'electric', 'borealis', 'stratos', 'aurora'],
    'ecomm':         ['orbit', 'electric', 'peach', 'gamma-dark', 'aurora'],
    'media':         ['aurora', 'electric', 'gamma-dark', 'atacama', 'incandescent'],
    'telecom':       ['marine', 'borealis', 'stratos', 'blues', 'blue-steel'],
    'education':     ['icebreaker', 'serene', 'commons', 'consultant', 'sage'],
    'finance':       ['consultant', 'ash', 'howlite', 'chimney-smoke', 'slate'],
    'banking':       ['marine', 'consultant', 'ash', 'slate', 'blues'],
    'legal':         ['ash', 'slate', 'chimney-smoke', 'onyx', 'vortex'],
    'consulting':    ['consultant', 'ash', 'howlite', 'slate', 'coal'],
    'healthcare':    ['sage', 'serene', 'sprout', 'commons', 'pearl'],
    'medical':       ['serene', 'sage', 'commons', 'sprout', 'tranquil'],
    'pharma':        ['commons', 'serene', 'pearl', 'sage', 'icebreaker'],
    'manufacturing': ['slate', 'coal', 'chimney-smoke', 'blue-steel', 'ash'],
    'construction':  ['slate', 'coal', 'marine', 'chimney-smoke', 'ash'],
    'retail':        ['peach', 'leimoon', 'terracotta', 'orbit', 'flamingo'],
    'fashion':       ['onyx', 'vortex', 'creme', 'gold-leaf', 'chocolate'],
    'beauty':        ['flamingo', 'malibu', 'ashrose', 'creme', 'lavender'],
    'food':          ['terracotta', 'oasis', 'cornfield', 'sage', 'cornflower'],
    'restaurant':    ['terracotta', 'oasis', 'cornfield', 'cigar', 'clementa'],
    'agriculture':   ['cornfield', 'sage', 'sprout', 'oasis', 'plant-shop'],
    'real_estate':   ['creme', 'linen', 'chisel', 'dune', 'gold-leaf'],
    'hotel':         ['gold-leaf', 'creme', 'linen', 'dune', 'aurum'],
    'hospitality':   ['gold-leaf', 'terracotta', 'creme', 'linen', 'dune'],
    'travel':        ['borealis', 'malibu', 'aurora', 'seafoam', 'cornflower'],
    'logistics':     ['marine', 'chimney-smoke', 'blue-steel', 'slate', 'borealis'],
    'transport':     ['marine', 'slate', 'blue-steel', 'borealis', 'chimney-smoke'],
    'auto':          ['stratos', 'blue-steel', 'chimney-smoke', 'slate', 'onyx'],
    'sport':         ['orbit', 'electric', 'borealis', 'canaveral', 'rush'],
    'textile':       ['creme', 'linen', 'chisel', 'terracotta', 'chocolate'],
    'other':         ['default-light', 'pearl', 'icebreaker', 'commons', 'slate'],
}

# Hue → theme refinements (applied on top of industry selection)
HUE_OVERRIDES = {
    'red':     ['rush', 'sanguine', 'canaveral'],
    'orange':  ['canaveral', 'peach', 'electric', 'gamma-dark'],
    'yellow':  ['bee-happy', 'vanilla', 'cornfield'],
    'green':   ['sage', 'sprout', 'pistachio', 'plant-shop', 'verdigris'],
    'blue':    ['marine', 'borealis', 'blues', 'tranquil', 'icebreaker'],
    'purple':  ['aurora', 'nightsky', 'urqsghgfv9ay2j0', 'blueberry'],
    'dark':    ['stratos', 'nebulae', 'vortex', 'onyx', 'founder'],
    'neutral': ['howlite', 'pearl', 'ash', 'chimney-smoke', 'slate'],
}


# ── Color helpers ────────────────────────────────────────────────

def _to_rgb(h: str):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) < 6: return (128, 128, 128)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _brightness(h: str) -> float:
    r, g, b = _to_rgb(h)
    return r * .299 + g * .587 + b * .114

def _saturation(h: str) -> float:
    r, g, b = _to_rgb(h)
    return max(r, g, b) - min(r, g, b)

def _dominant_hue(h: str) -> str:
    """
    Returns a broad hue bucket: 'dark', 'neutral', 'red', 'orange',
    'yellow', 'green', 'blue', 'purple'.
    Browns and golds are intentionally bucketed as 'neutral' so that
    earthy industry themes win over the orange colour overrides.
    """
    try:
        r, g, b = _to_rgb(h)
        bright = _brightness(h)
        sat    = _saturation(h)

        if bright < 55:
            return 'dark'
        if sat < 28:
            return 'neutral'

        if r >= g and r >= b:
            # Vivid red / maroon: G and B both very low — always 'red'
            if g < 60 and b < 60 and r > 90:
                return 'red'
            g_over_b = g / max(b, 1)
            # True vivid orange: G clearly above B and well-saturated
            if g_over_b > 1.6 and sat > 100:
                return 'orange'
            # Brown / gold / earth tones: low saturation — let industry win
            if sat < 100:
                return 'neutral'
            return 'red'

        if g >= r and g >= b:
            return 'green'
        if b >= r and b >= g:
            return 'purple' if r > 110 else 'blue'
    except Exception:
        pass
    return 'neutral'


# Hues strong enough to override industry-based selection
_STRONG_HUES = {'dark', 'red', 'blue', 'green', 'purple'}


def pick_gamma_theme(industry: str, primary_hex: str) -> str:
    """
    Pick the best Gamma theme for the company based on industry and brand colour.
    Always returns a valid theme ID.

    Priority:
      1. Industry candidate that also matches brand colour hue  (best match)
      2. Colour override, only for strong/distinctive hues       (colour-led)
      3. First industry candidate                               (safe default)
    """
    i = (industry or '').lower().replace('_', ' ')

    candidates = INDUSTRY_THEMES['other']
    for key, themes in INDUSTRY_THEMES.items():
        norm_key = key.replace('_', ' ')
        if norm_key in i or key in i:
            candidates = themes
            break

    try:
        hue       = _dominant_hue(primary_hex)
        overrides = HUE_OVERRIDES.get(hue, [])

        # 1. Industry + colour match
        for o in overrides:
            if o in candidates:
                return o

        # 2. Colour override only for clearly distinctive hues
        if hue in _STRONG_HUES and overrides:
            return overrides[0]
    except Exception:
        pass

    # 3. Industry default
    return candidates[0]


# ── Prompt builder ───────────────────────────────────────────────

def build_gamma_prompt(company_data: dict) -> str:
    """
    Convert company research JSON into a rich structured markdown prompt
    with explicit --- card breaks so Gamma honours the slide structure.
    Each section is separated by '---' and cardSplit='inputTextBreaks' is
    set in the API payload, giving one Gamma card per slide.
    """
    cn      = company_data.get('company_name', 'Company')
    tag     = company_data.get('tagline', '')
    wu      = company_data.get('website', '')
    contact = company_data.get('contact', {})
    slides  = company_data.get('slides', [])
    total   = len(slides)

    cards = []  # each entry = one card's markdown text

    # ── Card 1: Cover / title ────────────────────────────────────
    cover_lines = [f"# {cn}"]
    if tag:
        cover_lines.append(f"### {tag}")
    if wu:
        cover_lines.append(f"*{wu}*")
    # Hero stats on the cover
    title_slide = next((s for s in slides if s.get('slide_number') == 1), {})
    hero_stats  = title_slide.get('stats') or {}
    if hero_stats:
        items = list(hero_stats.items())[:4]
        # Render as a small table for Gamma to turn into a stat grid
        cover_lines.append("")
        cover_lines.append("| " + " | ".join(k for k, _ in items) + " |")
        cover_lines.append("| " + " | ".join("---" for _ in items) + " |")
        cover_lines.append("| " + " | ".join(str(v) for _, v in items) + " |")
    cards.append('\n'.join(cover_lines))

    # ── Content slides ───────────────────────────────────────────
    for sd in slides:
        n     = sd.get('slide_number', 0)
        title = sd.get('title', '')
        desc  = sd.get('description', '')
        pts   = sd.get('key_points', [])
        stats = sd.get('stats')

        if n == 1 or n == total:
            continue  # covered by cover and closing cards

        card_lines = [f"## {title}", ""]

        if desc:
            card_lines.append(f"> {desc}")
            card_lines.append("")

        # Stats as a visual table Gamma can render as a grid
        if stats and isinstance(stats, dict) and stats:
            items = list(stats.items())[:5]
            card_lines.append("| " + " | ".join(k for k, _ in items) + " |")
            card_lines.append("| " + " | ".join("---" for _ in items) + " |")
            card_lines.append("| " + " | ".join(str(v) for _, v in items) + " |")
            card_lines.append("")

        # Key points as bullets
        if pts:
            for pt in pts:
                card_lines.append(f"- {pt}")
            card_lines.append("")

        cards.append('\n'.join(card_lines))

    # ── Closing card ─────────────────────────────────────────────
    closing   = next((s for s in slides if s.get('slide_number') == total), {})
    close_lines = ["## Thank You", ""]
    close_desc  = closing.get('description', '')
    if close_desc:
        close_lines.append(f"> {close_desc}")
        close_lines.append("")

    contact_lines = []
    if wu:                         contact_lines.append(f"🌐 **Website:** {wu}")
    if contact.get('phone'):       contact_lines.append(f"📞 **Phone:** {contact['phone']}")
    if contact.get('email'):       contact_lines.append(f"📧 **Email:** {contact['email']}")
    if contact.get('address'):     contact_lines.append(f"📍 **Address:** {contact['address']}")
    close_lines.extend(contact_lines)
    cards.append('\n'.join(close_lines))

    # Join all cards with explicit break markers
    return '\n\n---\n\n'.join(cards)


# ── Gamma API call ───────────────────────────────────────────────

def generate_with_gamma(company_data: dict,
                         gamma_api_key: str,
                         primary_hex: str,
                         accent_hex: str,
                         export_pptx: bool = True) -> dict:
    """
    Generate a presentation using Gamma AI and return results dict:
      {
        'gamma_url':  str,          # shareable Gamma link
        'export_url': str | None,   # PPTX download URL (expires ~1 week)
        'pptx_bytes': bytes | None, # downloaded PPTX bytes
        'theme_id':   str,          # Gamma theme used
      }

    Raises ValueError on API / auth errors.
    """
    cn       = company_data.get('company_name', 'Company')
    industry = company_data.get('industry_type', 'other')
    num_slides = len(company_data.get('slides', []))

    theme_id = pick_gamma_theme(industry, primary_hex)
    prompt   = build_gamma_prompt(company_data)

    headers = {
        'Authorization': f'Bearer {gamma_api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    payload = {
        'inputText':  prompt,
        'themeId':    theme_id,
        'format':     'presentation',
        # 'generate' lets Gamma's AI design beautiful layouts from the outline.
        # 'preserve' bypasses the AI — that's why the old output was unimpressive.
        'textMode':   'generate',
        # cardSplit='inputTextBreaks' tells Gamma to honour the '---' separators
        # in our prompt, so each section becomes exactly one slide.
        'cardSplit':  'inputTextBreaks',
        'cardOptions': {
            'dimensions': '16x9',
        },
        'imageOptions': {
            # AI-generated images match content better than stock photos
            'source':      'aiGenerated',
            'stylePreset': 'photorealistic',
        },
        'textOptions': {
            'language': 'en-in',
            'tone':     'professional',
            # 'detailed' gives richer slide content vs 'medium'
            'amount':   'detailed',
        },
    }
    if export_pptx:
        payload['exportAs'] = 'pptx'

    resp = requests.post(
        f'{GAMMA_API_BASE}/generate',
        headers=headers,
        json=payload,
        timeout=180,
    )

    if resp.status_code == 401:
        raise ValueError(
            'Invalid Gamma API key. '
            'Get yours at https://gamma.app/settings/api'
        )
    if resp.status_code == 403:
        raise ValueError(
            'Gamma API access denied — check your plan supports API generation.'
        )
    if resp.status_code not in (200, 201, 202):
        raise ValueError(
            f'Gamma API error {resp.status_code}: {resp.text[:400]}'
        )

    data = resp.json()

    # Handle async generation (202 Accepted)
    if resp.status_code == 202:
        gen_id = data.get('generationId') or data.get('id', '')
        if gen_id:
            data = _poll_generation(gen_id, headers)

    gamma_url  = (data.get('gammaUrl') or data.get('url') or
                  f"https://gamma.app/docs/{data.get('id','')}")
    export_url = data.get('exportUrl') or data.get('pptxUrl')

    pptx_bytes = None
    if export_url:
        try:
            dl = requests.get(export_url, timeout=90)
            if dl.status_code == 200:
                pptx_bytes = dl.content
        except Exception:
            pass

    return {
        'gamma_url':  gamma_url,
        'export_url': export_url,
        'pptx_bytes': pptx_bytes,
        'theme_id':   theme_id,
    }


def _poll_generation(gen_id: str, headers: dict,
                     max_wait: int = 120, interval: int = 5) -> dict:
    """Poll a Gamma async generation until it completes."""
    import time
    for _ in range(max_wait // interval):
        time.sleep(interval)
        resp = requests.get(
            f'{GAMMA_API_BASE}/generations/{gen_id}',
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            status = data.get('status', '').lower()
            if status in ('completed', 'done', 'success', ''):
                return data
            if status in ('failed', 'error'):
                raise ValueError(f'Gamma generation failed: {data.get("error","unknown")}')
    raise ValueError('Gamma generation timed out. Try again or use Classic PPTX mode.')


# ── Theme display info ───────────────────────────────────────────

THEME_DISPLAY = {
    'stratos':      ('🌌 Stratos',    'Dark navy gradient · High-contrast · Tech'),
    'nebulae':      ('🌠 Nebulae',    'Dark space gradient · Vibrant highlights'),
    'borealis':     ('🌊 Borealis',   'Dark navy · Teal & green neon accents'),
    'founder':      ('⚫ Founder',    'Dark minimal · Clean sans-serif · Modern'),
    'aurora':       ('🌅 Aurora',     'Dark gradient · Fuchsia & purple'),
    'electric':     ('⚡ Electric',   'Dark gradient · Orange & pink highlights'),
    'rush':         ('🔴 Rush',       'Red & white · Bold & vibrant'),
    'marine':       ('🌊 Marine',     'Dark navy · White · Classic'),
    'consultant':   ('📋 Consultant', 'Light blue · White · Corporate'),
    'ash':          ('⬛ Ash',        'Black & white · Geometric · Formal'),
    'slate':        ('🪨 Slate',      'Dark gray · Corporate · Subtle'),
    'sage':         ('🌿 Sage',       'Light green-beige · Clean · Healthcare'),
    'serene':       ('🔵 Serene',     'Sky blue · White · Calm & simple'),
    'sprout':       ('🌱 Sprout',     'Soft mint green · Earthy · Natural'),
    'peach':        ('🍑 Peach',      'Warm peach-orange · Vibrant · Fresh'),
    'terracotta':   ('🏺 Terracotta', 'Earthy warm tones · Organic · Classic'),
    'gold-leaf':    ('🏆 Gold Leaf',  'Champagne gold · Ivory · Luxury'),
    'creme':        ('🤍 Creme',      'Cream & beige · Elegant · Minimal'),
    'onyx':         ('⚫ Onyx',       'Black & white · Luxury · Minimal'),
    'icebreaker':   ('❄️ Icebreaker', 'Light blue & white · Clean · Professional'),
    'howlite':      ('⬜ Howlite',    'White & black · Minimal · Clean'),
    'chimney-smoke':('🌫️ Chimney Smoke','Light gray gradient · Corporate · Quiet'),
    'default-light':('📄 Basic Light', 'Clean light blue & white · Simple'),
}

def theme_display_name(theme_id: str) -> tuple:
    return THEME_DISPLAY.get(theme_id, (f'✨ {theme_id.title()}', 'Gamma theme'))
