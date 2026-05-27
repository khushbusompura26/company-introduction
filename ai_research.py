"""
ai_research.py — OpenRouter + Claude research
Uses real website content as primary source to prevent hallucination.
"""

import requests, json, re
from urllib.parse import urljoin

# ── Website content scraper ─────────────────────────────────────

def _scrape_website_text(url: str, max_chars: int = 10000) -> str:
    """
    Fetch the homepage (and /about page if found) and return clean plain text.
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

    pages_to_try = [url]
    # Try common about page paths — including Shopify (/pages/about-us) and WordPress (/about) patterns
    for suffix in ('/pages/about-us', '/pages/about', '/about-us', '/about',
                   '/company', '/our-story', '/pages/our-story', '/pages/company'):
        pages_to_try.append(urljoin(url.rstrip('/') + '/', suffix.lstrip('/')))

    for page_url in pages_to_try[:5]:
        try:
            r = requests.get(page_url, timeout=10, headers=hdrs, allow_redirects=True)
            if r.status_code == 200:
                text = _clean(r.text)
                if len(text) > 200:
                    collected.append(f"[PAGE: {page_url}]\n{text[:4000]}")
        except Exception:
            pass

    combined = '\n\n'.join(collected)
    return combined[:max_chars] if combined else ''


# ── System prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a corporate presentation designer creating an introduction deck for an Indian business.

═══════════════════════════════════════════════════
ACCURACY RULES — STRICTLY FOLLOW — NO EXCEPTIONS
═══════════════════════════════════════════════════
1. USE ONLY VERIFIED FACTS — information from the website content provided, or facts you are 100% certain about from well-known public sources.
2. DO NOT INVENT OR ESTIMATE — never fabricate specific numbers, revenue figures, employee counts, dealer counts, award names, founding years, or statistics.
3. WHEN IN DOUBT → use "—" as the value. It is better to show "—" than a wrong number.
4. SMALL / UNKNOWN COMPANIES — if the company is not well-known and the website does not mention a specific fact, describe what they DO (their service/product) rather than making up metrics.
5. HISTORY SLIDES — only include years and events you are CERTAIN about. If fewer than 4 real events are known, use fewer bullet points. Do NOT invent milestones.
6. STATS FIELDS — only fill stats with real values found in the website content or widely known public data. If no real stats are available, set "stats": null.
7. CONTACT DETAILS — use only what appears on the website. Never invent phone numbers or emails.

OUTPUT RULES:
- Return ONLY a raw JSON object. Start with { end with }
- No markdown code blocks, no ```json
- ALL string values on ONE line — no real newlines inside strings
- NO markdown in values — plain text only
- key_points: under 20 words each
- script: under 120 words, conversational Hinglish

BRAND COLORS:
- Look at the website content for clues about colors (logo descriptions, hex codes, color names)
- For well-known brands you recognise, use their actual brand colors
- If genuinely unknown, suggest a professional color appropriate for the industry

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
      "key_points": ["Verified fact 1", "Verified fact 2", "Verified fact 3"],
      "description": "2-3 sentences using only verified or website-sourced facts.",
      "stats": {"Label": "Value"},
      "script": "Hinglish narration under 120 words."
    }
  ],
  "production_notes": {"total_runtime": "20 minutes", "pace": "140 wpm", "music_suggestion": "Light instrumental", "recording_tips": "Quiet room"}
}

Create exactly 18 slides:
1.  Title Slide — company name, tagline, key stats (only verified ones)
2.  Company Overview — founding year, HQ, what they do, team size if known
3.  Industry and Business Type — sector, B2B/B2C, business model
4.  Founder and Legacy — founder name and story (only if known/verifiable)
5.  Directors and Team — leadership names if available, else describe team culture
6.  Company History Part 1 — key_points format: "YEAR: event" — ONLY VERIFIED events
7.  Company History Part 2 — key_points format: "YEAR: event" — ONLY VERIFIED events
8.  Operations and Process — how they deliver their product/service (can be general)
9.  Customers and Dealer Network — client types and regions (general if specifics unknown)
10. Distribution Network — how products/services reach customers
11. Geographic Reach — states/cities served (only if verifiable, else describe scope)
12. Vision Mission Values — key_points format: "VISION: text", "MISSION: text", "VALUE: text"
13. Target Audience — customer personas, demographics
14. Key Strengths and USP — key_points format: "Strength Name: explanation"
15. Company Growth — growth story with real data; if unavailable describe trajectory
16. Products and Services — actual product/service catalog from website
17. Brand and Marketing — online presence, campaigns if known
18. Contact and Closing — real contact details from website

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
        'model': model, 'max_tokens': 16000, 'temperature': 0.1,
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
