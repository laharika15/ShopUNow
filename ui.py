import streamlit as st
import uuid
from database import initialize_database
from agent import graph_app
from memory import conversation_memory

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
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        margin-top: 10px;
    }

    .subtitle {
        color: #64748B;
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 5px;
        margin-bottom: 1.5rem;
    }
    
    /* Modern Button Styling */
    div.stButton > button:first-child {
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
col1, col2 = st.columns([1, 4])
with col1:
    import os
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=120)
    else:
        st.markdown("<h1>🛍️</h1>", unsafe_allow_html=True)

with col2:
    st.markdown(
        '<div class="main-title">ShopUNow Assistant</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="subtitle">'
        'Intelligent enterprise support powered by Agentic AI, RAG, and LangGraph'
        '</div>',
        unsafe_allow_html=True
    )

st.divider()

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "escalation_pending" not in st.session_state:
    st.session_state.escalation_pending = False

if "escalation_query" not in st.session_state:
    st.session_state.escalation_query = ""

if "escalation_confirmation" not in st.session_state:
    st.session_state.escalation_confirmation = None
# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("💡 Try an Example")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        conversation_memory.clear(st.session_state.session_id)
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
    st.write("• Human support escalation")
    st.write("• Contact information collection")
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

            with st.spinner(
                "🤖 ShopUNow AI is analyzing your question..."
            ):
                result = graph_app.invoke({
                    "query": query,
                    "session_id": st.session_state.session_id
                })

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
            
            conversation_memory.add_turn(st.session_state.session_id, query, result["response"])

            # -----------------------------
            # Human escalation detected
            # -----------------------------
            if result.get("needs_escalation", False):

                st.session_state.escalation_pending = True
                st.session_state.escalation_query = query

    except Exception as e:
        st.error(f"Something went wrong: {e}")


# -----------------------------
# Human Support Contact Form
# -----------------------------
if (
    st.session_state.escalation_pending
    and not st.session_state.escalation_confirmation
):

    st.divider()

    st.subheader("📞 Contact ShopUNow Support")

    st.write(
        "Please provide your contact details below. "
        "A ShopUNow support representative will follow up with you."
    )

    with st.form("human_support_form"):

        name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        phone = st.text_input(
            "Phone Number",
            placeholder="Enter your phone number"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address"
        )

        submitted = st.form_submit_button(
            "Submit Support Request",
            use_container_width=True
        )

        if submitted:

            if not name.strip():
                st.error("Please enter your name.")

            elif not phone.strip():
                st.error("Please enter your phone number.")

            elif not email.strip():
                st.error("Please enter your email address.")

            elif "@" not in email:
                st.error("Please enter a valid email address.")

            else:

                st.session_state.escalation_confirmation = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip()
                }

                st.session_state.escalation_pending = False

                st.rerun()


# -----------------------------
# Escalation Confirmation
# -----------------------------
if st.session_state.escalation_confirmation:

    contact = st.session_state.escalation_confirmation

    st.divider()

    st.success(
        "✅ Your support request has been received!"
    )

    st.subheader("📋 Information Received")

    st.write(f"**Name:** {contact['name']}")
    st.write(f"**Phone:** {contact['phone']}")
    st.write(f"**Email:** {contact['email']}")

    st.info(
        "Thank you! A ShopUNow support representative "
        "will reach out to you soon."
    )

    if st.button(
        "Start New Support Request",
        use_container_width=True
    ):
        st.session_state.escalation_confirmation = None
        st.session_state.escalation_query = ""
        st.rerun()
