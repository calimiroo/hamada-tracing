import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- حل مشكلة نقص distutils لضمان عمل المتصفح في Python 3.13 ---
try:
    import distutils.version
except ImportError:
    import sys
    from packaging import version
    import types
    m = types.ModuleType('distutils')
    sys.modules['distutils'] = m
    m.version = types.ModuleType('distutils.version')
    sys.modules['distutils.version'] = m.version
    m.version.LooseVersion = version.parse

# استيراد المكتبات المطلوبة (تأكد من تثبيت streamlit-aggrid في requirements.txt)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
except ImportError:
    st.error("مكتبة st-aggrid غير مثبتة. يرجى إضافتها لملف requirements.txt")
    st.stop()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal Pro", layout="wide")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'df_main' not in st.session_state:
    st.session_state['df_main'] = None
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'

# --- قائمة الجنسيات كاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.title("⚙️ خيارات التنسيق")
    if st.button("🪄 Format Date (dd/mm/yyyy)"):
        if st.session_state.df_main is not None:
            try:
                st.session_state.df_main['Date of Birth'] = pd.to_datetime(st.session_state.df_main['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("تم تنسيق التواريخ!")
                st.rerun()
            except: st.error("خطأ: تأكد من عمود Date of Birth")
        else: st.warning("ارفع ملف أولاً")
    st.markdown("---")

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_section"): # تم تسمية الفورم لضمان عدم التداخل
        st.subheader("Protected Access")
        pwd = st.text_input("Enter Password", type="password")
        submit_pwd = st.form_submit_button("Login") # الزر الإلزامي للفورم
        if submit_pwd:
            if pwd == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Wrong Password")
    st.stop()

# --- وظائف الاستخراج ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"--user-data-dir=/tmp/chrome_{int(time.time())}")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def extract_data(driver, passport, nationality, dob):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_in = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_in)
        dob_in.clear()
        dob_in.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_in)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(10)
        
        def gv(lbl):
            try:
                xp = f"//span[contains(text(), '{lbl}')]/following::span[1] | //label[contains(text(), '{lbl}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except: return 'Not Found'

        return {
            "Passport Number": passport, "Card Number": gv("Card Number"), 
            "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None

# --- واجهة التبويبات ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    with st.form("single_search_form"): # إضافة فورم كامل لحل مشكلة الزر
        c1, c2, c3 = st.columns(3)
        p_in = c1.text_input("Passport Number")
        n_in = c2.selectbox("Nationality", countries_list)
        d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1))
        submit_single = st.form_submit_button("Search Now") # الزر الإلزامي للفورم

        if submit_single:
            if p_in and n_in != "Select Nationality" and d_in:
                with st.spinner("Searching..."):
                    dr = get_driver()
                    res = extract_data(dr, p_in, n_in, d_in.strftime("%d/%m/%Y"))
                    dr.quit()
                    if res: st.table(pd.DataFrame([res]))
                    else: st.error("No data found.")

with tab2:
    uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
    if uploaded:
        if st.session_state.df_main is None:
            st.session_state.df_main = pd.read_excel(uploaded)
        
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df_main)
        gb.configure_pagination(paginationPageSize=10)
        gb.configure_side_bar() # تفعيل المينو الجانبي المطلوب
        grid_opt = gb.build()

        st.info("Right-click inside table for context menu.")
        grid_resp = AgGrid(st.session_state.df_main, gridOptions=grid_opt, theme='alpine', height=350)
        st.session_state.df_main = grid_resp['data']

        if st.button("▶️ Start Batch Search"):
            st.session_state.run_state = 'running'
            st.write("Processing...")
            # هنا تضع حلقة البحث...
