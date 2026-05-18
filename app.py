"""
app.py — Company Introduction Generator
Auto-branded PPT + Hinglish script · 3 distinct design styles
"""

import streamlit as st

st.set_page_config(page_title="Company Introduction Generator", page_icon="🎯",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""<style>
.block-container{max-width:720px;padding-top:1.5rem}
h1{color:#1B3A6B!important;text-align:center}
.subtitle{text-align:center;color:#64748B;margin-top:-.5rem;margin-bottom:1.5rem;font-size:1rem}
div[data-testid="stFormSubmitButton"]>button{background-color:#e8694a!important;color:white!important;font-weight:700!important;font-size:16px!important;border:none!important;border-radius:10px!important;padding:.65rem!important;width:100%!important}
div[data-testid="stFormSubmitButton"]>button:hover{background-color:#d4593c!important}
.stDownloadButton>button{font-weight:600!important;border-radius:10px!important;width:100%!important;padding:.6rem!important}
label{font-weight:600!important;color:#1B3A6B!important;letter-spacing:.02em}
.info-card{background:#EFF3FA;border-left:4px solid #1B3A6B;padding:1rem 1.2rem;border-radius:8px;margin:1rem 0}
.success-card{background:#E8F8EE;border-left:4px solid #1D9E75;padding:1rem 1.2rem;border-radius:8px;margin:1rem 0}
.swatch{display:inline-block;width:22px;height:22px;border-radius:5px;border:1px solid #ccc;vertical-align:middle;margin-right:5px}
</style>""", unsafe_allow_html=True)

for k,v in {'pptx_bytes':None,'docx_bytes':None,'company_data':None,'gen_name':None,
             'slide_count':0,'safe_name':None,'primary_hex':'1B3A6B','accent_hex':'C8A951',
             'style_used':None,'industry':None}.items():
    if k not in st.session_state: st.session_state[k]=v

STYLE_INFO = {
    'professional': ('📋 Professional','Clean white · Left accent bars · Navy stat cards','Education · Finance · Legal · Publishing'),
    'bold':         ('⚡ Bold Split Panel','Solid color left panel · White content right · Modern feel','Technology · IT · Software · Consulting'),
    'cards':        ('🎨 Clean Cards','Light warm background · Floating white cards · Pill stats','Retail · Manufacturing · Healthcare · Food'),
}

st.markdown("# 🎯 Company Introduction Generator")
st.markdown('<p class="subtitle">Professional PPT + Hinglish Script · 3 Design Styles · Auto-branded from Website Colors</p>', unsafe_allow_html=True)

with st.expander("🎨 See the 3 design styles", expanded=False):
    c1,c2,c3=st.columns(3)
    for col,(k,(name,desc,ind)) in zip([c1,c2,c3], STYLE_INFO.items()):
        with col:
            st.markdown(f"**{name}**"); st.caption(desc); st.caption(f"*{ind}*")

st.divider()

with st.form("gen_form", clear_on_submit=False):
    company_name = st.text_input("COMPANY NAME *", placeholder="e.g. Shivalal Agarwala & Co.")
    website_url  = st.text_input("WEBSITE URL *",  placeholder="https://www.yourcompany.com")
    api_key      = st.text_input("OPENROUTER API KEY *", type="password", placeholder="sk-or-v1-...")
    model = "anthropic/claude-sonnet-4-6"
    submitted = st.form_submit_button("🚀  Generate Both Documents", use_container_width=True)

if submitted:
    errors=[]
    if not company_name.strip(): errors.append("Company name is required.")
    if not website_url.strip():  errors.append("Website URL is required.")
    if not api_key.strip():      errors.append("OpenRouter API key is required.")
    if website_url.strip() and not website_url.startswith(('http://','https://')): errors.append("Website URL must start with http:// or https://")
    if errors:
        for e in errors: st.error(f"⚠️ {e}")
        st.stop()

    for k in ('pptx_bytes','docx_bytes','company_data','gen_name','slide_count','safe_name','style_used','industry'):
        st.session_state[k]=None

    from ai_research   import research_company
    from ppt_builder   import build_presentation
    from doc_builder   import build_script_document
    from color_extractor import extract_website_colors

    progress=st.progress(0,text="Starting…"); status=st.empty()

    try:
        status.info("🎨 **Extracting brand colors** from website…")
        progress.progress(8, text="Reading website…")
        primary_hex, accent_hex = extract_website_colors(website_url.strip())
        st.session_state.primary_hex=primary_hex; st.session_state.accent_hex=accent_hex

        status.info(f"🔍 **Researching** {company_name} with Claude AI… *(30–60 sec)*")
        progress.progress(15, text="Calling Claude AI…")
        company_data = research_company(company_name.strip(), website_url.strip(), api_key.strip(), model)

        slide_count=len(company_data.get('slides',[])); gen_name=company_data.get('company_name', company_name)
        industry=company_data.get('industry_type','other')
        st.session_state.industry=industry
        progress.progress(45, text=f"Got {slide_count} slides! Industry: {industry}")

        status.info(f"📊 **Building presentation** — auto-selecting design for {industry} industry…")
        progress.progress(60, text="Generating PPTX…")
        pptx_bytes, style_used = build_presentation(company_data, primary_hex, accent_hex)
        st.session_state.style_used=style_used
        progress.progress(80, text="PPTX done!")

        status.info("📄 **Creating Hinglish video script…**")
        docx_bytes = build_script_document(company_data)
        progress.progress(100, text="Complete!")
        status.empty(); progress.empty()

        st.session_state.pptx_bytes=pptx_bytes; st.session_state.docx_bytes=docx_bytes
        st.session_state.company_data=company_data; st.session_state.gen_name=gen_name
        st.session_state.slide_count=slide_count
        st.session_state.safe_name="".join(c for c in gen_name if c.isalnum() or c in (' ','-')).strip().replace(' ','_')

    except ValueError as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Generation failed:** {e}")
        st.info("💡 Check your API key and credits at openrouter.ai")
    except Exception as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Unexpected error:** {e}"); st.exception(e)

if st.session_state.pptx_bytes and st.session_state.docx_bytes:
    gen_name=st.session_state.gen_name; slide_count=st.session_state.slide_count
    safe_name=st.session_state.safe_name; pptx_bytes=st.session_state.pptx_bytes
    docx_bytes=st.session_state.docx_bytes; primary_hex=st.session_state.primary_hex
    accent_hex=st.session_state.accent_hex; style_used=st.session_state.style_used
    industry=st.session_state.industry; company_data=st.session_state.company_data

    sname,sdesc,sind=STYLE_INFO.get(style_used, STYLE_INFO['professional'])

    st.markdown(
        f'<div class="success-card">'
        f'🎉 <strong>Both documents ready!</strong><br><br>'
        f'<strong>{gen_name}</strong> &nbsp;·&nbsp; {slide_count} slides &nbsp;·&nbsp; Industry: <em>{industry}</em><br><br>'
        f'<strong>Design: {sname}</strong> — {sdesc}<br>'
        f'<span class="swatch" style="background:#{primary_hex}"></span>#{primary_hex} &nbsp;'
        f'<span class="swatch" style="background:#{accent_hex}"></span>#{accent_hex} — from website'
        f'</div>', unsafe_allow_html=True)

    st.divider(); st.subheader("📥 Download Your Documents")
    st.caption("Both files stay available — download one, then the other.")

    dl1,dl2=st.columns(2)
    with dl1:
        st.download_button("📊  Download Presentation (.pptx)", data=pptx_bytes,
            file_name=f"{safe_name}_Presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True, key="dl_pptx")
        st.caption(f"{sname} design · #{primary_hex} · {slide_count} slides")
    with dl2:
        st.download_button("📄  Download Video Script (.docx)", data=docx_bytes,
            file_name=f"{safe_name}_Video_Script.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True, key="dl_docx")
        st.caption("Hinglish narration · Slide-by-slide")

    st.divider()
    if st.button("🔄  Generate for a different company", use_container_width=True):
        for k in ('pptx_bytes','docx_bytes','company_data','gen_name','slide_count','safe_name','style_used','industry'):
            st.session_state[k]=None
        st.rerun()

    if company_data:
        with st.expander("👁  Preview slide content", expanded=False):
            for sl in company_data.get('slides',[]):
                st.markdown(f"**Slide {sl['slide_number']}: {sl['title']}**")
                for pt in sl.get('key_points',[])[:4]: st.markdown(f"&nbsp;&nbsp;▸ {pt}")
                stats=sl.get('stats')
                if stats and isinstance(stats,dict):
                    cols=st.columns(min(len(stats),4))
                    for col,(k,v) in zip(cols,stats.items()): col.metric(k,v)
                st.divider()

st.divider()
st.markdown("<p style='text-align:center;color:#AABBD4;font-size:.8rem'>Company Introduction Generator · Claude AI via OpenRouter · python-pptx + python-docx</p>", unsafe_allow_html=True)
