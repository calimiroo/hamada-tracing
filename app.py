import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# إعداد الصفحة وإخفاء العناصر غير الضرورية
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stAppDeployButton {display:none;}</style>", unsafe_allow_html=True)

# --- إدارة حالة الجلسة (Session State) ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop_process' not in st.session_state: st.session_state.stop_process = False
if 'is_paused' not in st.session_state: st.session_state.is_paused = False
if 'batch_results' not in st.session_state: st.session_state.batch_results = []

# --- نظام تسجيل الدخول ---
if not st.session_state.authenticated:
    st.subheader("🔒 Login Required")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Incorrect Password")
    st.stop()

# --- الهيدر العلوي ---
col_head, col_out = st.columns([0.8, 0.2])
col_head.title("HAMADA TRACING SITE TEST")
if col_out.button("🔴 Log Out", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# --- قائمة الجنسيات الكاملة ---
countries = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def perform_scraping(passport, nationality, dob):
    if not passport or not nationality or nationality == "Select Nationality" or not dob: return "Wrong Format"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(passport))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(1)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Not Found"
        
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(dob))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        def get_v(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span | //*[contains(text(), '{label}')]/parent::div/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else "Not Found"
            except: return "Not Found"

        job = get_v("Job Description")
        if job == "Not Found": return "Not Found"
        
        return {
            "Job Description": job, "Card Number": get_v("Card Number"),
            "Contract Start": get_v("Contract Start"), "Contract End": get_v("Contract End"),
            "Basic Salary": get_v("Basic Salary"), "Total Salary": get_v("Total Salary")
        }
    except Exception: return "Not Found"
    finally:
        try: driver.quit()
        except: pass

# --- الواجهة ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    with st.form("single_form"):
        c1, c2, c3 = st.columns(3)
        p_in = c1.text_input("Passport Number")
        n_in = c2.selectbox("Nationality", countries)
        d_in = c3.text_input("DOB (DD/MM/YYYY)") # تاريخ ميلاد مفتوح
        submit = st.form_submit_button("Start Search")
    
    if submit:
        start_t = time.time()
        with st.spinner("Searching..."):
            res = perform_scraping(p_in, n_in, d_in)
            if isinstance(res, dict):
                st.success(f"✅ Found! | Time: {round(time.time()-start_t, 2)}s")
                st.table(pd.DataFrame([{"Passport":p_in, "Nationality":n_in, "DOB":d_in, **res}]))
            else: st.error(f"❌ Result: {res}")

with tab2:
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="main_uploader")
    if up_file:
        df_orig = pd.read_excel(up_file)
        total = len(df_orig)
        
        # --- تقسيم عرض الإكسل المرفوع (10 سجلات في الصفحة) ---
        st.write(f"📊 **Total Records: {total}**")
        rows_per_page = 10
        num_pages = (total // rows_per_page) + (1 if total % rows_per_page > 0 else 0)
        page = st.number_input("Page Viewer (10 records/page)", min_value=1, max_value=num_pages, step=1) - 1
        st.table(df_orig.iloc[page*rows_per_page : (page+1)*rows_per_page])

        st.divider()
        # أزرار التحكم
        c1, c2, c3, c4 = st.columns(4)
        run_btn = c1.button("🚀 START", use_container_width=True)
        stop_btn = c2.button("🛑 STOP", use_container_width=True)
        pause_btn = c3.button("⏸️ PAUSE", use_container_width=True)
        resum_btn = c4.button("▶️ RESUME", use_container_width=True)

        if stop_btn: st.session_state.stop_process = True
        if pause_btn: st.session_state.is_paused = True
        if resum_btn: st.session_state.is_paused = False

        status_box = st.empty()
        pb = st.progress(0)
        table_box = st.empty()

        if run_btn:
            st.session_state.stop_process = False
            st.session_state.is_paused = False
            st.session_state.batch_results = []
            start_batch_t = time.time()
            
            for i, row in df_orig.iterrows():
                if st.session_state.stop_process: break
                while st.session_state.is_paused:
                    status_box.info(f"⏸️ Paused at record {i+1}...")
                    time.sleep(1)
                    if st.session_state.stop_process: break
                if st.session_state.stop_process: break

                p, n, d = str(row[0]), str(row[1]), str(row[2])
                res = perform_scraping(p, n, d)
                
                # بناء السجل (دائماً يظهر السجل لضمان شمولية الإكسل المستخرج)
                entry = {"#": i+1, "Passport": p, "Nationality": n, "DOB": d}
                if isinstance(res, dict): entry.update(res)
                else:
                    err_val = res if res else "Not Found"
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[col] = err_val
                
                st.session_state.batch_results.append(entry)
                
                elapsed = round(time.time() - start_batch_t, 1)
                pb.progress((i+1)/total)
                status_box.markdown(f"### 🔍 Searching: {i+1}/{total} | ⏱️ Timer: {elapsed}s")
                table_box.dataframe(pd.DataFrame(st.session_state.batch_results), use_container_width=True, hide_index=True)

            st.success("✅ Process Complete.")
            final_df = pd.DataFrame(st.session_state.batch_results)
            st.download_button("📥 Download Full Results (Excel/CSV)", final_df.to_csv(index=False).encode('utf-8'), "Full_Results.csv", use_container_width=True)
