import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import streamlit as st

from src.chat.scouting_chat import ask_scouting_assistant
from src.export.scout_exporter import export_docx, export_pdf


st.set_page_config(
    page_title="AI Scouting Assistant",
    page_icon="🏀",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1200px;
        padding-top: 3rem;
    }

    .hero {
        font-size: 64px;
        font-weight: 900;
        letter-spacing: -2px;
        margin-bottom: 0px;
    }

    .subhero {
        font-size: 30px;
        color: #777;
        margin-bottom: 35px;
    }

    .stChatMessage {
        font-size: 18px;
        padding: 20px;
        border-radius: 18px;
    }

    textarea {
        font-size: 18px !important;
    }

    input {
        font-size: 18px !important;
    }

    .stButton button {
        border-radius: 12px;
        font-size: 18px;
        padding: 0.7rem 1.2rem;
    }

    .download-row {
        margin-top: 20px;
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
            "Example:\\n"
            "- #12 is questionable\\n"
            "- They have been playing more zone\\n"
            "- Emphasize transition defense\\n"
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

if st.session_state.latest_report:
    st.markdown("---")
    st.subheader("Export Scout")

    col1, col2 = st.columns(2)

    docx_file = export_docx(st.session_state.latest_report, team_name)
    pdf_file = export_pdf(st.session_state.latest_report, team_name)

    with col1:
        st.download_button(
            label="Download DOCX",
            data=docx_file,
            file_name=f"{team_name}_scout.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with col2:
        st.download_button(
            label="Download PDF",
            data=pdf_file,
            file_name=f"{team_name}_scout.pdf",
            mime="application/pdf",
        )