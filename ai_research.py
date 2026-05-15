"""
ai_research.py — OpenRouter API call with Claude
Researches company and returns structured JSON for PPT + script
"""

import requests
import json
import re

SYSTEM_PROMPT = """You are an expert company researcher and corporate presentation designer for Indian businesses.

Research the company THOROUGHLY from all sources: website, LinkedIn, IndiaMART, JustDial, news articles, social media, Google reviews, and any publicly available information.

Return ONLY valid JSON. No markdown. No explanation. Start with { and end with }.

{
  "company_name": "Full official company name",
  "tagline": "Company tagline or motto",
  "website": "website URL",
  "contact": {"phone": "", "email": "", "address": "", "whatsapp": ""},
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": ["Detailed point 1 — 10 to 20 words with real specific facts", "Point 2", "Point 3", "Point 4", "Point 5"],
      "description": "2-3 specific informative sentences providing real context for this slide.",
      "stats": {"Metric Label": "Value", "Metric 2": "Value 2"},
      "header_color": "1B3A6B",
      "accent_color": "C8A951",
      "script": "Full Hinglish (Hindi in Roman script) narration for this slide. Write as a professional Indian corporate narrator speaks — conversational, informative, natural. 40-70 seconds of content."
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
1. Title Slide — company name, tagline, key stats (years, products, clients, cities)
2. Company Overview — what they do, founding year, HQ, key numbers
3. Industry & Business Type — sector, B2B/B2C, model, segments
4. Founder & Legacy — who, when, why, background story, inspiration
5. Directors & Team — leadership, departments, culture
6. Company History Part 1 — format each point as "1940s: description" or "1960: event"
7. Company History Part 2 — format each point as "2005: description" or "2015: event"
8. Manufacturing / Operations / Service Delivery — step by step
9. Customers Served & Dealer Areas — types, network, partnerships
10. Distribution Network — physical and digital channels
11. Geographic Reach — states, cities, countries
12. Vision Mission Values — format as "VISION: ...", "MISSION: ...", "VALUE: ..."
13. Target Audience — personas, demographics, needs
14. Key Strengths & USP — format as "Strength Name: description" (minimum 6)
15. Company Growth & Scale — metrics, growth story
16. Products & Services Part 1 — main catalog with descriptions
17. Products & Services Part 2 — digital, supplements, packages
18. Brand & Marketing — campaigns, social media, community
19. Customer Testimonials — real quotes if available
20. Awards & Recognition — certifications, awards, press
21. Future Roadmap — expansion plans, upcoming products, goals
22. Contact & Closing — all contact details + tagline

Rules:
- key_points: 5-8 DETAILED bullets (10-20 words each with specific facts, years, numbers)
- description: 2-3 specific informative sentences with real data
- stats: 3-5 key metrics relevant to the slide (use null only if truly impossible)
- script: Full Hinglish narration, conversational, 40-70 seconds per slide
- History slides: format key_points as "YEAR/DECADE: event description"
- USP slides: format key_points as "Strength Name: detailed explanation"
- Vision/Values slide: format key_points as "VISION: ...", "MISSION: ...", "VALUE: ..."

RETURN ONLY VALID JSON. Start with {"""


def research_company(company_name: str, website_url: str, api_key: str,
                     model: str = 'anthropic/claude-3.5-sonnet') -> dict:
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
                    f'Return ONLY valid JSON starting with {{'
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

    # Strip markdown fences if present
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)

    # Extract JSON object
    start = content.find('{')
    end   = content.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No JSON object found in AI response. Preview: {content[:300]}')

    try:
        data = json.loads(content[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f'JSON parse failed: {e}. Preview: {content[start:start+300]}')

    # Validate
    slides = data.get('slides', [])
    if len(slides) < 5:
        raise ValueError(
            f'Only {len(slides)} slides generated — too few. '
            'Check API credits or try a different model.'
        )

    # Enrich / normalise each slide
    data['slides'] = [
        {
            'slide_number': s.get('slide_number', i + 1),
            'title':        s.get('title', f'Slide {i+1}'),
            'key_points':   [str(p) for p in s.get('key_points', [])],
            'description':  s.get('description', ''),
            'stats':        s.get('stats') if isinstance(s.get('stats'), dict) else None,
            'header_color': s.get('header_color', '1B3A6B'),
            'accent_color': s.get('accent_color', 'C8A951'),
            'script':       s.get('script', ''),
        }
        for i, s in enumerate(slides)
    ]

    return data
