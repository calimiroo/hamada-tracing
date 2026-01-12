import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# إعدادات الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# إدارة حالة الجلسة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop_process' not in st.session_state: st.session_state.stop_process = False
if 'is_paused' not in st.session_state: st.session_state.is_paused = False

# نظام تسجيل الدخول
if not st.session_state.authenticated:
    st.subheader("Login Required")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# قائمة الجنسيات الكاملة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def perform_scraping(passport, nationality, dob):
    p_str = str(passport).strip()
    # منطق Format Error: بيانات ناقصة أو مسافات في الجواز
    if not p_str or nationality == "Select Nationality" or not str(dob).strip() or " " in p_str:
        return "Format Error"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p_str)
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
    except: return "Not Found"
    finally:
        if driver: driver.quit()

# الواجهة
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.text_input("DOB (DD/MM/YYYY)", key="s_d")
    if st.button("Search", key="s_btn"):
        with st.spinner("Searching..."):
            res = perform_scraping(p_in, n_in, d_in)
            if isinstance(res, dict): st.table(pd.DataFrame([res]))
            else: st.error(f"Result: {res}")

with tab2:
    up_file = st.file_uploader("Upload Excel", type=["xlsx"])
    if up_file:
        df_full = pd.read_excel(up_file)
        st.write(f"📊 **Total Records:** {len(df_full)}")
        
        # ميزة عرض 10 سجلات في الصفحة لمعاينة البيانات
        rows_per_page = 10
        pages = (len(df_full) // rows_per_page) + (1 if len(df_full) % rows_per_page > 0 else 0)
        curr_page = st.selectbox("Preview Page (10 records/page)", range(1, pages + 1)) - 1
        st.table(df_full.iloc[curr_page * rows_per_page : (curr_page + 1) * rows_per_page])

        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🚀 Start Search"):
            st.session_state.stop_process = False
            results = []
            pb = st.progress(0)
            status = st.empty()
            table_hold = st.empty()
            start_time = time.time()

            for i, row in df_full.iterrows():
                if st.session_state.stop_process: break
                while st.session_state.is_paused:
                    status.warning(f"Paused at record {i+1}...")
                    time.sleep(1)

                # تنفيذ البحث
                res = perform_scraping(row[0], row[1], row[2])
                
                # بناء السجل النهائي (إلحاق جميع العملاء)
                entry = {"#": i + 1, "Passport": row[0], "Nationality": row[1], "DOB": row[2]}
                if isinstance(res, dict):
                    entry.update(res)
                else:
                    # تعبئة الحقول بكلمة Not Found أو Format Error
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[col] = res
                
                results.append(entry)
                pb.progress((i + 1) / len(df_full))
                status.info(f"Progress: {i+1}/{len(df_full)} | Time: {round(time.time()-start_time,1)}s")
                table_hold.dataframe(pd.DataFrame(results))

            st.success("✅ Completed.")
            st.download_button("Download CSV", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")

        if c2.button("🛑 STOP"): st.session_state.stop_process = True
        if c3.button("⏸️ PAUSE"): st.session_state.is_paused = True
        if c4.button("▶️ RESUME"): st.session_state.is_paused = False
