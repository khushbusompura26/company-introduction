"""
app.py — Company Introduction Generator
Streamlit web app that generates professional PPT + Hinglish video script
using Claude AI via OpenRouter
"""

import streamlit as st

# ── Page config (must be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="Company Introduction Generator",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
/* Main container */
.block-container { max-width: 720px; padding-top: 1.5rem; }

/* Title */
h1 { color: #1B3A6B !important; text-align: center; }

/* Subtitle */
.subtitle { text-align:center; color:#64748B; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:1rem; }

/* Generate button */
div[data-testid="stFormSubmitButton"] > button {
    background-color: #e8694a !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #d4593c !important;
}

/* Download buttons */
.stDownloadButton > button {
    font-weight: 600 !important;
    border-radius: 10px !important;
    width: 100% !important;
    padding: 0.6rem !important;
}

/* Input labels */
label { font-weight: 600 !important; color: #1B3A6B !important; letter-spacing: 0.02em; }

/* Success box */
.success-card {
    background: #E8F8EE;
    border-left: 4px solid #1D9E75;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    margin: 1rem 0;
}

/* Badge pill */
.badge {
    display: inline-block;
    background: #F0F4FF;
    color: #3A5BBD;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.markdown("# 🎯 Company Introduction Generator")
st.markdown(
    '<p class="subtitle">Professional PPT + Hinglish Video Script &nbsp;·&nbsp; '
    'Powered by Claude AI via OpenRouter</p>',
    unsafe_allow_html=True
)
st.divider()

# ── Form ───────────────────────────────────────────────────────
with st.form("gen_form", clear_on_submit=False):
    company_name = st.text_input(
        "COMPANY NAME *",
        placeholder="e.g. Shivalal Agarwala & Co."
    )
    website_url = st.text_input(
        "WEBSITE URL *",
        placeholder="https://www.yourcompany.com"
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        api_key = st.text_input(
            "OPENROUTER API KEY *",
            type="password",
            placeholder="sk-or-v1-..."
        )
    with col2:
        model = st.selectbox(
            "Claude Model",
            options=[
                "anthropic/claude-3.5-sonnet",
                "anthropic/claude-3.5-haiku",
                "anthropic/claude-3-opus",
            ],
            help="claude-3.5-sonnet gives best quality. haiku is faster and cheaper."
        )

    submitted = st.form_submit_button(
        "🚀  Generate Both Documents",
        use_container_width=True
    )

# ── Processing ─────────────────────────────────────────────────
if submitted:
    # Validate inputs
    errors = []
    if not company_name.strip():
        errors.append("Company name is required.")
    if not website_url.strip():
        errors.append("Website URL is required.")
    if not api_key.strip():
        errors.append("OpenRouter API key is required.")
    if website_url.strip() and not website_url.startswith(('http://', 'https://')):
        errors.append("Website URL must start with http:// or https://")

    if errors:
        for e in errors:
            st.error(f"⚠️ {e}")
        st.stop()

    # Import builders (lazy import for faster startup)
    from ai_research import research_company
    from ppt_builder import build_presentation
    from doc_builder import build_script_document

    # Progress indicators
    progress  = st.progress(0, text="Starting…")
    status_ph = st.empty()

    try:
        # ── Step 1: AI Research ──────────────────────────────
        status_ph.info(
            f"🔍 **Researching** {company_name} with Claude AI…  "
            f"*(this usually takes 30–60 seconds)*"
        )
        progress.progress(15, text="Calling Claude AI…")

        company_data = research_company(
            company_name.strip(),
            website_url.strip(),
            api_key.strip(),
            model
        )

        slide_count = len(company_data.get('slides', []))
        gen_name    = company_data.get('company_name', company_name)
        progress.progress(45, text=f"Got {slide_count} slides from Claude!")
        status_ph.success(f"✅ Research complete — {slide_count} slides planned for **{gen_name}**")

        # ── Step 2: Build PPTX ───────────────────────────────
        status_ph.info("📊 **Building presentation** — Navy + Gold theme, varied layouts…")
        progress.progress(60, text="Generating PPTX…")
        pptx_bytes = build_presentation(company_data)
        progress.progress(80, text="PPTX done! Building script document…")

        # ── Step 3: Build DOCX ───────────────────────────────
        status_ph.info("📄 **Creating Hinglish video script** document…")
        docx_bytes = build_script_document(company_data)
        progress.progress(100, text="Complete!")

        # ── Success ──────────────────────────────────────────
        status_ph.empty()
        progress.empty()

        st.markdown(
            f'<div class="success-card">'
            f'🎉 <strong>Both documents are ready!</strong><br>'
            f'Company: <strong>{gen_name}</strong> &nbsp;·&nbsp; '
            f'{slide_count} slides &nbsp;·&nbsp; '
            f'Hinglish script included'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── Download buttons ─────────────────────────────────
        safe = "".join(
            c for c in gen_name if c.isalnum() or c in (' ', '-')
        ).strip().replace(' ', '_')

        st.divider()
        st.subheader("📥 Download Your Documents")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="📊  Download Presentation (.pptx)",
                data=pptx_bytes,
                file_name=f"{safe}_Presentation.pptx",
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".presentationml.presentation"
                ),
                use_container_width=True
            )
            st.caption(f"Navy + Gold theme · {slide_count} slides · Georgia / Calibri fonts")

        with dl2:
            st.download_button(
                label="📄  Download Video Script (.docx)",
                data=docx_bytes,
                file_name=f"{safe}_Video_Script.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document"
                ),
                use_container_width=True
            )
            st.caption("Hinglish narration · Slide-by-slide · Production notes")

        # ── Slide preview ─────────────────────────────────────
        st.divider()
        with st.expander("👁  Preview generated slide content", expanded=False):
            for sl in company_data.get('slides', []):
                st.markdown(
                    f"**Slide {sl['slide_number']}: {sl['title']}**"
                )
                for pt in sl.get('key_points', [])[:4]:
                    st.markdown(f"&nbsp;&nbsp;▸ {pt}")

                stats = sl.get('stats')
                if stats and isinstance(stats, dict):
                    cols = st.columns(min(len(stats), 4))
                    for col, (k, v) in zip(cols, stats.items()):
                        col.metric(k, v)

                st.divider()

    except ValueError as e:
        progress.empty()
        status_ph.empty()
        st.error(f"❌ **Generation failed:** {e}")
        st.info(
            "💡 **Common fixes:**\n"
            "- Check your OpenRouter API key is correct\n"
            "- Make sure you have credits at openrouter.ai\n"
            "- Try a different Claude model\n"
            "- Verify the website URL is accessible"
        )
    except Exception as e:
        progress.empty()
        status_ph.empty()
        st.error(f"❌ **Unexpected error:** {e}")
        st.exception(e)

# ── Footer ─────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#AABBD4;font-size:0.8rem'>"
    "Company Introduction Generator &nbsp;·&nbsp; "
    "Powered by Claude AI via OpenRouter &nbsp;·&nbsp; "
    "python-pptx + python-docx"
    "</p>",
    unsafe_allow_html=True
)
