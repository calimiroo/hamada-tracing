import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from deep_translator import GoogleTranslator
import re

# --- 1. إعداد الصفحة والتصميم (UI) ---
st.set_page_config(page_title="MOHRE Tracer", layout="wide")

# تخصيص الألوان باستخدام CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .found-row { background-color: #d4edda !important; } /* أخضر فاتح */
    .notfound-row { background-color: #f8d7da !important; } /* أحمر فاتح */
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ HAMADA TRACING - PROFESSIONAL MODE")

# --- 2. إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []

# قائمة الجنسيات الكاملة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Mauritania", "Mauritius", "Mexico", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "Norway", "Oman", "Pakistan", "Palestine", "Panama", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Somalia", "South Africa", "South Korea", "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- 3. نظام الألوان (Styling Function) ---
def style_dataframe(df):
    def apply_color(row):
        if row['Status'] == 'Found':
            return ['background-color: #d4edda'] * len(row) # أخضر فاتح
        return ['background-color: #f8d7da'] * len(row)    # أحمر فاتح
    return df.style.apply(apply_color, axis=1)

# --- 4. وظيفة المتصفح (Cloud Compatible) ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options, headless=True, use_subprocess=True)
    return driver

# --- 5. منطق البحث الاستخراجي ---
def extract_data(passport, nationality, dob_str):
    driver = None
    try:
        driver = get_driver()
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        
        wait = WebDriverWait(driver, 15)
        # إدخال البيانات
        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(5)
        
        # قراءة النتائج
        def get_val(label):
            try:
                path = f"//span[contains(text(), '{label}')]/following::span[1]"
                return driver.find_element(By.XPATH, path).text.strip()
            except: return "N/A"

        card = get_val("Card Number")
        if card == "N/A": return None

        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Card Number": card,
            "Job Description": get_val("Job Description"),
            "Total Salary": get_val("Total Salary"),
            "Status": "Found"
        }
    except: return None
    finally:
        if driver: driver.quit()

# --- 6. تسجيل الدخول والواجهة ---
if not st.session_state.authenticated:
    with st.form("login"):
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login") and pwd == "Bilkish":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

tab1, tab2 = st.tabs(["البحث الفردي", "رفع ملف Excel"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_num = c1.text_input("رقم الجواز")
    p_nat = c2.selectbox("الجنسية", countries_list)
    p_dob = c3.date_input("تاريخ الميلاد", value=None)
    
    if st.button("بحث الآن", type="primary"):
        if p_num and p_dob and p_nat != "Select Nationality":
            with st.spinner("جاري البحث..."):
                res = extract_data(p_num, p_nat, p_dob.strftime("%d/%m/%Y"))
                if res:
                    st.success("تم العثور على البيانات")
                    st.table(style_dataframe(pd.DataFrame([res])))
                else:
                    st.error("لم يتم العثور على بيانات")

with tab2:
    file = st.file_uploader("ارفع ملف الإكسيل", type=["xlsx"])
    if file:
        df_input = pd.read_excel(file)
        if st.button("▶️ بدء المعالجة الجماعية"):
            st.session_state.batch_results = []
            bar = st.progress(0)
            status = st.empty()
            
            for i, row in df_input.iterrows():
                p = str(row.get('Passport Number', ''))
                n = str(row.get('Nationality', ''))
                # معالجة التاريخ الذكية
                d_raw = row.get('Date of Birth')
                d = pd.to_datetime(d_raw).strftime('%d/%m/%Y') if not isinstance(d_raw, str) else d_raw
                
                status.text(f"جاري فحص: {p}")
                res = extract_data(p, n, d)
                
                if res:
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": p, "Nationality": n, "Date of Birth": d, 
                        "Status": "Not Found", "Card Number": "N/A", "Job Description": "N/A", "Total Salary": "N/A"
                    })
                bar.progress((i+1)/len(df_input))
            
            final_df = pd.DataFrame(st.session_state.batch_results)
            st.dataframe(style_dataframe(final_df), use_container_width=True)
            
            # زر التحميل
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 تحميل النتائج كـ CSV", csv, "results.csv", "text/csv")
