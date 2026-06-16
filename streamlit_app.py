import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import io
from datetime import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Tax Invoice Extractor", page_icon="🧾")
st.title("🧾 Tax Invoice PDF Extractor")
st.markdown("ระบบสกัดข้อมูลใบกำกับภาษีชุดใหญ่ (รองรับ 50+ หน้า)")

# --- แถบข้าง (Sidebar) ---
with st.sidebar:
    st.header("🔑 เปิดใช้งานระบบ (API Key)")
    api_key = st.text_input("ใส่ Gemini API Key ของคุณเพื่อเปิดใช้งาน", type="password")
    st.info("หากยังไม่มี API Key ให้ไปขอได้ที่: [aistudio.google.com](https://aistudio.google.com)")

# --- ส่วนประมวลผล ---
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    uploaded_file = st.file_uploader("เลือกไฟล์ PDF ใบกำกับภาษี (รองรับไฟล์หลายหน้า)", type="pdf")

    if uploaded_file is not None:
        if st.button("🚀 เริ่มประมวลผลด่วน"):
            with st.spinner("🧠 กำลังวิเคราะห์ข้อมูล..."):
                try:
                    pdf_bytes = uploaded_file.read()
                    pdf_data = {'mime_type': 'application/pdf', 'data': pdf_bytes}
                    prompt = """สกัดข้อมูลใบกำกับภาษีทุกใบใน PDF นี้เป็น JSON List: [{date, no, name, tax_id, branch, amount, vat, total, remark}]
                    ข้อบังคับสำคัญ:
                    1. ในช่อง 'name' ให้ใช้ชื่อ "ผู้ขาย" (Vendor / Seller / ร้านค้าที่ออกใบกำกับภาษี) เท่านั้น ห้ามเอาชื่อผู้ซื้อหรือตัวเรามาใส่
                    2. ในช่อง 'tax_id' ให้ใช้เลขประจำตัวผู้เสียภาษีของ "ผู้ขาย" เท่านั้น
                    3. ในช่อง 'branch' ให้ใช้สาขาของ "ผู้ขาย" เช่น HEAD OFFICE หรือ 00001
                    4. ในช่อง 'remark' ให้ใช้ข้อความหรือหมายเลขใดๆ ที่มีการเขียนเพิ่มเติมด้วยดินสอหรือลายมือไว้บนบริเวณหัวกระดาษ (เช่น เลขอ้างอิงภายใน เลข PU หรือเลขเอกสารอื่นๆ) หากไม่มีการเขียนเพิ่มเติมใดๆ ให้ใส่เป็นค่าว่าง
                    """
                    
                    response = model.generate_content([prompt, pdf_data], generation_config={"response_mime_type": "application/json"})
                    data_list = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                    if isinstance(data_list, dict): data_list = [data_list]
                    
                    df = pd.DataFrame(data_list)
                    st.success(f"✅ วิเคราะห์เสร็จสิ้น! พบทั้งหมด {len(df)} รายการ")
                    st.dataframe(df) # แสดงตารางบนหน้าเว็บ
                    
                    # 1. ฟังก์ชันสร้างไฟล์ Excel
                    def to_excel(df_data):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_data.to_excel(writer, index=False, sheet_name='Tax_Report')
                        return output.getvalue()
                    
                    # 2. แปลงข้อมูลใน DataFrame ให้เป็นไฟล์ Excel
                    excel_data = to_excel(df)
                    
                    # 3. ปุ่มดาวน์โหลด .xlsx
                    st.download_button(
                        label="📥 ดาวน์โหลดเป็นไฟล์ Excel (.xlsx)",
                        data=excel_data,
                        file_name=f"Manus_Tax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
else:
    st.warning("👈 กรุณาใส่ API Key ที่แถบด้านซ้ายก่อนครับ")