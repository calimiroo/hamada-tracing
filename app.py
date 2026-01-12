import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- 1. إعدادات الصفحة والأمان ---
st.set_page_config(page_title="MOHRE Portal System", layout="wide")

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop_process' not in st.session_state: st.session_state.stop_process = False
if 'is_paused' not in st.session_state: st.session_state.is_paused = False

# نظام الدخول
if not st.session_state.authenticated:
    st.subheader("🔒 Login Required")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 2. محرك البحث (الرأس السحابي) ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def perform_scraping(passport, nationality, dob):
    p_str = str(passport).strip()
    if not p_str or nationality == "Select Nationality" or " " in p_str:
        return "Format Error"

    driver = get_driver()
    if not driver: return "System Error"

    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        
        # إدخال البيانات الأساسية
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p_str)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Nationality Not Found"
        
        # كتابة التاريخ (الطريقة الناجحة)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_field, str(dob))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        # استخراج البيانات (تم تحسينه لضمان عدم ظهور N/A)
        def extract(label):
            try:
                # البحث عن النص داخل الـ span أو الـ div المجاور للعنوان
                xpath = f"//div[contains(text(), '{label}')]/following-sibling::div//span | //span[contains(text(), '{label}')]/following-sibling::span"
                element = driver.find_element(By.XPATH, xpath)
                val = element.text.strip()
                return val if val else "Not Found"
            except:
                return "Not Found"

        # التحقق من وجود نتيجة أصلاً
        job = extract("Job Description")
        if job == "Not Found":
            # محاولة أخيرة باستخدام البحث العام عن النص
            try:
                job = driver.find_element(By.ID, "lblJobDescription").text.strip()
            except:
                return "Data Not Found"

        return {
            "Job Description": job,
            "Card Number": extract("Card Number"),
            "Contract Start": extract("Contract Start"),
            "Contract End": extract("Contract End"),
            "Basic Salary": extract("Basic Salary"),
            "Total Salary": extract("Total Salary")
        }
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        driver.quit()

# --- 3. واجهة المستخدم الرسومية ---
st.title("🚀 HAMADA TRACING SYSTEM v3.0")

tab1, tab2 = st.tabs(["🔍 Single Search", "📁 Batch Processing (Excel)"])

# قائمة الجنسيات المختصرة (يمكنك زيادتها)
countries = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines", "Nepal", "Sri Lanka"]

with tab1:
    st.subheader("Individual Inquiry")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", placeholder="A1234567")
    n_in = c2.selectbox("Nationality", countries)
    d_in = c3.text_input("DOB (DD/MM/YYYY)", placeholder="01/01/1990")
    
    if st.button("Start Search"):
        with st.spinner("Extracting data from MOHRE..."):
            res = perform_scraping(p_in, n_in, d_in)
            if isinstance(res, dict):
                st.success("✅ Data Extracted Successfully!")
                st.table(pd.DataFrame([res]))
            else:
                st.error(f"❌ {res}")

with tab2:
    st.subheader("Excel Mass Processing")
    uploaded_file = st.file_uploader("Upload XLSX File", type=["xlsx"])
    
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        st.info(f"Loaded {len(df_input)} records.")
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        start_btn = col_btn1.button("▶️ Start Batch")
        stop_btn = col_btn2.button("🛑 Stop")
        pause_btn = col_btn3.button("⏸️ Pause")
        resume_btn = col_btn4.button("▶️ Resume")

        if stop_btn: st.session_state.stop_process = True
        if pause_btn: st.session_state.is_paused = True
        if resume_btn: st.session_state.is_paused = False

        if start_btn:
            st.session_state.stop_process = False
            results_list = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty()

            for i, row in df_input.iterrows():
                if st.session_state.stop_process:
                    st.warning("Process Stopped by User.")
                    break
                
                while st.session_state.is_paused:
                    status_text.warning(f"Paused at record {i+1}...")
                    time.sleep(1)

                status_text.info(f"Processing {i+1} of {len(df_input)}: {row[0]}")
                
                # تنفيذ المسح
                outcome = perform_scraping(row[0], row[1], row[2])
                
                # تجميع النتيجة
                entry = {"#": i+1, "Passport": row[0], "Status": "Success" if isinstance(outcome, dict) else outcome}
                if isinstance(outcome, dict):
                    entry.update(outcome)
                else:
                    # تعبئة الخانات الفارغة في حال الخطأ
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[col] = outcome
                
                results_list.append(entry)
                
                # تحديث الواجهة
                progress_bar.progress((i + 1) / len(df_input))
                table_placeholder.dataframe(pd.DataFrame(results_list))

            st.success("🏁 Batch Completed!")
            final_df = pd.DataFrame(results_list)
            st.download_button("📥 Download Results", final_df.to_csv(index=False).encode('utf-8'), "MOHRE_Results.csv")
