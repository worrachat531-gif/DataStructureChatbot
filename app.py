# app.py

import os
import google.generativeai as genai
import pandas as pd
import streamlit as st
# from prompt import PROMPT_WORKAW # ลบการนำเข้า PROMPT_WORKAW ออก
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from document_reader import get_kmutnb_summary

# กำหนดค่า API
genai.configure(api_key="AIzaSyBwjubsasfW5ZuDYwahEr_Be0dXgmBkuyo") # อย่าลืมใส่ API Key ของคุณที่นี่

# ปรับ generation_config ให้เหมาะสมกับการตอบคำถามเฉพาะด้าน
generation_config = {
    "temperature": 0.2,  # เพิ่มความยืดหยุ่นในการตอบเล็กน้อย
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,  # เพิ่มความยาวการตอบเพื่อรองรับคำอธิบายที่ละเอียดขึ้น
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

@st.cache_data
def load_document_content():
    """โหลดเนื้อหาเอกสารแค่ครั้งเดียว"""
    file_path = r"C:\kmutnb_chatbot\workaw\DataSetDataStructure.docx"
    try:
        document_content = get_kmutnb_summary(file_path) # get_kmutnb_summary ตอนนี้จะคืนค่าเนื้อหาเต็ม
        if document_content.startswith("Error:") or not document_content.strip():
            return None, document_content
        return document_content, None
    except Exception as e:
        return None, f"Error reading file: {e}"

# โหลดเอกสาร
document_content_for_context, error = load_document_content()
if error:
    st.error(error)
    st.stop()

# ปรับปรุง PROMPT ให้ตรงจุดมากขึ้น
ENHANCED_PROMPT = f"""
คุณคือ DataStructure Chatbot ผู้ช่วยตอบคำถามเฉพาะด้าน Data Structure สำหรับนักศึกษา
หน้าที่ของคุณ:
1. ตอบคำถามเกี่ยวกับ Data Structure **โดยอ้างอิงจากเอกสารที่กำหนดให้เท่านั้นและอย่างเคร่งครัด**
2. ให้คำอธิบายที่ชัดเจน เข้าใจง่าย เหมาะกับระดับนักศึกษา
3. ใช้ภาษาไทยในการตอบ มีความสุภาพ
4. หากคำถามไม่เกี่ยวข้องกับ Data Structure หรือไม่มีข้อมูลที่เกี่ยวข้องโดยตรงในเอกสาร ให้แจ้งว่า "ขออภัย ไม่มีข้อมูลในเอกสารที่เกี่ยวข้องกับคำถามนี้"

กฎการตอบคำถาม:
- ตอบโดยอ้างอิงจากข้อมูลในเอกสารเท่านั้น **ห้ามสร้างข้อมูลขึ้นมาเองเด็ดขาด**
- ไม่ต้องระบุแหล่งที่มาของข้อมูล (เช่น หน้าที่, ส่วนที่)
- หากไม่มีข้อมูลในเอกสาร ให้บอกว่า "ขออภัย ไม่มีข้อมูลในเอกสารที่เกี่ยวข้องกับคำถามนี้"
- ใช้ตัวอย่างและอธิบายเพิ่มเติมเมื่อจำเป็น หากมีอยู่ในเอกสาร

ข้อมูลจากเอกสาร Data Structure:
{document_content_for_context}
"""
# ลบการรวม PROMPT_WORKAW เพื่อหลีกเลี่ยงคำสั่งที่ขัดแย้ง

def create_model():
    """สร้าง model ด้วย enhanced prompt"""
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=SAFETY_SETTINGS,
        generation_config=generation_config,
        system_instruction=ENHANCED_PROMPT
    )

def is_datastructure_related(question):
    """ตรวจสอบว่าคำถามเกี่ยวข้องกับ Data Structure หรือไม่"""
    ds_keywords = [
        'array', 'linked list', 'stack', 'queue', 'tree', 'graph',
        'hash', 'sorting', 'searching', 'algorithm', 'data structure',
        'อาร์เรย์', 'ลิงค์ลิสต์', 'สแตก', 'คิว', 'ต้นไม้', 'กราฟ',
        'การเรียงลำดับ', 'การค้นหา', 'อัลกอริทึม', 'โครงสร้างข้อมูล',
        'โครงสร้างข้อมูลเชิงเส้น', 'โครงสร้างข้อมูลไม่เชิงเส้น',
        'infix', 'postfix', 'traversal', 'binary search tree', 'bst',
        'heap', 'priority queue', 'adjacency matrix', 'bfs', 'dfs',
        'time complexity', 'big o', 'operation', 'การดำเนินงาน',
        'เวลาการทำงาน', 'ประสิทธิภาพ', 'โครงสร้าง','ส่วนประกอบของโหนด',
        'Pointer Link','การสร้าง','การเพิ่ม','การแทรก','การลบ','โค้ดการสร้าง',
        'โค้ดการเพิ่ม','โค้ดการแทรก','โค้ดการลบ','Linear','Circular','Priority',
        'ยกตัวอย่าง','Push','Pop','Top','Overflow','Underflow','Stack Pointer',
        'Stack Element','peek','การแทนข้อมูลกราฟ','Depth First Search (DFS)','Breadth First Search (BFS)','Tree',
        'แผนภาพต้นไม้','Root Node','Leaf Node','Subtree','Binary Tree','Full Binary Tree','Complete Binary Tree',
        'Inorder Traversal','Preorder Traversal','Postorder Traversal','BST'
    ]
    # ตรวจสอบคำที่เกี่ยวข้องกับ Data Structure
    return any(keyword.lower() in question.lower() for keyword in ds_keywords) or \
           "datastructure" in question.lower().replace(" ", "") or \
           "โครงสร้างข้อมูล" in question.lower().replace(" ", "")

