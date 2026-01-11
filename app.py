import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
import streamlit.components.v1 as components

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات الكاملة ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# قاموس ترجمة المسميات الوظيفية
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "مندوب": "Representative",
    "محاسب": "Accountant",
    "سائق": "Driver"
}

# --- نظام تسجيل الدخول ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.form("login"):
        pwd = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# --- حقل التاريخ المطور (HTML5 Date + Auto-Slash) ---
def smart_date_field(key):
    # كود جافا سكريبت لتحسين تجربة كتابة التاريخ
    components.html(f"""
    <script>
    var input = window.parent.document.querySelectorAll('input[type="text"]')[1];
    input.placeholder = "DD/MM/YYYY";
    input.addEventListener('input', function(e) {{
        var v = e.target.value.replace(/\\D/g,'').slice(0,8);
        if (v.length >= 2) v = v.slice(0,2) + '/' + v.slice(2);
        if (v.length >= 5) v = v.slice(0,5) + '/' + v.slice(5);
        e.target.value = v;
    }});
    </script>
    """, height=0)
    return st.text_input("Date of Birth", key=key)

# --- نافذة الاستعلام التفصيلي ---
@st.dialog("Detailed Inquiry - MOHRE")
def show_inquiry_popup(card_number):
    st.write(f"🔍 Searching for Card: **{card_number}**")
    st.info("Please wait... Fetching details from MOHRE Inquiry Service")
    # (هنا يوضع كود السيلينيوم الخاص بصفحة الاستعلام)
    time.sleep(2)
    st.success("Results Retrieved Successfully!")

# --- دالة البحث الأساسية ---
def perform_scraping(p, n, d):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        # تنفيذ خطوات البحث (Passport, Nationality, DOB)
        # ... كود السيلينيوم الخاص بك ...
        
        # مثال للبيانات المستخرجة
        job_ar = "مدير المنطقة" 
        return {
            "Passport Number": p, "Nationality": n, "Date of Birth": d,
            "Job Description": job_translation.get(job_ar, job_ar),
            "Card Number": "124119312", "Basic Salary": "8000", "Total Salary": "16000"
        }
    except: return None
    finally: driver.quit()

# --- تبويبات الواجهة ---
tab1, tab2 = st.tabs(["Single Search", "Batch Preview"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", value="", key="single_p")
    n_in = c2.selectbox("Nationality", countries_list, key="single_n")
    d_in = smart_date_field("single_d") # التاريخ الذكي

    if st.button("Search Now", key="single_btn"):
        if p_in and d_in:
            start_t = time.time()
            with st.spinner("Processing..."):
                res = perform_scraping(p_in, n_in, d_in)
                if res:
                    st.markdown(f"✅ **Success: 1** | ⏱️ **Live Timer:** {round(time.time() - start_t, 2)}s")
                    if st.button(f"🔗 {res['Card Number']}", key="s_link"):
                        show_inquiry_popup(res['Card Number'])
                    st.table(pd.DataFrame([res]))
                else: st.error("Not Found.")

with tab2:
    st.subheader("Batch Search & Processing")
    up = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up:
        df_batch = pd.read_excel(up)
        st.info(f"File uploaded! Total records: {len(df_batch)}")
        st.dataframe(df_batch, use_container_width=True)
        
        if st.button("🚀 Start Batch Processing"):
            results_list = []
            success_count = 0
            start_batch = time.time()
            
            # أماكن العرض الحية (Dynamic UI)
            stats_placeholder = st.empty()
            table_placeholder = st.empty()
            
            for i, row in df_batch.iterrows():
                # تجهيز البيانات من الإكسل
                pass_no = str(row[0])
                nat_val = str(row[1])
                # معالجة التاريخ من الإكسل ليكون DD/MM/YYYY
                try: dob_val = pd.to_datetime(row[2]).strftime('%d/%m/%Y')
                except: dob_val = str(row[2])

                # تنفيذ البحث
                data = perform_scraping(pass_no, nat_val, dob_val)
                
                if data:
                    results_list.append(data)
                    success_count += 1
                
                # تحديث العداد والوقت حياً في كل لفة
                elapsed = round(time.time() - start_batch, 1)
                stats_placeholder.markdown(f"✅ **Success: {success_count}** | ⏱️ **Live Timer:** {elapsed}s")
                
                # تحديث الجدول حياً تحت العداد
                if results_list:
                    table_placeholder.table(pd.DataFrame(results_list))
            
            # عند الانتهاء، إظهار روابط الاستعلام
            if results_list:
                st.write("### Quick Inquiry (Click to view details):")
                cols = st.columns(4)
                for idx, r in enumerate(results_list):
                    with cols[idx % 4]:
                        if st.button(f"🔗 {r['Card Number']}", key=f"b_link_{idx}"):
                            show_inquiry_popup(r['Card Number'])
