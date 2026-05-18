"""
ai_research.py — OpenRouter API call with Claude
"""

import requests, json, re

SYSTEM_PROMPT = """You are an expert company researcher and corporate presentation designer for Indian businesses.

Research the company THOROUGHLY from their website, LinkedIn, IndiaMART, JustDial, news articles and social media.

STRICT OUTPUT RULES:
1. Return ONLY a raw JSON object. Start with { end with }
2. No markdown code blocks. No ```json
3. ALL string values on a single line — no real line breaks inside strings
4. NO markdown inside values — plain text URLs, plain text emails, no **bold**, no __underline__
5. Keep each script under 120 words. Keep each key_point under 20 words.

Return this exact structure:
{
  "company_name": "Full company name",
  "tagline": "Company tagline",
  "industry_type": "One of: education, technology, manufacturing, retail, healthcare, finance, food, real estate, other",
  "website": "https://example.com",
  "contact": {"phone": "+91-XXXXXXXXXX", "email": "info@example.com", "address": "City, State, India", "whatsapp": ""},
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "key_points": ["Point one with specific facts", "Point two", "Point three", "Point four", "Point five"],
      "description": "Two to three sentences with real specific facts.",
      "stats": {"Label": "Value"},
      "header_color": "1B3A6B",
      "accent_color": "C8A951",
      "script": "Hinglish narration under 120 words. Conversational and natural."
    }
  ],
  "production_notes": {"total_runtime": "20 minutes", "pace": "140 wpm", "music_suggestion": "Light instrumental", "recording_tips": "Quiet room"}
}

Create exactly 18 slides:
1. Title Slide — name, tagline, 4 key stats
2. Company Overview — founding, HQ, key facts
3. Industry and Business Type — sector, model
4. Founder and Legacy — story, vision (format key_points as narrative facts)
5. Directors and Team — leadership, departments
6. Company History Part 1 — format: "1940s: event", "1960: event"
7. Company History Part 2 — format: "2005: event", "2015: event"
8. Operations — production/service process
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

CRITICAL: industry_type must be exactly one of: education, technology, manufacturing, retail, healthcare, finance, food, real estate, other
RETURN ONLY VALID JSON. Plain text only."""


def _sanitize(raw: str) -> str:
    raw = re.sub(r'```json\s*','',raw); raw = re.sub(r'```\s*','',raw)
    raw = re.sub(r'\[([^\]]*)\]\(mailto:[^)]*\)', r'\1', raw)
    raw = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'\2', raw)
    raw = re.sub(r'__((?:(?!__).)+?)__', r'\1', raw, flags=re.DOTALL)
    raw = re.sub(r'\*\*((?:(?!\*\*).)+?)\*\*', r'\1', raw, flags=re.DOTALL)
    result=[]; in_str=False; i=0
    while i<len(raw):
        c=raw[i]
        if c=='\\' and in_str and i+1<len(raw):
            result.append(c); result.append(raw[i+1]); i+=2; continue
        if c=='"': in_str=not in_str; result.append(c); i+=1; continue
        if in_str:
            if c=='\n': result.append('\\n')
            elif c=='\r': pass
            elif c=='\t': result.append('\\t')
            else: result.append(c)
        else: result.append(c)
        i+=1
    return ''.join(result)


def research_company(company_name, website_url, api_key, model='anthropic/claude-sonnet-4-6'):
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
                f'Company Name: {company_name}\nWebsite: {website_url}\n\n'
                f'Return ONLY the raw JSON. Start with {{. No markdown. Plain text only.'
            )}
        ]
    }
    resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
                         headers=headers, json=payload, timeout=180)
    if resp.status_code != 200:
        raise ValueError(f'OpenRouter API error {resp.status_code}: {resp.text[:400]}')

    content = resp.json()['choices'][0]['message']['content'].strip()
    start=content.find('{'); end=content.rfind('}')
    if start==-1 or end==-1:
        raise ValueError(f'No JSON found. Preview: {content[:200]}')

    clean = _sanitize(content[start:end+1])
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        ctx = clean[max(0,e.pos-80):e.pos+80]
        raise ValueError(f'JSON parse failed at pos {e.pos}: {e.msg}\nContext: ...{ctx}...')

    slides = data.get('slides', [])
    if len(slides) < 5:
        raise ValueError(f'Only {len(slides)} slides. Check API credits at openrouter.ai')

    data['slides'] = [{
        'slide_number': int(s.get('slide_number', i+1)),
        'title':        str(s.get('title', f'Slide {i+1}')),
        'key_points':   [str(p) for p in (s.get('key_points') or [])],
        'description':  str(s.get('description', '')),
        'stats':        s.get('stats') if isinstance(s.get('stats'), dict) else None,
        'header_color': str(s.get('header_color', '1B3A6B')),
        'accent_color': str(s.get('accent_color', 'C8A951')),
        'script':       str(s.get('script', '')),
    } for i,s in enumerate(slides)]

    return data
