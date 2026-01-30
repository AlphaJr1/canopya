"""
RAG Dashboard - Dashboard sederhana untuk visualisasi RAG process
Menampilkan query user dan top-k retrieved documents dengan scores
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.rag_storage import get_rag_process

# Page config
st.set_page_config(
    page_title="RAG Process Viewer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS - Dark mode dengan kontras optimal untuk readability
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background: #0e1117;
    }
    
    /* Headings - Pure white untuk kontras maksimal */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Body text - Light gray untuk readability */
    p, span, div {
        color: #e0e0e0;
    }
    
    /* Metric cards - Dark blue-gray dengan border subtle */
    .metric-card {
        background: #1a1f2e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        margin-bottom: 15px;
    }
    
    /* Document info cards */
    .doc-card {
        background: #1a1f2e;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 10px;
    }
    
    /* Score colors dengan kontras baik */
    .score-high {
        color: #66bb6a;
        font-weight: bold;
    }
    
    .score-medium {
        color: #ffa726;
        font-weight: bold;
    }
    
    .score-low {
        color: #ef5350;
        font-weight: bold;
    }
    
    /* Streamlit code blocks - Dark background dengan light text */
    .stCodeBlock {
        background-color: #1a1f2e !important;
    }
    
    code {
        background-color: #1a1f2e !important;
        color: #e0e0e0 !important;
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    pre {
        background-color: #1a1f2e !important;
        border: 1px solid #2d3748 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    
    pre code {
        color: #e8eaed !important;
        background-color: transparent !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1a1f2e !important;
        border: 1px solid #2d3748 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #242b3d !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0e1117 !important;
        border: 1px solid #2d3748 !important;
        border-top: none !important;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #9ca3af !important;
    }
    
    /* Text area (jika masih ada) */
    .stTextArea textarea {
        background: #1a1f2e !important;
        color: #e8eaed !important;
        border: 1px solid #2d3748 !important;
    }
    
    /* Scrollbar styling untuk code blocks */
    pre::-webkit-scrollbar {
        height: 8px;
        width: 8px;
    }
    
    pre::-webkit-scrollbar-track {
        background: #0e1117;
        border-radius: 4px;
    }
    
    pre::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 4px;
    }
    
    pre::-webkit-scrollbar-thumb:hover {
        background: #5a6578;
    }
</style>
""", unsafe_allow_html=True)

# Get query_id from URL parameter
try:
    # Try new API first (Streamlit >= 1.30)
    query_params = st.query_params
    query_id = query_params.get("query_id", None)
except AttributeError:
    # Fallback to old API (Streamlit < 1.30)
    query_params = st.experimental_get_query_params()
    query_id = query_params.get("query_id", [None])[0]

if not query_id:
    st.title("RAG Process Viewer")
    st.info("Tidak ada query_id yang diberikan. Akses dashboard ini melalui link dari chatbot.")
    st.stop()

# Load RAG process data
data = get_rag_process(query_id)

if not data:
    st.title("RAG Process Viewer")
    st.error(f"Query ID '{query_id}' tidak ditemukan atau sudah expired.")
    st.stop()

# Display RAG process
st.title("RAG Process Viewer")

# Query info
st.markdown("### User Query")
st.markdown(f"""
<div class="metric-card">
    <p style="font-size: 1.1em; margin: 0;"><strong>{data['query']}</strong></p>
    <p style="color: #888; font-size: 0.9em; margin-top: 10px;">
        Timestamp: {data['timestamp'][:19]} | Intent: {data['intent']}
    </p>
</div>
""", unsafe_allow_html=True)

# Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Retrieved Documents", data['num_docs'])

with col2:
    avg_score = data['avg_score']
    st.metric("Average Similarity", f"{avg_score:.4f}")

with col3:
    # Determine quality based on avg score
    if avg_score >= 0.7:
        quality = "High"
        quality_color = "#4CAF50"
    elif avg_score >= 0.5:
        quality = "Medium"
        quality_color = "#FFC107"
    else:
        quality = "Low"
        quality_color = "#F44336"
    
    st.markdown(f"""
    <div style="background: #1e2936; padding: 15px; border-radius: 5px; text-align: center;">
        <p style="color: #888; font-size: 0.875rem; margin: 0;">Retrieval Quality</p>
        <p style="color: {quality_color}; font-size: 1.5rem; font-weight: bold; margin: 5px 0 0 0;">
            {quality}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Retrieved documents
st.markdown("### Retrieved Documents (Top-K)")

documents = data.get('documents', [])

for i, doc in enumerate(documents, 1):
    score = doc.get('score', 0)
    
    # Determine score class
    if score >= 0.7:
        score_class = "score-high"
        border_color = "#4CAF50"
    elif score >= 0.5:
        score_class = "score-medium"
        border_color = "#FFC107"
    else:
        score_class = "score-low"
        border_color = "#F44336"
    
    # Document header
    col_a, col_b = st.columns([3, 1])
    
    with col_a:
        st.markdown(f"**Document {i}** - {doc.get('source', 'Unknown')}")
    
    with col_b:
        st.markdown(f"<span class='{score_class}'>Score: {score:.4f}</span>", unsafe_allow_html=True)
    
    # Document content
    st.markdown(f"""
    <div class="doc-card" style="border-left-color: {border_color};">
        <p style="margin: 0;"><strong>Source:</strong> {doc.get('source', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>Page:</strong> {doc.get('page', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>Rank:</strong> {i}/{len(documents)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Document text - menggunakan st.code agar terlihat jelas di dark theme
    with st.expander("📄 Lihat Isi Dokumen (Chunking)", expanded=True):
        st.code(
            doc.get('text', 'N/A'),
            language=None,
            line_numbers=False
        )
    
    st.markdown("<br>", unsafe_allow_html=True)

# Bot response
st.markdown("---")
st.markdown("### Bot Response")
st.markdown(f"""
<div class="metric-card">
    <p style="white-space: pre-wrap; margin: 0;">{data['response']}</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9em;'>"
    "RAG Process Viewer | Aeropon"
    "</div>",
    unsafe_allow_html=True
)
