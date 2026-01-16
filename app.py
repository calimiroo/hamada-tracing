import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal - Pro", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'last_index' not in st.session_state:
    st.session_state['last_index'] = 0
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'df_ready' not in st.session_state:
    st.session_state['df_ready'] = None

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_form"):
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login") and pwd_input == "Bilkish":
            st.session_state['authenticated'] = True
            st.rerun()
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

def color_status(val):
    if val == 'Found': return 'background-color: #90EE90'
    if val == 'Not Found': return 'background-color: #FFCCCB'
    return ''

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # مسار مؤقت فريد لتجنب OSError
    user_data_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_data_dir}")
    try:
        return uc.Chrome(options=options, headless=True, use_subprocess=False)
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def extract_data_logic(driver, passport, nationality, dob_str):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
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
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def gv(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'

        c_num = gv("Card Number")
        if c_num == 'Not Found': return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(gv("Job Description")),
            "Card Number": c_num, "Card Issue": gv("Card Issue"), "Card Expiry": gv("Card Expiry"), 
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None

# --- واجهة المستخدم ---
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines", "Jordan", "Syria"]

tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            drv = get_driver()
            with st.spinner("Searching..."):
                res = extract_data_logic(drv, p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res: st.table(pd.DataFrame([res]))
                else: st.error("No data found.")
            if drv: drv.quit()

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        if st.session_state.df_ready is None:
            st.session_state.df_ready = pd.read_excel(uploaded_file)
        
        if st.button("🪄 Force Excel Dates Format (dd/mm/yyyy)"):
            try:
                st.session_state.df_ready['Date of Birth'] = pd.to_datetime(st.session_state.df_ready['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("All dates formatted!")
            except: st.error("Check 'Date of Birth' column name.")

        st.dataframe(st.session_state.df_ready, height=150)

        col1, col2, col3 = st.columns(3)
        if col1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if not st.session_state.start_time_ref: st.session_state.start_time_ref = time.time()
        if col2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if col3.button("⏹️ Reset"):
            st.session_state.update({'run_state': 'stopped', 'batch_results': [], 'last_index': 0, 'start_time_ref': None, 'df_ready': None})
            st.rerun()

        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            live_table = st.empty()
            
            driver = get_driver()
            df_proc = st.session_state.df_ready
            
            for i in range(st.session_state.last_index, len(df_proc)):
                while st.session_state.run_state == 'paused':
                    status_text.warning("Paused...")
                    time.sleep(1)
                if st.session_state.run_state == 'stopped': break
                
                row = df_proc.iloc[i]
                res = extract_data_logic(driver, str(row.get('Passport Number', '')).strip(), str(row.get('Nationality', 'Egypt')).strip(), str(row.get('Date of Birth', '')))
                
                if res: st.session_state.batch_results.append(res)
                else: st.session_state.batch_results.append({"Passport Number": row.get('Passport Number'), "Status": "Not Found"})
                
                st.session_state.last_index = i + 1
                if (i + 1) % 40 == 0: # تدوير المتصفح كل 40 اسم
                    driver.quit()
                    driver = get_driver()

                elapsed = time.time() - st.session_state.start_time_ref
                progress_bar.progress((i + 1) / len(df_proc))
                stats_area.markdown(f"✅ **Processed:** {i+1} | ⏱️ **Timer:** `{format_time(elapsed)}`")
                live_table.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']))

            if driver: driver.quit()
