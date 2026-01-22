import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv
import tempfile
import os
import uuid

# ================= CONFIG =================
st.set_page_config(page_title=" Voice chatbot", layout="wide")
load_dotenv()

@st.cache_resource
def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

client = get_client()

# ================= SESSION STATE =================
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# ================= SIDEBAR =================
with st.sidebar:
    st.title("💬 Chats")

    if st.button("➕ New Chat"):
        st.session_state.current_chat = None

    for cid, msgs in st.session_state.conversations.items():
        if not msgs:
            continue
        if st.button(msgs[0]["content"][:30], key=cid):
            st.session_state.current_chat = cid

    if st.session_state.current_chat and st.button("🗑 Delete Chat"):
        del st.session_state.conversations[st.session_state.current_chat]
        st.session_state.current_chat = None

# ================= CHAT STATE =================
def get_messages():
    if st.session_state.current_chat is None:
        cid = str(uuid.uuid4())
        st.session_state.conversations[cid] = []
        st.session_state.current_chat = cid
    return st.session_state.conversations[st.session_state.current_chat]

messages = get_messages()

st.title("  Voice chatbot")

# ================= CHAT CONTAINER (KEY FIX) =================
chat_container = st.container()

with chat_container:
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ================= INPUT BAR (OUTSIDE CONTAINER) =================
col_text, col_voice = st.columns([9, 1])

with col_text:
    prompt = st.chat_input("Message Chatbot...")

with col_voice:
    voice_clicked = st.button("🎤")

# ================= RESPONSE =================
def get_response():
    return client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.6,
        max_tokens=120
    ).choices[0].message.content

# ================= TEXT INPUT =================
if prompt:
    messages.append({"role": "user", "content": prompt})
    messages.append({"role": "assistant", "content": get_response()})

# ================= VOICE INPUT =================
if voice_clicked:
    audio = sd.rec(int(2.5 * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(tmp.name, 16000, audio)

    r = sr.Recognizer()
    with sr.AudioFile(tmp.name) as source:
        try:
            text = r.recognize_google(r.record(source))
            messages.append({"role": "user", "content": text})
            messages.append({"role": "assistant", "content": get_response()})
        except:
            pass
