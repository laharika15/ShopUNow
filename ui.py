import uuid
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
# INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# SESSION STATE
# ============================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "escalation_pending" not in st.session_state:
    st.session_state.escalation_pending = False

if "escalation_query" not in st.session_state:
    st.session_state.escalation_query = ""

if "escalation_confirmation" not in st.session_state:
    st.session_state.escalation_confirmation = None


# ============================================================
# PROFESSIONAL DESIGN
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background: #f6f8fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    /* Remove excessive Streamlit spacing */
    [data-testid="stVerticalBlock"] {
        gap: 0.6rem;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    [data-testid="stSidebar"] {
        background: #0b2a52;
        border-right: 1px solid #163f70;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    [data-testid="stSidebar"] .stImage {
        margin-bottom: 5px;
    }

    .sidebar-tagline {
        color: #b9c9dc;
        font-size: 0.82rem;
        margin-top: -5px;
        margin-bottom: 25px;
        line-height: 1.4;
    }

    .sidebar-heading {
        color: #ffffff;
        font-size: 0.86rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-top: 18px;
        margin-bottom: 10px;
    }

    .sidebar-item {
        color: #d7e3f0;
        font-size: 0.84rem;
        padding: 5px 0;
        line-height: 1.35;
    }

    .sidebar-capability {
        color: #c9d8e8;
        font-size: 0.80rem;
        padding: 4px 0;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
        margin: 18px 0;
    }

    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.07);
        color: white;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 9px;
        font-size: 0.82rem;
        text-align: left;
        min-height: 42px;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.14);
        border-color: #ff9d24;
        color: white;
        transform: translateY(-1px);
    }


    /* ======================================================
       TOP HEADER
       ====================================================== */

    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 16px;
        padding: 14px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 14px rgba(11, 42, 82, 0.045);
    }

    .top-header-title {
        color: #0b2a52;
        font-size: 1.22rem;
        font-weight: 700;
        margin: 0;
    }

    .top-header-subtitle {
        color: #667085;
        font-size: 0.78rem;
        margin-top: 2px;
    }

    .online-status {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #ecfdf3;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 6px 11px;
        border-radius: 20px;
        font-size: 0.73rem;
        font-weight: 650;
        white-space: nowrap;
    }


    /* ======================================================
       WELCOME AREA
       ====================================================== */

    .welcome-card {
        background: linear-gradient(
            135deg,
            #ffffff 0%,
            #f4f8ff 100%
        );
        border: 1px solid #dce6f3;
        border-radius: 20px;
        padding: 34px 30px;
        margin-bottom: 18px;
        box-shadow: 0 6px 24px rgba(11, 42, 82, 0.055);
    }

    .welcome-status {
        color: #15803d;
        font-size: 0.76rem;
        font-weight: 650;
        margin-bottom: 9px;
    }

    .welcome-title {
        color: #0b2a52;
        font-size: 2rem;
        font-weight: 750;
        line-height: 1.2;
        margin-bottom: 10px;
    }

    .welcome-text {
        color: #667085;
        font-size: 0.98rem;
        line-height: 1.65;
        max-width: 700px;
        margin-bottom: 12px;
    }

    .technology-line {
        color: #98a2b3;
        font-size: 0.73rem;
        letter-spacing: 0.15px;
    }


    /* ======================================================
       DEPARTMENT CARDS
       ====================================================== */

    .department-card {
        background: #ffffff;
        border: 1px solid #e4e9f0;
        border-radius: 15px;
        padding: 17px 16px;
        min-height: 104px;
        box-shadow: 0 3px 12px rgba(11, 42, 82, 0.035);
        transition: all 0.2s ease;
    }

    .department-card:hover {
        border-color: #c8d8eb;
        box-shadow: 0 6px 18px rgba(11, 42, 82, 0.07);
        transform: translateY(-2px);
    }

    .department-icon {
        font-size: 1.25rem;
        margin-bottom: 5px;
    }

    .department-name {
        color: #0b2a52;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .department-description {
        color: #667085;
        font-size: 0.72rem;
        line-height: 1.35;
    }


    /* ======================================================
       QUICK QUESTIONS
       ====================================================== */

    .quick-title {
        color: #0b2a52;
        font-size: 0.92rem;
        font-weight: 700;
        margin-top: 18px;
        margin-bottom: 4px;
    }

    .quick-subtitle {
        color: #98a2b3;
        font-size: 0.74rem;
        margin-bottom: 8px;
    }

    .quick-question button {
        min-height: 46px;
    }


    /* ======================================================
       CHAT
       ====================================================== */

    [data-testid="stChatMessage"] {
        border-radius: 16px;
        margin-bottom: 10px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    [data-testid="stChatMessageContent"] {
        font-size: 0.94rem;
        line-height: 1.65;
    }

    [data-testid="stChatMessageAvatarIcon-user"] {
        background: #e9eef5;
    }

    [data-testid="stChatMessageAvatarIcon-assistant"] {
        background: #e9eef5;
    }


    /* ======================================================
       CHAT INPUT
       ====================================================== */

    [data-testid="stChatInput"] {
        padding-top: 8px;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
        border: 1px solid #d5dce6 !important;
        background: #ffffff !important;
        font-size: 0.92rem !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #7b9fc7 !important;
        box-shadow: 0 0 0 2px rgba(39, 91, 145, 0.08) !important;
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
        background: #f0f5fb;
        color: #24568c;
        font-size: 0.68rem;
        font-weight: 650;
        border: 1px solid #dbe7f3;
    }

    .sentiment-badge {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 20px;
        background: #fff7ed;
        color: #c2410c;
        font-size: 0.68rem;
        font-weight: 650;
        border: 1px solid #fed7aa;
    }


    /* ======================================================
       SUPPORT SECTION
       ====================================================== */

    .section-card {
        background: #ffffff;
        border: 1px solid #e4e9f0;
        border-radius: 17px;
        padding: 23px;
        margin-top: 24px;
        box-shadow: 0 4px 18px rgba(11, 42, 82, 0.045);
    }

    .section-title {
        color: #0b2a52;
        font-size: 1.12rem;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .section-description {
        color: #667085;
        font-size: 0.87rem;
        line-height: 1.55;
    }

    [data-testid="stForm"] {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e4e9f0;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .footer {
        text-align: center;
        color: #98a2b3;
        font-size: 0.70rem;
        margin-top: 38px;
        padding-top: 18px;
        border-top: 1px solid #e4e9f0;
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
            padding: 25px 20px;
        }

        .welcome-title {
            font-size: 1.55rem;
        }

        .top-header {
            padding: 12px 15px;
        }

        .top-header-title {
            font-size: 1rem;
        }

        .online-status {
            font-size: 0.66rem;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # EXISTING LOGO — PRESERVED
    # --------------------------------------------------------

    try:
        st.image(
            "assets/shopunow_logo.png",
            width=210,
        )
    except Exception:
        st.markdown(
            """
            <div style="
                font-size:1.7rem;
                font-weight:750;
                margin-bottom:15px;
            ">
                🛍️ ShopUNow
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="sidebar-tagline">
            AI-powered support assistant
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CHAT CONTROLS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">Quick Actions</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "↻  Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []

        conversation_memory.clear(
            st.session_state.session_id
        )

        st.session_state.escalation_pending = False
        st.session_state.escalation_query = ""
        st.session_state.escalation_confirmation = None

        st.rerun()

    # --------------------------------------------------------
    # EXAMPLES
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">Example Questions</div>',
        unsafe_allow_html=True,
    )

    example_questions = [
        "How do I reset my ShopUNow employee VPN password?",
        "How do I apply for a vacation day?",
        "What should I do if my laptop is running slow?",
        "I am extremely frustrated because my VPN has been broken for days!",
    ]

    for question in example_questions:
        if st.button(
            question,
            use_container_width=True,
            key=f"example_{question}",
        ):
            st.session_state.pending_question = question
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # DEPARTMENTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">Departments</div>',
        unsafe_allow_html=True,
    )

    departments = [
        "👥  HR",
        "💻  IT Support",
        "💳  Billing & Payments",
        "📦  Shipping & Delivery",
    ]

    for department in departments:
        st.markdown(
            f'<div class="sidebar-item">{department}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # --------------------------------------------------------
    # AI CAPABILITIES
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-heading">AI Capabilities</div>',
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
            f'<div class="sidebar-capability">✓ {capability}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="top-header">

        <div>
            <div class="top-header-title">
                ShopUNow AI Assistant
            </div>

            <div class="top-header-subtitle">
                Intelligent retail support
            </div>
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

    dept_col1, dept_col2, dept_col3, dept_col4 = st.columns(4)

    department_cards = [
        (
            dept_col1,
            "👥",
            "HR",
            "Leave, policies & employee support",
        ),
        (
            dept_col2,
            "💻",
            "IT Support",
            "Technical issues & access help",
        ),
        (
            dept_col3,
            "💳",
            "Billing & Payments",
            "Payments, refunds & billing",
        ),
        (
            dept_col4,
            "📦",
            "Shipping & Delivery",
            "Orders, delivery & tracking",
        ),
    ]

    for column, icon, name, description in department_cards:

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

    q_col1, q_col2 = st.columns(2)

    quick_questions = [
        "How do I request paid time off?",
        "What should I do if my laptop is running slow?",
        "How can I request a refund?",
        "Where can I check my order status?",
    ]

    with q_col1:

        if st.button(
            "💬  How do I request paid time off?",
            use_container_width=True,
            key="quick_q1",
        ):
            st.session_state.pending_question = quick_questions[0]
            st.rerun()

        if st.button(
            "💬  How can I request a refund?",
            use_container_width=True,
            key="quick_q3",
        ):
            st.session_state.pending_question = quick_questions[2]
            st.rerun()

    with q_col2:

        if st.button(
            "💬  What should I do if my laptop is running slow?",
            use_container_width=True,
            key="quick_q2",
        ):
            st.session_state.pending_question = quick_questions[1]
            st.rerun()

        if st.button(
            "💬  Where can I check my order status?",
            use_container_width=True,
            key="quick_q4",
        ):
            st.session_state.pending_question = quick_questions[3]
            st.rerun()


# ============================================================
# DISPLAY CONVERSATION
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="🤖" if message["role"] == "assistant" else "👤",
    ):

        st.write(message["content"])

        if (
            message["role"] == "assistant"
            and "metadata" in message
        ):

            department = message["metadata"].get(
                "department",
                "Unknown",
            )

            sentiment = message["metadata"].get(
                "sentiment",
                "Unknown",
            )

            st.markdown(
                f"""
                <div class="metadata-container">

                    <span class="metadata-badge">
                        🏢 {department}
                    </span>

                    <span class="sentiment-badge">
                        💬 {sentiment}
                    </span>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# USER INPUT
# ============================================================

query = st.chat_input(
    "Ask ShopUNow a question..."
)

if "pending_question" in st.session_state:

    query = st.session_state.pop(
        "pending_question"
    )


# ============================================================
# PROCESS QUERY
# ============================================================

if query:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message(
        "user",
        avatar="👤",
    ):
        st.write(query)

    try:

        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):

            with st.spinner(
                "ShopUNow AI is analyzing your question..."
            ):

                result = run_agent(
                    query=query,
                    session_id=st.session_state.session_id,
                )

            st.write(
                result["response"]
            )

            department = result.get(
                "department",
                "Unknown",
            )

            sentiment = result.get(
                "sentiment",
                "Unknown",
            )

            st.markdown(
                f"""
                <div class="metadata-container">

                    <span class="metadata-badge">
                        🏢 {department}
                    </span>

                    <span class="sentiment-badge">
                        💬 {sentiment}
                    </span>

                </div>
                """,
                unsafe_allow_html=True,
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["response"],
                "metadata": {
                    "department": department,
                    "sentiment": sentiment,
                },
            }
        )

        # ----------------------------------------------------
        # HUMAN ESCALATION DETECTED
        # ----------------------------------------------------

        if result.get(
            "needs_escalation",
            False,
        ):

            st.session_state.escalation_pending = True
            st.session_state.escalation_query = query

    except Exception as e:

        st.error(
            f"Something went wrong: {e}"
        )


# ============================================================
# HUMAN SUPPORT FORM
# ============================================================

if (
    st.session_state.escalation_pending
    and not st.session_state.escalation_confirmation
):

    st.markdown(
        """
        <div class="section-card">

            <div class="section-title">
                📞 Connect with Human Support
            </div>

            <div class="section-description">
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
        <div class="section-card">

            <div class="section-title">
                ✅ Support Request Received
            </div>

            <div class="section-description">
                Your information has been successfully submitted.
                A ShopUNow support representative will reach out
                to you soon.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

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
