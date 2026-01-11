import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قائمة الجنسيات المختصرة (للتجربة) - يمكنك وضع القائمة الكاملة هنا
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Jordan"]

# قاموس الترجمة للمسميات الوظيفية
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "مندوب": "Representative",
    "محاسب": "Accountant"
}

# نظام الدخول
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.form("login_form"):
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# --- دالة الاستعلام (Inquiry) تفتح في نافذة منفصلة ---
@st.dialog("MOHRE Inquiry Details")
def show_inquiry(card_number):
    st.write(f"🔍 Searching MOHRE for Card: **{card_number}**")
    st.info("Wait... Fetching company information...")
    # هنا تضع كود السيلينيوم الخاص بصفحة الاستعلام
    time.sleep(2)
    st.success("Data Retrieved.")

# --- دالة الاستخراج الأصلية ---
def extract_data(passport, nationality, dob_str):
    # (نفس كود السيلينيوم الخاص بك دون تغيير في المنطق)
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        # ... بقية خطوات السيلينيوم ...
        
        # مثال للنتيجة مع الترجمة
        job_ar = "مدير المنطقة" # قيمة افتراضية للتجربة
        card_num = "124119312"
        
        return {
            "Passport": passport,
            "Nationality": nationality,
            "DOB": dob_str,
            "Job Description": job_translation.get(job_ar, job_ar),
            "Card Number": card_num,
            "Basic": "8000",
            "Total": "16000"
        }
    except: return None
    finally: driver.quit()

# الواجهة الأساسية
tab1, tab2 = st.tabs(["Single Search", "Batch Preview"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    with col1: passport = st.text_input("Passport Number")
    with col2: nationality = st.selectbox("Nationality", countries_list)
    with col3: 
        # تعديل التاريخ: فارغ كافتراضي مع نص إرشادي
        dob_input = st.text_input("Date of Birth", placeholder="DD/MM/YYYY")

    if st.button("Search Now"):
        if passport and dob_input:
            start_time = time.time()
            with st.spinner("Processing..."):
                res = extract_data(passport, nationality, dob_input)
                if res:
                    elapsed = round(time.time() - start_time, 2)
                    st.markdown(f"✅ **Success: 1** | ⏱️ **Live Timer:** {elapsed}s")
                    
                    # عرض النتيجة مع جعل "رقم البطاقة" رابطاً يفتح الاستعلام
                    df = pd.DataFrame([res])
                    st.data_editor(
                        df,
                        column_config={
                            "Card Number": st.column_config.LinkColumn(
                                "Card Number (Click to Inquiry)",
                                help="Click the number to open MOHRE details",
                                # هنا الرابط يحول المستخدم لصفحة الاستعلام (أو يفتح الدايالوج برمجياً)
                                validate="^\\d+$",
                            )
                        },
                        disabled=True,
                        hide_index=True
                    )
                    # زر تفعيل الـ Dialog (لأن الجدول لا يفتح دايالوج مباشرة في Streamlit)
                    if st.button(f"🔎 Click here to view details for {res['Card Number']}"):
                        show_inquiry(res['Card Number'])
                else: st.error("No results found.")

with tab2:
    st.subheader("Batch Processing")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        st.write("File Preview:")
        st.dataframe(df_input, use_container_width=True)
        
        if st.button("Start Batch Processing"):
            results = []
            success_count = 0
            start_batch = time.time()
            
            progress_area = st.empty()
            table_area = st.empty()
            
            for idx, row in df_input.iterrows():
                # تحديث العداد والوقت حياً (Live)
                elapsed = round(time.time() - start_batch, 1)
                progress_area.markdown(f"✅ **Success: {success_count}** | ⏱️ **Live Timer:** {elapsed}s")
                
                # استخراج البيانات
                res = extract_data(str(row[0]), str(row[1]), str(row[2]))
                if res:
                    results.append(res)
                    success_count += 1
                    # تحديث الجدول حياً
                    table_area.table(pd.DataFrame(results))
            
            st.success(f"Finished! Total: {success_count} in {round(time.time()-start_batch, 2)}s")
