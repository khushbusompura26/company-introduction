"""
ai_research.py — OpenRouter API call with Claude
Researches company and returns structured JSON for PPT + script
"""

import requests
import json
import re

SYSTEM_PROMPT = """You are an expert company researcher and corporate presentation designer for Indian businesses.

Research the company THOROUGHLY from all sources: website, LinkedIn, IndiaMART, JustDial, news articles, social media, Google reviews, and any publicly available information.

CRITICAL RULES FOR JSON OUTPUT:
- Return ONLY valid JSON. No markdown. No explanation. Start with { and end with }.
- Do NOT use markdown formatting inside JSON values. No **bold**, no __underline__, no [links](url), no *italic*.
- URLs must be plain text: https://example.com NOT __https://example.com__
- Emails must be plain text: info@example.com NOT [info@example.com](mailto:info@example.com)
- All string values must be plain text only — no markdown symbols whatsoever.

{
  "company_name": "Full official company name",
  "tagline": "Company tagline or motto",
  "website": "https://example.com",
  "contact": {"phone": "+91-XXXXXXXXXX", "email": "info@example.com", "address": "City, State, India", "whatsapp": ""},
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": ["Detailed point 1 with real specific facts 10 to 20 words", "Point 2", "Point 3", "Point 4", "Point 5"],
      "description": "2-3 specific informative sentences providing real context for this slide.",
      "stats": {"Metric Label": "Value", "Metric 2": "Value 2"},
      "header_color": "1B3A6B",
      "accent_color": "C8A951",
      "script": "Full Hinglish narration for this slide. Write as a professional Indian corporate narrator speaks — conversational, informative, natural. 40-70 seconds of content."
    }
  ],
  "production_notes": {
    "total_runtime": "20-25 minutes",
    "pace": "130-150 words per minute",
    "music_suggestion": "Light professional instrumental background",
    "recording_tips": "Record in quiet space, mic 15-20cm distance"
  }
}

Create exactly 18-22 slides in this order:
1. Title Slide — company name, tagline, key stats
2. Company Overview — what they do, founding year, HQ, key numbers
3. Industry and Business Type — sector, B2B/B2C, model, segments
4. Founder and Legacy — who, when, why, background story, inspiration
5. Directors and Team — leadership, departments, culture
6. Company History Part 1 — format each point as "1940s: description" or "1960: event"
7. Company History Part 2 — format each point as "2005: description" or "2015: event"
8. Manufacturing and Operations — step by step process
9. Customers Served and Dealer Areas — types, network, partnerships
10. Distribution Network — physical and digital channels
11. Geographic Reach — states, cities, countries
12. Vision Mission Values — format as "VISION: ...", "MISSION: ...", "VALUE: ..."
13. Target Audience — personas, demographics, needs
14. Key Strengths and USP — format as "Strength Name: description" minimum 6
15. Company Growth and Scale — metrics, growth story
16. Products and Services Part 1 — main catalog with descriptions
17. Products and Services Part 2 — digital, supplements, packages
18. Brand and Marketing — campaigns, social media, community
19. Customer Testimonials — real quotes if available
20. Awards and Recognition — certifications, awards, press
21. Future Roadmap — expansion plans, upcoming products, goals
22. Contact and Closing — all contact details and tagline

Rules:
- key_points: 5-8 DETAILED bullets (10-20 words each with specific facts, years, numbers)
- description: 2-3 specific informative sentences with real data
- stats: 3-5 key metrics relevant to the slide. Use null if truly no stats possible.
- script: Full Hinglish narration, conversational, 40-70 seconds per slide
- History slides: format key_points as "YEAR/DECADE: event description"
- USP slides: format key_points as "Strength Name: detailed explanation"
- NO markdown inside any JSON string value

RETURN ONLY VALID JSON. Start with {"""


def _clean_markdown(text: str) -> str:
    """
    Remove markdown formatting that Claude sometimes adds inside JSON strings.
    This prevents JSON parse failures caused by markdown symbols.
    """
    # Remove markdown links: [text](url) → url
    text = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'\2', text)

    # Remove bold underline: __text__ → text
    text = re.sub(r'__([^_]*)__', r'\1', text)

    # Remove bold asterisks: **text** → text
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)

    # Remove italic asterisk: *text* → text (careful not to break things)
    text = re.sub(r'\*([^*\n]+)\*', r'\1', text)

    # Remove italic underscore: _text_ → text (only inside JSON strings)
    text = re.sub(r'(?<=["\s])_([^_\n]+)_(?=[",\s}])', r'\1', text)

    return text


def research_company(company_name: str, website_url: str, api_key: str,
                     model: str = 'anthropic/claude-sonnet-4-6') -> dict:
    """
    Call OpenRouter API with Claude to research company and generate slides data.
    Returns parsed JSON dict with company_name, slides[], production_notes, etc.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://company-intro-generator.streamlit.app',
        'X-Title': 'Company Introduction Generator'
    }

    payload = {
        'model': model,
        'max_tokens': 8000,
        'temperature': 0.3,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': (
                    f'Research and generate the complete company introduction JSON for:\n'
                    f'Company Name: {company_name}\n'
                    f'Website: {website_url}\n\n'
                    f'IMPORTANT: Return ONLY valid JSON. No markdown formatting inside values. '
                    f'Plain text only. Start with {{'
                )
            }
        ]
    }

    resp = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=120
    )

    if resp.status_code != 200:
        raise ValueError(
            f'OpenRouter API error {resp.status_code}: {resp.text[:400]}'
        )

    content = resp.json()['choices'][0]['message']['content'].strip()

    # ── Clean up AI response ───────────────────────────────────

    # Strip markdown code fences if present
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)

    # Extract JSON object boundaries
    start = content.find('{')
    end   = content.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No JSON object found in AI response. Preview: {content[:300]}')

    raw = content[start:end + 1]

    # Remove markdown formatting that Claude sometimes adds inside string values
    raw = _clean_markdown(raw)

    # ── Parse JSON ─────────────────────────────────────────────
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        # Try a more aggressive clean and retry
        raw_aggressive = re.sub(r'[^\x00-\x7F]', '', raw)   # strip non-ASCII
        try:
            data = json.loads(raw_aggressive)
        except json.JSONDecodeError:
            raise ValueError(
                f'JSON parse failed: {e}. '
                f'Preview: {raw[max(0, e.pos-100):e.pos+100]}'
            )

    # ── Validate ───────────────────────────────────────────────
    slides = data.get('slides', [])
    if len(slides) < 5:
        raise ValueError(
            f'Only {len(slides)} slides generated — too few. '
            'Check API credits or try again.'
        )

    # ── Normalise slides ───────────────────────────────────────
    data['slides'] = [
        {
            'slide_number': s.get('slide_number', i + 1),
            'title':        str(s.get('title', f'Slide {i+1}')),
            'key_points':   [str(p) for p in s.get('key_points', [])],
            'description':  str(s.get('description', '')),
            'stats':        s.get('stats') if isinstance(s.get('stats'), dict) else None,
            'header_color': s.get('header_color', '1B3A6B'),
            'accent_color': s.get('accent_color', 'C8A951'),
            'script':       str(s.get('script', '')),
        }
        for i, s in enumerate(slides)
    ]

    return data
