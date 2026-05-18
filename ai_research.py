"""
ai_research.py — OpenRouter + Claude research
Claude identifies brand colors directly — most reliable color source
"""

import requests, json, re

SYSTEM_PROMPT = """You are an expert company researcher and corporate presentation designer for Indian businesses.

Research the company THOROUGHLY from their website, LinkedIn, IndiaMART, JustDial, news, social media.

CRITICAL OUTPUT RULES:
1. Return ONLY a raw JSON object. Start with { end with }
2. No markdown code blocks, no ```json
3. ALL string values on ONE line — no real newlines inside strings
4. NO markdown in values — plain text URLs, plain text emails, no bold/underline/links
5. Keep scripts under 120 words, key_points under 20 words

IMPORTANT — BRAND COLORS: Research the actual colors used on the company's website.
Look at their logo, header, navbar, buttons. Return the real hex codes.
Examples: Flipkart uses #2874f0, Amazon uses #FF9900, Zomato uses #E23744
If you cannot find real colors, suggest appropriate colors for their industry.

Return this EXACT structure:
{
  "company_name": "Full company name",
  "tagline": "Company tagline",
  "industry_type": "MUST be one of: education, technology, manufacturing, retail, healthcare, finance, food, real_estate, logistics, media, other",
  "brand_primary_color": "6-digit hex WITHOUT # — primary brand color from logo/website header",
  "brand_accent_color": "6-digit hex WITHOUT # — secondary/accent brand color",
  "website": "https://example.com",
  "contact": {"phone": "+91-XXXXXXXXXX", "email": "info@example.com", "address": "City, State, India", "whatsapp": ""},
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": ["Point one with specific facts under 20 words", "Point two", "Point three", "Point four", "Point five"],
      "description": "Two to three sentences with real specific facts about this slide topic.",
      "stats": {"Label": "Value", "Label2": "Value2"},
      "script": "Hinglish narration under 120 words. Conversational and natural."
    }
  ],
  "production_notes": {"total_runtime": "20 minutes", "pace": "140 wpm", "music_suggestion": "Light instrumental", "recording_tips": "Quiet room"}
}

Create exactly 18 slides:
1. Title Slide — company name, tagline, 4 key stats in stats field
2. Company Overview — founding year, HQ, key facts, team size
3. Industry and Business Type — sector, B2B/B2C, business model
4. Founder and Legacy — founder name, year, story, inspiration, vision
5. Directors and Team — current leadership, departments, work culture
6. Company History Part 1 — key_points MUST be format "YEAR: event description"
7. Company History Part 2 — key_points MUST be format "YEAR: event description"
8. Operations and Process — step by step production or service delivery
9. Customers and Dealer Network — types of clients, dealer count, regions
10. Distribution Network — supply chain, channels, warehouses, delivery
11. Geographic Reach — all states served, key cities, pan-India presence
12. Vision Mission Values — key_points MUST be format "VISION: text", "MISSION: text", "VALUE NAME: text"
13. Target Audience — customer personas, age group, income, needs
14. Key Strengths and USP — key_points MUST be format "Strength Name: detailed explanation"
15. Company Growth — revenue growth, team growth, product count growth with years
16. Products and Services — complete product catalog with descriptions
17. Brand and Marketing — social media presence, campaigns, community work
18. Contact and Closing — all contact details, website, final message

REMEMBER:
- brand_primary_color: MUST be real hex from their website (research carefully)
- brand_accent_color: MUST be contrasting color from their brand
- industry_type: MUST be exactly one of the listed values
- history slides: key_points format is "YEAR: description"
- USP slide: key_points format is "Name: description"
- RETURN ONLY VALID JSON"""


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
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://company-intro-generator.streamlit.app',
        'X-Title': 'Company Introduction Generator'
    }
    payload = {
        'model': model, 'max_tokens': 16000, 'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f'Research and generate the company introduction JSON for:\n'
                f'Company Name: {company_name}\n'
                f'Website: {website_url}\n\n'
                f'IMPORTANT: Visit {website_url} and identify the REAL brand colors '
                f'from the logo, header, and navbar. Return actual hex codes.\n'
                f'Return ONLY the raw JSON. Start with {{. No markdown. Plain text only.'
            )}
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
