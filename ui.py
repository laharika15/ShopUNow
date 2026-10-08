import uuid
import streamlit as st

from database import initialize_database
from agent import run_agent
from memory import conversation_memory


# ============================================================
# INITIALIZATION
# ============================================================

initialize_database()

st.set_page_config(
    page_title="ShopUNow AI Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
# CUSTOM DESIGN
# ============================================================

st.markdown(
    """
    <style>

    /* -------------------------------------------------------
       GLOBAL
    ------------------------------------------------------- */

    .stApp {
        background: #f7f9fc;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* -------------------------------------------------------
       SIDEBAR
    ------------------------------------------------------- */

    [data-testid="stSidebar"] {
        background: #0b2a52;
        border-right: 1px solid #163f70;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.08);
        color: white;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        text-align: left;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.16);
        border-color: #ff9d24;
        color: white;
    }

    /* -------------------------------------------------------
       HEADER
    ------------------------------------------------------- */

    .brand-header {
        background: white;
        border-radius: 18px;
        padding: 18px 24px;
        margin-bottom: 20px;
        border: 1px solid #e4e9f0;
        box-shadow: 0 4px 18px rgba(11, 42, 82, 0.06);
    }

    .brand-title {
        font-size: 2rem;
        font-weight: 750;
        color: #0b2a52;
        margin-bottom: 2px;
    }

    .brand-subtitle {
        color: #667085;
        font-size: 0.95rem;
        margin-top: 0;
    }

    .online-status {
        display: inline-block;
        background: #ecfdf3;
        color: #15803d;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 8px;
    }

    /* -------------------------------------------------------
       WELCOME CARD
    ------------------------------------------------------- */

    .welcome-card {
        background: linear-gradient(
            135deg,
            #ffffff 0%,
            #f4f8ff 100%
        );
        border: 1px solid #dce6f3;
        border-radius: 20px;
        padding: 32px;
        margin: 20px 0 25px 0;
        box-shadow: 0 6px 24px rgba(11, 42, 82, 0.06);
    }

    .welcome-title {
        color: #0b2a52;
        font-size: 1.65rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .welcome-text {
        color: #667085;
        font-size: 1rem;
        line-height: 1.6;
    }

    .capability {
        background: white;
        border: 1px solid #e5eaf1;
        border-radius: 12px;
        padding: 14px;
        margin-top: 10px;
        color: #344054;
        font-size: 0.9rem;
    }

    /* -------------------------------------------------------
       CHAT
    ------------------------------------------------------- */

    [data-testid="stChatMessage"] {
        border-radius: 16px;
        margin-bottom: 12px;
    }

    [data-testid="stChatMessageContent"] {
        font-size: 0.96rem;
        line-height: 1.65;
    }

    /* -------------------------------------------------------
       CHAT INPUT
    ------------------------------------------------------- */

    [data-testid="stChatInput"] {
        border-radius: 16px;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
        border: 1px solid #d5dce6 !important;
        background: white !important;
    }

    /* -------------------------------------------------------
       METADATA BADGES
    ------------------------------------------------------- */

    .metadata-container {
        display: flex;
        gap: 8px;
        margin-top: 10px;
    }

    .metadata-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background: #f0f5fb;
        color: #24568c;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid #dbe7f3;
    }

    .sentiment-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background: #fff7ed;
        color: #c2410c;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid #fed7aa;
    }

    /* -------------------------------------------------------
       SECTION CARDS
    ------------------------------------------------------- */

    .section-card {
        background: white;
        border: 1px solid #e4e9f0;
        border-radius: 18px;
        padding: 24px;
        margin-top: 25px;
        box-shadow: 0 4px 18px rgba(11, 42, 82, 0.05);
    }

    .section-title {
        color: #0b2a52;
        font-size: 1.25rem;
        font-weight: 700;
    }

    .section-description {
        color: #667085;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* -------------------------------------------------------
       BUTTONS
    ------------------------------------------------------- */

    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }

    /* -------------------------------------------------------
       SUPPORT FORM
    ------------------------------------------------------- */

    [data-testid="stForm"] {
        background: white;
        padding: 22px;
        border-radius: 16px;
        border: 1px solid #e4e9f0;
    }

    /* -------------------------------------------------------
       DIVIDER
    ------------------------------------------------------- */

    hr {
        border-color: #e4e9f0 !important;
    }

    /* -------------------------------------------------------
       FOOTER
    ------------------------------------------------------- */

    .footer {
        text-align: center;
        color: #98a2b3;
        font-size: 0.78rem;
        margin-top: 40px;
        padding-top: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # Logo
    try:
        st.image(
            "assets/shopunow_logo.png",
            width=210,
        )
    except Exception:
        st.markdown(
            """
            <div style="
                font-size: 1.7rem;
                font-weight: 750;
                margin-bottom: 15px;
            ">
                🛍️ ShopUNow
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="
            color:#b9c9dc;
            font-size:0.85rem;
            margin-bottom:20px;
        ">
            AI-powered support assistant
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💡 Try an Example")

    if st.button(
        "🗑️  Clear Chat",
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

    st.markdown("")

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
        ):
            st.session_state.pending_question = question

    st.divider()

    st.markdown("### Departments")

    departments = [
        "👥 HR",
        "💻 IT Support",
        "💳 Billing & Payments",
        "📦 Shipping & Delivery",
    ]

    for department in departments:
        st.markdown(
            f"""
            <div style="
                padding:7px 0;
                color:#d7e3f0;
                font-size:0.88rem;
            ">
                {department}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 🤖 AI Capabilities")

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
            <div style="
                padding:5px 0;
                color:#c9d8e8;
                font-size:0.82rem;
            ">
                ✓ {capability}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="brand-header">
        <div class="brand-title">
            🛍️ ShopUNow AI Assistant
        </div>

        <div class="brand-subtitle">
            Intelligent support powered by Agentic AI, RAG & LangGraph
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

            <div class="welcome-title">
                👋 Welcome to ShopUNow
            </div>

            <div class="welcome-text">
                I'm your AI support assistant. Ask me a question and
                I'll route it to the right department and provide a
                knowledge-grounded answer.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="capability">
                <b>🎯 Smart Routing</b><br>
                Automatically identifies the right department.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="capability">
                <b>🧠 Knowledge Grounded</b><br>
                Answers are based on the ShopUNow knowledge base.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="capability">
                <b>👤 Human Support</b><br>
                Escalates conversations when human help is needed.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")


# ============================================================
# DISPLAY PREVIOUS MESSAGES
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
    "Ask your ShopUNow question..."
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

        # Human escalation detected
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
                It looks like this conversation would benefit from
                human assistance. Please provide your contact
                information and a ShopUNow support representative
                will follow up with you.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

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
        ShopUNow AI Assistant &nbsp;•&nbsp;
        Agentic AI &nbsp;•&nbsp;
        RAG &nbsp;•&nbsp;
        LangGraph
    </div>
    """,
    unsafe_allow_html=True,
)         
