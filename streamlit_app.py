import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import io
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและดีไซน์ (UX/UI Custom CSS) ---
st.set_page_config(
    page_title="Smart AI Financial Extractor", 
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        transform: translateY(-1px);
    }
    div[data-testid="stExpander"] {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Smart AI Financial Extractor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ระบบสกัดและวิเคราะห์ข้อมูลจาก PDF คู่กับผังบัญชีด้วย AI (Gemini Flash)</div>', unsafe_allow_html=True)

# --- 2. แถบข้าง (Sidebar) สำหรับตั้งค่าระบบ ---
with st.sidebar:
    st.header("🔑 เปิดใช้งานระบบ (API Key)")
    api_key = st.text_input("ใส่ Gemini API Key ของคุณเพื่อเปิดใช้งาน", type="password")
    st.info("หากยังไม่มี API Key ให้ไปขอได้ที่: [aistudio.google.com](https://aistudio.google.com)")
    
    st.write("---")
    st.header("🏢 ข้อมูลนิติบุคคล")
    
    # ช่องกรอกเลข 13 หลัก
    tax_id = st.text_input("กรอกเลขทะเบียนนิติบุคคล 13 หลัก:", max_chars=13, placeholder="เช่น 01055XXXXXXXX")
    
    # เปิดช่องให้ทุกคนพิมพ์ชื่อบริษัทและประเภทธุรกิจเองได้อย่างอิสระ ถูกต้องตรงเป๊ะแน่นอน
    company_name = st.text_input("ชื่อบริษัทที่ต้องการทำบัญชี:", placeholder="กรุณาพิมพ์ชื่อบริษัท เช่น บริษัท XXXXXXXX จำกัด")
    business_type = st.text_area("ลักษณะธุรกิจ:", placeholder="เช่น ผลิตและจำหน่ายเบเกอรี่, คาเฟ่, บริการไอที")
    
    # ทำงานอัตโนมัติเมื่อกรอกครบ 13 หลัก และมี API Key แล้ว
    #if len(tax_id) == 13 and api_key:
    #    genai.configure(api_key=api_key)
    #    
    #    with st.spinner("🔍 AI กำลังสืบค้นข้อมูลบริษัทจากเลข 13 หลัก..."):
    #        try:
    #            # สั่งให้ Gemini ค้นหาข้อมูลบริษัทบนอินเทอร์เน็ต
    #            search_model = genai.GenerativeModel(
    #                model_name="gemini 2.5 flash"
    #            )                    

    #            search_prompt = f"""
    #            คุณคือผู้ช่วยอัจฉริยะ จงบอกชื่อบริษัทหรือห้างหุ้นส่วนของไทยที่ตรงกับเลขทะเบียนนิติบุคคล 13 หลักนี้: {tax_id} 
    #            พร้อมสรุปสั้นๆ ว่าเขาทำธุรกิจเกี่ยวกับอะไร
    #            
    #            ตอบกลับเป็นรูปแบบ JSON โครงสร้างดังนี้เท่านั้น ห้ามมีข้อความอื่น:
    #            {{
    #              "company_name": "ชื่อบริษัท",
    #              "business_type": "ประเภทธุรกิจ"
    #            }}
    #            """
                
    #            search_response = search_model.generate_content(search_prompt)
    #            search_text = search_response.text.strip()
                
    #            # Clean JSON format
    #            if search_text.startswith("```json"):
    #                search_text = search_text.split("```json")[1].split("```")[0].strip()
    #            elif search_text.startswith("```"):
    #                search_text = search_text.split("```")[1].split("```")[0].strip()
                
    #            info = json.loads(search_text)
    #            company_name = info.get("company_name", "")
    #            business_type = info.get("business_type", "")
                
    #            if company_name:
    #                st.success("✅ ดึงข้อมูลบริษัทสำเร็จ!")
    #            else:
    #                st.warning("❓ ไม่พบข้อมูลบริษัทจากเลขนี้ในระบบภายนอก")
                    
    #        except Exception as e:
    #            st.error(f"⚠️ ไม่สามารถสืบค้นข้อมูลได้อัตโนมัติ: {e}")
    
    # แสดงผลข้อมูลที่ค้นหาได้ในหน้า UI (หรือให้ผู้ใช้กรอกเองถ้า AI หาไม่เจอ)
    #company_name = st.text_input("ชื่อบริษัทที่ตรวจพบ:", value=company_name)
    #business_type = st.text_area("ลักษณะธุรกิจ:", value=business_type, placeholder="เช่น บริการซอฟต์แวร์, คาเฟ่")
    
    st.write("---")
    st.header("⚙️ ตั้งค่าประเภทเอกสาร")
    doc_type = st.selectbox(
        "เลือกประเภทเอกสารใน PDF หลัก:",
        [
            "ใบกำกับภาษี/ใบเสร็จรับเงิน (Tax Invoice/Receipt)", 
            "Statement ธนาคาร (Bank Statement)", 
            "สลิปโอนเงิน (Transfer Slip)", 
            "เอกสารทั่วไป/ตารางทั่วไป (General Document)"
        ]
    )

# ตรวจสอบการกรอก API Key ก่อนเริ่มทำงาน
if not api_key:
    st.warning("⚠️ กรุณาใส่ Gemini API Key ที่แถบซ้ายมือเพื่อเริ่มต้นใช้งานครับ")
    st.stop()

# กำหนดค่าให้ระบบ AI
genai.configure(api_key=api_key)

# --- 3. ส่วนอัปโหลดไฟล์ (Main UI) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 1. เอกสารหลักที่ต้องการให้อ่าน")
    pdf_file = st.file_uploader("อัปโหลดไฟล์ PDF (Statement / Invoice / Receipt)", type=["pdf"])

with col2:
    st.subheader("📂 2. ผังบัญชีของบริษัท (ตัวเลือกเสริม)")
    coa_file = st.file_uploader("อัปโหลดผังบัญชีเพื่อบันทึกโค้ดอัตโนมัติ (Excel)", type=["xlsx", "xls"])

# --- 4. ประมวลผลผังบัญชี ---
coa_context = "ไม่มีการอัปโหลดผังบัญชีมา ให้วิเคราะห์ชื่อบัญชีที่เหมาะสมตามมาตรฐานสากล"
if coa_file is not None:
    try:
        df_coa = pd.read_excel(coa_file)
        with st.expander("🔍 ตรวจสอบข้อมูลผังบัญชีที่อัปโหลด", expanded=False):
            st.dataframe(df_coa, use_container_width=True)
        # แปลงข้อมูลผังบัญชีเป็น String เพื่อส่งให้ AI
        coa_context = df_coa.to_string(index=False)
    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่านไฟล์ผังบัญชีได้: {e}")

# --- 5. เริ่มทำการแปลงและวิเคราะห์ข้อมูล ---
if pdf_file is not None:
    st.write("---")
    if st.button("🚀 เริ่มวิเคราะห์และแปลงข้อมูลเป็น Excel"):
        with st.status("⏳ AI กำลังอ่านและวิเคราะห์เอกสารอย่างละเอียด...", expanded=True) as status:
            try:
                # เตรียมข้อมูลไฟล์ PDF สำหรับส่งให้ Gemini API
                pdf_data = pdf_file.read()
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": pdf_data
                }
                
                # ออกแบบ Prompt แบบละเอียด โดยเพิ่มบริบทของบริษัทและรองรับ Slip
                prompt = f"""
                คุณคือผู้เชี่ยวชาญด้านบัญชีและการเงินของไทย 
                หน้าที่ของคุณคืออ่านเอกสาร PDF ที่แนบมานี้ (ประเภท: {doc_type}) และทำการวิเคราะห์ข้อมูลอย่างถูกต้อง

                [ข้อมูลบริบทของบริษัทผู้ใช้งาน]
                - ชื่อบริษัท: {company_name if company_name else 'ไม่ได้ระบุ'}
                - ลักษณะธุรกิจ: {business_type if business_type else 'ธุรกิจทั่วไป'}
                *ใช้ข้อมูลธุรกิจนี้ในการพิจารณาเพื่อลงหมวดหมู่บัญชีให้สอดคล้องกับความเป็นจริง*

                [ข้อมูลผังบัญชีของบริษัท]
                {coa_context}

                จงดึงข้อมูลทุกรายการ (Transactions) ออกมา โดยมีเงื่อนไขการดึงข้อมูลตามประเภทเอกสารดังนี้:
                1. วันที่ (Date) - แปลงเป็นรูปแบบ YYYY-MM-DD
                2. เวลา (Time) - ระบุเวลาเป็นรูปแบบ HH:MM (หากเอกสารไม่มีให้ใส่ "-")
                3. รายละเอียดรายการ (Description) - สำหรับสลิปโอนเงิน ให้ระบุว่า "โอนเงินจาก [ชื่อผู้โอน] ไปยัง [ชื่อผู้รับโอน]" ให้ชัดเจน
                4. จำนวนเงิน (Amount) - ตัวเลขสุทธิรวม
                5. ประเภททางบัญชี (Account Type) - ระบุว่าเป็น 'รายได้', 'ค่าใช้จ่าย', 'สินทรัพย์' หรือ 'หนี้สิน'
                6. ชื่อบัญชีและรหัสบัญชี (Account Code & Name) - เลือกโค้ดและชื่อที่ตรงที่สุดจากผังบัญชี ถ้าไม่มีให้แนะนำบัญชีที่ใกล้เคียงที่สุด
                7. ประเภทภาษีมูลค่าเพิ่ม (VAT Type) - วิเคราะห์ว่าเป็น 'VAT 7%', 'VAT 0%' หรือ 'ยกเว้น VAT'
                8. ประเภทหัก ณ ที่จ่าย (WHT Type) - ระบุการทำ หัก ณ ที่จ่าย (เช่น ค่าบริการ 3%, หรือระบุ 'ไม่มี')

                สำคัญมาก: จงตอบกลับเฉพาะข้อมูลในรูปแบบ JSON Array เท่านั้น ห้ามมีข้อความอื่นขึ้นต้นหรือลงท้าย โดยโครงสร้างเป็นดังนี้:
                [
                  {{
                    "date": "YYYY-MM-DD",
                    "time": "HH:MM",
                    "description": "โอนเงินจาก... ไปยัง...",
                    "amount": 0.0,
                    "account_type": "...",
                    "account_code_name": "...",
                    "vat_type": "...",
                    "wht_type": "..."
                  }}
                ]
                """
                
                # เรียกใช้งานโมเดล Gemini 2.5 Flash
                model = genai.GenerativeModel("gemini-2.5-flash")
                status.write("🧠 กำลังส่งข้อมูลให้ AI วิเคราะห์โครงสร้างบัญชีและภาษี...")
                response = model.generate_content([pdf_part, prompt])
                
                # ทำความสะอาดผลลัพธ์ JSON จาก AI
                result_text = response.text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif result_text.startswith("```"):
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                # แปลง JSON เป็น DataFrame
                data_list = json.loads(result_text)
                df_result = pd.DataFrame(data_list)
                
                # ปรับหัวตารางให้สวยงามอ่านง่าย (เรียงลำดับตาม Key ใน JSON)
                df_result.columns = [
                    "วันที่", "เวลา", "รายละเอียดรายการ", "จำนวนเงิน", 
                    "ประเภททางบัญชี", "รหัสและชื่อบัญชี", "ประเภท VAT", "หัก ณ ที่จ่าย (WHT)"
                ]
                
                status.update(label="✨ วิเคราะห์ข้อมูลสำเร็จ!", state="complete", expanded=False)
                
                # --- 6. แสดงผลลัพธ์บน UI ---
                st.subheader("📊 ผลลัพธ์การวิเคราะห์จาก AI")
                st.dataframe(df_result, use_container_width=True)
                
                # ทำปุ่มดาวน์โหลดไฟล์ Excel (Sheet เดียวจบตามเงื่อนไข)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_result.to_excel(writer, index=False, sheet_name='Financial_Analysis')
                
                st.write("---")
                st.download_button(
                    label="📥 ดาวน์โหลดไฟล์ Excel ผลการวิเคราะห์",
                    data=buffer.getvalue(),
                    file_name=f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except json.JSONDecodeError:
                status.update(label="❌ AI ตอบกลับรูปแบบข้อมูลไม่ถูกต้อง", state="error")
                st.error("ไม่สามารถแปลงข้อมูลเป็นตารางได้เนื่องจากโครงสร้างข้อมูลผิดพลาด ลองกดใหม่อีกครั้งครับ")
                with st.expander("ดูผลลัพธ์ดิบจาก AI"):
                    st.code(response.text)
            except Exception as e:
                status.update(label="❌ เกิดข้อผิดพลาดในระบบ", state="error")
                st.error(f"เกิดข้อผิดพลาด: {e}")