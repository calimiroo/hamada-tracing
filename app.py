import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
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

# قائمة الجنسيات المختصرة (للعرض)
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines", "Jordan", "Syria"] # يمكن استبدالها بالقائمة الكاملة

# --- وظائف المساعدة ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
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
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
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
    finally: driver.quit()

# --- واجهة المستخدم ---
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
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res: st.table(pd.DataFrame([res]))
                else: st.error("No data found.")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        if st.session_state.df_ready is None:
            st.session_state.df_ready = pd.read_excel(uploaded_file)
        
        # --- زر الفورمات الإجمالي لملف الإكسل ---
        if st.button("🪄 Force Excel Dates Format (dd/mm/yyyy)"):
            try:
                # تحويل عمود التاريخ في الملف بالكامل
                st.session_state.df_ready['Date of Birth'] = pd.to_datetime(st.session_state.df_ready['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("All dates in Excel have been formatted to dd/mm/yyyy!")
            except Exception as e:
                st.error(f"Error formatting dates: {e}")

        st.write(f"Total records: {len(st.session_state.df_ready)}")
        st.dataframe(st.session_state.df_ready, height=150)

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
            st.session_state.df_ready = None
            st.rerun()

        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            live_table_area = st.empty()
            
            actual_success = 0
            df_to_process = st.session_state.df_ready
            
            for i, row in df_to_process.iterrows():
                while st.session_state.run_state == 'paused':
                    status_text.warning("Paused... click Resume to continue.")
                    time.sleep(1)
                
                if st.session_state.run_state == 'stopped': break
                
                if i < len(st.session_state.batch_results):
                    if st.session_state.batch_results[i].get("Status") == "Found": actual_success += 1
                    continue

                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                dob = str(row.get('Date of Birth', ''))

                status_text.info(f"Processing {i+1}/{len(df_to_process)}: {p_num}")
                res = extract_data(p_num, nat, dob)
                
                if res:
                    actual_success += 1
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                        "Job Description": "N/A", "Card Number": "N/A", "Status": "Not Found"
                    })

                elapsed_seconds = time.time() - st.session_state.start_time_ref
                progress_bar.progress((i + 1) / len(df_to_process))
                stats_area.markdown(f"✅ **Actual Success:** {actual_success} | ⏱️ **Total Time:** `{format_time(elapsed_seconds)}`")
                
                current_df = pd.DataFrame(st.session_state.batch_results)
                live_table_area.dataframe(current_df.style.map(color_status, subset=['Status']), use_container_width=True)

            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df_to_process):
                st.success("Batch Completed!")
                st.download_button("Download CSV", pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'), "results.csv")
