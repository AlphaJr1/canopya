"""
Streamlit Chat Tester for Aeropon Hybrid Chatbot
Simple local playground to send messages to FastAPI /chat endpoint
"""

import os
import random
from typing import Any, Dict, List

import requests
import streamlit as st


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
FASTAPI_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{FASTAPI_BASE_URL}/health"

# Pool pertanyaan contoh untuk shortcut
SAMPLE_QUESTIONS = [
    "Apa itu sistem aeroponik?",
    "Bagaimana cara kerja aeroponik?",
    "Apa keuntungan menggunakan aeroponik?",
    "Berapa pH ideal untuk tanaman aeroponik?",
    "Bagaimana cara mengatur pH air?",
    "Apa fungsi sensor pH?",
    "Bagaimana cara kalibrasi sensor?",
    "Apa itu nutrisi hidroponik?",
    "Berapa EC yang ideal untuk tanaman?",
    "Bagaimana cara mengatasi pH terlalu tinggi?",
    "Bagaimana cara mengatasi pH terlalu rendah?",
    "Apa perbedaan aeroponik dan hidroponik?",
    "Tanaman apa yang cocok untuk aeroponik?",
    "Berapa suhu ideal untuk aeroponik?",
    "Bagaimana cara merawat sistem aeroponik?",
    "Apa itu PPM dalam aeroponik?",
    "Bagaimana cara mengukur nutrisi?",
    "Apa yang harus dilakukan jika tanaman layu?",
    "Berapa lama waktu penyemprotan ideal?",
    "Apa itu interval penyemprotan?",
    "Bagaimana cara membersihkan sistem?",
    "Apa fungsi pompa dalam aeroponik?",
    "Bagaimana cara memilih nozzle yang tepat?",
    "Apa itu root zone?",
    "Bagaimana cara mencegah algae?",
    "Apa penyebab akar busuk?",
    "Bagaimana cara mengatasi clogging nozzle?",
    "Berapa kelembaban ideal untuk aeroponik?",
    "Apa itu DWC dan perbedaannya dengan aeroponik?",
    "Bagaimana cara monitoring sistem otomatis?",
]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def init_session_state() -> None:
    """Ensure required keys exist in session_state."""
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, Any]] = []
    
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def refresh_random_questions() -> None:
    """Refresh 4 random questions."""
    st.session_state.random_questions = random.sample(SAMPLE_QUESTIONS, min(4, len(SAMPLE_QUESTIONS)))


def get_random_questions() -> List[str]:
    """Get 4 random questions, initialize if needed."""
    if "random_questions" not in st.session_state:
        refresh_random_questions()
    return st.session_state.random_questions


def call_chat_api(
    message: str,
    user_id: str,
    language: str = "id",
    include_images: bool = False,
) -> Dict[str, Any]:
    """
    Call FastAPI /chat endpoint.

    Payload shape follows ChatRequest in services/fastapi/main.py:
    - message: str
    - user_id: Optional[str]
    - language: str
    - include_images: bool
    - session_id: Optional[str]
    - conversation_history: Optional[List[Dict[str, str]]]
    """
    # Build conversation history from previous messages
    history: List[Dict[str, str]] = []
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "message": msg["content"]})

    payload: Dict[str, Any] = {
        "message": message,
        "user_id": user_id or None,
        "language": language,
        "include_images": include_images,
        "session_id": user_id or None,
        "conversation_history": history if history else None,
    }

    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_health_api() -> Dict[str, Any]:
    """Call FastAPI /health endpoint, return empty dict on failure."""
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def render_message(role: str, content: str, meta: Dict[str, Any] | None = None) -> None:
    """Render a single chat message with optional debug meta in an expander."""
    with st.chat_message(role):
        st.markdown(content)

        if meta:
            with st.expander("Lihat detail teknis"):
                # Only show a few useful fields if present
                intent = meta.get("intent")
                confidence = meta.get("confidence")
                has_sensor = meta.get("has_sensor_data")
                sensor_data = meta.get("sensor_data")
                rag_conf = meta.get("rag_confidence")
                sources = meta.get("sources")
                rag_dashboard_url = meta.get("rag_dashboard_url")

                if intent is not None:
                    st.write(f"**Intent**: {intent}")
                if confidence is not None:
                    st.write(f"**Confidence**: {confidence:.2f}")
                if has_sensor is not None:
                    st.write(f"**Has sensor data**: {has_sensor}")
                if sensor_data:
                    st.write("**Sensor data**:")
                    st.json(sensor_data)
                if rag_conf is not None:
                    st.write(f"**RAG confidence**: {rag_conf:.2f}")
                if sources:
                    st.write("**Sources**:")
                    st.write(", ".join(sources))
                if rag_dashboard_url:
                    st.write("**RAG dashboard URL**:")
                    st.write(rag_dashboard_url)


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Aeropon Chatbot Tester",
    page_icon="💬",
    layout="centered",
)