def clear_history():
    """ล้างประวัติการสนทนา"""
    st.session_state["messages"] = [
        {
            "role": "model",
            "content": "สวัสดีค่ะ! ฉันคือ DataStructure Chatbot 🤖\nพร้อมตอบคำถามเกี่ยวกับโครงสร้างข้อมูล (Data Structure) ให้นักศึกษาค่ะ\n\nสามารถสอบถามเรื่องใดก็ได้เกี่ยวกับ Data Structure เช่น Array, Linked List, Stack, Queue, Tree, Graph และอื่นๆ ค่ะ"
        }
    ]
    st.rerun()

def generate_response(prompt, model):
    """สร้างคำตอบจากโมเดล"""
    try:
        # ตรวจสอบคำถามพิเศษ
        if prompt.lower().startswith("add") or prompt.lower().endswith("add"):
            return "ขอบคุณสำหรับข้อเสนอแนะค่ะ 😊"

        # ตรวจสอบว่าเกี่ยวกับ Data Structure หรือไม่
        if not is_datastructure_related(prompt):
            return "ขออภัยค่ะ ฉันสามารถตอบคำถามเกี่ยวกับ Data Structure (โครงสร้างข้อมูล) เท่านั้นค่ะ กรุณาถามเรื่องที่เกี่ยวข้องกับ Array, Linked List, Stack, Queue, Tree, Graph หรือหัวข้ออื่นๆ ใน Data Structure ค่ะ"

        # สร้าง history สำหรับ chat
        history_for_chat = []
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                history_for_chat.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "model":
                history_for_chat.append({"role": "model", "parts": [{"text": msg["content"]}]})

        # เริ่ม chat session และส่งคำถาม
        chat_session = model.start_chat(history=history_for_chat)
        response = chat_session.send_message(prompt)

        return response.text

    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)} กรุณาลองใหม่อีกครั้งค่ะ"

# UI ส่วน Sidebar
with st.sidebar:
    st.header("🛠️ เมนู")
    if st.button("🗑️ ล้างประวัติการสนทนา", use_container_width=True):
        clear_history()

    st.divider()
    st.subheader("📚 หัวข้อที่สามารถถามได้")
    st.write("• Array (อาร์เรย์)")
    st.write("• Linked List (ลิงค์ลิสต์)")
    st.write("• Stack (สแตก)")
    st.write("• Queue (คิว)")
    st.write("• Tree (ต้นไม้)")
    st.write("• Graph (กราฟ)")

# หัวข้อหลัก
st.title("💬 DataStructure Chatbot")
st.caption("🤖 ผู้ช่วยตอบคำถามเกี่ยวกับโครงสร้างข้อมูล | KMUTNB Dataset")

# แสดงคำเตือนหากเอกสารไม่พร้อม
if not document_content_for_context:
    st.warning("⚠️ ระบบไม่สามารถโหลดเอกสารได้ หรือเอกสารว่างเปล่า กรุณาตรวจสอบไฟล์และเส้นทาง")
    st.stop() # หยุดการทำงานหากเนื้อหาเอกสารไม่พร้อม

# เริ่มต้น session state
if "messages" not in st.session_state:
    clear_history()

if "model" not in st.session_state:
    st.session_state["model"] = create_model()

# แสดงประวัติการสนทนา
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# รับ input จากผู้ใช้
if prompt := st.chat_input("💭 ถามเรื่อง Data Structure ได้เลยค่ะ เช่น 'อธิบาย Stack หน่อย' หรือ 'Array กับ Linked List ต่างกันอย่างไร'..."):
    # แสดงข้อความของผู้ใช้
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # สร้างและแสดงคำตอบ
    with st.chat_message("model"):
        with st.spinner("กำลังคิด... 🤔"):
            response = generate_response(prompt, st.session_state["model"])
            st.write(response)
            st.session_state["messages"].append({"role": "model", "content": response})