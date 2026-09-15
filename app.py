import os
import streamlit as st
from groq import Groq
from PIL import Image
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io

# Streamlit UI কনফিগারেশন
st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")

# Groq API Key সেটআপ
GROQ_API_KEY = st.secrets"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" 
client = Groq(api_key=GROQ_API_KEY)

# সেশন স্টেট ইনিশিয়ালাইজেশন
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Chat 1"
    st.session_state.chats["Chat 1"] = []

# --- সাইডবার (Sidebar) ---
with st.sidebar:
    st.title("🤖 AI Agent Menu (Groq)")
    
    # New Chat বাটন
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_id = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
        st.rerun()

    st.markdown("---")
    
    # ১. পারসোনা বা রোল সিলেকশন
    system_role = st.selectbox(
        "🎭 Agent Persona:",
        ["General Assistant", "Expert Programmer", "English Tutor", "Creative Writer"]
    )
    
    st.markdown("---")
    
    # ২. ভয়েস ইনপুট সেকশন
    st.subheader("🎙️ Voice Input")
    audio_bytes = audio_recorder(text="কথা বলতে ট্যাপ করুন", icon_size="2x")
    
    st.markdown("---")
    
    # ৩. টেক্সট ফাইল আপলোডার
    st.subheader("📎 Attach Files")
    uploaded_file = st.file_uploader("টেক্সট ফাইল সিলেক্ট করুন", type=["txt"])
    
    file_text_content = ""
    if uploaded_file is not None:
        file_text_content = uploaded_file.read().decode("utf-8")
        st.success("Text File Loaded!")

    st.markdown("---")
    st.subheader("📜 Chat History")
    
    chat_list = list(st.session_state.chats.keys())
    selected_chat = st.radio(
        "Select Chat:", 
        chat_list, 
        index=chat_list.index(st.session_state.current_chat_id)
    )
    st.session_state.current_chat_id = selected_chat

# --- মূল চ্যাট উইন্ডো (Main Chat Area) ---
st.title(f"💬 {st.session_state.current_chat_id}")

current_messages = st.session_state.chats[st.session_state.current_chat_id]

# মেমোরি থেকে আগের মেসেজ ডিসপ্লে
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message and message["audio"] is not None:
            st.audio(message["audio"], format="audio/mp3")

# ইনপুট হ্যান্ডলিং
prompt = st.chat_input("কী জানতে চান লিখুন...")

if audio_bytes and prompt is None:
    prompt = "রেকর্ড করা ভয়েস বার্তাটি বিশ্লেষণ করে উত্তর দাও।"

if prompt:
    final_prompt = prompt
    if file_text_content:
        final_prompt = f"File Context:\n{file_text_content}\n\nUser Question: {prompt}"

    # ১. ইউজার মেসেজ দেখানো ও সেভ করা
    with st.chat_message("user"):
        st.markdown(prompt)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
    user_msg_data = {"role": "user", "content": prompt}
    current_messages.append(user_msg_data)

    # ২. Groq API রেসপন্স তৈরি (Llama 3.3 70B Model)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # চ্যাট হিস্ট্রি Groq মেসেজ ফরম্যাটে রূপান্তর
            messages_payload = [
                {"role": "system", "content": f"You are acting as a {system_role}."}
            ]
            for msg in current_messages:
                messages_payload.append({"role": msg["role"], "content": msg["content"]})

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages_payload,
                stream=True,
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                
            message_placeholder.markdown(full_response)
            
            # ভয়েস রেসপন্স প্রসেসিং
            if full_response.strip():
                tts = gTTS(text=full_response, lang='bn')
                sound_file = io.BytesIO()
                tts.write_to_fp(sound_file)
                st.audio(sound_file, format="audio/mp3")
                current_messages.append({"role": "assistant", "content": full_response, "audio": sound_file})

        except Exception as e:
            full_response = f"Error: {str(e)}"
            message_placeholder.markdown(full_response)
            current_messages.append({"role": "assistant", "content": full_response})
