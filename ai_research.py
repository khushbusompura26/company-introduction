"""
ai_research.py — OpenRouter API call with Claude
Researches company and returns structured JSON for PPT + script
"""

import requests
import json
import re

SYSTEM_PROMPT = """You are an expert company researcher and corporate presentation designer for Indian businesses.

Research the company THOROUGHLY from their website, LinkedIn, IndiaMART, JustDial, news articles and social media.

STRICT OUTPUT RULES — FOLLOW EXACTLY:
1. Return ONLY a raw JSON object. Nothing else before or after it.
2. Start your response with { and end with }
3. Do NOT wrap in markdown code blocks. No ```json or ```
4. ALL string values must be on a single line. No actual line breaks inside string values.
5. Do NOT use any markdown inside string values:
   - No **bold**, no __underline__, no *italic*
   - No [text](url) link format — write URLs as plain text only
   - No mailto: links — write email addresses as plain text only
   - Correct: "website": "https://example.com"
   - Wrong:   "website": "__https://example.com/__"
   - Correct: "email": "info@example.com"
   - Wrong:   "email": "[info@example.com](mailto:info@example.com)"
6. Use \\n (escaped) if you need a line break inside a string value
7. Keep each script field under 120 words
8. Keep each key_point under 20 words

Return this exact JSON structure:
{
  "company_name": "Full company name",
  "tagline": "Company tagline",
  "website": "https://example.com",
  "contact": {
    "phone": "+91-XXXXXXXXXX",
    "email": "info@example.com",
    "address": "City, State, India",
    "whatsapp": "+91-XXXXXXXXXX"
  },
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": [
        "Point one with specific facts and numbers here",
        "Point two with specific details",
        "Point three with real information",
        "Point four with data",
        "Point five with facts"
      ],
      "description": "Two to three sentences describing this slide with real facts.",
      "stats": {"Label One": "Value", "Label Two": "Value"},
      "header_color": "1B3A6B",
      "accent_color": "C8A951",
      "script": "Hinglish narration for this slide in under 120 words. Keep it conversational and natural."
    }
  ],
  "production_notes": {
    "total_runtime": "20 minutes",
    "pace": "140 words per minute",
    "music_suggestion": "Light instrumental",
    "recording_tips": "Quiet room, mic 15cm away"
  }
}

Create exactly 18 slides covering:
1. Title Slide — name, tagline, 4 key stats
2. Company Overview — founding, HQ, key facts
3. Industry and Business Type — sector, model
4. Founder and Legacy — story, vision
5. Directors and Team — leadership, departments
6. Company History Part 1 — format: "1940s: event", "1960: event"
7. Company History Part 2 — format: "2005: event", "2015: event"
8. Operations — production process steps
9. Customers and Dealers — network, types
10. Distribution Network — channels
11. Geographic Reach — states, cities
12. Vision Mission Values — format: "VISION: ...", "MISSION: ...", "VALUE: ..."
13. Target Audience — personas, demographics
14. Key Strengths and USP — format: "Name: description" for each
15. Company Growth — metrics, milestones
16. Products and Services — full catalog
17. Brand and Marketing — social, campaigns
18. Contact and Closing — all contact details

REMEMBER: Plain text only in all string values. No markdown. No line breaks inside strings."""


def _sanitize_json(raw: str) -> str:
    # Step 1: Remove markdown code fences
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)

    # Step 2: Remove markdown links [text](url) -> url
    raw = re.sub(r'\[([^\]]*)\]\(mailto:[^)]*\)', r'\1', raw)
    raw = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'\2', raw)

    # Step 3: Remove __text__ -> text (non-greedy, handles URLs)
    raw = re.sub(r'__((?:(?!__).)+?)__', r'\1', raw, flags=re.DOTALL)

    # Step 4: Remove **text** -> text
    raw = re.sub(r'\*\*((?:(?!\*\*).)+?)\*\*', r'\1', raw, flags=re.DOTALL)

    # Step 5: Fix unescaped newlines/tabs inside JSON string values
    result = []
    in_string = False
    i = 0
    while i < len(raw):
        c = raw[i]

        if c == '\\' and in_string and i + 1 < len(raw):
            result.append(c)
            result.append(raw[i + 1])
            i += 2
            continue

        if c == '"':
            in_string = not in_string
            result.append(c)
            i += 1
            continue

        if in_string:
            if c == '\n':
                result.append('\\n')
            elif c == '\r':
                pass
            elif c == '\t':
                result.append('\\t')
            else:
                result.append(c)
        else:
            result.append(c)

        i += 1

    return ''.join(result)


def research_company(company_name: str, website_url: str, api_key: str,
                     model: str = 'anthropic/claude-sonnet-4-6') -> dict:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://company-intro-generator.streamlit.app',
        'X-Title': 'Company Introduction Generator'
    }

    payload = {
        'model': model,
        'max_tokens': 16000,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': (
                    f'Research and generate the company introduction JSON for:\n'
                    f'Company Name: {company_name}\n'
                    f'Website: {website_url}\n\n'
                    f'Return ONLY the raw JSON object. '
                    f'Start with {{ and end with }}. '
                    f'No markdown. No code blocks. '
                    f'Plain text only inside all string values.'
                )
            }
        ]
    }

    resp = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=180
    )

    if resp.status_code != 200:
        raise ValueError(f'OpenRouter API error {resp.status_code}: {resp.text[:400]}')

    raw_content = resp.json()['choices'][0]['message']['content'].strip()

    # Extract JSON object
    start = raw_content.find('{')
    end   = raw_content.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f'No JSON object found. Preview: {raw_content[:200]}')

    raw_json   = raw_content[start:end + 1]
    clean_json = _sanitize_json(raw_json)

    try:
        data = json.loads(clean_json)
    except json.JSONDecodeError as e:
        pos     = e.pos
        context = clean_json[max(0, pos - 80):pos + 80]
        raise ValueError(
            f'JSON parse failed at position {pos}: {e.msg}\n'
            f'Context around error: ...{context}...'
        )

    slides = data.get('slides', [])
    if len(slides) < 5:
        raise ValueError(
            f'Only {len(slides)} slides returned. Check your API credits at openrouter.ai'
        )

    data['slides'] = [
        {
            'slide_number': int(s.get('slide_number', i + 1)),
            'title':        str(s.get('title', f'Slide {i+1}')),
            'key_points':   [str(p) for p in (s.get('key_points') or [])],
            'description':  str(s.get('description', '')),
            'stats':        s.get('stats') if isinstance(s.get('stats'), dict) else None,
            'header_color': str(s.get('header_color', '1B3A6B')),
            'accent_color': str(s.get('accent_color', 'C8A951')),
            'script':       str(s.get('script', '')),
        }
        for i, s in enumerate(slides)
    ]

    return data
