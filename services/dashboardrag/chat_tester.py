"""
Streamlit Chat Tester for Aeropon Hybrid Chatbot
Simple local playground to send messages to FastAPI /chat endpoint
"""

import os
from typing import Any, Dict, List

import requests
import streamlit as st


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
FASTAPI_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{FASTAPI_BASE_URL}/health"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def init_session_state() -> None:
    """Ensure required keys exist in session_state."""
    if "messages" not in st.session_state:
        # Each message: {"role": "user"|"assistant", "content": str, "meta": dict | None}
        st.session_state.messages: List[Dict[str, Any]] = []


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

# Sidebar controls
st.sidebar.title("Pengaturan")
user_id = st.sidebar.text_input("User ID", value="local-tester")
language = st.sidebar.selectbox("Bahasa", options=["id", "en"], index=0)
include_images = st.sidebar.checkbox("Include images (dari RAG)", value=False)

if st.sidebar.button("Cek Health FastAPI"):
    health = call_health_api()
    if "error" in health:
        st.sidebar.error(f"Gagal memanggil /health: {health['error']}")
    else:
        st.sidebar.success("FastAPI sehat")
        st.sidebar.json(health)

if st.sidebar.button("Clear chat"):
    st.session_state.messages = []

st.title("Aeropon Chatbot - Streamlit Tester")
st.write(
    "Halaman ini membantu kamu menguji chatbot Aeropon secara lokal melalui "
    "`POST /chat` di FastAPI."
)

# Render existing conversation
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("meta"))

# Chat input
prompt = st.chat_input("Ketik pesan untuk chatbot...")
if prompt:
    # Append user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "meta": None}
    )
    render_message("user", prompt)

    # Call backend
    try:
        with st.spinner("Menghubungi FastAPI /chat..."):
            result = call_chat_api(
                message=prompt,
                user_id=user_id,
                language=language,
                include_images=include_images,
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

    except requests.RequestException as exc:
        error_msg = (
            "Tidak bisa terhubung ke FastAPI di "
            f"`{CHAT_ENDPOINT}`.\n\nDetail: {exc}"
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": error_msg, "meta": None}
        )
        render_message("assistant", error_msg)

