import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

# نظام أمان لاستيراد مكتبة الترجمة
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- نظام تسجيل الدخول (كلمة السر: Hamada) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

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

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# دالة الترجمة التلقائية
def safe_translate(text):
    if not text or text == "Not Found": return text
    if HAS_TRANSLATOR:
        try:
            if any("\u0600" <= c <= "\u06FF" for c in text):
                return GoogleTranslator(source='ar', target='en').translate(text)
        except: return text
    return text

# دالة البحث
def perform_scraping(passport, nationality, dob):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1.5)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_field)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def get_v(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'

        job_raw = get_v("Job Description")
        return {
            "Passport": passport, "Nationality": nationality, "DOB": dob,
            "Job Description": safe_translate(job_raw),
            "Card Number": get_v("Card Number"), "Basic Salary": get_v("Basic Salary"), "Total Salary": get_v("Total Salary")
        }
    except: return None
    finally: driver.quit()

# الواجهة
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p_s")
    n_in = c2.selectbox("Nationality", countries_list, key="n_s")
    d_in = c3.text_input("Date of Birth (DD/MM/YYYY)", key="d_s")

    if st.button("Start Search", key="btn_s"):
        if p_in and d_in:
            start = time.time()
            pb = st.progress(0)
            st_area = st.empty()
            with st.spinner("Processing..."):
                pb.progress(50)
                res = perform_scraping(p_in, n_in, d_in)
                pb.progress(100)
                if res:
                    st_area.success(f"✅ Success: 1 | ⏱️ Timer: {round(time.time()-start, 2)}s")
                    st.dataframe(pd.DataFrame([res]), use_container_width=True)
                else: st_area.error("❌ No results found.")

with tab2:
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        df = pd.read_excel(up)
        if st.button("Start Search", key="btn_b"):
            results = []
            count = 0
            start_b = time.time()
            pb_b = st.progress(0)
            msg_b = st.empty()
            tbl_b = st.empty()
            
            for i, row in df.iterrows():
                data = perform_scraping(str(row[0]), str(row[1]), str(row[2]))
                if data:
                    results.append(data)
                    count += 1
                elapsed = round(time.time() - start_b, 1)
                pb_b.progress((i + 1) / len(df))
                msg_b.markdown(f"### ✅ Found: {count} / {len(df)} | ⏱️ Timer: {elapsed}s")
                if results:
                    tbl_b.dataframe(pd.DataFrame(results), use_container_width=True)

            if results:
                st.download_button("📥 Download Results", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "results.csv")
