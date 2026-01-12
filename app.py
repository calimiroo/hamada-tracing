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

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- إدارة حالة الجلسة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'stop_process' not in st.session_state:
    st.session_state['stop_process'] = False
if 'is_paused' not in st.session_state:
    st.session_state['is_paused'] = False

# --- نظام تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.container():
        st.subheader("Login Required")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd_input == "Hamada":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password.")
    st.stop()

# --- الهيدر: العنوان وزر تسجيل الخروج ---
col_title, col_logout = st.columns([0.85, 0.15])
with col_title:
    st.title("HAMADA TRACING SITE TEST")
with col_logout:
    if st.button("🔴 Log Out", use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def safe_translate(text):
    if not text or text in ["Not Found", "Format Error"] or not HAS_TRANSLATOR: return text
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='ar', target='en').translate(text)
    except: pass
    return text

def perform_scraping(passport, nationality, dob):
    # فحص المسافات أو البيانات الفارغة التي تعطل البحث
    if not passport or not nationality or nationality == "Select Nationality" or not dob or " " in str(passport):
        return "Format Error"

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
        if items: 
            items[0].click()
        else:
            return "Not Found"

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
    if st.button("🗑️ Clear Inputs", key="clr_s"): st.rerun()
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="ps_1")
    n_in = col2.selectbox("Nationality", countries_list, key="na_1")
    d_in = col3.text_input("Date of Birth (DD/MM/YYYY)", key="db_1")

    if st.button("Start Search", key="run_s"):
        if p_in and d_in:
            start_single = time.time()
            with st.spinner("Searching..."):
                res = perform_scraping(p_in, n_in, d_in)
                elapsed = round(time.time() - start_single, 2)
                if isinstance(res, dict):
                    st.success(f"✅ Success! | ⏱️ Time: {elapsed}s")
                    full_res = {"Passport": p_in, "Nationality": n_in, "DOB": d_in}
                    full_res.update(res)
                    st.table(pd.DataFrame([full_res]))
                else: 
                    st.error(f"❌ Result: {res} | ⏱️ Time: {elapsed}s")

with tab2:
    st.subheader("Batch Excel Processing")
    if st.button("🗑️ Reset Batch", key="clr_b"): st.rerun()
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if up_file:
        df_preview = pd.read_excel(up_file)
        total_records = len(df_preview)
        
        # --- إضافة ميزة عرض 10 في كل صفحة ---
        st.write(f"📊 **Total records in file:** {total_records}")
        rows_per_page = 10
        num_pages = (total_records // rows_per_page) + (1 if total_records % rows_per_page > 0 else 0)
        
        page_num = st.selectbox("Select Page to Preview", range(1, num_pages + 1)) - 1
        start_idx = page_num * rows_per_page
        end_idx = min(start_idx + rows_per_page, total_records)
        
        st.table(df_preview.iloc[start_idx:end_idx])
        
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        start_btn = c1.button("🚀 Start Search", use_container_width=True)
        stop_btn = c2.button("🛑 STOP", use_container_width=True)
        pause_btn = c3.button("⏸️ Pause", use_container_width=True)
        resume_btn = c4.button("▶️ Resume", use_container_width=True)

        if stop_btn: st.session_state.stop_process = True
        if pause_btn: st.session_state.is_paused = True
        if resume_btn: st.session_state.is_paused = False

        if start_btn:
            st.session_state.stop_process = False
            st.session_state.is_paused = False
            final_results = []
            found_count = 0
            start_batch = time.time()
            
            pb = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty()
            
            for i, row in df_preview.iterrows():
                if st.session_state.stop_process:
                    st.warning("⚠️ Process Stopped.")
                    break
                
                while st.session_state.is_paused:
                    status_text.info(f"⏸️ Search Paused at record {i+1}. Waiting for Resume...")
                    time.sleep(1)
                    if st.session_state.stop_process: break
                
                if st.session_state.stop_process: break

                p_val, n_val, d_val = str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip()
                
                # استدعاء البحث
                res = perform_scraping(p_val, n_val, d_val)
                
                # بناء السطر لكل عميل (سواء نجح أو فشل)
                data_row = {
                    "#": i + 1,
                    "Passport": p_val,
                    "Nationality": n_val,
                    "DOB": d_val
                }
                
                if isinstance(res, dict):
                    found_count += 1
                    data_row.update(res)
                else:
                    # في حال فشل البحث نضع الحالة المطلوبة في جميع الأعمدة
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        data_row[col] = res
                
                final_results.append(data_row)
                
                elapsed = round(time.time() - start_batch, 1)
                pb.progress((i + 1) / total_records)
                status_text.markdown(f"### 🔍 Searching: {i+1}/{total_records} | ✅ Found: {found_count} | ⏱️ Timer: {elapsed}s")
                
                # عرض النتائج المتراكمة أولاً بأول
                table_placeholder.dataframe(pd.DataFrame(final_results), use_container_width=True, hide_index=True)

            if final_results:
                st.success("✅ Batch processing completed.")
                csv_data = pd.DataFrame(final_results).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download ALL Results (CSV)", csv_data, "MOHRE_Full_Results.csv", use_container_width=True)