init_session_state()

st.title("Canopya Chatbot Tester")
st.write(
    "Halaman ini digunakan untuk menguji kemampuan chatbot Canopya dalam menjawab "
    "pertanyaan seputar sistem aeroponik. Anda dapat mengirim pesan dan melihat "
    "respons chatbot secara real-time untuk memastikan kualitas jawaban."
)

# Custom CSS untuk tombol merah
st.markdown("""
<style>
button[data-testid="baseButton-secondary"][key="clear_chat"] {
    background-color: #ff6b6b !important;
    color: white !important;
    border: 1px solid #ff5252 !important;
}
button[data-testid="baseButton-secondary"][key="clear_chat"]:hover {
    background-color: #ff5252 !important;
    color: white !important;
    border: 1px solid #ff3838 !important;
}
</style>
""", unsafe_allow_html=True)

# Tombol clear di bawah subtitle
if st.button("🗑️ Hapus Semua Percakapan", key="clear_chat", type="secondary"):
    st.session_state.messages = []
    st.rerun()

st.markdown("---")

# Render existing conversation
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("meta"))

# Shortcut pertanyaan (di atas input field)
st.markdown("### 💡 Coba pertanyaan ini:")
random_questions = get_random_questions()

cols = st.columns(4)
for idx, question in enumerate(random_questions):
    with cols[idx]:
        if st.button(question, key=f"q_{idx}", use_container_width=True):
            st.session_state.pending_question = question
            refresh_random_questions()

# Chat input
prompt = st.chat_input("Ketik pesan untuk chatbot...")

# Cek jika ada pending question dari shortcut button
if st.session_state.pending_question:
    prompt = st.session_state.pending_question
    st.session_state.pending_question = None

# Process message (dari shortcut atau chat input)
if prompt:
    # Append user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "meta": None}
    )
    render_message("user", prompt)
    
    # Call backend dengan default values
    try:
        with st.spinner("Menghubungi FastAPI /chat..."):
            result = call_chat_api(
                message=prompt,
                user_id="local-tester",
                language="id",
                include_images=False,
            )

        answer = result.get("answer", "")

        # Build meta from response
        meta: Dict[str, Any] = {
            "intent": result.get("intent"),
            "confidence": result.get("confidence"),
            "has_sensor_data": result.get("has_sensor_data"),
            "sensor_data": result.get("sensor_data"),
            "rag_confidence": result.get("rag_confidence"),
            "sources": result.get("sources"),
            "rag_dashboard_url": result.get("rag_dashboard_url"),
        }

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "meta": meta}
        )
        render_message("assistant", answer, meta)
        refresh_random_questions()
        st.rerun()

    except requests.RequestException as exc:
        error_msg = (
            "Tidak bisa terhubung ke FastAPI di "
            f"`{CHAT_ENDPOINT}`.\n\nDetail: {exc}"
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": error_msg, "meta": None}
        )
        render_message("assistant", error_msg)
