import streamlit as st
import os
import pandas as pd
from PIL import Image
from src.graph import create_agent_graph
import src.config as config

# Page configurations
st.set_page_config(
    page_title="Autonomous Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using HTML inject
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    /* Font styles overrides */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #0f121d;
        color: #f3f4f6;
    }
    
    /* Title container with gradient glow */
    .title-banner {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
    }
    .title-banner h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 3rem !important;
        margin: 0;
        letter-spacing: -1px;
    }
    .title-banner p {
        font-size: 1.15rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Config indicator blocks */
    .key-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .key-active {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .key-inactive {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .key-optional {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    /* Glassmorphic cards */
    .dashboard-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom tabs headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.02);
        padding: 6px;
        border-radius: 12px;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        background-color: transparent;
        border: none;
        color: #9ca3af;
        font-weight: 600;
        padding: 0 20px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important;
        background-color: rgba(59, 130, 246, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# Application Title Header
st.markdown("""
<div class="title-banner">
    <h1>Autonomous Data Analyst</h1>
    <p>Advanced Multi-Agent Insights Machine Powered by LangGraph & LangChain</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Settings & Keys Status
st.sidebar.title("🛠️ System Engine Status")

# Helper to verify key presence
def get_status_badge(key_val, is_required=True):
    if key_val and "your_" not in key_val.lower():
        return '<span class="key-badge key-active">● Active</span>'
    elif is_required:
        return '<span class="key-badge key-inactive">○ Missing</span>'
    else:
        return '<span class="key-badge key-optional">⚡ Fallback Active</span>'

st.sidebar.subheader("API Keys Configuration")
st.sidebar.markdown(f"**Gemini LLM Key**: {get_status_badge(config.GEMINI_API_KEY)}", unsafe_allow_html=True)
st.sidebar.markdown(f"**OpenAI LLM Key**: {get_status_badge(config.OPENAI_API_KEY, is_required=False)}", unsafe_allow_html=True)
st.sidebar.markdown(f"**Tavily Search**: {get_status_badge(config.TAVILY_API_KEY)}", unsafe_allow_html=True)
st.sidebar.markdown(f"**Weather API**: {get_status_badge(config.OPENWEATHER_API_KEY, is_required=False)}", unsafe_allow_html=True)
st.sidebar.markdown(f"**Kaggle Database**: {get_status_badge(config.KAGGLE_USERNAME, is_required=False)}", unsafe_allow_html=True)

# Date context setter
current_date_input = st.sidebar.date_input(
    "Set Execution Current Date",
    value=pd.to_datetime("2026-06-21")
).strftime("%B %d, %Y")

st.sidebar.info(
    "💡 Tip: If you don't have Kaggle or Weather API keys, the agent will dynamically fall back to "
    "general web searches, wttr.in, and yfinance tools without crashing."
)

# User Query input
user_query = st.text_area(
    "Ask the Data Analyst Agent to research, analyze, and plot data:",
    placeholder="e.g. Compare the performance of Nvidia (NVDA) and Apple (AAPL) stock prices for the last month. Identify any correlation, plot their trajectories, and suggest which represents a better risk-adjusted return today.",
    value="",
    height=80
)

# State initialization
if "run_state" not in st.session_state:
    st.session_state["run_state"] = None

submit_btn = st.button("🚀 Analyze & Generate Insights", type="primary")

if submit_btn and user_query.strip():
    with st.spinner("Initializing multi-agent graph..."):
        # Clear output folder prior to run to avoid mixing past reports/plots
        if os.path.exists(config.OUTPUT_DIR):
            for file in os.listdir(config.OUTPUT_DIR):
                try:
                    os.remove(os.path.join(config.OUTPUT_DIR, file))
                except Exception:
                    pass
                    
        # Define default state
        initial_state = {
            "query": user_query,
            "current_date": current_date_input,
            "plan": [],
            "collected_data": {},
            "execution_logs": [],
            "charts": [],
            "findings": "",
            "final_report": "",
            "errors": []
        }
        
        # Instantiate Graph
        graph = create_agent_graph()
        
        # Container to stream agent operations logs
        status_box = st.status("🧠 Agent State Machine Executing...", expanded=True)
        
        # We hook into stdout print statements or simply run steps.
        # Since invoke() runs synchronously, we'll run it and display outputs.
        try:
            with status_box:
                st.write("📋 **Planner** is examining query and establishing a plan...")
                # Note: A real streaming representation can be achieved using graph.stream()
                # Let's perform state extraction
                final_state = graph.invoke(initial_state)
                st.write("🎉 Agent finished all nodes successfully!")
            
            st.session_state["run_state"] = final_state
            st.success("Analysis Completed successfully!")
        except Exception as e:
            st.error(f"Execution Error: {e}")
            st.session_state["run_state"] = None

# If we have a completed execution state, render tabs
if st.session_state["run_state"]:
    state = st.session_state["run_state"]
    
    # Visual Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Senior Analyst Report", 
        "📈 Visualizations", 
        "📂 Collected Datasets", 
        "🧠 Agent Execution Logs"
    ])
    
    with tab1:
        st.markdown(state.get("final_report", "No report compiled."))
        
    with tab2:
        st.subheader("Visual Charts")
        charts = state.get("charts", [])
        if charts:
            cols = st.columns(len(charts))
            for idx, chart_name in enumerate(charts):
                chart_path = os.path.join(config.OUTPUT_DIR, chart_name)
                if os.path.exists(chart_path):
                    with cols[idx]:
                        image = Image.open(chart_path)
                        st.image(image, caption=chart_name, use_container_width=True)
        else:
            st.info("No charts were generated during this run.")
            
    with tab3:
        st.subheader("Datasets Generated")
        # List CSV files in outputs folder
        if os.path.exists(config.OUTPUT_DIR):
            csv_files = [f for f in os.listdir(config.OUTPUT_DIR) if f.endswith(".csv")]
            if csv_files:
                for csv_file in csv_files:
                    st.write(f"📁 **{csv_file}**")
                    df_preview = pd.read_csv(os.path.join(config.OUTPUT_DIR, csv_file))
                    st.dataframe(df_preview.head(5))
            else:
                st.info("No CSV data files are currently downloaded.")
        else:
            st.info("No output datasets are available.")
            
    with tab4:
        st.subheader("Detailed Execution Steps")
        
        # Display Planner steps
        if state.get("plan"):
            st.markdown("### 📋 Formulated Roadmap Plan")
            for idx, step in enumerate(state["plan"]):
                st.markdown(f"{idx+1}. {step}")
                
        # Display Collector Logs
        if state.get("collected_data"):
            st.markdown("### 📥 API Collector Node Details")
            for key, val in state["collected_data"].items():
                with st.expander(f"Data source: {key}"):
                    st.write(f"**Arguments:** {val.get('args')}")
                    st.text(val.get("result", ""))
                    
        # Display Analyst sandbox iterations
        if state.get("execution_logs"):
            st.markdown("### 💻 Python Execution Logs (Data Sandbox)")
            for entry in state["execution_logs"]:
                status_icon = "✅ Success" if entry["success"] else "❌ Failed"
                with st.expander(f"Sandbox Run {entry['attempt']} - {status_icon}"):
                    st.markdown("**Code Executed:**")
                    st.code(entry["code"], language="python")
                    st.markdown("**Stdout Output:**")
                    st.text(entry["stdout"])
                    if entry["stderr"]:
                        st.markdown("**Stderr/Traceback:**")
                        st.text(entry["stderr"])
                        
        if state.get("errors"):
            st.markdown("### ⚠️ Warnings / Errors")
            for err in state["errors"]:
                st.warning(err)
