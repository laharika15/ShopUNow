import streamlit as st
from database import initialize_database
from agent import graph_app

initialize_database()

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="ShopUNow AI Assistant",
    page_icon="🛍️",
    layout="centered"
)

# -----------------------------
# Custom styling
# -----------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown(
    '<div class="main-title">🛍️ ShopUNow AI Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Intelligent support powered by Agentic AI, RAG, and LangGraph'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("💡 Try an Example")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    example_questions = [
        "How do I reset my ShopUNow employee VPN password?",
        "How do I apply for a vacation day?",
        "What should I do if my laptop is running slow?",
        "I am extremely frustrated because my VPN has been broken for days!"
    ]

    for question in example_questions:
        if st.button(question, use_container_width=True):
            st.session_state.pending_question = question

    st.divider()

    st.caption("Supported departments")
    st.write("• HR")
    st.write("• IT Support")
    st.write("• Billing & Payments")
    st.write("• Shipping & Delivery")

    st.divider()

    st.caption("🤖 AI capabilities")
    st.write("• Department-aware routing")
    st.write("• Knowledge-grounded answers")
    st.write("• Sentiment detection")
    st.write("• Human escalation")
    st.write("• Hallucination prevention")

# -----------------------------
# Display previous messages
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant" and "metadata" in message:
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.caption("Department")
                st.write(message["metadata"]["department"])

            with col2:
                st.caption("Sentiment")
                st.write(message["metadata"]["sentiment"])

# -----------------------------
# Get user input
# -----------------------------
query = st.chat_input("Ask your ShopUNow question...")

if "pending_question" in st.session_state:
    query = st.session_state.pop("pending_question")

# -----------------------------
# Process query
# -----------------------------
if query:

    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    with st.chat_message("user"):
        st.write(query)

    try:
        with st.chat_message("assistant"):

            with st.spinner("🤖 ShopUNow AI is analyzing your question..."):
                result = graph_app.invoke({"query": query})

            st.write(result["response"])

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.caption("Department")
                st.write(result["department"])

            with col2:
                st.caption("Sentiment")
                st.write(result["sentiment"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "metadata": {
                    "department": result["department"],
                    "sentiment": result["sentiment"]
                }
            })

    except Exception as e:
        st.error(f"Something went wrong: {e}")
