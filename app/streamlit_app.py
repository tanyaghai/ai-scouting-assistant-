import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import streamlit as st

from src.chat.scouting_chat import ask_scouting_assistant
from src.export.scout_template_docx import export_chapman_style_docx
from src.export.scout_pdf_converter import export_chapman_style_pdf


st.set_page_config(
    page_title="AI Scouting Assistant",
    page_icon="🏀",
    layout="wide",
)

st.markdown(
    """
<style>
.main .block-container {
    max-width: 950px;
    padding-top: 4rem;
    padding-bottom: 8rem;
}

.hero {
    font-size: 64px;
    font-weight: 900;
    letter-spacing: -1.5px;
    margin-bottom: 0.25rem;
    color: #242633;
}

.subhero {
    font-size: 30px;
    color: #6b7280;
    margin-bottom: 2.5rem;
}

section[data-testid="stSidebar"] {
    min-width: 360px !important;
    max-width: 360px !important;
    background-color: #f7f7fb;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
    font-size: 16px !important;
}

input, textarea {
    font-size: 18px !important;
    line-height: 1.5 !important;
}

div[data-testid="stChatMessage"] {
    font-size: 20px !important;
    line-height: 1.6 !important;
    padding: 1.25rem 1.4rem !important;
    border-radius: 22px !important;
}

.stMarkdown p,
.stMarkdown li {
    font-size: 20px !important;
    line-height: 1.6 !important;
}

div[data-testid="stChatInput"] {
    max-width: 950px;
    margin: 0 auto;
}

div[data-testid="stChatInput"] textarea {
    font-size: 22px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    min-height: 72px !important;
    padding: 18px 22px !important;
    border-radius: 20px !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    font-size: 22px !important;
    color: #8b8b8b !important;
    opacity: 1 !important;
}

div[data-testid="stChatInput"] button {
    transform: scale(1.35);
}

.stButton button,
.stDownloadButton button {
    font-size: 18px !important;
    border-radius: 14px !important;
    padding: 0.75rem 1.25rem !important;
}

.export-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 22px;
    border-radius: 18px;
    margin-top: 24px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="hero">Hi Coach Chanel.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subhero">What can I help you prepare for today?</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Scout Setup")

    team_name = st.text_input(
        "Opponent",
        value="Claremont_Mudd_Scripps",
    )

    coach_notes = st.text_area(
        "Coach notes",
        placeholder=(
            "Example:\n"
            "- #12 is questionable\n"
            "- They have been playing more zone\n"
            "- Emphasize transition defense\n"
            "- Shorter rotation recently"
        ),
        height=230,
    )

    st.markdown("---")
    st.caption(
        "Uses current stats, recent form, player profiles, ML archetypes, coach notes, and historical scout style."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_report" not in st.session_state:
    st.session_state.latest_report = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_request = st.chat_input(
    "Ask for a scout, personnel notes, keys to the win, or a game plan..."
)

if user_request:
    st.session_state.messages.append({"role": "user", "content": user_request})

    with st.chat_message("user"):
        st.markdown(user_request)

    with st.chat_message("assistant"):
        status = st.status("Building scout...", expanded=True)

        status.write("🏀 Loading opponent statistics")
        status.write("🧠 Building scouting context")
        status.write("📈 Analyzing recent form")
        status.write("📚 Applying historical scout style")
        status.write("🤖 Writing response with Qwen")

        response = ask_scouting_assistant(
            team_name=team_name,
            coach_notes=coach_notes,
            user_request=user_request,
        )

        status.update(label="Scout ready", state="complete", expanded=False)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.latest_report = response


# -------------------------------------------------------
# Export
# -------------------------------------------------------

if st.session_state.latest_report:
    st.markdown("---")
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.subheader("Export Scout")

    col1, col2 = st.columns(2)

    with st.spinner("Preparing DOCX..."):
        docx_file = export_chapman_style_docx(team_name)

    with col1:
        st.download_button(
            label="📄 Download Scout DOCX",
            data=docx_file.getvalue(),
            file_name=f"{team_name}_Scout.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    try:
        with st.spinner("Preparing PDF..."):
            pdf_file = export_chapman_style_pdf(team_name)

        with col2:
            st.download_button(
                label="📕 Download Scout PDF",
                data=pdf_file.getvalue(),
                file_name=f"{team_name}_Scout.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    except Exception as error:
        with col2:
            st.warning("PDF export needs LibreOffice/soffice working locally.")
            st.caption(str(error))

    st.markdown("</div>", unsafe_allow_html=True)