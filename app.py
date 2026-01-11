import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from deep_translator import GoogleTranslator  # مكتبة للترجمة التلقائية الفورية

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal - Auto Search", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة (بدون اختصارات) ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- دالة الترجمة التلقائية (API) ---
def translate_job(text):
    try:
        # فحص إذا كان النص يحتوي على لغة عربية
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='ar', target='en').translate(text)
        return text
    except:
        return text

# --- محرك البحث السيلينيوم الأصلي ---
def scrap_mohre(passport, nationality, dob_str):
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
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def get_field(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job_raw = get_field("Job Description")
        
        return {
            "Passport": passport,
            "Nationality": nationality,
            "DOB": dob_str,
            "Job Description": translate_job(job_raw), # ترجمة تلقائية فورية
            "Card Number": get_field("Card Number"),
            "Basic Salary": get_field("Basic Salary"),
            "Total Salary": get_field("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم وفصل التبويبات ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing (Excel)"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", placeholder="Type here...", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.text_input("Date of Birth", placeholder="DD/MM/YYYY", key="s_d")

    if st.button("Search Person"):
        if p_in and d_in:
            start_t = time.time()
            # شريط بروسيس وعداد لحظي
            prog_bar = st.progress(0)
            status_txt = st.empty()
            
            with st.spinner("Connecting to MOHRE..."):
                prog_bar.progress(40)
                res = scrap_mohre(p_in, n_in, d_in)
                prog_bar.progress(100)
                
                if res:
                    elapsed = round(time.time() - start_t, 2)
                    status_txt.success(f"✅ Success: 1 | ⏱️ Live Timer: {elapsed}s")
                    st.dataframe(pd.DataFrame([res]), use_container_width=True)
                else:
                    status_txt.error("❌ No results found in the database for this record.")

with tab2:
    st.subheader("Batch Excel Processing")
    file_up = st.file_uploader("Upload XLSX File", type=["xlsx"])
    if file_up:
        df_raw = pd.read_excel(file_up)
        st.dataframe(df_raw.head(), use_container_width=True)
        
        if st.button("🚀 Start Global Search"):
            final_list = []
            count = 0
            start_b = time.time()
            
            # العدادات اللحظية وشريط التقدم
            p_bar = st.progress(0)
            s_msg = st.empty()
            t_area = st.empty()
            
            total = len(df_raw)
            for i, row in df_raw.iterrows():
                # تشغيل السكرابر
                data = scrap_mohre(str(row[0]), str(row[1]), str(row[2]))
                
                if data:
                    final_list.append(data)
                    count += 1
                
                # تحديث الـ Live UI
                elapsed_b = round(time.time() - start_b, 1)
                p_bar.progress((i + 1) / total)
                s_msg.markdown(f"### ✅ Found: {count} / {total} | ⏱️ Timer: {elapsed_b}s")
                
                if final_list:
                    t_area.dataframe(pd.DataFrame(final_list), use_container_width=True)

            if final_list:
                st.success(f"Processing Complete! Found {count} results.")
                # زر التحميل النهائي
                csv_data = pd.DataFrame(final_list).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results (CSV)", csv_data, "MOHRE_Results.csv", "text/csv")
            else:
                st.error("❌ Process finished, but no matching records were found.")
