import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# إدارة الحالة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop_process' not in st.session_state: st.session_state.stop_process = False
if 'is_paused' not in st.session_state: st.session_state.is_paused = False

# تسجيل الدخول
if not st.session_state.authenticated:
    st.subheader("Login Required")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# قائمة الجنسيات
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)

def perform_scraping(p, n, d):
    p_str = str(p).strip()
    if not p_str or n == "Select Nationality" or not str(d).strip() or " " in p_str:
        return "Format Error"
    
    driver = None
    try:
        driver = get_driver()
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p_str)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(n))
        time.sleep(1.5)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Not Found"
        
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(d))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span | //*[contains(text(), '{label}')]/parent::div/following-sibling::div"
                v = driver.find_element(By.XPATH, xpath).text.strip()
                return v if v else "Not Found"
            except: return "Not Found"

        job = gv("Job Description")
        if job == "Not Found": return "Not Found"
        return {"Job Description": job, "Card Number": gv("Card Number"), "Contract Start": gv("Contract Start"), "Contract End": gv("Contract End"), "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary")}
    except: return "Not Found"
    finally:
        if driver: driver.quit()

# الواجهة
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p1")
    n_in = c2.selectbox("Nationality", countries_list, key="n1")
    d_in = c3.text_input("DOB (DD/MM/YYYY)", key="d1")
    if st.button("Search"):
        with st.spinner("Searching..."):
            res = perform_scraping(p_in, n_in, d_in)
            if isinstance(res, dict): st.table(pd.DataFrame([res]))
            else: st.error(f"Result: {res}")

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df = pd.read_excel(f)
        st.write(f"Total Records: {len(df)}")
        # عرض 10 سجلات
        pg = st.number_input("Page (10 per page)", 1, (len(df)//10)+1, 1) - 1
        st.table(df.iloc[pg*10 : (pg+1)*10])
        
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🚀 Start Process"):
            st.session_state.stop_process = False
            results = []
            pb = st.progress(0)
            status = st.empty()
            table_hold = st.empty()
            start = time.time()
            for i, row in df.iterrows():
                if st.session_state.stop_process: break
                while st.session_state.is_paused:
                    status.warning("Paused...")
                    time.sleep(1)
                
                res = perform_scraping(row[0], row[1], row[2])
                entry = {"#": i+1, "Passport": row[0], "Nationality": row[1], "DOB": row[2]}
                if isinstance(res, dict): entry.update(res)
                else:
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[col] = res
                results.append(entry)
                pb.progress((i+1)/len(df))
                status.info(f"Progress: {i+1}/{len(df)} | Time: {round(time.time()-start,1)}s")
                table_hold.dataframe(pd.DataFrame(results))
            
            st.success("Task Completed.")
            st.download_button("Download CSV", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")

        if c2.button("🛑 STOP"): st.session_state.stop_process = True
        if c3.button("⏸️ PAUSE"): st.session_state.is_paused = True
        if c4.button("▶️ RESUME"): st.session_state.is_paused = False
