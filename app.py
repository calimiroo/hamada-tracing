import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قائمة الجنسيات الكاملة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# ترجمة المسميات الوظيفية
job_trans = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "محاسب": "Accountant",
    "سائق": "Driver"
}

# --- نظام تسجيل الدخول ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.container():
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    st.stop()

# --- دالة الاستخراج ---
def extract_data(passport, nationality, dob_str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        # منطق البحث الخاص بك...
        
        job_ar = "مدير المنطقة" # قيمة تجريبية
        card_num = "124119312" # قيمة تجريبية
        
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": job_trans.get(job_ar, job_ar),
            "Card Number": card_num,
            "Basic Salary": "8000",
            "Total Salary": "16000"
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="s_p")
    n_in = col2.selectbox("Nationality", countries_list, key="s_n")
    d_in = col3.text_input("Date of Birth", placeholder="DD/MM/YYYY", key="s_d")

    if st.button("Search Now", key="s_btn"):
        if p_in and d_in:
            start_t = time.time()
            with st.spinner("Processing..."):
                result = extract_data(p_in, n_in, d_in)
                if result:
                    st.markdown(f"✅ **Success: 1** | ⏱️ **Live Timer:** {round(time.time() - start_t, 2)}s")
                    # عرض النتيجة في جدول مريح للعين
                    st.dataframe(pd.DataFrame([result]), use_container_width=True)
                else:
                    st.error("Not Found.")

with tab2:
    st.subheader("Batch Search")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        df_full = pd.read_excel(uploaded_file)
        st.info(f"Total records found: {len(df_full)}")
        st.dataframe(df_full, use_container_width=True, height=200) 
        
        if st.button("🚀 Start Batch Processing", key="b_btn"):
            results = []
            success_count = 0
            start_batch_t = time.time()
            
            # أماكن العرض الحية
            stats_placeholder = st.empty()
            table_placeholder = st.empty()
            
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
                
                # تحديث العداد والوقت حياً
                elapsed = round(time.time() - start_batch_t, 1)
                stats_placeholder.markdown(f"### ✅ Success: {success_count} | ⏱️ Live Timer: {elapsed}s")
                
                # تحديث الجدول حياً ببيانات الأشخاص الذين تم العثور عليهم
                if results:
                    table_placeholder.dataframe(pd.DataFrame(results), use_container_width=True)
            
            if results:
                st.success("Batch Processing Completed!")
                st.download_button("Download Results", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "results.csv")
