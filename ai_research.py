"""
ai_research.py — OpenRouter + Claude research
Uses real website content as primary source to prevent hallucination.
"""

import requests, json, re
from urllib.parse import urljoin

# ── Website content scraper ─────────────────────────────────────

def _scrape_website_text(url: str, max_chars: int = 18000) -> str:
    """
    Fetch the homepage + multiple key pages and return clean plain text.
    Tries homepage, about, team, products/services, contact, catalogue pages.
    Used as grounding context for the AI to prevent hallucination.
    """
    UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    hdrs = {'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.8'}
    collected = []

    def _clean(html: str) -> str:
        # Remove script, style, nav, footer, header tags and their content
        html = re.sub(r'<(script|style|noscript|nav|footer|iframe)[^>]*>.*?</\1>',
                      ' ', html, flags=re.I | re.DOTALL)
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Collapse whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    base = url.rstrip('/')
    # Comprehensive list: homepage first, then all key pages
    # Covers Shopify (/pages/*), WordPress (/about, /team), standard (/services, /products)
    suffixes = [
        '',                     # homepage
        '/pages/about-us', '/pages/about', '/pages/our-story', '/pages/company',
        '/about-us', '/about', '/our-story', '/company',
        '/team', '/our-team', '/pages/team', '/pages/our-team', '/leadership',
        '/services', '/products', '/catalogue', '/catalog',
        '/pages/services', '/pages/products', '/pages/catalogue',
        '/contact', '/contact-us', '/pages/contact', '/pages/contact-us',
    ]

    visited = set()
    for suffix in suffixes:
        page_url = base + suffix if suffix else url
        if page_url in visited:
            continue
        visited.add(page_url)
        try:
            r = requests.get(page_url, timeout=10, headers=hdrs, allow_redirects=True)
            if r.status_code == 200:
                text = _clean(r.text)
                if len(text) > 300:
                    collected.append(f"[PAGE: {page_url}]\n{text[:4000]}")
                    if len('\n\n'.join(collected)) >= max_chars:
                        break
        except Exception:
            pass

    combined = '\n\n'.join(collected)
    return combined[:max_chars] if combined else ''


# ── System prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a corporate presentation designer creating a comprehensive, detailed introduction deck for an Indian business.

═══════════════════════════════════════════════════
ACCURACY RULES — STRICTLY FOLLOW — NO EXCEPTIONS
═══════════════════════════════════════════════════
1. USE ONLY VERIFIED FACTS — information from the website content provided, or facts you are 100% certain about.
2. DO NOT INVENT OR ESTIMATE — never fabricate numbers, revenue, employee counts, dealer counts, award names, founding years, or statistics.
3. WHEN IN DOUBT → use "—". It is better to show "—" than a wrong number.
4. SMALL / UNKNOWN COMPANIES — describe what they DO rather than inventing metrics.
5. HISTORY SLIDES — only include years/events you are CERTAIN about. Do NOT invent milestones.
6. STATS FIELDS — only fill with real values from the website. If unavailable, set "stats": null.
7. CONTACT DETAILS — use only what appears on the website. Never invent phone/email.

CONTENT DEPTH RULES — EVERY SLIDE MUST BE RICH AND COMPLETE:
- key_points: 6-8 per slide. Each point must be 20-35 words — detailed, informative, with context. NOT one-liners.
- description: 4-6 sentences. Thorough, informative, reads like a professional paragraph.
- script: 200-280 words per slide. Conversational Hinglish narration — professional Indian corporate video style. Detailed enough that anyone can record directly without adding anything.
- stats: Include whenever real data is available — founding year, team size, product count, cities, etc.
- Every slide must feel COMPLETE and CONTENT-RICH — no sparse or minimal slides.

