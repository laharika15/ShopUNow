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

if "escalation_pending" not in st.session_state:
    st.session_state.escalation_pending = False

if "escalation_query" not in st.session_state:
    st.session_state.escalation_query = ""

if "escalation_confirmation" not in st.session_state:
    st.session_state.escalation_confirmation = None


# ============================================================
# PROFESSIONAL ENTERPRISE UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background-color: #F4F6F9;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    [data-testid="stSidebar"] {
        background-color: #0B2545 !important;
        border-right: 1px solid #173B64;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] caption,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 9px;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stSidebar"] .stButton button p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.16) !important;
        color: #FFFFFF !important;
        border-color: #10B981 !important;
        transform: translateY(-1px);
    }

    [data-testid="stSidebar"] .stButton button:hover p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    .sidebar-heading {
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .sidebar-description {
        color: #B9C9DC !important;
        font-size: 0.80rem;
        line-height: 1.4;
        margin-bottom: 20px;
    }

    .sidebar-capability {
        color: #C9D8E8 !important;
        font-size: 0.80rem;
        padding: 4px 0;
    }


    /* ======================================================
       MAIN HEADER
       ====================================================== */

    .header-container {
        background-color: #FFFFFF;
        padding: 18px 22px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 3px 14px rgba(0, 0, 0, 0.045);
        margin-bottom: 18px;
    }

    .top-header-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B !important;
        margin-bottom: 2px;
    }

    .top-header-subtitle {
        font-size: 0.80rem;
        color: #64748B !important;
    }

    .online-status {
        display: inline-block;
        font-size: 0.73rem;
        color: #059669 !important;
        font-weight: 650;
        background-color: #ECFDF3;
        border: 1px solid #BBF7D0;
        padding: 5px 10px;
        border-radius: 20px;
        margin-top: 9px;
    }


    /* ======================================================
       WELCOME CARD
       ====================================================== */

    .welcome-card {
        background: linear-gradient(
            135deg,
            #FFFFFF 0%,
            #F4F8FF 100%
        );

        border: 1px solid #DCE6F3;
        border-radius: 20px;

        padding: 30px;

        margin-bottom: 18px;

        box-shadow:
            0 6px 24px rgba(11, 42, 82, 0.055);
    }

    .welcome-status {
        display: inline-block;

        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.07em;

        color: #059669 !important;

        background-color: #D1FAE5;

        border: 1px solid #A7F3D0;

        padding: 5px 9px;

        border-radius: 5px;

        margin-bottom: 10px;
    }

    .welcome-title {
        color: #0B2A52 !important;
        font-size: 2rem;
        font-weight: 750;
        line-height: 1.2;
        margin-bottom: 10px;
    }

    .welcome-text {
        color: #667085 !important;
        font-size: 0.96rem;
        line-height: 1.65;
        max-width: 700px;
        margin-bottom: 12px;
    }

    .technology-line {
        color: #98A2B3 !important;
        font-size: 0.72rem;
        letter-spacing: 0.01em;
    }


    /* ======================================================
       DEPARTMENT CARDS
       ====================================================== */

    .department-card {
        background: #FFFFFF;

        border: 1px solid #E4E9F0;
        border-radius: 15px;

        padding: 16px;

        min-height: 105px;

        box-shadow:
            0 3px 12px rgba(11, 42, 82, 0.035);

        transition: all 0.2s ease;
    }

    .department-card:hover {
        border-color: #C8D8EB;

        box-shadow:
            0 6px 18px rgba(11, 42, 82, 0.07);

        transform: translateY(-2px);
    }

    .department-icon {
        font-size: 1.25rem;
        margin-bottom: 4px;
    }

    .department-name {
        color: #0B2A52 !important;
        font-size: 0.87rem;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .department-description {
        color: #667085 !important;
        font-size: 0.70rem;
        line-height: 1.35;
    }


    /* ======================================================
       QUICK QUESTIONS
       ====================================================== */

    .quick-title {
        color: #0B2A52 !important;
        font-size: 0.92rem;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 3px;
    }

    .quick-subtitle {
        color: #98A2B3 !important;
        font-size: 0.74rem;
        margin-bottom: 8px;
    }


    /* ======================================================
       CHAT
       ====================================================== */

    [data-testid="stChatMessage"] {
        border-radius: 16px;
        margin-bottom: 10px;
    }

    [data-testid="stChatMessageContent"] {
        font-size: 0.94rem;
        line-height: 1.65;
    }


    /* ======================================================
       CHAT INPUT
       ====================================================== */

    [data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
        border: 1px solid #D5DCE6 !important;
        background-color: #FFFFFF !important;
        font-size: 0.92rem !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #7B9FC7 !important;
        box-shadow:
            0 0 0 2px rgba(39, 91, 145, 0.08) !important;
    }


    /* ======================================================
       METADATA
       ====================================================== */

    .metadata-container {
        display: flex;
        gap: 7px;
        flex-wrap: wrap;
        margin-top: 10px;
    }

    .metadata-badge {
        display: inline-block;

        padding: 4px 9px;

        border-radius: 20px;

        background-color: #F0F5FB;
        color: #24568C !important;

        font-size: 0.68rem;
        font-weight: 650;

        border: 1px solid #DBE7F3;
    }

    .sentiment-badge {
        display: inline-block;

        padding: 4px 9px;

        border-radius: 20px;

        background-color: #FFF7ED;
        color: #C2410C !important;

        font-size: 0.68rem;
        font-weight: 650;

        border: 1px solid #FED7AA;
    }

    .scope-badge {
        display: inline-block;

        padding: 4px 9px;

        border-radius: 20px;

        background-color: #F5F3FF;
        color: #6D28D9 !important;

        font-size: 0.68rem;
        font-weight: 650;

        border: 1px solid #DDD6FE;
    }


    /* ======================================================
       SUPPORT CARD
       ====================================================== */

    .support-card {
        background: #FFFFFF;

        border: 1px solid #E4E9F0;
        border-radius: 17px;

        padding: 23px;

        margin-top: 25px;

        box-shadow:
            0 4px 18px rgba(11, 42, 82, 0.045);
    }

    .support-title {
        color: #0B2A52 !important;
        font-size: 1.12rem;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .support-description {
        color: #667085 !important;
        font-size: 0.87rem;
        line-height: 1.55;
    }

    [data-testid="stForm"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E4E9F0;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .footer {
        text-align: center;

        color: #98A2B3 !important;

        font-size: 0.70rem;

        margin-top: 38px;
        padding-top: 18px;

        border-top: 1px solid #E4E9F0;
    }


    /* ======================================================
       MOBILE
       ====================================================== */

    @media (max-width: 700px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .welcome-card {
            padding: 23px 20px;
        }

        .welcome-title {
            font-size: 1.55rem;
        }

        .department-card {
            margin-bottom: 8px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AVATARS
# ============================================================

USER_AVATAR = "👤"

try:
    with open(
        "assets/shopunow_logo.png",
        "rb",
    ):
        BOT_AVATAR = "assets/shopunow_logo.png"

except FileNotFoundError:
    BOT_AVATAR = "🛍️"


# ============================================================
# RESPONSE STREAMING
# ============================================================

def text_streamer(text_block: str):
    """
    Creates a lightweight word-by-word response animation.
    """
    for word in text_block.split(" "):
        yield word + " "
        time.sleep(0.025)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # EXISTING SHOPUNOW LOGO — NOT CHANGED
    # --------------------------------------------------------

    try:
        st.image(
            "assets/shopunow_logo.png",
            width=210,
        )

        st.markdown(
            """
            <div class="sidebar-description">
                AI-powered support assistant
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception:

        st.title("🛍️ ShopUNow")

        st.caption(
            "AI-powered support assistant"
        )

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">QUICK ACTIONS</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🔄  Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.active_prompt = None

        st.session_state.escalation_pending = False
        st.session_state.escalation_query = ""
        st.session_state.escalation_confirmation = None

        conversation_memory.clear(
            st.session_state.session_id
        )

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # EXAMPLE QUESTIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">EXAMPLE QUESTIONS</div>',
        unsafe_allow_html=True,
    )

    example_questions = [
        "How do I reset my ShopUNow employee VPN password?",
        "How do I apply for a vacation day?",
        "What should I do if my laptop is running slow?",
        "I am extremely frustrated because my VPN has been broken for days!",
    ]

    for index, question in enumerate(
        example_questions
    ):

        if st.button(
            question,
            use_container_width=True,
            key=f"example_question_{index}",
        ):

            st.session_state.active_prompt = question
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # DEPARTMENTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">DEPARTMENTS</div>',
        unsafe_allow_html=True,
    )

    department_actions = [
        (
            "👥  HR Department",
            "I need assistance from the HR department regarding company policy.",
        ),
        (
            "💻  IT Support",
            "I need to open an IT technical support request.",
        ),
        (
            "💳  Billing & Payments",
            "I have a question about billing or payments.",
        ),
        (
            "📦  Shipping & Delivery",
            "I need help with shipping or delivery.",
        ),
    ]

    for index, (label, prompt) in enumerate(
        department_actions
    ):

        if st.button(
            label,
            use_container_width=True,
            key=f"department_{index}",
        ):

            st.session_state.active_prompt = prompt
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # AI CAPABILITIES
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">AI CAPABILITIES</div>',
        unsafe_allow_html=True,
    )

    capabilities = [
        "Department-aware routing",
        "Knowledge-grounded answers",
        "Sentiment detection",
        "Conversational memory",
        "Human escalation",
        "Hallucination prevention",
    ]

    for capability in capabilities:

        st.markdown(
            f"""
            <div class="sidebar-capability">
                ✓ {capability}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN HEADER
# ============================================================

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


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.messages:

    st.markdown(
        """
        <div class="welcome-card">

            <div class="welcome-status">
                ● READY TO HELP
            </div>

            <div class="welcome-title">
                👋 Welcome to ShopUNow
            </div>

            <div class="welcome-text">
                Your intelligent retail support assistant.
                Ask a question and I'll connect you with the
                right department and provide an answer grounded
                in the ShopUNow knowledge base.
            </div>

            <div class="technology-line">
                Powered by Agentic AI · RAG · LangGraph
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # DEPARTMENT CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    cards = [
        (
            col1,
            "👥",
            "HR",
            "Leave, policies & employee support",
        ),
        (
            col2,
            "💻",
            "IT Support",
            "Technical issues & access help",
        ),
        (
            col3,
            "💳",
            "Billing & Payments",
            "Payments, refunds & billing",
        ),
        (
            col4,
            "📦",
            "Shipping & Delivery",
            "Orders, delivery & tracking",
        ),
    ]

    for column, icon, name, description in cards:

        with column:

            st.markdown(
                f"""
                <div class="department-card">

                    <div class="department-icon">
                        {icon}
                    </div>

                    <div class="department-name">
                        {name}
                    </div>

                    <div class="department-description">
                        {description}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # QUICK QUESTIONS
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="quick-title">
            Try asking
        </div>

        <div class="quick-subtitle">
            Select a question to start a conversation
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2 = st.columns(2)

    with q1:

        if st.button(
            "💬  How do I request paid time off?",
            use_container_width=True,
            key="quick_paid_time_off",
        ):

            st.session_state.active_prompt = (
                "How do I request paid time off?"
            )

            st.rerun()

        if st.button(
            "💬  How can I request a refund?",
            use_container_width=True,
            key="quick_refund",
        ):

            st.session_state.active_prompt = (
                "How can I request a refund?"
            )

            st.rerun()

    with q2:

        if st.button(
            "💬  What should I do if my laptop is running slow?",
            use_container_width=True,
            key="quick_laptop",
        ):

            st.session_state.active_prompt = (
                "What should I do if my laptop is running slow?"
            )

            st.rerun()

        if st.button(
            "💬  Where can I check my order status?",
            use_container_width=True,
            key="quick_order",
        ):

            st.session_state.active_prompt = (
                "Where can I check my order status?"
            )

            st.rerun()


# ============================================================
# DISPLAY EXISTING CHAT
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

        st.write(
            message["content"]
        )

        if (
            message["role"] == "assistant"
            and "metadata" in message
        ):

            meta = message["metadata"]

            department = meta.get(
                "department",
                "N/A",
            )

            sentiment = meta.get(
                "sentiment",
                "N/A",
            )

            scope = meta.get(
                "scope",
                "In-Scope",
            )

            st.markdown(
                f"""
                <div class="metadata-container">

                    <span class="metadata-badge">
                        📁 {department}
                    </span>

                    <span class="sentiment-badge">
                        🎭 {sentiment}
                    </span>

                    <span class="scope-badge">
                        🎯 {scope}
                    </span>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# USER INPUT
# ============================================================

user_input = st.chat_input(
    "Ask ShopUNow a question..."
)

final_prompt = None


if st.session_state.active_prompt:

    final_prompt = (
        st.session_state.active_prompt
    )

    st.session_state.active_prompt = None

elif user_input:

    final_prompt = user_input


# ============================================================
# PROCESS USER QUERY
# ============================================================

if final_prompt:

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
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message(
        "user",
        avatar=USER_AVATAR,
    ):

        st.write(final_prompt)

    # --------------------------------------------------------
    # GENERATE ASSISTANT RESPONSE
    # --------------------------------------------------------

    with st.chat_message(
        "assistant",
        avatar=BOT_AVATAR,
    ):

        department_meta = "Unknown"
        sentiment_meta = "Neutral"
        scope_meta = "In-Scope"
        clean_output = ""

        try:

            with st.spinner(
                "ShopUNow AI is analyzing your question..."
            ):

                raw_response = run_agent(
                    final_prompt,
                    st.session_state.session_id,
                )

            # ------------------------------------------------
            # PARSE BACKEND RESPONSE
            # ------------------------------------------------

            if isinstance(
                raw_response,
                dict,
            ):

                response_data = raw_response

            else:

                response_data = json.loads(
                    raw_response
                )

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

            needs_escalation = response_data.get(
                "needs_escalation",
                False,
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            # Backend returned plain text
            clean_output = str(
                raw_response
            )

            needs_escalation = False

        except Exception:

            clean_output = (
                "I encountered an issue processing "
                "your request. Please try your message again."
            )

            needs_escalation = False

        # ----------------------------------------------------
        # STREAM RESPONSE
        # ----------------------------------------------------

        st.write_stream(
            text_streamer(
                clean_output
            )
        )

        # ----------------------------------------------------
        # DISPLAY METADATA
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="metadata-container">

                <span class="metadata-badge">
                    📁 {department_meta}
                </span>

                <span class="sentiment-badge">
                    🎭 {sentiment_meta}
                </span>

                <span class="scope-badge">
                    🎯 {scope_meta}
                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # SAVE ASSISTANT MESSAGE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # HUMAN ESCALATION
    # --------------------------------------------------------

    if needs_escalation:

        st.session_state.escalation_pending = True

        st.session_state.escalation_query = (
            final_prompt
        )

    # --------------------------------------------------------
    # RENDER UPDATED CHAT
    # --------------------------------------------------------

    st.rerun()


# ============================================================
# HUMAN SUPPORT FORM
# ============================================================

if (
    st.session_state.escalation_pending
    and not st.session_state.escalation_confirmation
):

    st.markdown(
        """
        <div class="support-card">

            <div class="support-title">
                📞 Connect with Human Support
            </div>

            <div class="support-description">
                It looks like this conversation would benefit
                from human assistance. Please provide your
                contact information and a ShopUNow support
                representative will follow up with you.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(
        "human_support_form"
    ):

        name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
        )

        phone = st.text_input(
            "Phone Number",
            placeholder="Enter your phone number",
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address",
        )

        submitted = st.form_submit_button(
            "Submit Support Request",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Please enter your name."
                )

            elif not phone.strip():

                st.error(
                    "Please enter your phone number."
                )

            elif not email.strip():

                st.error(
                    "Please enter your email address."
                )

            elif "@" not in email:

                st.error(
                    "Please enter a valid email address."
                )

            else:

                st.session_state.escalation_confirmation = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                }

                st.session_state.escalation_pending = False

                st.rerun()


# ============================================================
# ESCALATION CONFIRMATION
# ============================================================

if st.session_state.escalation_confirmation:

    contact = (
        st.session_state.escalation_confirmation
    )

    st.markdown(
        """
        <div class="support-card">

            <div class="support-title">
                ✅ Support Request Received
            </div>

            <div class="support-description">
                Your information has been successfully submitted.
                A ShopUNow support representative will reach out
                to you soon.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Name",
            contact["name"],
        )

    with col2:

        st.metric(
            "Phone",
            contact["phone"],
        )

    with col3:

        st.metric(
            "Email",
            contact["email"],
        )

    st.info(
        "Thank you! A ShopUNow support representative "
        "will reach out to you soon."
    )

    if st.button(
        "Start New Support Request",
        use_container_width=True,
    ):

        st.session_state.escalation_confirmation = None
        st.session_state.escalation_query = ""

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        ShopUNow AI Assistant
        &nbsp;•&nbsp;
        Agentic AI
        &nbsp;•&nbsp;
        RAG
        &nbsp;•&nbsp;
        LangGraph
    </div>
    """,
    unsafe_allow_html=True,
)
