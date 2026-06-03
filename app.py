"""
app.py — Company Introduction Generator
Two modes:
  ✨ Gamma (Pro) — beautiful AI-designed presentation via Gamma · shareable link + PPTX download
  📊 Classic     — python-pptx with brand colours · always available
"""

import streamlit as st, re

st.set_page_config(page_title="Company Introduction Generator", page_icon="🎯",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""<style>
.block-container{max-width:760px;padding-top:1.5rem}
h1{color:#1B3A6B!important;text-align:center}
.subtitle{text-align:center;color:#64748B;margin-top:-.5rem;margin-bottom:1.5rem;font-size:1rem}
div[data-testid="stFormSubmitButton"]>button{
  background:linear-gradient(135deg,#6B48FF,#e8694a)!important;
  color:white!important;font-weight:700!important;font-size:16px!important;
  border:none!important;border-radius:10px!important;
  padding:.65rem!important;width:100%!important}
div[data-testid="stFormSubmitButton"]>button:hover{opacity:.9!important}
.stDownloadButton>button{font-weight:600!important;border-radius:10px!important;
  width:100%!important;padding:.6rem!important}
label{font-weight:600!important;color:#1B3A6B!important;letter-spacing:.02em}
.success-card{background:#E8F8EE;border-left:4px solid #1D9E75;
  padding:1rem 1.2rem;border-radius:8px;margin:1rem 0}
.gamma-card{background:linear-gradient(135deg,#F0EEFF,#EAF4FF);
  border-left:4px solid #6B48FF;padding:1rem 1.2rem;border-radius:8px;margin:1rem 0}
.color-row{display:flex;align-items:center;gap:8px;margin:6px 0}
.swatch{width:26px;height:26px;border-radius:5px;border:1px solid #ccc;display:inline-block}
.mode-badge{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:.75rem;font-weight:700;margin-left:6px}
.mode-gamma{background:#6B48FF;color:white}
.mode-classic{background:#e8694a;color:white}
</style>""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────
_defaults = {
    'pptx_bytes': None, 'docx_bytes': None, 'company_data': None,
    'gen_name': None, 'slide_count': 0, 'safe_name': None,
    'primary_hex': '1B3A6B', 'accent_hex': 'C8A951',
    'style_used': None, 'industry': None, 'color_source': None,
    'gamma_url': None, 'gamma_export_url': None, 'gamma_theme': None,
    'mode_used': None,
}
for k, v in _defaults.items():
    if k not in st.session_state: st.session_state[k] = v

STYLE_INFO = {
    'professional': ('📋 Professional', 'Dark title · White slides · Left accent bars'),
    'bold':         ('⚡ Bold Split',   'Half-page colour panel · Content on right'),
    'cards':        ('🃏 Clean Cards',  'Light background · Floating white cards · Pill stats'),
}

# ── Header ───────────────────────────────────────────────────────
st.markdown("# 🎯 Company Introduction Generator")
st.markdown(
    '<p class="subtitle">'
    'Auto-branded PPT + Hinglish Script · Brand colours from website · '
    '✨ Gamma AI Design <em>(recommended)</em> or 📊 Classic PPTX'
    '</p>',
    unsafe_allow_html=True
)
st.divider()

# ── Form ─────────────────────────────────────────────────────────
with st.form("gen_form", clear_on_submit=False):
    company_name = st.text_input("COMPANY NAME *", placeholder="e.g. Shivalal Agarwala & Co.")
    website_url  = st.text_input("WEBSITE URL *",  placeholder="https://www.yourcompany.com")
    api_key      = st.text_input(
        "OPENROUTER API KEY *", type="password", placeholder="sk-or-v1-…"
    )

    st.markdown("---")
    st.markdown(
        "##### ✨ Gamma AI Design &nbsp;<span style='background:#6B48FF;color:white;"
        "padding:2px 9px;border-radius:12px;font-size:.72rem;font-weight:700'>"
        "RECOMMENDED</span>",
        unsafe_allow_html=True
    )
    st.caption(
        "Gamma creates beautifully designed, image-rich presentations automatically. "
        "Leave blank to fall back to Classic PPTX."
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        gamma_api_key = st.text_input(
            "GAMMA API KEY",
            type="password",
            placeholder="Paste your Gamma API key here (free)",
            help="Get your free API key at gamma.app/settings/api"
        )
    with c2:
        st.markdown(
            '<div style="padding-top:1.9rem;font-size:.82rem;color:#6B48FF">'
            '🔗 <a href="https://gamma.app/settings/api" target="_blank" '
            'style="color:#6B48FF;font-weight:600">Get free Gamma key →</a><br>'
            '<span style="color:#888;font-size:.75rem">Free account · No credit card</span>'
            '</div>',
            unsafe_allow_html=True
        )

    model = "anthropic/claude-sonnet-4-6"
    submitted = st.form_submit_button("🚀  Generate Both Documents", use_container_width=True)

# ── Validation & generation ──────────────────────────────────────
if submitted:
    errors = []
    if not company_name.strip(): errors.append("Company name is required.")
    if not website_url.strip():  errors.append("Website URL is required.")
    if not api_key.strip():      errors.append("OpenRouter API key is required.")
    if website_url.strip() and not website_url.startswith(('http://', 'https://')):
        errors.append("Website URL must start with http:// or https://")
    if errors:
        for e in errors: st.error(f"⚠️ {e}")
        st.stop()

    # Reset
    for k in _defaults:
        st.session_state[k] = _defaults[k]

    from ai_research     import research_company
    from ppt_builder     import build_presentation
    from doc_builder     import build_script_document
    from color_extractor import extract_website_colors

    use_gamma = bool(gamma_api_key.strip())

    progress = st.progress(0, text="Starting…")
    status   = st.empty()

    try:
        # ── Step 1: scrape brand colours ─────────────────────────
        status.info("🎨 **Scanning website** for brand colours…")
        progress.progress(8, text="Scanning CSS and meta tags…")
        scraped_primary, scraped_accent = extract_website_colors(website_url.strip())

        # ── Step 2: AI research ──────────────────────────────────
        status.info(f"🔍 **Researching** {company_name} with Claude AI… *(30–60 s)*")
        progress.progress(15, text="Calling Claude AI…")
        company_data = research_company(
            company_name.strip(), website_url.strip(), api_key.strip(), model
        )

        slide_count = len(company_data.get('slides', []))
        gen_name    = company_data.get('company_name', company_name)
        industry    = company_data.get('industry_type', 'other')
        ai_primary  = company_data.get('brand_primary_color', '')
        ai_accent   = company_data.get('brand_accent_color', '')

        def valid(h): return bool(h and re.match(r'^[0-9A-Fa-f]{6}$', h))

        scraped_is_real = (scraped_primary != '1B3A6B' and valid(scraped_primary))
        if scraped_is_real:
            primary_hex  = scraped_primary
            accent_hex   = scraped_accent if valid(scraped_accent) else (ai_accent if valid(ai_accent) else 'C8A951')
            color_source = f"Website CSS (#{primary_hex} + #{accent_hex})"
        elif valid(ai_primary):
            primary_hex  = ai_primary
            accent_hex   = ai_accent if valid(ai_accent) else 'C8A951'
            color_source = f"Claude AI identified (#{primary_hex} + #{accent_hex})"
        else:
            primary_hex  = '1B3A6B'
            accent_hex   = 'C8A951'
            color_source = "Default (website did not expose brand colours)"

        st.session_state.primary_hex  = primary_hex
        st.session_state.accent_hex   = accent_hex
        st.session_state.color_source = color_source
        st.session_state.industry     = industry

        progress.progress(45, text=f"Got {slide_count} slides! Industry: {industry}")
        status.success(f"✅ Research done — {slide_count} slides · {color_source}")

        # ── Step 3: Generate presentation ───────────────────────
        if use_gamma:
            from gamma_builder import generate_with_gamma, theme_display_name

            status.info("✨ **Gamma AI** is designing your presentation…")
            progress.progress(58, text="Calling Gamma AI — this takes ~30–60 s…")

            gamma_result = generate_with_gamma(
                company_data   = company_data,
                gamma_api_key  = gamma_api_key.strip(),
                primary_hex    = primary_hex,
                accent_hex     = accent_hex,
                export_pptx    = True,
            )

            st.session_state.gamma_url        = gamma_result['gamma_url']
            st.session_state.gamma_export_url = gamma_result['export_url']
            st.session_state.gamma_theme      = gamma_result['theme_id']
            st.session_state.mode_used        = 'gamma'

            # If Gamma returned PPTX bytes, store them; otherwise build Classic as fallback
            if gamma_result['pptx_bytes']:
                st.session_state.pptx_bytes = gamma_result['pptx_bytes']
                st.session_state.style_used = 'gamma'
            else:
                # Gamma link available but no direct download — build Classic as backup
                progress.progress(72, text="Building Classic PPTX as backup…")
                pptx_bytes, style_used = build_presentation(company_data, primary_hex, accent_hex)
                st.session_state.pptx_bytes = pptx_bytes
                st.session_state.style_used = style_used

        else:
            status.info("📊 **Building Classic presentation…**")
            progress.progress(60, text="Generating PPTX…")
            pptx_bytes, style_used = build_presentation(company_data, primary_hex, accent_hex)
            st.session_state.pptx_bytes = pptx_bytes
            st.session_state.style_used = style_used
            st.session_state.mode_used  = 'classic'

        progress.progress(82, text="Building script…")

        # ── Step 4: Build DOCX script ────────────────────────────
        status.info("📄 **Creating Hinglish video script…**")
        docx_bytes = build_script_document(company_data)
        progress.progress(100, text="Complete!")
        status.empty(); progress.empty()

        st.session_state.docx_bytes   = docx_bytes
        st.session_state.company_data = company_data
        st.session_state.gen_name     = gen_name
        st.session_state.slide_count  = slide_count
        st.session_state.safe_name    = "".join(
            c for c in gen_name if c.isalnum() or c in (' ', '-')
        ).strip().replace(' ', '_')

    except ValueError as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Generation failed:** {e}")
        if 'Gamma' in str(e) or 'gamma' in str(e):
            st.info("💡 Check your Gamma API key at gamma.app/settings/api — or leave it blank to use Classic PPTX.")
        else:
            st.info("💡 Check your OpenRouter API key and credits at openrouter.ai")
    except Exception as e:
        progress.empty(); status.empty()
        st.error(f"❌ **Unexpected error:** {e}"); st.exception(e)


# ── Results section ──────────────────────────────────────────────
if st.session_state.pptx_bytes and st.session_state.docx_bytes:
    gn  = st.session_state.gen_name;    sc  = st.session_state.slide_count
    sn  = st.session_state.safe_name;   pb  = st.session_state.pptx_bytes
    db  = st.session_state.docx_bytes;  ph  = st.session_state.primary_hex
    ah  = st.session_state.accent_hex;  sw  = st.session_state.style_used
    ind = st.session_state.industry;    cs  = st.session_state.color_source
    cd  = st.session_state.company_data
    mode = st.session_state.mode_used

    gamma_url   = st.session_state.gamma_url
    gamma_theme = st.session_state.gamma_theme

    # ── Gamma mode result ───────────────────────────────────────
    if mode == 'gamma' and gamma_url:
        from gamma_builder import theme_display_name
        tname, tdesc = theme_display_name(gamma_theme or '')
        st.markdown(
            f'<div class="gamma-card">'
            f'✨ <strong>Gamma presentation ready!</strong>'
            f'<span class="mode-badge mode-gamma">Gamma Pro</span><br><br>'
            f'<strong>{gn}</strong> &nbsp;·&nbsp; {sc} slides &nbsp;·&nbsp; '
            f'Industry: <em>{ind}</em><br><br>'
            f'<strong>Theme: {tname}</strong> — {tdesc}<br><br>'
            f'<div class="color-row">'
            f'<span class="swatch" style="background:#{ph}"></span>'
            f'<strong>#{ph}</strong> &nbsp;&nbsp;'
            f'<span class="swatch" style="background:#{ah}"></span>'
            f'<strong>#{ah}</strong>'
            f'</div>'
            f'<small style="color:#888">{cs}</small>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Gamma link button
        st.link_button(
            "🔗  Open in Gamma (view · edit · share)",
            gamma_url,
            use_container_width=True,
        )
        st.caption("💡 Open in Gamma to change the theme, edit slides, or share a live link.")
        st.markdown("")

    else:
        # Classic mode result
        sname, sdesc = STYLE_INFO.get(sw, ('📋 Classic', 'Brand-coloured PPTX'))
        st.markdown(
            f'<div class="success-card">'
            f'🎉 <strong>Both documents ready!</strong>'
            f'<span class="mode-badge mode-classic">Classic PPTX</span><br><br>'
            f'<strong>{gn}</strong> &nbsp;·&nbsp; {sc} slides &nbsp;·&nbsp; '
            f'Industry: <em>{ind}</em><br><br>'
            f'<strong>Design: {sname}</strong> — {sdesc}<br><br>'
            f'<div class="color-row">'
            f'<span class="swatch" style="background:#{ph}"></span>'
            f'<strong>#{ph}</strong> &nbsp;&nbsp;'
            f'<span class="swatch" style="background:#{ah}"></span>'
            f'<strong>#{ah}</strong>'
            f'</div>'
            f'<small style="color:#888">{cs}</small>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.subheader("📥 Download Your Documents")
    st.caption("Both files stay available — download one, then the other.")

    d1, d2 = st.columns(2)
    with d1:
        pptx_label = (
            "✨  Download Gamma Presentation (.pptx)"
            if mode == 'gamma' and st.session_state.gamma_export_url
            else "📊  Download Presentation (.pptx)"
        )
        st.download_button(
            pptx_label,
            data=pb,
            file_name=f"{sn}_Presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
            key="dl_pptx",
        )
        if mode == 'gamma':
            st.caption(f"✨ Gamma Pro design · #{ph} · {sc} slides")
        else:
            sname, _ = STYLE_INFO.get(sw, ('Classic', ''))
            st.caption(f"{sname} · #{ph} theme · {sc} slides")
    with d2:
        st.download_button(
            "📄  Download Video Script (.docx)",
            data=db,
            file_name=f"{sn}_Video_Script.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key="dl_docx",
        )
        st.caption("Hinglish narration · Slide-by-slide")

    st.divider()
    if st.button("🔄  Generate for a different company", use_container_width=True):
        for k in _defaults:
            st.session_state[k] = _defaults[k]
        st.rerun()

    if cd:
        with st.expander("👁  Preview slide content", expanded=False):
            for sl in cd.get('slides', []):
                st.markdown(f"**Slide {sl['slide_number']}: {sl['title']}**")
                for pt in sl.get('key_points', [])[:4]:
                    st.markdown(f"&nbsp;&nbsp;▸ {pt}")
                stats = sl.get('stats')
                if stats and isinstance(stats, dict):
                    cols = st.columns(min(len(stats), 4))
                    for col, (k, v) in zip(cols, stats.items()):
                        col.metric(k, v)
                st.divider()

st.divider()
st.markdown(
    "<p style='text-align:center;color:#AABBD4;font-size:.8rem'>"
    "Company Introduction Generator · Claude AI via OpenRouter · "
    "✨ Gamma Pro Design · python-pptx · python-docx"
    "</p>",
    unsafe_allow_html=True
)
