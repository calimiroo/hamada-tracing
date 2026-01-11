import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from deep_translator import GoogleTranslator  # للترجمة التلقائية الفورية

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal - Professional Search", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة (بدون أي اختصار) ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- دالة الترجمة التلقائية الذكية ---
def auto_translate(text):
    try:
        # إذا كان النص يحتوي على حروف عربية، قم بترجمته فوراً
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='ar', target='en').translate(text)
        return text
    except:
        return text

# --- محرك البحث السيلينيوم (Logic) ---
def perform_mohre_search(passport, nationality, dob):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        # إدخال رقم الجواز
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        
        # اختيار الجنسية
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1.5)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        # إدخال تاريخ الميلاد (بدون اختصار سنوات)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_field)
        
        # تنفيذ البحث
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def get_text_by_label(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job_ar = get_text_by_label("Job Description")
        
        return {
            "Passport": passport,
            "Nationality": nationality,
            "DOB": dob,
            "Job Description": auto_translate(job_ar), # الترجمة التلقائية هنا
            "Card Number": get_text_by_label("Card Number"),
            "Basic Salary": get_text_by_label("Basic Salary"),
            "Total Salary": get_text_by_label("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing (Excel)"])

with tab1:
    st.subheader("Single Search Mode")
    c1, c2, c3 = st.columns(3)
    p_val = c1.text_input("Passport Number", key="s_p_input")
    n_val = c2.selectbox("Nationality", countries_list, key="s_n_input")
    d_val = c3.text_input("Date of Birth (DD/MM/YYYY)", key="s_d_input")

    if st.button("Start Search", key="single_btn"):
        if p_val and d_val:
            start_time = time.time()
            # شريط التقدم والعدادات اللحظية
            p_bar = st.progress(0)
            status_msg = st.empty()
            
            with st.spinner("Accessing MOHRE..."):
                p_bar.progress(50)
                res = perform_mohre_search(p_val, n_val, d_val)
                p_bar.progress(100)
                
                if res:
                    elapsed = round(time.time() - start_time, 2)
                    status_msg.success(f"✅ Success: 1 | ⏱️ Live Timer: {elapsed}s")
                    st.dataframe(pd.DataFrame([res]), use_container_width=True)
                else:
                    status_msg.error("❌ No results found in MOHRE database for this entry.")

with tab2:
    st.subheader("Batch Excel Processing")
    uploaded_file = st.file_uploader("Upload XLSX File", type=["xlsx"])
    if uploaded_file:
        df_source = pd.read_excel(uploaded_file)
        st.info(f"Loaded {len(df_source)} records.")
        
        if st.button("🚀 Run Global Search", key="batch_btn"):
            batch_results = []
            found_count = 0
            start_batch_time = time.time()
            
            # العناصر اللحظية
            prog_batch = st.progress(0)
            stats_batch = st.empty()
            table_batch = st.empty()
            
            total_records = len(df_source)
            for index, row in df_source.iterrows():
                # تشغيل محرك البحث
                data = perform_mohre_search(str(row[0]), str(row[1]), str(row[2]))
                
                if data:
                    batch_results.append(data)
                    found_count += 1
                
                # تحديث الـ UI حياً (Live Updates)
                elapsed_now = round(time.time() - start_batch_time, 1)
                prog_batch.progress((index + 1) / total_records)
                stats_batch.markdown(f"### ✅ Found: {found_count} / {total_records} | ⏱️ Timer: {elapsed_now}s")
                
                if batch_results:
                    table_batch.dataframe(pd.DataFrame(batch_results), use_container_width=True)

            if batch_results:
                st.success("Batch Completed Successfully!")
                # زر تحميل النتائج
                csv_file = pd.DataFrame(batch_results).to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Final Results (CSV)", csv_file, "MOHRE_Results.csv", "text/csv")
            else:
                st.error("❌ Process finished, but no matching records were found.")
