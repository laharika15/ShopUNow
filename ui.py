import re
import html
import streamlit as st

from database import initialize_database
from agent import graph_app

# PAGE CONFIGURATION

st.set_page_config(
    page_title="ShopUNow | AI Support",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# DATABASE

initialize_database()

# CUSTOM CSS

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f7f9fc;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* ---------- HEADER ---------- */

    .shop-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 6px;
    }

    .shop-logo {
        width: 52px;
        height: 52px;
        border-radius: 15px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.20);
    }

    .shop-title {
        font-size: 2.15rem;
        font-weight: 750;
        color: #111827;
        letter-spacing: -0.7px;
        line-height: 1.1;
    }

    .shop-subtitle {
        color: #64748b;
        font-size: 0.98rem;
        margin-top: 4px;
    }

    /* ---------- STATUS ---------- */

    .status-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 15px;
        margin-bottom: 24px;
    }

    .status-dot {
        width: 9px;
        height: 9px;
        background: #22c55e;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
    }

    .status-text {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
    }

    /* ---------- WELCOME CARD ---------- */

    .welcome-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 24px;
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.05);
    }

    .welcome-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .welcome-text {
        color: #64748b;
        font-size: 0.96rem;
        line-height: 1.6;
    }

    /* ---------- CAPABILITY CARDS ---------- */

    .capability-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px;
        min-height: 120px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
    }

    .capability-icon {
        font-size: 23px;
        margin-bottom: 8px;
    }

    .capability-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 5px;
    }

    .capability-text {
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.45;
    }

    /* ---------- CHAT ---------- */

    [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 6px 2px;
    }

    [data-testid="stChatMessageContent"] {
        font-size: 0.95rem;
        line-height: 1.65;
    }

    /* ---------- METADATA CARD ---------- */

    .metadata-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 15px;
        margin-top: 12px;
    }

    .metadata-label {
        font-size: 0.70rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .metadata-value {
        font-size: 0.85rem;
        color: #334155;
        font-weight: 650;
    }

    /* ---------- SIDEBAR ---------- */

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .sidebar-brand {
        font-size: 1.15rem;
        font-weight: 750;
        color: #111827;
        margin-bottom: 4px;
    }

    .sidebar-description {
        color: #64748b;
        font-size: 0.78rem;
        line-height: 1.5;
        margin-bottom: 18px;
    }

    .sidebar-section {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        font-weight: 750;
        margin-top: 20px;
        margin-bottom: 9px;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background: white;
        color: #334155;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 9px 12px;
        transition: all 0.15s ease;
    }

    .stButton > button:hover {
        border-color: #93c5fd;
        background: #eff6ff;
        color: #1d4ed8;
    }

    /* ---------- CHAT INPUT ---------- */

    [data-testid="stChatInput"] {
        border-radius: 16px;
    }

    /* ---------- DIVIDERS ---------- */

    hr {
        border-color: #e5e7eb;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.72rem;
        margin-top: 35px;
        padding-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
# HELPER FUNCTIONS

def clean_response(text: str) -> str:
    """
    Prevent raw HTML/XML-like fragments from appearing in
    the user-facing response.
    """

    if not text:
        return ""

    text = str(text)

    # Remove common HTML tags
    text = re.sub(r"<\/?[a-zA-Z][^>]*>", "", text)

    # Remove accidental HTML entities
    text = html.unescape(text)

    # Clean excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def department_icon(department: str) -> str:
    icons = {
        "HR": "👥",
        "IT Support": "💻",
        "Billing & Payments": "💳",
        "Shipping & Delivery": "📦",
        "Unknown": "❔",
    }

    return icons.get(department, "🤖")


def sentiment_icon(sentiment: str) -> str:
    icons = {
        "Positive": "😊",
        "Neutral": "😐",
        "Negative": "⚠️",
    }

    return icons.get(sentiment, "•")

# SESSION STATE

if "messages" not in st.session_state:
    st.session_state.messages = []

# SIDEBAR

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">🛍️ ShopUNow</div>
        <div class="sidebar-description">
            Your intelligent support assistant for everyday
            ShopUNow questions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🗑️  Clear conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        '<div class="sidebar-section">Try asking</div>',
        unsafe_allow_html=True,
    )

    example_questions = [
        "How do I reset my employee VPN password?",
        "How do I apply for a vacation day?",
        "What should I do if my laptop is running slow?",
        "Where is my ShopUNow package?",
    ]

    for question in example_questions:
        if st.button(
            question,
            key=f"example_{question}",
            use_container_width=True,
        ):
            st.session_state.pending_question = question

    st.markdown(
        '<div class="sidebar-section">Supported areas</div>',
        unsafe_allow_html=True,
    )

    departments = [
        ("👥", "HR"),
        ("💻", "IT Support"),
        ("💳", "Billing & Payments"),
        ("📦", "Shipping & Delivery"),
    ]

    for icon, department in departments:
        st.markdown(
            f"""
            <div style="
                padding:7px 0;
                color:#475569;
                font-size:0.84rem;
            ">
                {icon}&nbsp;&nbsp;{department}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sidebar-section">AI capabilities</div>',
        unsafe_allow_html=True,
    )

    capabilities = [
        "🎯 Department-aware routing",
        "📚 Knowledge-grounded answers",
        "🧠 Sentiment detection",
        "🙋 Human escalation",
        "🛡️ Hallucination prevention",
    ]

    for capability in capabilities:
        st.markdown(
            f"""
            <div style="
                padding:5px 0;
                color:#64748b;
                font-size:0.78rem;
            ">
                {capability}
            </div>
            """,
            unsafe_allow_html=True,
        )

# MAIN HEADER

st.markdown(
    """
    <div class="shop-header">
        <div class="shop-logo">🛍️</div>
        <div>
            <div class="shop-title">ShopUNow AI Assistant</div>
            <div class="shop-subtitle">
                Intelligent support powered by Agentic AI + RAG
            </div>
        </div>
    </div>

    <div class="status-row">
        <span class="status-dot"></span>
        <span class="status-text">AI Assistant Online</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# WELCOME SCREEN

if not st.session_state.messages:

    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-title">
                How can I help you today?
            </div>

            <div class="welcome-text">
                Ask a question about HR, IT Support, Billing & Payments,
                or Shipping & Delivery. ShopUNow routes your request to
                the right area and provides answers grounded in its
                support knowledge.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="capability-card">
                <div class="capability-icon">🎯</div>
                <div class="capability-title">
                    Smart Routing
                </div>
                <div class="capability-text">
                    Understands your intent and routes your question
                    to the appropriate support area.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="capability-card">
                <div class="capability-icon">📚</div>
                <div class="capability-title">
                    Grounded Answers
                </div>
                <div class="capability-text">
                    Answers are generated from ShopUNow's trusted
                    knowledge base.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="capability-card">
                <div class="capability-icon">🙋</div>
                <div class="capability-title">
                    Human Escalation
                </div>
                <div class="capability-text">
                    Frustrated or sensitive requests can be routed
                    toward human support.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

# DISPLAY EXISTING MESSAGES

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            clean_response(message["content"])
        )

        if (
            message["role"] == "assistant"
            and "metadata" in message
        ):

            department = message["metadata"].get(
                "department",
                "Unknown"
            )

            sentiment = message["metadata"].get(
                "sentiment",
                "Neutral"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"""
                    <div class="metadata-card">
                        <div class="metadata-label">
                            Department
                        </div>
                        <div class="metadata-value">
                            {department_icon(department)}
                            &nbsp; {department}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""
                    <div class="metadata-card">
                        <div class="metadata-label">
                            Sentiment
                        </div>
                        <div class="metadata-value">
                            {sentiment_icon(sentiment)}
                            &nbsp; {sentiment}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# USER INPUT

query = st.chat_input(
    "Ask ShopUNow anything about support..."
)

if "pending_question" in st.session_state:

    query = st.session_state.pop(
        "pending_question"
    )

# PROCESS QUERY


if query:

    query = query.strip()

    if query:

        # Save user message
       
        st.session_state.messages.append(
            {
                "role": "user",
                "content": query,
            }
        )

        with st.chat_message("user"):
            st.markdown(query)
            
        # Generate response

        try:

            with st.chat_message("assistant"):

                with st.spinner(
                    "ShopUNow AI is thinking..."
                ):

                    result = graph_app.invoke(
                        {
                            "query": query
                        }
                    )

                response = clean_response(
                    result.get(
                        "response",
                        "I'm sorry, I couldn't process that request."
                    )
                )

                department = result.get(
                    "department",
                    "Unknown"
                )

                sentiment = result.get(
                    "sentiment",
                    "Neutral"
                )

                # Display response
        

                st.markdown(response)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(
                        f"""
                        <div class="metadata-card">
                            <div class="metadata-label">
                                Department
                            </div>
                            <div class="metadata-value">
                                {department_icon(department)}
                                &nbsp; {department}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.markdown(
                        f"""
                        <div class="metadata-card">
                            <div class="metadata-label">
                                Sentiment
                            </div>
                            <div class="metadata-value">
                                {sentiment_icon(sentiment)}
                                &nbsp; {sentiment}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Save assistant message
            
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                        "metadata": {
                            "department": department,
                            "sentiment": sentiment,
                        },
                    }
                )

        except Exception:

            st.error(
                "I'm sorry, something went wrong while "
                "processing your request. Please try again."
            )

# FOOTER

st.markdown(
    """
    <div class="footer">
        ShopUNow AI Assistant · Agentic RAG ·
        Department-aware support
    </div>
    """,
    unsafe_allow_html=True,
)
