import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal - Professional", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- قاموس الترجمة للمسميات ---
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "محاسب": "Accountant",
    "سائق": "Driver",
    "مندوب مبيعات": "Sales Representative",
    "فني": "Technician"
}

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
            else: st.error("❌ Incorrect Password")
    st.stop()

# --- دالة البحث الأصلية (Scraping Logic) ---
def extract_data_from_mohre(passport, nationality, dob_str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        
        # تنفيذ خطوات البحث في موقع MOHRE
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
        time.sleep(10) # انتظار استخراج النتيجة

        def get_val(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job_ar = get_val("Job Description")
        
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": job_translation.get(job_ar, job_ar), # ترجمة تلقائية
            "Card Number": get_val("Card Number"),
            "Card Issue": get_val("Card Issue"),
            "Card Expiry": get_val("Card Expiry"),
            "Basic Salary": get_val("Basic Salary"),
            "Total Salary": get_val("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", placeholder="Enter Passport")
    n_in = c2.selectbox("Nationality", countries_list)
    d_in = c3.text_input("Date of Birth", placeholder="DD/MM/YYYY")

    if st.button("Start Search"):
        if p_in and d_in:
            start_t = time.time()
            with st.spinner("Searching in MOHRE Portal..."):
                res = extract_data_from_mohre(p_in, n_in, d_in)
                if res:
                    st.success(f"✅ Success: 1 | ⏱️ Live Timer: {round(time.time()-start_t, 2)}s")
                    st.dataframe(pd.DataFrame([res]), use_container_width=True)
                else: st.error("❌ Not Found in MOHRE Database")

with tab2:
    st.subheader("Batch processing (Excel)")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if file:
        df_input = pd.read_excel(file)
        st.dataframe(df_input, use_container_width=True)
        
        if st.button("🚀 Start Batch Search"):
            results_list = []
            success_count = 0
            start_batch = time.time()
            
            # مناطق التحديث الحي (Live UI)
            stats_area = st.empty()
            table_area = st.empty()
            
            for i, row in df_input.iterrows():
                # تجهيز البيانات من الصف
                p_no = str(row[0]).strip()
                nat = str(row[1]).strip()
                try: dob_f = pd.to_datetime(row[2]).strftime('%d/%m/%Y')
                except: dob_f = str(row[2])

                # تنفيذ البحث الفعلي
                data = extract_data_from_mohre(p_no, nat, dob_f)
                
                if data:
                    results_list.append(data)
                    success_count += 1
                
                # تحديث العداد والوقت حياً
                elapsed = round(time.time() - start_batch, 1)
                stats_area.markdown(f"### ✅ Success: {success_count} | ⏱️ Live Timer: {elapsed}s")
                
                # تحديث الجدول حياً ببيانات الأشخاص الذين تم العثور عليهم
                if results_list:
                    table_area.dataframe(pd.DataFrame(results_list), use_container_width=True)
            
            if results_list:
                st.success("✅ Batch Completed!")
                st.download_button("Download Full Results", pd.DataFrame(results_list).to_csv(index=False).encode('utf-8'), "results.csv")
