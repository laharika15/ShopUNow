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

# Initialize database
initialize_database()

# ============================================================
# SESSION STATE POOL
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dynamic prompt buffer for sidebar actions
if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None

# ============================================================
# MODERN ENTERPRISE UI STYLING (CSS)
# ============================================================
st.markdown(
    """
    <style>
    /* Global App Background */
    .stApp {
        background-color: #F4F6F9;
    }
    
    /* Elegant Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #0B2545 !important;
    }
    
    /* Target only text paragraphs, titles, and captions to be white */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] caption,
    [data-testid="stSidebar"] div {
        color: #FFFFFF;
    }
    
    /* FIX FOR SIDEBAR BUTTON TEXT INVISIBILITY */
    [data-testid="stSidebar"] .stButton button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Hover state for sidebar buttons */
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.16) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
    }

    /* Main Layout Framework */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }

    /* Custom Header Badges & Typography */
    .header-container {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR NAVIGATION & QUICK ACTIONS
# ============================================================
with st.sidebar:
    # Try loading your logo file
    try:
        st.image("shopunow_logo.png", use_container_width=True)
    except Exception:
        # Fallback text if file path is unreachable
        st.title("🛍️ ShopUNow")
        st.caption("⚠️ 'shopunow_logo.png' not found in project directory folder.")
        
    st.write("---")
    
    st.subheader("QUICK ACTIONS")
    if st.button("🔄 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_prompt = None
        st.rerun()
        
    st.write("---")
    st.subheader("EXAMPLE QUESTIONS")
    
    if st.button("How do I reset my ShopUNow employee VPN password?", use_container_width=True):
        st.session_state.active_prompt = "How do I reset my ShopUNow employee VPN password?"
        st.rerun()
        
    if st.button("How do I apply for a vacation day?", use_container_width=True):
        st.session_state.active_prompt = "How do I apply for a vacation day?"
        st.rerun()
        
    if st.button("What should I do if my laptop is running slow?", use_container_width=True):
        st.session_state.active_prompt = "What should I do if my laptop is running slow?"
        st.rerun()
        
    if st.button("I am extremely frustrated because my VPN has been broken for days!", use_container_width=True):
        st.session_state.active_prompt = "I am extremely frustrated because my VPN has been broken for days!"
        st.rerun()

    st.write("---")
    
    st.subheader("DEPARTMENTS")
    
    if st.button("👥 HR Department", use_container_width=True):
        st.session_state.active_prompt = "I need assistance from the HR department regarding company policy."
        st.rerun()
        
    if st.button("💻 IT Support", use_container_width=True):
        st.session_state.active_prompt = "I need to open an IT technical support request."
        st.rerun()
        
    if st.button("💳 Billing & Payments", use_container_width=True):
        st.session_state.active_prompt = "I have a question about vendor billing or employee payments."
        st.rerun()
        
    if st.button("📦 Shipping & Delivery", use_container_width=True):
        st.session_state.active_prompt = "Show me the tracking options or shipping department procedures."
        st.rerun()

# ============================================================
# MAIN INTERFACE RENDERER
# ============================================================

# CONDITIONAL WELCOME HEADERS (Only show if there is no chat history yet)
if not st.session_state.messages:
    st.markdown(
        """
        <div class="header-container">
            <div class="top-header-title">ShopUNow AI Assistant</div>
            <div class="top-header-subtitle">Intelligent retail support</div>
            <div class="online-status">● AI Assistant Online</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown('<div class="welcome-status">● READY TO HELP</div>', unsafe_allow_html=True)

# Render Existing Chat Log
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle Prompt Inputs (From sidebar interactions or manual field entry)
user_input = st.chat_input("Ask ShopUNow a question...")
final_prompt = None

if st.session_state.active_prompt:
    final_prompt = st.session_state.active_prompt
    st.session_state.active_prompt = None  # Flush buffer immediately
elif user_input:
    final_prompt = user_input

# Process the Message submission
if final_prompt:
    with st.chat_message("user"):
        st.write(final_prompt)
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Processing request..."):
            try:
                response = run_agent(final_prompt, st.session_state.session_id)
            except Exception:
                response = "I have logged your request. Let me know if you need specific step-by-step assistance."
            st.write(response)
            
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
