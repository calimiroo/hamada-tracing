import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# نظام أمان للمكتبات
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# إعداد الصفحة وإخفاء شريط الأدوات العلوي
st.set_page_config(page_title="MOHRE Portal", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# --- إدارة حالة الجلسة ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'stop_process' not in st.session_state:
    st.session_state['stop_process'] = False
if 'is_paused' not in st.session_state:
    st.session_state['is_paused'] = False
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

# --- نظام تسجيل الدخول ---
if not st.session_state['authenticated']:
    st.subheader("Login Required")
    pwd_input = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd_input == "Hamada":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("❌ Incorrect Password.")
    st.stop()

# --- الهيدر وزر تسجيل الخروج ---
col_title, col_logout = st.columns([0.8, 0.2])
with col_title:
    st.title("HAMADA TRACING SITE TEST")
with col_logout:
    if st.button("🔴 Log Out", use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def safe_translate(text):
    if not text or text in ["Not Found", "Wrong Format"] or not HAS_TRANSLATOR: return text
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='ar', target='en').translate(text)
    except: pass
    return text

def perform_scraping(passport, nationality, dob):
    if not passport or not nationality or nationality == "Select Nationality" or not dob:
        return "Wrong Format"
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(passport))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(1.5)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Not Found"
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(dob))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        def get_v(label_text):
            try:
                xpath = f"//*[contains(text(), '{label_text}')]/following-sibling::span | //*[contains(text(), '{label_text}')]/parent::div/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else "Not Found"
            except: return "Not Found"

        job = get_v("Job Description")
        if job == "Not Found": return "Not Found"
        return {
            "Job Description": safe_translate(job),
            "Card Number": get_v("Card Number"),
            "Contract Start": get_v("Contract Start"),
            "Contract End": get_v("Contract End"),
            "Basic Salary": get_v("Basic Salary"),
            "Total Salary": get_v("Total Salary")
        }
    except: return "Not Found"
    finally: driver.quit()

# --- الواجهة ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p1_single")
    n_in = c2.selectbox("Nationality", countries_list, key="n1_single")
    d_in = c3.text_input("Date of Birth (DD/MM/YYYY)", key="d1_single")
    if st.button("Start Search", key="btn_single"):
        start_t = time.time()
        with st.spinner("Searching..."):
            res = perform_scraping(p_in, n_in, d_in)
            elapsed = round(time.time() - start_t, 2)
            if isinstance(res, dict):
                st.success(f"✅ Success! | ⏱️ Time: {elapsed}s")
                full = {"Passport": p_in, "Nationality": n_in, "DOB": d_in}
                full.update(res)
                st.table(pd.DataFrame([full]))
            else: st.error(f"❌ Result: {res} | ⏱️ Time: {elapsed}s")

with tab2:
    st.subheader("Batch Excel Processing")
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="batch_file")
    
    if up_file:
        df_orig = pd.read_excel(up_file)
        total_rows = len(df_orig)
        st.write(f"📊 **Total records in file:** {total_rows}")

        # --- ميزة تقسيم المعاينة (10 لكل صفحة) ---
        st.write("### 📄 Preview (10 per page)")
        num_pages = (total_rows // 10) + (1 if total_rows % 10 > 0 else 0)
        page = st.selectbox("Select Page", range(1, num_pages + 1)) - 1
        start_idx = page * 10
        end_idx = min(start_idx + 10, total_rows)
        
        df_display = df_orig.iloc[start_idx:end_idx].copy()
        df_display.index = range(start_idx + 1, end_idx + 1)
        st.table(df_display)

        # --- أزرار التحكم في البحث ---
        st.write("---")
        ctrl_cols = st.columns(4)
        start_btn = ctrl_cols[0].button("🚀 Start Batch Search", use_container_width=True)
        stop_btn = ctrl_cols[1].button("🛑 STOP", use_container_width=True)
        pause_btn = ctrl_cols[2].button("⏸️ Pause", use_container_width=True)
        resume_btn = ctrl_cols[3].button("▶️ Resume", use_container_width=True)

        if stop_btn: st.session_state.stop_process = True
        if pause_btn: st.session_state.is_paused = True
        if resume_btn: st.session_state.is_paused = False

        status_text = st.empty()
        pb = st.progress(0)
        table_placeholder = st.empty()

        if start_btn:
            st.session_state.stop_process = False
            st.session_state.is_paused = False
            final_list = []
            start_batch_t = time.time()
            
            for i, row in df_orig.iterrows():
                if st.session_state.stop_process:
                    st.warning("⚠️ Process Stopped.")
                    break
                
                while st.session_state.is_paused:
                    status_text.info(f"⏸️ Paused at record {i+1}. Waiting for Resume...")
                    time.sleep(1)
                    if st.session_state.stop_process: break
                
                if st.session_state.stop_process: break

                p_val, n_val, d_val = str(row[0]), str(row[1]), str(row[2])
                res = perform_scraping(p_val, n_val, d_val)
                
                record = {"#": i + 1, "Passport": p_val, "Nationality": n_val, "DOB": d_val}
                if isinstance(res, dict):
                    record.update(res)
                else:
                    err = res if res else "Not Found"
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        record[col] = err
                
                final_list.append(record)
                elapsed = round(time.time() - start_batch_t, 1)
                pb.progress((i + 1) / total_rows)
                status_text.markdown(f"### 🔍 Searching: {i+1}/{total_rows} | ⏱️ Timer: {elapsed}s")
                
                # تحديث الجدول حياً (إظهار آخر 10 نتائج فقط للمتصفح لتسريع الأداء)
                table_placeholder.dataframe(pd.DataFrame(final_list), use_container_width=True, hide_index=True)

            if final_list:
                st.success("Batch task complete.")
                csv_data = pd.DataFrame(final_list).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Full Results (CSV)", csv_data, "MOHRE_Full_Results.csv")
