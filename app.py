"""
app.py — Company Introduction Generator
Colors: AI identifies brand colors + web scraping validates
Layouts: 3 distinct styles auto-selected by industry
"""

import streamlit as st, re

st.set_page_config(page_title="Company Introduction Generator", page_icon="🎯",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""<style>
.block-container{max-width:720px;padding-top:1.5rem}
h1{color:#1B3A6B!important;text-align:center}
.subtitle{text-align:center;color:#64748B;margin-top:-.5rem;margin-bottom:1.5rem;font-size:1rem}
div[data-testid="stFormSubmitButton"]>button{background-color:#e8694a!important;color:white!important;
  font-weight:700!important;font-size:16px!important;border:none!important;border-radius:10px!important;
  padding:.65rem!important;width:100%!important}
div[data-testid="stFormSubmitButton"]>button:hover{background-color:#d4593c!important}
.stDownloadButton>button{font-weight:600!important;border-radius:10px!important;width:100%!important;padding:.6rem!important}
label{font-weight:600!important;color:#1B3A6B!important;letter-spacing:.02em}
.success-card{background:#E8F8EE;border-left:4px solid #1D9E75;padding:1rem 1.2rem;border-radius:8px;margin:1rem 0}
.color-row{display:flex;align-items:center;gap:8px;margin:6px 0}
.swatch{width:28px;height:28px;border-radius:6px;border:1px solid #ccc;display:inline-block}
</style>""", unsafe_allow_html=True)

for k,v in {'pptx_bytes':None,'docx_bytes':None,'company_data':None,'gen_name':None,
             'slide_count':0,'safe_name':None,'primary_hex':'1B3A6B','accent_hex':'C8A951',
             'style_used':None,'industry':None,'color_source':None}.items():
    if k not in st.session_state: st.session_state[k]=v

STYLE_INFO = {
    'professional': ('📋 Professional', 'Dark title · White slides · Left accent bars'),
    'bold':         ('⚡ Bold Split',   'Half-page color panel · Content on right'),
    'cards':        ('🃏 Clean Cards',  'Light background · Floating white cards · Pill stats'),
}

st.markdown("# 🎯 Company Introduction Generator")
st.markdown('<p class="subtitle">Auto-branded PPT + Hinglish Script · Brand colors detected from website · 3 distinct layouts</p>', unsafe_allow_html=True)
st.divider()

with st.form("gen_form", clear_on_submit=False):
    company_name = st.text_input("COMPANY NAME *", placeholder="e.g. Shivalal Agarwala & Co.")
    website_url  = st.text_input("WEBSITE URL *",  placeholder="https://www.yourcompany.com")
    api_key      = st.text_input("OPENROUTER API KEY *", type="password", placeholder="sk-or-v1-...")
    model = "anthropic/claude-sonnet-4-6"
    submitted = st.form_submit_button("🚀  Generate Both Documents", use_container_width=True)

if submitted:
    errors = []
    if not company_name.strip(): errors.append("Company name is required.")
    if not website_url.strip():  errors.append("Website URL is required.")
    if not api_key.strip():      errors.append("OpenRouter API key is required.")
    if website_url.strip() and not website_url.startswith(('http://','https://')):
        errors.append("Website URL must start with http:// or https://")
    if errors:
        for e in errors: st.error(f"⚠️ {e}")
        st.stop()

    for k in ('pptx_bytes','docx_bytes','company_data','gen_name','slide_count','safe_name','style_used','industry','color_source'):
        st.session_state[k] = None

    from ai_research     import research_company
    from ppt_builder     import build_presentation
    from doc_builder     import build_script_document
    from color_extractor import extract_website_colors

    progress = st.progress(0, text="Starting…")
    status   = st.empty()

    try:
        # Step 1: scrape website colors (fast first pass)
        status.info("🎨 **Scanning website** for brand colors…")
        progress.progress(8, text="Scanning CSS and meta tags…")
        scraped_primary, scraped_accent = extract_website_colors(website_url.strip())

        # Step 2: AI research (Claude also identifies brand colors)
        status.info(f"🔍 **Researching** {company_name} with Claude AI… *(30–60 seconds)*")
        progress.progress(15, text="Calling Claude AI…")
        company_data = research_company(
            company_name.strip(), website_url.strip(), api_key.strip(), model
        )

        slide_count = len(company_data.get('slides', []))
        gen_name    = company_data.get('company_name', company_name)
        industry    = company_data.get('industry_type', 'other')
        ai_primary  = company_data.get('brand_primary_color', '')
        ai_accent   = company_data.get('brand_accent_color', '')

        # Decide which colors to use:
        # AI-identified colors are most accurate; scraped colors are visual verification
        def valid(h): return bool(h and re.match(r'^[0-9A-Fa-f]{6}$', h))

        # Use scraped if they're not the default navy/gold AND are valid
        scraped_is_real = (scraped_primary != '1B3A6B' and valid(scraped_primary))

        if scraped_is_real:
            primary_hex = scraped_primary
            accent_hex  = scraped_accent if valid(scraped_accent) else (ai_accent if valid(ai_accent) else 'C8A951')
            color_source = f"Website CSS (#{primary_hex} + #{accent_hex})"
        elif valid(ai_primary):
            primary_hex = ai_primary
            accent_hex  = ai_accent if valid(ai_accent) else 'C8A951'
            color_source = f"Claude AI identified (#{primary_hex} + #{accent_hex})"
        else:
            primary_hex = '1B3A6B'
            accent_hex  = 'C8A951'
            color_source = "Default (website did not expose brand colors)"

        st.session_state.primary_hex  = primary_hex
        st.session_state.accent_hex   = accent_hex
        st.session_state.color_source = color_source
        st.session_state.industry     = industry

        progress.progress(48, text=f"Got {slide_count} slides! Industry: {industry}")
        status.success(f"✅ Research done — {slide_count} slides · {color_source}")

        # Step 3: Build PPT
        status.info(f"📊 **Building presentation** ({STYLE_INFO.get(company_data.get('_style',''), ('',''))[0]} layout)…")
        progress.progress(62, text="Generating PPTX…")
        pptx_bytes, style_used = build_presentation(company_data, primary_hex, accent_hex)
        progress.progress(82, text="PPTX done! Building script…")

        # Step 4: Build DOCX
        status.info("📄 **Creating Hinglish video script…**")
        docx_bytes = build_script_document(company_data)
        progress.progress(100, text="Complete!")
        status.empty(); progress.empty()

        st.session_state.pptx_bytes   = pptx_bytes
        st.session_state.docx_bytes   = docx_bytes
        st.session_state.company_data = company_data
        st.session_state.gen_name     = gen_name
        st.session_state.slide_count  = slide_count
        st.session_state.style_used   = style_used
        st.session_state.safe_name    = "".join(
            c for c in gen_name if c.isalnum() or c in (' ','-')
        ).strip().replace(' ','_')

    except ValueError as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Generation failed:** {e}")
        st.info("💡 Check your API key and credits at openrouter.ai")
    except Exception as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Unexpected error:** {e}"); st.exception(e)

if st.session_state.pptx_bytes and st.session_state.docx_bytes:
    gn   = st.session_state.gen_name;  sc   = st.session_state.slide_count
    sn   = st.session_state.safe_name; pb   = st.session_state.pptx_bytes
    db   = st.session_state.docx_bytes; ph  = st.session_state.primary_hex
    ah   = st.session_state.accent_hex; sw  = st.session_state.style_used
    ind  = st.session_state.industry;   cs  = st.session_state.color_source
    cd   = st.session_state.company_data

    sname, sdesc = STYLE_INFO.get(sw, ('📋 Professional','Clean professional layout'))

    st.markdown(
        f'<div class="success-card">'
        f'🎉 <strong>Both documents ready!</strong><br><br>'
        f'<strong>{gn}</strong> &nbsp;·&nbsp; {sc} slides &nbsp;·&nbsp; Industry: <em>{ind}</em><br><br>'
        f'<strong>Design: {sname}</strong> — {sdesc}<br><br>'
        f'<div class="color-row">'
        f'<span class="swatch" style="background:#{ph}"></span>'
        f'<strong>#{ph}</strong> &nbsp;&nbsp;'
        f'<span class="swatch" style="background:#{ah}"></span>'
        f'<strong>#{ah}</strong>'
        f'</div>'
        f'<small style="color:#888">{cs}</small>'
        f'</div>', unsafe_allow_html=True)

    st.divider(); st.subheader("📥 Download Your Documents")
    st.caption("Both files stay available — download one, then the other.")

    d1, d2 = st.columns(2)
    with d1:
        st.download_button("📊  Download Presentation (.pptx)", data=pb,
            file_name=f"{sn}_Presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True, key="dl_pptx")
        st.caption(f"{sname} · #{ph} theme · {sc} slides")
    with d2:
        st.download_button("📄  Download Video Script (.docx)", data=db,
            file_name=f"{sn}_Video_Script.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True, key="dl_docx")
        st.caption("Hinglish narration · Slide-by-slide")

    st.divider()
    if st.button("🔄  Generate for a different company", use_container_width=True):
        for k in ('pptx_bytes','docx_bytes','company_data','gen_name','slide_count','safe_name','style_used','industry','color_source'):
            st.session_state[k] = None
        st.rerun()

    if cd:
        with st.expander("👁  Preview slide content", expanded=False):
            for sl in cd.get('slides',[]):
                st.markdown(f"**Slide {sl['slide_number']}: {sl['title']}**")
                for pt in sl.get('key_points',[])[:4]: st.markdown(f"&nbsp;&nbsp;▸ {pt}")
                stats = sl.get('stats')
                if stats and isinstance(stats,dict):
                    cols = st.columns(min(len(stats),4))
                    for col,(k,v) in zip(cols,stats.items()): col.metric(k,v)
                st.divider()

st.divider()
st.markdown("<p style='text-align:center;color:#AABBD4;font-size:.8rem'>Company Introduction Generator · Claude AI via OpenRouter · python-pptx + python-docx</p>", unsafe_allow_html=True)
