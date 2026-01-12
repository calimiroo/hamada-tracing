import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# إدارة الحالة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'batch_results' not in st.session_state: st.session_state.batch_results = []
if 'is_paused' not in st.session_state: st.session_state.is_paused = False
if 'stop_process' not in st.session_state: st.session_state.stop_process = False

# تسجيل الدخول
if not st.session_state.authenticated:
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# قائمة الجنسيات الكاملة
all_countries = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # لتجنب مشاكل المسارات في سيرفر Streamlit
    return webdriver.Chrome(options=options)

def scrap(p, n, d):
    if not p or n == "Select Nationality" or not d: return "Wrong Format"
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(2)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(p))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(n))
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if not items: return "Not Found"
        items[0].click()
        
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_field, str(d))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)
        
        res = {}
        labels = ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]
        for label in labels:
            try:
                path = f"//*[contains(text(), '{label}')]/following-sibling::span | //*[contains(text(), '{label}')]/parent::div/following-sibling::div"
                val = driver.find_element(By.XPATH, path).text.strip()
                res[label] = val if val else "Not Found"
            except: res[label] = "Not Found"
        
        return res if res.get("Job Description") != "Not Found" else "Not Found"
    except: return "Not Found"
    finally: driver.quit()

# الواجهة
t1, t2 = st.tabs(["Single", "Batch"])

with t2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df = pd.read_excel(f)
        st.write(f"Total: {len(df)}")
        
        # عرض 10 سجلات فقط
        page = st.number_input("Page Viewer", 1, (len(df)//10)+1, 1) - 1
        st.table(df.iloc[page*10 : (page+1)*10])
        
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🚀 START"):
            st.session_state.stop_process = False
            st.session_state.batch_results = []
            status = st.empty()
            pb = st.progress(0)
            table_hold = st.empty()
            start_time = time.time()
            
            for i, row in df.iterrows():
                if st.session_state.stop_process: break
                while st.session_state.is_paused:
                    status.warning("Paused...")
                    time.sleep(1)
                
                res = scrap(row[0], row[1], row[2])
                entry = {"#": i+1, "Passport": row[0], "Nationality": row[1], "DOB": row[2]}
                if isinstance(res, dict): entry.update(res)
                else:
                    for l in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[l] = res
                
                st.session_state.batch_results.append(entry)
                pb.progress((i+1)/len(df))
                status.info(f"Searching: {i+1}/{len(df)} | Time: {round(time.time()-start_time,1)}s")
                table_hold.dataframe(pd.DataFrame(st.session_state.batch_results))
            
            st.success("Finished!")
            st.download_button("Download CSV", pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'), "results.csv")

        if c2.button("🛑 STOP"): st.session_state.stop_process = True
        if c3.button("⏸️ PAUSE"): st.session_state.is_paused = True
        if c4.button("▶️ RESUME"): st.session_state.is_paused = False
