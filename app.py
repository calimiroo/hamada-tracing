import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- حل مشكلة نقص distutils في Python 3.13 لضمان عمل المتصفح ---
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

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal Pro", layout="wide")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'df_main' not in st.session_state:
    st.session_state['df_main'] = None

# --- قائمة الجنسيات كاملة بدون اختصار ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- القائمة الجانبية (Sidebar) مع زر التنسيق المطلوب ---
with st.sidebar:
    st.title("⚙️ التحكم والأدوات")
    st.markdown("---")
    
    # زر تنسيق التاريخ الأنيق
    if st.button("🪄 Format Date (dd/mm/yyyy)"):
        if st.session_state.df_main is not None:
            try:
                # محاولة تحويل العمود لتنسيق تاريخ يوم/شهر/سنة
                st.session_state.df_main['Date of Birth'] = pd.to_datetime(st.session_state.df_main['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("✅ تم توحيد تنسيق التواريخ في الجدول")
                st.rerun()
            except Exception as e:
                st.error("❌ فشل التنسيق: تأكد من وجود عمود 'Date of Birth'")
        else:
            st.warning("⚠️ يرجى رفع ملف Excel أولاً!")

    st.markdown("---")
    st.caption("Developed for HAMADA SITE v2.0")

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# --- وظائف المساعدة ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

# دالة المتصفح (تمنع خطأ OSError 24 عن طريق تنظيف المسارات)
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # مسار فريد لتحرير الملفات المفتوحة في النظام
    user_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_dir}")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

def extract_data(driver, passport, nationality, dob_str):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(2)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(10)

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        card_num = get_value("Card Number")
        if card_num == 'Not Found': return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"), 
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"),
            "Status": "Found"
        }
    except: return None

# --- واجهة المستخدم الرئيسية ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                driver = get_driver()
                res = extract_data(driver, p_in, n_in, d_in.strftime("%d/%m/%Y"))
                driver.quit()
                if res: st.table(pd.DataFrame([res]))
                else: st.error("No data found.")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        if st.session_state.df_main is None:
            st.session_state.df_main = pd.read_excel(uploaded_file)
        
        st.write(f"Total records: {len(st.session_state.df_main)}")

        # --- إعداد AgGrid لتفعيل المينو والتحكم بالجدول ---
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df_main)
        gb.configure_pagination(paginationPageSize=10)
        gb.configure_side_bar() # تفعيل القائمة الجانبية المتقدمة للجدول
        gb.configure_default_column(editable=True, groupable=True, filter=True)
        grid_opt = gb.build()

        st.info("💡 يمكنك الضغط بالزر الأيمن أو استخدام القائمة الجانبية للجدول للتحكم بالأعمدة.")
        grid_resp = AgGrid(
            st.session_state.df_main,
            gridOptions=grid_opt,
            theme='alpine',
            height=350,
            update_mode=GridUpdateMode.MODEL_CHANGED
        )
        st.session_state.df_main = grid_resp['data']

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None:
                st.session_state.start_time_ref = time.time()
        
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
        
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.rerun()

        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            live_table_area = st.empty()
            
            actual_success = 0
            
            # تشغيل المتصفح الأول
            driver = get_driver()
            
            for i, row in st.session_state.df_main.iterrows():
                # تدوير المتصفح كل 15 اسم لمنع تعليق الذاكرة (OSError 24)
                if i > 0 and i % 15 == 0:
                    driver.quit()
                    driver = get_driver()

                while st.session_state.run_state == 'paused':
                    status_text.warning("Paused... click Resume to continue.")
                    time.sleep(1)
                
                if st.session_state.run_state == 'stopped':
                    break
                
                # تخطي ما تمت معالجته
                if i < len(st.session_state.batch_results):
                    if st.session_state.batch_results[i].get("Status") == "Found":
                        actual_success += 1
                    continue

                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                dob = str(row.get('Date of Birth', ''))

                status_text.info(f"Processing {i+1}/{len(st.session_state.df_main)}: {p_num}")
                res = extract_data(driver, p_num, nat, dob)
                
                if res:
                    actual_success += 1
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                        "Job Description": "N/A", "Card Number": "N/A", "Card Issue": "N/A",
                        "Card Expiry": "N/A", "Basic Salary": "N/A", "Total Salary": "N/A",
                        "Status": "Not Found"
                    })

                elapsed = time.time() - st.session_state.start_time_ref
                progress_bar.progress((i + 1) / len(st.session_state.df_main))
                stats_area.markdown(f"✅ **Success:** {actual_success} | ⏱️ **Time:** `{format_time(elapsed)}`")
                
                current_df = pd.DataFrame(st.session_state.batch_results)
                live_table_area.dataframe(current_df.style.map(color_status, subset=['Status']), use_container_width=True)

            driver.quit()
            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(st.session_state.df_main):
                st.success("Batch Completed!")
                final_df = pd.DataFrame(st.session_state.batch_results)
                st.download_button("Download Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "results.csv")
