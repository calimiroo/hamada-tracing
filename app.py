import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قائمة الجنسيات الكاملة (كما هي في كودك)
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# قاموس شامل لترجمة المسميات الوظيفية (يمكنك إضافة المزيد هنا)
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "محاسب": "Accountant",
    "سائق": "Driver",
    "مندوب": "Representative",
    "فني": "Technician",
    "مدير": "Manager",
    "مبرمج": "Programmer",
    "منسق": "Coordinator"
}

# نظام تسجيل الدخول (كما هو)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# دالة الاستخراج الأصلية
def extract_data(passport, nationality, dob_str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
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
        time.sleep(10)

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job_ar = get_value("Job Description")
        # ترجمة المسمى الوظيفي
        translated_job = job_translation.get(job_ar, job_ar)

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translated_job,
            "Card Number": get_value("Card Number"), "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"), 
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"),
        }
    except: return None
    finally: driver.quit()

# واجهة المستخدم
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="s_p")
    n_in = col2.selectbox("Nationality", countries_list, key="s_n")
    d_in = col3.text_input("Date of Birth", placeholder="DD/MM/YYYY", key="s_d")

    if st.button("Search Now"):
        if p_in and d_in:
            start_time = time.time()
            # شريط البروسيس والعدادات للبحث الفردي
            progress_bar = st.progress(0)
            status_area = st.empty()
            
            with st.spinner("Processing..."):
                for percent_complete in range(100):
                    time.sleep(0.01) # محاكاة شريط التقدم أثناء بدء السيلينيوم
                    progress_bar.progress(percent_complete + 1)
                    elapsed = round(time.time() - start_time, 1)
                    status_area.markdown(f"✅ **Success: 0** | ⏱️ **Live Timer:** {elapsed}s")
                
                result = extract_data(p_in, n_in, d_in)
                if result:
                    elapsed = round(time.time() - start_time, 2)
                    status_area.markdown(f"✅ **Success: 1** | ⏱️ **Live Timer:** {elapsed}s")
                    st.dataframe(pd.DataFrame([result]), use_container_width=True)
                else: st.error("Not Found.")

with tab2:
    st.subheader("Batch Processing")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df_full = pd.read_excel(uploaded_file)
        st.dataframe(df_full, use_container_width=True)
        
        if st.button("🚀 Start Batch Search"):
            results = []
            success_count = 0
            start_batch_time = time.time()
            
            # مناطق العرض الحية
            progress_bar = st.progress(0)
            stats_placeholder = st.empty()
            table_placeholder = st.empty()
            
            total_rows = len(df_full)
            
            for i, row in df_full.iterrows():
                # تجهيز البيانات
                p_no = str(row[0]).strip()
                nat = str(row[1]).strip()
                try: dob = pd.to_datetime(row[2]).strftime('%d/%m/%Y')
                except: dob = str(row[2])

                # تنفيذ البحث
                res = extract_data(p_no, nat, dob)
                
                if res:
                    results.append(res)
                    success_count += 1
                
                # تحديث العداد والوقت والشريط حياً
                elapsed = round(time.time() - start_batch_time, 1)
                progress_bar.progress((i + 1) / total_rows)
                stats_placeholder.markdown(f"### ✅ **Success: {success_count} / {total_rows}** | ⏱️ **Live Timer:** {elapsed}s")
                
                # تحديث الجدول حياً
                if results:
                    table_placeholder.dataframe(pd.DataFrame(results), use_container_width=True)
            
            st.success("Batch Completed!")
