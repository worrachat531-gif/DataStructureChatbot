import os
import google.generativeai as genai
import pandas as pd
import streamlit as st
# from prompt import PROMPT_WORKAW # ลบการนำเข้า PROMPT_WORKAW ออก
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from document_reader import get_kmutnb_summary

# กำหนดค่า API
genai.configure(api_key="AIzaSyC6qjppnnf9g1G8rCNOD4hh6tsHplGYiK0") # อย่าลืมใส่ API Key ของคุณที่นี่

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
    # *** เปลี่ยนบรรทัดนี้ ***
    # ให้เป็นชื่อไฟล์ตรงๆ หาก DataSetDataStructure.docx อยู่ใน Root ของโปรเจกต์
    file_path = "DataSetDataStructure.docx"

    # หากคุณสร้างโฟลเดอร์ย่อย เช่น 'data' แล้วเอาไฟล์ไปไว้ในนั้น ให้เป็นแบบนี้:
    # file_path = "data/DataSetDataStructure.docx"

    try:
        document_content = get_kmutnb_summary(file_path)
        if document_content.startswith("Error:") or not document_content.strip():
            return None, document_content
        return document_content, None
    except Exception as e:
        # อาจจะเพิ่ม print(f"Current working directory: {os.getcwd()}")
        # เพื่อช่วย Debug ตอนทดสอบบนเครื่อง Local หาก Path ยังมีปัญหา
        return None, f"Error reading file at {file_path}: {e}" # เพิ่ม {file_path} เพื่อให้เห็น Path ที่มีปัญหา

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
        model_name="gemini-2.5-flash", # เปลี่ยนเป็น gemini-2.5-flash ที่นี่
        safety_settings=SAFETY_SETTINGS,
        generation_config=generation_config,
        system_instruction=ENHANCED_PROMPT
    )

