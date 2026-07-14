import streamlit as st
from langfuse.langchain import CallbackHandler
from review_lab.agents.graph import build_review_graph

# 1. Page Configurations
st.set_page_config(
    page_title="Review Lab",
    page_icon="🤖",
    layout="wide"
)

# Apply central theme (Blue for Review Lab)
st.markdown("<style>:root {--accent: #3B82F6;}</style>", unsafe_allow_html=True)

@st.cache_resource
def get_graph():
    return build_review_graph()

review_graph = get_graph()

# 2. Header Block
st.title("🤖 Review Lab")
st.markdown("### Multi-Agent Code Review Pipeline (LangGraph)")
st.info("Paste your Python code below. The Supervisor will route it to Security, Style, and Performance agents for a comprehensive review.")

# 3. Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Observability")
    st.markdown("---")
    st.markdown("[🔍 Open Langfuse Dashboard](http://localhost:3000)")
    st.caption("All agent routing, tool calls, and latency metrics are traced live in Langfuse.")
    
    st.markdown("### Agent Roster")
    st.markdown("- 👮 **Security Agent** (Bandit)")
    st.markdown("- 💅 **Style Agent** (Pylint)")
    st.markdown("- ⚡ **Performance Agent** (AST)")

# 4. Main Panel
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Input: Python Code Snippet")
    
    default_code = """import os

def process_user_data(user_input):
    # Intentional bad style, security, and performance
    secret="12345"
    os.system("echo " + user_input)
    
    res = []
    for i in range(100):
        for j in range(100):
            res.append(i * j)
            
    return res
"""
    code_input = st.text_area("Code to Review", value=default_code, height=350)
    review_btn = st.button("Run Multi-Agent Review", use_container_width=True)

with col2:
    st.markdown("#### Output: Lead Reviewer Summary")
    
    if review_btn and code_input:
        with st.spinner("Agents are reviewing the code... (Check Langfuse for trace)"):
            try:
                # Initialize Langfuse tracing for the UI interaction
                langfuse_handler = CallbackHandler()
                
                initial_state = {
                    "messages": [],
                    "code_snippet": code_input,
                    "next_agent": "supervisor",
                    "final_review": ""
                }
                
                # Invoke the LangGraph directly
                result = review_graph.invoke(
                    initial_state,
                    config={"callbacks": [langfuse_handler]}
                )
                
                final_review = result.get("final_review", "No review generated.")
                
                st.success("✅ Review Complete!")
                with st.expander("📝 View Full Markdown Review", expanded=True):
                    st.markdown(final_review)
                    
            except Exception as e:
                st.error("❌ The review pipeline failed.")
                st.code(str(e), language="python")
    elif not review_btn:
        st.caption("Awaiting your code... Press the button to unleash the agents.")