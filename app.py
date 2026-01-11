import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

# --- إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="MOHRE Portal - Hamada", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- قاموس ترجمة المسميات ---
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "محاسب": "Accountant",
    "سائق": "Driver",
    "مندوب مبيعات": "Sales Representative"
}

# --- نظام تسجيل الدخول ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.container():
        st.subheader("Protected Access")
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("❌ Incorrect Password")
    st.stop()

# --- نافذة الاستعلام (MOHRE Inquiry) ---
@st.dialog("Detailed Inquiry Result")
def open_inquiry_details(card_no):
    st.write(f"🔍 **Inquiry for Card Number:** {card_no}")
    st.info("Searching company details... Please wait.")
    # (كود السيلينيوم للاستعلام عن الشركة يوضع هنا)
    time.sleep(2)
    st.success("✅ Information Retrieved Successfully.")

# --- محرك البحث الأساسي ---
def run_scraper(passport, nation, dob):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        # إدخال البيانات (مثال توضيحي للمنطق)
        # driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        # ... خطوات السيلينيوم ...
        
        # محاكاة نتيجة مستخرجة
        job_ar = "مدير المنطقة"
        return {
            "Passport Number": passport,
            "Nationality": nation,
            "Date of Birth": dob,
            "Job Description": job_translation.get(job_ar, job_ar),
            "Card Number": "124119312",
            "Basic Salary": "8000",
            "Total Salary": "16000"
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
    # التاريخ اليدوي المطور (بدون Use Calendar)
    d_in = c3.text_input("Date of Birth", placeholder="DD/MM/YYYY", help="Format: Day/Month/Year")

    if st.button("Start Search", key="btn_s"):
        if p_in and d_in:
            start = time.time()
            with st.spinner("Searching..."):
                res = run_scraper(p_in, n_in, d_in)
                if res:
                    st.success(f"✅ Success: 1 | ⏱️ Live Timer: {round(time.time()-start, 2)}s")
                    # عرض رقم البطاقة كرابط
                    if st.button(f"🔎 Click to Inquiry: {res['Card Number']}", key="link_s"):
                        open_inquiry_details(res['Card Number'])
                    st.table(pd.DataFrame([res]))
                else: st.error("No Data Found")

with tab2:
    st.subheader("Batch File Processing")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if file:
        df_input = pd.read_excel(file)
        st.write("📋 File Preview:")
        st.dataframe(df_input, use_container_width=True)
        
        if st.button("🚀 Start Batch Search"):
            results_list = []
            success_count = 0
            start_batch = time.time()
            
            # مناطق العرض الحية
            stats_box = st.empty()
            table_box = st.empty()
            
            for i, row in df_input.iterrows():
                # تجهيز البيانات
                p_no = str(row[0])
                nat = str(row[1])
                try: dob_final = pd.to_datetime(row[2]).strftime('%d/%m/%Y')
                except: dob_final = str(row[2])

                # تنفيذ البحث
                data = run_scraper(p_no, nat, dob_final)
                
                if data:
                    results_list.append(data)
                    success_count += 1
                
                # تحديث العداد والوقت حياً (Live UI)
                elapsed = round(time.time() - start_batch, 1)
                stats_box.markdown(f"### ✅ Success: {success_count} | ⏱️ Live Timer: {elapsed}s")
                
                # تحديث الجدول حياً ببيانات الأشخاص الذين تم العثور عليهم
                if results_list:
                    table_box.table(pd.DataFrame(results_list))
            
            # الروابط النهائية
            if results_list:
                st.write("---")
                st.subheader("Quick Access Links:")
                for r in results_list:
                    if st.button(f"📄 Inquiry Card: {r['Card Number']}", key=f"b_lk_{r['Card Number']}"):
                        open_inquiry_details(r['Card Number'])
