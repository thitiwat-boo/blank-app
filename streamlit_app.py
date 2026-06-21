import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import io
from datetime import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Universal PDF to Excel Converter", page_icon="📊")
st.title("📊 Universal PDF to Excel Extractor")
st.markdown("ระบบสกัดข้อมูลจาก PDF ทุกรูปแบบให้เป็นตาราง Excel ด้วย AI (Gemini Flash)")

# --- แถบข้าง (Sidebar) ---
with st.sidebar:
    st.header("🔑 เปิดใช้งานระบบ (API Key)")
    api_key = st.text_input("ใส่ Gemini API Key ของคุณเพื่อเปิดใช้งาน", type="password")
    st.info("หากยังไม่มี API Key ให้ไปขอได้ที่: [aistudio.google.com](https://aistudio.google.com)")
    
    st.write("---")
    st.header("📂 ตั้งค่าการแปลงไฟล์")
    # เพิ่มเมนูให้เลือกประเภทเอกสาร เพื่อเปลี่ยน Prompt ให้ตรงกับงาน
    doc_type = st.selectbox(
        "เลือกประเภทเอกสารใน PDF:",
        ["ใบกำกับภาษี (Tax Invoice)", "Statement ธนาคาร (Bank Statement)", "เอกสารทั่วไป/ตารางทั่วไป (General Document)"]
    )

