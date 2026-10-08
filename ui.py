```python
import uuid
import json
import time
import streamlit as st

from database import initialize_database
from agent import run_agent
from memory import conversation_memory


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="ShopUNow AI Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# INITIALIZE BACKEND DATA STRUCTURES
# ============================================================
initialize_database()


# ============================================================
# SESSION STATE POOL
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None


# ============================================================
# MODERN ENTERPRISE UI STYLING
# ============================================================
st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL APP BACKGROUND
       ======================================================== */
    .stApp {
        background-color: #F4F6F9;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */
    [data-testid="stSidebar"] {
        background-color: #0B2545 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] caption,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #FFFFFF !important;
    }


    /* ========================================================
       SIDEBAR BUTTONS
       ======================================================== */
    [data-testid="stSidebar"] .stButton button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.20) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stSidebar"] .stButton button p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.18) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
    }

    [data-testid="stSidebar"] .stButton button:hover p {
        color: #FFFFFF !important;
    }


    /* ========================================================
       MAIN CONTENT CONTAINER
       ======================================================== */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }


    /* ========================================================
       WELCOME HEADER
       ======================================================== */
    .header-container {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    .top-header-title {
        font-size: 24px;
        font-weight: 700;
        color: #1E293B !important;
    }

    .top-header-subtitle {
        font-size: 14px;
        color: #64748B !important;
    }

    .online-status {
        font-size: 13px;
        color: #10B981 !important;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .welcome-status {
        font-size: 12px;
        color: #059669 !important;
        font-weight: 700;
        letter-spacing: 0.05em;
        background-color: #D1FAE5;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AVATAR DEFINITIONS
# ============================================================
USER_AVATAR = "👤"

try:
    with open("assets/shopunow_logo.png", "rb") as f:
        BOT_AVATAR = "assets/shopunow_logo.png"
except FileNotFoundError:
    BOT_AVATAR = "🛍️"


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def text_streamer(text_block: str):
    """
    Simulates natural word-by-word streaming animation.
    """
    if not text_block:
        return

    for word in str(text_block).split(" "):
        yield word + " "
        time.sleep(0.04)


# ============================================================
# SIDEBAR NAVIGATION & QUICK ACTIONS
# ============================================================
with st.sidebar:

    # --------------------------------------------------------
    # SHOPUNOW LOGO
    # --------------------------------------------------------
    try:
        st.image(
            "assets/shopunow_logo.png",
            width=210,
        )
    except Exception:
        st.title("🛍️ ShopUNow")
        st.caption("AI-powered support assistant")

    st.write("---")


    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------
    st.subheader("QUICK ACTIONS")

    if st.button(
        "🔄 Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.active_prompt = None
        st.rerun()

    st.write("---")


    # --------------------------------------------------------
    # EXAMPLE QUESTIONS
    # --------------------------------------------------------
    st.subheader("EXAMPLE QUESTIONS")

    if st.button(
        "How do I reset my ShopUNow employee VPN password?",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "How do I reset my ShopUNow employee VPN password?"
        )
        st.rerun()

    if st.button(
        "How do I apply for a vacation day?",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "How do I apply for a vacation day?"
        )
        st.rerun()

    if st.button(
        "What should I do if my laptop is running slow?",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "What should I do if my laptop is running slow?"
        )
        st.rerun()

    if st.button(
        "I am extremely frustrated because my VPN has been broken for days!",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "I am extremely frustrated because my VPN has been broken for days!"
        )
        st.rerun()


    st.write("---")


    # --------------------------------------------------------
    # DEPARTMENTS
    # --------------------------------------------------------
    st.subheader("DEPARTMENTS")

    if st.button(
        "👥 HR Department",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "I need assistance from the HR department regarding company policy."
        )
        st.rerun()

    if st.button(
        "💻 IT Support",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "I need to open an IT technical support request."
        )
        st.rerun()

    if st.button(
        "💳 Billing & Payments",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "I have a question about vendor billing or employee payments."
        )
        st.rerun()

    if st.button(
        "📦 Shipping & Delivery",
        use_container_width=True,
    ):
        st.session_state.active_prompt = (
            "Show me the tracking options or shipping department procedures."
        )
        st.rerun()


# ============================================================
# MAIN INTERFACE
# ============================================================

# ------------------------------------------------------------
# CONDITIONAL WELCOME BANNER
# ------------------------------------------------------------
# Only display the welcome screen when there are no messages.
# ------------------------------------------------------------
if not st.session_state.messages:

    st.markdown(
        """
        <div class="header-container">
            <div class="top-header-title">
                ShopUNow AI Assistant
            </div>

            <div class="top-header-subtitle">
                Intelligent retail support
            </div>

            <div class="online-status">
                ● AI Assistant Online
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="welcome-status">● READY TO HELP</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# RENDER HISTORICAL CHAT LOG
# ------------------------------------------------------------
for message in st.session_state.messages:

    current_avatar = (
        USER_AVATAR
        if message["role"] == "user"
        else BOT_AVATAR
    )

    with st.chat_message(
        message["role"],
        avatar=current_avatar,
    ):

        st.write(message["content"])

        # ----------------------------------------------------
        # HISTORICAL ASSISTANT METADATA
        # ----------------------------------------------------
        if (
            message["role"] == "assistant"
            and "metadata" in message
        ):

            meta = message["metadata"]

            hist_cols = st.columns(3)

            hist_cols[0].caption(
                f"📁 **Dept:** "
                f"{meta.get('department', 'N/A')}"
            )

            hist_cols[1].caption(
                f"🎭 **Sentiment:** "
                f"{meta.get('sentiment', 'N/A')}"
            )

            hist_cols[2].caption(
                f"🎯 **Scope:** "
                f"{meta.get('scope', 'In-Scope')}"
            )


# ============================================================
# CHAT INPUT
# ============================================================
user_input = st.chat_input(
    "Ask ShopUNow a question..."
)

final_prompt = None


# ------------------------------------------------------------
# SIDEBAR PROMPT HAS PRIORITY
# ------------------------------------------------------------
if st.session_state.active_prompt:

    final_prompt = st.session_state.active_prompt

    # Consume the prompt so it is not submitted repeatedly.
    st.session_state.active_prompt = None


elif user_input:

    final_prompt = user_input


# ============================================================
# EXECUTE RESPONSE WORKFLOW
# ============================================================
if final_prompt:

    # --------------------------------------------------------
    # RENDER USER MESSAGE
    # --------------------------------------------------------
    with st.chat_message(
        "user",
        avatar=USER_AVATAR,
    ):
        st.write(final_prompt)

    # Save user message immediately.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": final_prompt,
        }
    )


    # --------------------------------------------------------
    # RENDER ASSISTANT RESPONSE
    # --------------------------------------------------------
    with st.chat_message(
        "assistant",
        avatar=BOT_AVATAR,
    ):

        with st.spinner("Processing request..."):

            # Default metadata values
            department_meta = "General"
            sentiment_meta = "Neutral"
            scope_meta = "In-Scope"
            clean_output = ""


            # =================================================
            # CALL AGENT
            # =================================================
            try:

                raw_response = run_agent(
                    final_prompt,
                    st.session_state.session_id,
                )


                # =================================================
                # PARSE AGENT RESPONSE
                # =================================================
                if isinstance(raw_response, dict):

                    response_data = raw_response

                else:

                    response_data = json.loads(
                        raw_response
                    )


                # =================================================
                # EXTRACT RESPONSE
                # =================================================
                clean_output = response_data.get(
                    "response",
                    "Could not fetch message contents.",
                )


                department_meta = response_data.get(
                    "department",
                    "General",
                )


                sentiment_meta = response_data.get(
                    "sentiment",
                    "Neutral",
                )


                scope_meta = response_data.get(
                    "scope",
                    "In-Scope",
                )


            # =================================================
            # FALLBACK FOR PLAIN TEXT RESPONSE
            # =================================================
            except (
                json.JSONDecodeError,
                TypeError,
            ):

                clean_output = str(raw_response)


            # =================================================
            # ABSOLUTE SAFETY FALLBACK
            # =================================================
            except Exception:

                clean_output = (
                    "I encountered an issue processing "
                    "your request. Please try your message again."
                )


            # =================================================
            # SAFETY: ENSURE OUTPUT IS STRING
            # =================================================
            if clean_output is None:
                clean_output = (
                    "I could not generate a response."
                )

            clean_output = str(clean_output)


            # =================================================
            # STREAM RESPONSE TO USER
            # =================================================
            st.write_stream(
                text_streamer(clean_output)
            )


            # =================================================
            # DISPLAY LIVE METADATA
            # =================================================
            live_cols = st.columns(3)

            live_cols[0].caption(
                f"📁 Dept: {department_meta}"
            )

            live_cols[1].caption(
                f"🎭 Sentiment: {sentiment_meta}"
            )

            live_cols[2].caption(
                f"🎯 Scope: {scope_meta}"
            )


            # =================================================
            # SAVE ASSISTANT MESSAGE TO SESSION STATE
            # =================================================
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": clean_output,
                    "metadata": {
                        "department": department_meta,
                        "sentiment": sentiment_meta,
                        "scope": scope_meta,
                    },
                }
            )


    # ========================================================
    # RERUN APPLICATION
    # ========================================================
    st.rerun()
```
