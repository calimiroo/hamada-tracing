import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from deep_translator import GoogleTranslator # مكتبة للترجمة التلقائية الفورية

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal - Auto Translate", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# دالة الترجمة التلقائية
def auto_translate(text):
    try:
        if text and any("\u0600" <= c <= "\u06FF" for c in text): # التأكد أن النص يحتوي على حروف عربية
            return GoogleTranslator(source='ar', target='en').translate(text)
        return text
    except:
        return text

# --- نظام تسجيل الدخول ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.container():
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# --- دالة البحث والاستخراج ---
def run_mohre_scraping(passport, nationality, dob_str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        # إدخال البيانات
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
        time.sleep(8)

        def get_v(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job_ar = get_v("Job Description")
        
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": auto_translate(job_ar), # ترجمة تلقائية فورية لأي مسمى
            "Card Number": get_v("Card Number"),
            "Card Issue": get_v("Card Issue"),
            "Card Expiry": get_v("Card Expiry"),
            "Basic Salary": get_v("Basic Salary"),
            "Total Salary": get_v("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
t1, t2 = st.tabs(["Single Search", "Batch Search"])

with t1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="p_s")
    n_in = col2.selectbox("Nationality", countries_list, key="n_s")
    d_in = col3.text_input("Date of Birth (DD/MM/YYYY)", key="d_s")

    if st.button("Search Now"):
        if p_in and d_in:
            start_t = time.time()
            prog = st.progress(0)
            status = st.empty()
            with st.spinner("Searching..."):
                prog.progress(50)
                res = run_mohre_scraping(p_in, n_in, d_in)
                prog.progress(100)
                if res:
                    elapsed = round(time.time() - start_t, 2)
                    status.success(f"✅ Success: 1 | ⏱️ Timer: {elapsed}s")
                    st.dataframe(pd.DataFrame([res]), use_container_width=True)
                else: status.error("❌ No results found.")

with t2:
    st.subheader("Batch Search (Excel)")
    up = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up:
        df_in = pd.read_excel(up)
        st.dataframe(df_in, use_container_width=True)
        if st.button("🚀 Start Batch Search"):
            final_results = []
            success_count = 0
            start_batch = time.time()
            prog_b = st.progress(0)
            stats_b = st.empty()
            table_b = st.empty()
            total = len(df_in)
            
            for i, row in df_in.iterrows():
                data = run_mohre_scraping(str(row[0]), str(row[1]), str(row[2]))
                if data:
                    final_results.append(data)
                    success_count += 1
                
                elapsed_b = round(time.time() - start_batch, 1)
                prog_b.progress((i + 1) / total)
                stats_b.markdown(f"### ✅ Found: {success_count} / {total} | ⏱️ Timer: {elapsed_b}s")
                if final_results:
                    table_b.dataframe(pd.DataFrame(final_results), use_container_width=True)

            if final_results:
                st.success(f"Batch Completed! {success_count} records extracted.")
                st.download_button("📥 Download Results (CSV)", pd.DataFrame(final_results).to_csv(index=False).encode('utf-8'), "mohre_results.csv")
            else: st.error("❌ No results found for the file records.")
