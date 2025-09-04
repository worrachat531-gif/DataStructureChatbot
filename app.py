import os
import google.generativeai as genai
import pandas as pd
import streamlit as st
from prompt import PROMPT_WORKAW
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from document_reader import get_kmutnb_summary

genai.configure(api_key="AIzaSyBdJWqbQ1VjYXGAccazO6IrzLW_GS0F1kM")
generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    # "max_output_tokens": 8192,
    "max_output_tokens": 512,  # Reduced to avoid rate limits
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=SAFETY_SETTINGS,
    generation_config=generation_config,
    system_instruction=PROMPT_WORKAW
    ,)


def clear_history():
    
    st.session_state["messages"] = [
        {"role": "model", "content": "DataStructure Chatbot สวัสดีค่ะ นักศึกษา สอบถามข้อมูลเกี่ยวกับ DataStructure เรื่องใดคะ"}
    ]
    st.rerun()


with st.sidebar:
    if st.button("Clear History"):
        clear_history()

st.title("💬 DataStructure Chatbot สวัสดีค่ะ")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "model",
            "content": "DataStructure Chatbot สวัสดีค่ะ นักศึกษา สอบถามข้อมูลเกี่ยวกับ DataStructure เรื่องใดคะ",
        }
    ]

# Read the KMUTNB dataset
file_path = f"C:\kmutnb_chatbot\workaw\DataSetDataStructure.docx"
try:
    file_content = get_kmutnb_summary(file_path)
    if file_content.startswith("Error:"):
        st.error(file_content)
        st.stop()
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()



for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    def generate_response():
        history = [
            {"role": msg["role"], "parts": [{"text": msg["content"]}]}
            for msg in st.session_state["messages"]
        ]
        if prompt.lower().startswith("add") or prompt.lower().endswith("add"):
            st.chat_message("model").write("ขอบคุณสำหรับคำแนะนำค่ะ")
            st.session_state["messages"].append({"role": "model", "content": "ขอบคุณสำหรับคำแนะนำค่ะ"})
        else:
            history.insert(1, {"role": "user", "parts": [{"text": file_content}]})
        
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            st.session_state["messages"].append({"role": "model", "content": response.text})
            st.chat_message("model").write(response.text)

    generate_response()