# --- ส่วนประมวลผล ---
if api_key:
    genai.configure(api_key=api_key)
    # แนะนำให้ใช้ gemini-1.5-flash สำหรับงานอ่านเอกสารและได้ความเร็วสูง
    model = genai.GenerativeModel('gemini-flash-latest')
    
    uploaded_file = st.file_uploader("เลือกไฟล์ PDF ที่ต้องการแปลง", type="pdf")

    if uploaded_file is not None:
        if st.button("🚀 เริ่มประมวลผล"):
            with st.spinner("🧠 AI กำลังอ่านและแปลงข้อมูลใน PDF... (อาจใช้เวลาสักครู่ตามจำนวนหน้า)"):
                try:
                    pdf_bytes = uploaded_file.read()
                    pdf_data = {'mime_type': 'application/pdf', 'data': pdf_bytes}
                    
                    # --- เลือก Prompt และ โครงสร้าง JSON ตามประเภทเอกสาร ---
                    if doc_type == "ใบกำกับภาษี (Tax Invoice)":
                        prompt = """สกัดข้อมูลใบกำกับภาษีทุกใบใน PDF นี้เป็น JSON List: [{date, no, name, tax_id, branch, amount, vat, total, remark}]
                        ข้อบังคับสำคัญ:
                        1. ในช่อง 'name' ให้ใช้ชื่อ "ผู้ขาย" (Vendor / Seller) เท่านั้น ห้ามเอาชื่อผู้ซื้อหรือตัวเรามาใส่
                        2. ในช่อง 'tax_id' ให้ใช้เลขประจำตัวผู้เสียภาษีของ "ผู้ขาย" เท่านั้น
                        3. ในช่อง 'branch' ให้ใช้สาขาของ "ผู้ขาย" เช่น HEAD OFFICE หรือ 00001
                        4. ในช่อง 'remark' ให้ใช้ข้อความหรือหมายเลขที่เขียนเพิ่มเติมด้วยลายมือบนหัวกระดาษ (ถ้ามี) ถ้าไม่มีให้เป็นค่าว่าง
                        """
                    
                    elif doc_type == "Statement ธนาคาร (Bank Statement)":
                        prompt = """สกัดข้อมูลรายการเดินบัญชี (Transaction History) ทั้งหมดใน PDF Statement นี้ ออกมาเป็น JSON List ของออบเจกต์ที่มีโครงสร้างดังนี้:
                        [{date, time, description, withdraw, deposit, balance, channel}]
                        
                        ข้อบังคับสำคัญ:
                        1. 'date': วันที่เกิดรายการ (พยายามปรับให้อยู่ในฟอร์แมต DD/MM/YYYY หรือตามที่ปรากฏในเอกสาร)
                        2. 'time': เวลาที่เกิดรายการ (ถ้ามี ถ้าไม่มีให้ใส่ค่าว่าง)
                        3. 'description': รายละเอียดรายการ หรือโค้ดธุรกรรม (เช่น TRANSFER, ATM, นาย A โอนเงิน)
                        4. 'withdraw': จำนวนเงินที่ถอน/โอนออก (ต้องเป็นตัวเลขเงิน หรือใส่ 0 หรือค่าว่างถ้าไม่มีรายการถอน)
                        5. 'deposit': จำนวนเงินที่ฝาก/โอนเข้า (ต้องเป็นตัวเลขเงิน หรือใส่ 0 หรือค่าว่างถ้าไม่มีรายการฝาก)
                        6. 'balance': ยอดเงินคงเหลือ ณ รายการนั้นๆ
                        7. 'channel': ช่องทาง เช่น Mobile Banking, ATM (ถ้ามี)
                        * ดึงข้อมูลมาให้ครบทุกแถว ทุกหน้า ห้ามข้ามรายการแม้แต่รายการเดียว *
                        """
                    
                    else: # เอกสารทั่วไป / ตารางทั่วไป
                        prompt = """วิเคราะห์และแปลงข้อมูลตารางหรือเนื้อหาหลักในเอกสาร PDF นี้ให้ออกมาเป็น JSON List (Array of Objects) 
                        โดยให้คุณวิเคราะห์เองว่า Column ที่เหมาะสมสำหรับข้อมูลชุดนี้ควรมีอะไรบ้าง เพื่อให้นำไปทำเป็นตาราง Excel ได้สวยงามและสมบูรณ์ที่สุด
                        
                        ข้อบังคับสำคัญ:
                        1. ห้ามสรุปข้อมูลย่อ ให้สกัดข้อมูลรายละเอียดรายบรรทัด/รายข้อมาให้ครบถ้วน
                        2. ตั้งชื่อ Key ของ JSON ให้เป็นภาษาอังกฤษที่สื่อความหมาย (เช่น item, qty, price, total, status, name)
                        """
                    
                    # สั่งงาน Gemini โดยบังคับ Output เป็น JSON
                    response = model.generate_content(
                        [prompt, pdf_data], 
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    # แปลงข้อความ JSON เป็น Python List
                    data_list = json.loads(response.text.strip())
                    if isinstance(data_list, dict): 
                        # ถ้า AI คืนค่ามาเป็น Object ชั้นเดียว (เช่น มี key ซ้อนอยู่ข้างใน) พยายามดึงตัวที่เป็น List ออกมา
                        for key, value in data_list.items():
                            if isinstance(value, list):
                                data_list = value
                                break
                        if isinstance(data_list, dict):
                            data_list = [data_list]
                    
                    # แปลงเป็น DataFrame
                    df = pd.DataFrame(data_list)
                    
                    st.success(f"✅ แปลงข้อมูลสำเร็จ! พบทั้งหมด {len(df)} แถว")
                    st.dataframe(df) # แสดงตารางบนหน้าเว็บ ให้ยูสเซอร์ตรวจทาน
                    
                    # ฟังก์ชันสร้างไฟล์ Excel
                    def to_excel(df_data):
                        output = io.BytesIO()
                        # ใช้ openpyxl ในการเขียนไฟล์
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_data.to_excel(writer, index=False, sheet_name='Data_Report')
                        return output.getvalue()
                    
                    excel_data = to_excel(df)
                    
                    # ปุ่มดาวน์โหลด .xlsx
                    file_prefix = "Statement" if "Statement" in doc_type else "Data" if "ทั่วไป" in doc_type else "Tax"
                    st.download_button(
                        label="📥 ดาวน์โหลดเป็นไฟล์ Excel (.xlsx)",
                        data=excel_data,
                        file_name=f"Manus_{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")
                    st.info("คำแนะนำ: หากไฟล์มีจำนวนหน้ามากเกินไป (เช่น เกิน 30-40 หน้าในคำสั่งเดียว) ลองแบ่งย่อยไฟล์แล้วอัปโหลดทีละส่วนครับ")
else:
    st.warning("👈 กรุณาใส่ API Key ที่แถบด้านซ้ายก่อนเพื่อเปิดใช้งานระบบ")