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
# INITIALIZE BACKEND
# ============================================================
initialize_database()


# ============================================================
# SESSION STATE
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None

# Added for human escalation form only
if "show_escalation_form" not in st.session_state:
    st.session_state.show_escalation_form = False

if "escalation_submitted" not in st.session_state:
    st.session_state.escalation_submitted = False

if "escalation_contact" not in st.session_state:
    st.session_state.escalation_contact = None


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
# GLOBAL UI STYLING
# ============================================================
st.markdown(
    """
    <style>

    /* ========================================================
       APP BACKGROUND
       ======================================================== */

    .stApp {
        background-color: #F4F6F9;
    }

    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }


    /* ========================================================
       MAIN PAGE MARKDOWN
       Only target actual markdown/text elements.
       Do NOT force color on every div/span.
       ======================================================== */

    .main .block-container .stMarkdown p,
    .main .block-container .stMarkdown h1,
    .main .block-container .stMarkdown h2,
    .main .block-container .stMarkdown h3,
    .main .block-container .stMarkdown h4,
    .main .block-container .stMarkdown h5,
    .main .block-container .stMarkdown h6 {
        color: #1E293B !important;
    }


    /* ========================================================
       CHAT MESSAGE TEXT
       ======================================================== */

    [data-testid="stChatMessage"] .stMarkdown p,
    [data-testid="stChatMessage"] .stMarkdown li,
    [data-testid="stChatMessage"] .stMarkdown strong,
    [data-testid="stChatMessage"] .stMarkdown em {
        color: #1E293B !important;
    }


    /* ========================================================
       CHAT INPUT
       ======================================================== */

    [data-testid="stChatInput"] {
        border-radius: 12px;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    [data-testid="stSidebar"] {
        background-color: #0B2545 !important;
    }


    /* ========================================================
       SIDEBAR TEXT
       ======================================================== */

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown {
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
    }

    [data-testid="stSidebar"] .stButton button p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.18) !important;
        border-color: #10B981 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTION
# ============================================================
def text_streamer(text_block: str):
    """
    Simulates a natural word-by-word response stream.
    """

    if not text_block:
        return

    for word in str(text_block).split():
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


    # ========================================================
    # QUICK ACTIONS
    # ========================================================
    st.subheader("QUICK ACTIONS")


    if st.button(
        "🔄 Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.active_prompt = None

        st.rerun()


    st.write("---")


    # ========================================================
    # EXAMPLE QUESTIONS
    # ========================================================
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


    # ========================================================
    # DEPARTMENTS
    # ========================================================
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
# MAIN INTERFACE RENDERER
# ============================================================

# ------------------------------------------------------------
# WELCOME HEADER
# ------------------------------------------------------------
# Uses native Streamlit components.
# No custom HTML is used here.
# The header disappears after the first message.
# ------------------------------------------------------------
if not st.session_state.messages:

    st.markdown(
        "## 🛍️ ShopUNow AI Assistant"
    )

    st.markdown(
        "**Intelligent retail support**"
    )

    st.success(
        "🟢 AI Assistant Online • READY TO HELP"
    )


# ============================================================
# RENDER HISTORICAL CHAT LOG
# ============================================================
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

        # ----------------------------------------------------
        # MESSAGE CONTENT
        # ----------------------------------------------------
        st.write(
            message["content"]
        )


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


# ============================================================
# CHAT INPUT
# ============================================================
user_input = st.chat_input(
    "Ask ShopUNow a question..."
)

final_prompt = None


# ============================================================
# DETERMINE FINAL PROMPT
# ============================================================

# Sidebar button prompt
if st.session_state.active_prompt:

    final_prompt = st.session_state.active_prompt

    # Consume prompt so it runs only once.
    st.session_state.active_prompt = None


# Normal chat input
elif user_input:

    final_prompt = user_input


# ============================================================
# EXECUTE RESPONSE WORKFLOW
# ============================================================
if final_prompt:

    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------
    with st.chat_message(
        "user",
        avatar=USER_AVATAR,
    ):

        st.write(
            final_prompt
        )


    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------
    st.session_state.messages.append(
        {
            "role": "user",
            "content": final_prompt,
        }
    )


    # --------------------------------------------------------
    # ASSISTANT RESPONSE
    # --------------------------------------------------------
    with st.chat_message(
        "assistant",
        avatar=BOT_AVATAR,
    ):

        with st.spinner(
            "Processing request..."
        ):

            # ------------------------------------------------
            # DEFAULT METADATA
            # ------------------------------------------------
            department_meta = "General"
            sentiment_meta = "Neutral"

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
                # PARSE RESPONSE
                # =================================================
                if isinstance(
                    raw_response,
                    dict,
                ):

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

            # =================================================
            # PLAIN TEXT FALLBACK
            # =================================================
            except (
                json.JSONDecodeError,
                TypeError,
            ):

                clean_output = str(
                    raw_response
                )


            # =================================================
            # GENERAL ERROR FALLBACK
            # =================================================
            except Exception:

                clean_output = (
                    "I encountered an issue processing "
                    "your request. Please try your message again."
                )


            # =================================================
            # ENSURE OUTPUT IS VALID
            # =================================================
            if clean_output is None:

                clean_output = (
                    "I could not generate a response."
                )


            clean_output = str(
                clean_output
            )


            # =================================================
            # HUMAN ESCALATION DETECTION (ADDED)
            # =================================================
            response_lower = clean_output.lower()

            escalation_phrases = (
                "human support",
                "human agent",
                "support representative",
                "contact the it service desk",
                "please provide your contact details",
                "contact details below",
            )

            st.session_state.show_escalation_form = any(
                phrase in response_lower
                for phrase in escalation_phrases
            )

            # Reset submission state for a newly triggered form
            if st.session_state.show_escalation_form:
                st.session_state.escalation_submitted = False
                st.session_state.escalation_contact = None


            # =================================================
            # STREAM RESPONSE
            # =================================================
            st.write_stream(
                text_streamer(
                    clean_output
                )
            )


            # =================================================
            # LIVE METADATA
            # =================================================
            live_cols = st.columns(3)


            live_cols[0].caption(
                f"📁 Dept: {department_meta}"
            )


            live_cols[1].caption(
                f"🎭 Sentiment: {sentiment_meta}"
            )

            # =================================================
            # SAVE ASSISTANT RESPONSE
            # =================================================
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": clean_output,
                    "metadata": {
                        "department": department_meta,
                        "sentiment": sentiment_meta,
                    },
                }
            )

    # ========================================================
    # REFRESH UI
    # ========================================================
    st.rerun()


# ============================================================
# HUMAN ESCALATION FORM (ADDED)
# ============================================================
if st.session_state.show_escalation_form:

    st.write("---")
    st.subheader("📞 Contact Human Support")

    st.write(
        "Please provide your contact details so our support "
        "team can follow up with you."
    )

    if not st.session_state.escalation_submitted:

        with st.form("human_escalation_form"):

            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
            )

            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
            )

            phone = st.text_input(
                "Phone Number",
                placeholder="Enter your phone number",
            )

            submitted = st.form_submit_button(
                "Submit Contact Details",
                use_container_width=True,
            )

            if submitted:

                if not full_name.strip():
                    st.error("Please enter your full name.")

                elif (
                    not email.strip()
                    or "@" not in email
                    or "." not in email.split("@")[-1]
                ):
                    st.error("Please enter a valid email address.")

                elif not phone.strip():
                    st.error("Please enter your phone number.")

                else:
                    st.session_state.escalation_contact = {
                        "full_name": full_name.strip(),
                        "email": email.strip(),
                        "phone": phone.strip(),
                    }

                    st.session_state.escalation_submitted = True
                    st.rerun()

    else:

        contact = st.session_state.escalation_contact

        st.success(
            "Your contact information has been received. "
            "Someone from the support team can follow up with you."
        )

        st.write("**Submitted Contact Details**")
        st.write(f"**Name:** {contact['full_name']}")
        st.write(f"**Email:** {contact['email']}")
        st.write(f"**Phone:** {contact['phone']}")