def is_datastructure_related(question):
    """ตรวจสอบว่าคำถามเกี่ยวข้องกับ Data Structure หรือไม่"""
    ds_keywords = [
       # General Data Structure Concepts (แนวคิดโครงสร้างข้อมูลทั่วไป)
    'data structure', 'algorithm', 'abstract data type', 'ADT', 'data types',
    'time complexity', 'space complexity', 'Big O notation', 'asymptotic notation',
    'operation', 'insertion', 'deletion', 'searching', 'traversal',
    'linear data structure', 'non-linear data structure', 'recursive', 'iterative',
    'pointer', 'reference', 'node', 'element', 'memory allocation', 'contiguous memory',
    'dynamic memory', 'worst-case', 'best-case', 'average-case', 'algorithm analysis',
    'โครงสร้างข้อมูล', 'อัลกอริทึม', 'ชนิดข้อมูลนามธรรม', 'ชนิดข้อมูล',
    'ความซับซ้อนเชิงเวลา', 'ความซับซ้อนเชิงพื้นที่', 'สัญกรณ์บิ๊กโอ', 'สัญกรณ์เชิงเส้นกำกับ',
    'การดำเนินการ', 'การเพิ่ม', 'การลบ', 'การค้นหา', 'การท่อง',
    'โครงสร้างข้อมูลเชิงเส้น', 'โครงสร้างข้อมูลไม่เชิงเส้น', 'การเรียกซ้ำ', 'การทำซ้ำ',
    'พอยน์เตอร์', 'การอ้างอิง', 'โหนด', 'ส่วนประกอบ', 'การจัดสรรหน่วยความจำ', 'หน่วยความจำต่อเนื่อง',
    'หน่วยความจำพลวัต', 'กรณีที่แย่ที่สุด', 'กรณีที่ดีที่สุด', 'กรณีเฉลี่ย', 'การวิเคราะห์อัลกอริทึม',
    'ประสิทธิภาพ', 'โครงสร้าง', 'ส่วนประกอบของโหนด', 'เหตุผล O(1)',

    # Array (อาร์เรย์)
    'array', 'index', 'element access', 'fixed-size array', 'dynamic array',
    'resizing array', 'multidimensional array', '2D array', 'contiguous allocation',
    'array operations', 'insertion at index', 'deletion at index', 'random access',
    'อาร์เรย์', 'ดัชนี', 'การเข้าถึงส่วนประกอบ', 'อาร์เรย์ขนาดคงที่', 'อาร์เรย์พลวัต',
    'การปรับขนาดอาร์เรย์', 'อาร์เรย์หลายมิติ', 'อาร์เรย์ 2 มิติ', 'การจัดสรรหน่วยความจำต่อเนื่อง',
    'การดำเนินการของอาร์เรย์', 'การแทรกที่ดัชนี', 'การลบที่ดัชนี', 'การเข้าถึงแบบสุ่ม',
    'Java การเข้าถึงข้อมูลในอาร์เรย์', 'Java การแทรกข้อมูล', 'Java การลบข้อมูล',
    'Java การค้นหาข้อมูล',

    # Linked List (ลิงค์ลิสต์)
    'linked list', 'singly linked list', 'doubly linked list', 'circular linked list',
    'head', 'tail', 'next pointer', 'previous pointer', 'node structure',
    'self-referential structure', 'linked list operations', 'insertion at beginning',
    'insertion at end', 'insertion after node', 'deletion from beginning',
    'deletion from end', 'deletion of node', 'traversal', 'Pointer Link',
    'ข้อดีของลิงค์ลิสต์', 'ข้อเสียของลิงค์ลิสต์',
    'ลิงค์ลิสต์', 'ลิงค์ลิสต์แบบเดี่ยว', 'ลิงค์ลิสต์แบบคู่', 'ลิงค์ลิสต์แบบวงกลม',
    'หัว', 'ท้าย', 'พอยน์เตอร์ชี้ถัดไป', 'พอยน์เตอร์ชี้ย้อนกลับ', 'โครงสร้างโหนด',
    'โครงสร้างอ้างอิงตัวเอง', 'การดำเนินการของลิงค์ลิสต์', 'การแทรกที่หัว',
    'การแทรกที่ท้าย', 'การแทรกหลังโหนด', 'การลบจากหัว', 'การลบจากท้าย',
    'การลบโหนด', 'การท่อง',

    # Stack (สแตก)
    'stack', 'LIFO', 'push', 'pop', 'peek', 'top', 'is_empty', 'is_full',
    'stack operations', 'overflow', 'underflow', 'stack pointer', 'stack element',
    'applications of stack', 'parenthesis matching', 'expression conversion',
    'infix to postfix', 'infix to prefix', 'function call stack', 'recursion implementation',
    'สแตก', 'LIFO (เข้าหลังออกก่อน)', 'พุช', 'ป๊อป', 'พีค', 'ท็อป', 'ว่างเปล่า', 'เต็ม',
    'การดำเนินการของสแตก', 'โอเวอร์โฟลว์', 'อันเดอร์โฟลว์', 'สแตกพอยน์เตอร์', 'ส่วนประกอบสแตก',
    'การประยุกต์ใช้สแตก', 'การจับคู่วงเล็บ', 'การแปลงนิพจน์',
    'อินฟิกซ์เป็นโพสต์ฟิกซ์', 'อินฟิกซ์เป็นพรีฟิกซ์', 'สแตกเรียกฟังก์ชัน', 'การประยุกต์ใช้การเรียกซ้ำ',
    'การทำงานของสเเตก', 'สเเตกประยุกต์', 'Push', 'Pop', 'Top', 'Overflow', 'Underflow',
    'Stack Pointer', 'Stack Element', 'peek',

    # Queue (คิว)
    'queue', 'FIFO', 'enqueue', 'dequeue', 'front', 'rear', 'peek (queue)', 'is_empty (queue)', 'is_full (queue)',
    'queue operations', 'circular queue', 'priority queue', 'double-ended queue', 'deque',
    'applications of queue', 'scheduling', 'buffering',
    'คิว', 'FIFO (เข้าก่อนออกก่อน)', 'เอนคิว', 'ดีคิว', 'ด้านหน้า', 'ด้านหลัง', 'พีค (คิว)', 'ว่างเปล่า (คิว)', 'เต็ม (คิว)',
    'การดำเนินการของคิว', 'คิววงกลม', 'คิวลำดับความสำคัญ', 'คิวสองทาง', 'เด็ค',
    'การประยุกต์ใช้คิว', 'การจัดตารางเวลา', 'การบัฟเฟอร์',
    'ฟิโฟ', 'ฟิโฟคือ', 'ประเภทของคิว', 'Linear', 'Circular', 'Priority',

    # Tree (ต้นไม้)
    'tree', 'root node', 'leaf node', 'internal node', 'parent node', 'child node',
    'sibling node', 'ancestor', 'descendant', 'subtree', 'depth', 'height', 'degree',
    'binary tree', 'binary search tree', 'bst', 'full binary tree', 'complete binary tree',
    'perfect binary tree', 'balanced tree', 'AVL tree', 'Red-Black tree', 'B-tree', 'B+ tree',
    'heap', 'min-heap', 'max-heap', 'priority queue (based on heap)',
    'tree traversal', 'inorder traversal', 'preorder traversal', 'postorder traversal',
    'level-order traversal', 'recursive traversal', 'iterative traversal', 'tree operations',
    'insertion in BST', 'deletion in BST', 'searching in BST',
    'ต้นไม้', 'โหนดราก', 'โหนดใบ', 'โหนดภายใน', 'โหนดแม่/พ่อ', 'โหนดลูก',
    'โหนดพี่น้อง', 'โหนดบรรพบุรุษ', 'โหนดลูกหลาน', 'ต้นไม้ย่อย', 'ความลึก', 'ความสูง', 'ดีกรี',
    'ต้นไม้ไบนารี', 'ต้นไม้ค้นหาไบนารี', 'บีเอสที', 'ต้นไม้ไบนารีแบบสมบูรณ์', 'ต้นไม้ไบนารีแบบเต็ม',
    'ต้นไม้ไบนารีแบบเพอร์เฟกต์', 'ต้นไม้สมดุล', 'ต้นไม้ AVL', 'ต้นไม้แดงดำ', 'บี-ทรี', 'บีพลัส-ทรี',
    'ฮีป', 'มินฮีป', 'แม็กซ์ฮีป', 'คิวลำดับความสำคัญ (อิงฮีป)',
    'การท่องต้นไม้', 'การท่องแบบอินออร์เดอร์', 'การท่องแบบพรีออร์เดอร์', 'การท่องแบบโพสต์ออร์เดอร์',
    'การท่องแบบเลเวลออร์เดอร์', 'การท่องแบบเรียกซ้ำ', 'การท่องแบบวนซ้ำ', 'การดำเนินการของต้นไม้',
    'การเพิ่มใน BST', 'การลบใน BST', 'การค้นหาใน BST',
    'แผนภาพต้นไม้', 'Root Node', 'Leaf Node', 'Subtree', 'Binary Tree', 'Full Binary Tree',
    'Complete Binary Tree', 'Inorder Traversal', 'Preorder Traversal', 'Postorder Traversal',
    'BST', 'การดำเนินการของต้มไม้',

    # Graph (กราฟ)
    'graph', 'vertex', 'node (graph)', 'edge', 'arc', 'directed graph', 'undirected graph',
    'weighted graph', 'unweighted graph', 'path', 'cycle', 'simple path', 'elementary path',
    'cycle detection', 'degree of vertex', 'in-degree', 'out-degree', 'adjacent vertices',
    'graph representation', 'adjacency matrix', 'adjacency list', 'incidence matrix',
    'BFS', 'DFS', 'Breadth First Search', 'Depth First Search', 'graph traversal',
    'shortest path', 'Dijkstra Algorithm', 'Bellman-Ford Algorithm', 'Floyd-Warshall Algorithm',
    'minimum spanning tree', 'MST', 'Prim’s Algorithm', 'Kruskal’s Algorithm',
    'topological sort', 'strongly connected components', 'applications of graphs',
    'social network', 'GPS / Shortest Path', 'network routing', 'connectivity', 'connected components',
    'กราฟ', 'จุดยอด', 'โหนด (กราฟ)', 'เส้นเชื่อม', 'อาร์ค', 'กราฟมีทิศทาง', 'กราฟไม่มีทิศทาง',
    'กราฟถ่วงน้ำหนัก', 'กราฟไม่ถ่วงน้ำหนัก', 'ทางเดิน', 'วงจร', 'ทางเดินเชิงเดียว', 'ทางเดินพื้นฐาน',
    'การตรวจจับวงจร', 'ดีกรีของจุดยอด', 'อิน-ดีกรี', 'เอาท์-ดีกรี', 'จุดยอดประชิด',
    'การแทนกราฟ', 'แอดจาเซนซีเมตริกซ์', 'แอดจาเซนซีลิสต์', 'อินซิเดนซ์เมตริกซ์',
    'บีเอฟเอส', 'ดีเอฟเอส', 'การค้นหาในแนวกว้าง', 'การค้นหาในแนวลึก', 'การท่องกราฟ',
    'เส้นทางที่สั้นที่สุด', 'อัลกอริทึมไดค์สตรา', 'อัลกอริทึมเบลล์แมน-ฟอร์ด', 'อัลกอริทึมฟลอยด์-วอร์แชล',
    'ต้นไม้ทอดข้ามที่น้อยที่สุด', 'เอ็มเอสที', 'อัลกอริทึมพริม', 'อัลกอริทึมครัสคัล',
    'การเรียงเชิงทอพอโลยี', 'ส่วนประกอบเชื่อมโยงอย่างเข้ม', 'การประยุกต์ใช้กราฟ',
    'เครือข่ายสังคม', 'จีพีเอส / เส้นทางที่สั้นที่สุด', 'การกำหนดเส้นทางเครือข่าย',
    'การเชื่อมต่อ', 'ส่วนประกอบที่เชื่อมโยง', 'Eage (เส้นเชื่อม)', 'Directed',
    'Undirected', 'Weighted', 'Unweighted', 'Graph Representation', 'Adjacency Matrix',
    'Adjacency List', 'BFS', 'DFS', 'Shortest Path', 'Dijkstra Algorithm',
    'Bellman-Ford Algorithm', 'Minimum Spanning Tree (MST)', 'Prim’s Algorithm (MST)',
    'Kruskal’s Algorithm', 'Social Network', 'GPS / Shortest Path', 'Network Routing',

    # Hashing (แฮชชิง)
    'hash', 'hash function', 'hash table', 'hash map', 'collision', 'collision resolution',
    'chaining', 'open addressing', 'linear probing', 'quadratic probing', 'double hashing',
    'perfect hash function', 'load factor',
    'แฮช', 'ฟังก์ชันแฮช', 'ตารางแฮช', 'แฮชแมพ', 'การชนกัน', 'การแก้ปัญหาการชนกัน',
    'การต่อโซ่', 'การจัดที่อยู่แบบเปิด', 'การตรวจสอบเชิงเส้น', 'การตรวจสอบเชิงกำลังสอง', 'การแฮชสองครั้ง',
    'ฟังก์ชันแฮชที่สมบูรณ์', 'โหลดแฟคเตอร์',

    # Sorting & Searching (การเรียงลำดับและการค้นหา)
    'sorting', 'searching', 'linear search', 'binary search',
    'bubble sort', 'selection sort', 'insertion sort', 'merge sort', 'quick sort',
    'heap sort', 'radix sort', 'counting sort', 'bucket sort',
    'stability (sorting)', 'in-place sorting', 'comparison sort',
    'การเรียงลำดับ', 'การค้นหา', 'การค้นหาเชิงเส้น', 'การค้นหาแบบไบนารี',
    'บับเบิลซอร์ต', 'ซีเล็กชันซอร์ต', 'อินเซอร์ชันซอร์ต', 'เมิร์จซอร์ต', 'ควิกซอร์ต',
    'ฮีปซอร์ต', 'แรดิกซ์ซอร์ต', 'เคาน์ติ้งซอร์ต', 'บักเก็ตซอร์ต',
    'ความเสถียร (การเรียงลำดับ)', 'การเรียงลำดับในตัว', 'การเรียงลำดับแบบเปรียบเทียบ',

    # Common Operations (การดำเนินการทั่วไป)
    'การสร้าง', 'การเพิ่ม', 'การแทรก', 'การลบ', 'โค้ดการสร้าง',
    'โค้ดการเพิ่ม', 'โค้ดการแทรก', 'โค้ดการลบ', 'ยกตัวอย่าง','ขอโค้ด',
    'Java', 'การเขียนโค้ด', 'ตัวอย่างโค้ด', 'Pseudocode', 'Big O analysis',
    'ภาษาซี', 'Python', 'JavaScript'
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
    if st.button("ล้างประวัติการสนทนา", use_container_width=True):
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