OUTPUT RULES:
- Return ONLY a raw JSON object. Start with { end with }
- No markdown code blocks, no ```json
- ALL string values on ONE line — no real newlines inside strings
- NO markdown in values — plain text only

BRAND COLORS:
- Look at website content for hex codes, color names, logo descriptions
- For well-known brands, use their actual brand colors
- If unknown, suggest a professional color for the industry

SLIDE COUNT: Create between 15-25 slides based on available data. If a topic has rich data, split into Part 1 and Part 2. If a topic has little data, keep it brief or merge. Let the data drive the slide count naturally. Minimum 15 slides.

Return this EXACT JSON structure:
{
  "company_name": "Full official company name",
  "tagline": "Company tagline — from website if available, else a factual short description",
  "industry_type": "MUST be one of: education, technology, manufacturing, retail, healthcare, finance, food, real_estate, logistics, media, other",
  "brand_primary_color": "6-digit hex WITHOUT #",
  "brand_accent_color": "6-digit hex WITHOUT #",
  "website": "https://example.com",
  "contact": {"phone": "from website or —", "email": "from website or —", "address": "from website or —", "whatsapp": ""},
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": ["Detailed point 1 with full context and explanation — 20-35 words", "Detailed point 2"],
      "description": "4-6 sentence thorough description using only verified or website-sourced facts.",
      "stats": {"Label": "Value"},
      "script": "Detailed Hinglish narration 200-280 words. Conversational, professional, record-ready."
    }
  ],
  "production_notes": {"total_runtime": "25-35 minutes", "pace": "130-140 wpm", "music_suggestion": "Light corporate instrumental", "recording_tips": "Quiet room, professional mic, natural conversational pace, pause between slides"}
}

CREATE SLIDES IN THIS SEQUENCE — adjust count per topic based on available data:

1.  Title Slide — company name, tagline, website, contact info. Stats: most impressive verified numbers (years in business, products/services count, cities, clients, etc.)
2.  Company Overview — detailed description of what company does. Fact cards: founded, HQ, size, website, email, phone, social media handles
3.  Industry & Business Type — industry classification, sector, B2B/B2C/both, business model, nature of operations, business segments
4.  Our Founder & Legacy — who founded it, when, why, their background and personal story, what inspired them. Only verified info — use "—" if not on website
5.  Directors / Owners & Team — current leadership/owners, key team departments and what each does, team size and culture
6.  Company History Part 1 — key_points format: "YEAR: detailed event description" — decade-by-decade from founding. ONLY VERIFIED milestones
7.  Company History Part 2 — key_points format: "YEAR: detailed event description" — continued to present day (include if enough verified data exists)
8.  Operations & Service Delivery — step-by-step how the company creates and delivers its product/service: facilities, process, quality, logistics
9.  Customers Served & Dealer Network — who the customers are (types, segments, industries), dealer/partner/franchise network, key customer statistics
10. Distribution Network & Digital Presence — physical distribution (offices, branches, agents, distributors) + all digital channels (website, app, social media, e-commerce, WhatsApp)
11. Geographic Reach — cities, states, countries served. Primary vs secondary markets. Export or international presence if any
12. Vision, Mission & Values — key_points format: "VISION: full statement", "MISSION: full statement", "VALUE: name — detailed explanation". Give full detailed statements
13. Target Audience — detailed customer personas: who they are, demographics, what they need, why they choose this company, which products they use
14. Key Strengths & USP — key_points format: "Strength Name: detailed explanation of why this is a real differentiator" — minimum 6 genuine strengths with real explanations
15. Company Growth & Scale — growth story with real data if available; metric cards showing scale; narrative of how company has grown
16. Products & Services Part 1 — complete detailed breakdown: every product/service category with descriptions, variants, who each is for
17. Products & Services Part 2 — continued catalog (create this slide if the product/service range is large)
[Add any additional slides relevant to this specific company based on website data — examples: Awards & Recognition, CSR Initiatives, Technology & Innovation, Future Roadmap, Customer Testimonials, Brand & Marketing, Digital Platform Features, etc.]
Last Slide: Contact & Closing — all contact details, social media handles, all addresses, closing tagline

RETURN ONLY VALID JSON"""


def _sanitize(raw: str) -> str:
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    raw = re.sub(r'\[([^\]]*)\]\(mailto:[^)]*\)', r'\1', raw)
    raw = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'\2', raw)
    raw = re.sub(r'__((?:(?!__).)+?)__', r'\1', raw, flags=re.DOTALL)
    raw = re.sub(r'\*\*((?:(?!\*\*).)+?)\*\*', r'\1', raw, flags=re.DOTALL)
    result = []; in_str = False; i = 0
    while i < len(raw):
        c = raw[i]
        if c == '\\' and in_str and i + 1 < len(raw):
            result.append(c); result.append(raw[i + 1]); i += 2; continue
        if c == '"':
            in_str = not in_str; result.append(c); i += 1; continue
        if in_str:
            if c == '\n': result.append('\\n')
            elif c == '\r': pass
            elif c == '\t': result.append('\\t')
            else: result.append(c)
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def _valid_hex(h: str) -> bool:
    return bool(h and re.match(r'^[0-9A-Fa-f]{6}$', h.strip().lstrip('#')))


def research_company(company_name: str, website_url: str, api_key: str,
                     model: str = 'anthropic/claude-sonnet-4-6') -> dict:

    # ── Step 0: Scrape real website content to ground the AI ────
    website_text = _scrape_website_text(website_url)
    if website_text:
        context_block = (
            f"WEBSITE CONTENT (use as primary source of facts):\n"
            f"{'─'*60}\n"
            f"{website_text}\n"
            f"{'─'*60}\n\n"
        )
    else:
        context_block = (
            "NOTE: Website content could not be fetched. "
            "Use only well-known public facts about this company. "
            "For anything uncertain, use '—' instead of guessing.\n\n"
        )

    user_message = (
        f"Generate the company introduction JSON for:\n"
        f"Company Name: {company_name}\n"
        f"Website: {website_url}\n\n"
        f"{context_block}"
        f"STRICT REMINDER: Only include facts found in the website content above "
        f"or that you are 100% certain about. "
        f"Use '—' for any stat or detail you cannot verify. "
        f"Return ONLY the raw JSON. Start with {{. No markdown."
    )

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://company-intro-generator.streamlit.app',
        'X-Title': 'Company Introduction Generator'
    }
    payload = {
        'model': model, 'max_tokens': 32000, 'temperature': 0.1,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': user_message},
        ]
    }

    resp = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers, json=payload, timeout=180
    )
    if resp.status_code != 200:
        raise ValueError(f'OpenRouter API error {resp.status_code}: {resp.text[:400]}')

    content = resp.json()['choices'][0]['message']['content'].strip()
    start = content.find('{'); end = content.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No JSON found. Preview: {content[:200]}')

    clean = _sanitize(content[start:end + 1])
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        ctx = clean[max(0, e.pos - 80):e.pos + 80]
        raise ValueError(f'JSON parse error at pos {e.pos}: {e.msg}\nContext: ...{ctx}...')

    slides = data.get('slides', [])
    if len(slides) < 5:
        raise ValueError(f'Only {len(slides)} slides returned. Check API credits.')

    # Validate and clean brand colors
    p_hex = str(data.get('brand_primary_color', '')).strip().lstrip('#').upper()
    a_hex = str(data.get('brand_accent_color',  '')).strip().lstrip('#').upper()
    data['brand_primary_color'] = p_hex if _valid_hex(p_hex) else '1B3A6B'
    data['brand_accent_color']  = a_hex if _valid_hex(a_hex) else 'C8A951'

    # Normalise slides
    data['slides'] = [{
        'slide_number': int(s.get('slide_number', i + 1)),
        'title':        str(s.get('title', f'Slide {i+1}')),
        'key_points':   [str(p) for p in (s.get('key_points') or [])],
        'description':  str(s.get('description', '')),
        'stats':        s.get('stats') if isinstance(s.get('stats'), dict) else None,
        'script':       str(s.get('script', '')),
    } for i, s in enumerate(slides)]

    return data
