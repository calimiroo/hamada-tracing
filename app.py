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

# قاموس الترجمة للمسميات الوظيفية
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

# --- حقل التاريخ الذكي (Auto-format DD/MM/YYYY) ---
def smart_date_input(label, key):
    # نص برمجي جافا سكريبت لإضافة الفواصل تلقائياً
    components.html(f"""
    <script>
    var input = window.parent.document.querySelectorAll('input[aria-label="{label}"]')[0];
    input.addEventListener('input', function(e) {{
        var val = e.target.value.replace(/\\D/g, '').match(/(\\d{{0,2}})(\\d{{0,2}})(\\d{{0,4}})/);
        e.target.value = !val[2] ? val[1] : val[1] + '/' + val[2] + (val[3] ? '/' + val[3] : '');
    }});
    </script>
    """, height=0)
    return st.text_input(label, placeholder="DD/MM/YYYY", key=key)

# --- نافذة الاستعلام التفصيلي ---
@st.dialog("Detailed Inquiry - MOHRE")
def show_inquiry_popup(card_number):
    st.write(f"🔍 Searching for Card: **{card_number}**")
    st.info("Please wait... Fetching company name and details.")
    # (هنا يوضع كود السيلينيوم للاستعلام عن الشركة)
    time.sleep(2)
    st.success("Details Found!")

# --- دالة البحث الأساسية ---
def perform_scraping(p, n, d):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        # ... خطوات السيلينيوم الخاصة بك ...
        job_ar = "مدير المنطقة" # مثال للنتيجة
        return {{
            "Passport Number": p, "Nationality": n, "Date of Birth": d,
            "Job Description": job_translation.get(job_ar, job_ar),
            "Card Number": "124119312", "Basic Salary": "8000", "Total Salary": "16000"
        }}
    except: return None
    finally: driver.quit()

# --- تبويبات الواجهة ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", value="")
    n_in = c2.selectbox("Nationality", countries_list)
    
    # حقل التاريخ الذكي مع اختيار التقويم المدمج
    with c3:
        use_cal = st.checkbox("Use Calendar", value=False)
        if use_cal:
            d_val = st.date_input("Pick Date", value=None, format="DD/MM/YYYY")
            d_in = d_val.strftime("%d/%m/%Y") if d_val else ""
        else:
            d_in = smart_date_input("Date of Birth", "d1")

    if st.button("Search Now"):
        if p_in and d_in:
            start_t = time.time()
            with st.spinner("Processing..."):
                res = perform_scraping(p_in, n_in, d_in)
                if res:
                    st.markdown(f"✅ **Success: 1** | ⏱️ **Live Timer:** {round(time.time() - start_t, 2)}s")
                    
                    # عرض رقم البطاقة كرابط تفاعلي
                    if st.button(f"🔗 {res['Card Number']}", key="single_link"):
                        show_inquiry_popup(res['Card Number'])
                    
                    st.table(pd.DataFrame([res]))
                else: st.error("Not Found.")

with tab2:
    st.subheader("Batch Search")
    up = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up:
        df_full = pd.read_excel(up)
        st.dataframe(df_full, use_container_width=True)
        
        if st.button("Start Batch Processing"):
            results = []
            success_count = 0
            start_batch = time.time()
            stats = st.empty()
            tbl = st.empty()
            
            for i, row in df_full.iterrows():
                # تحديث العداد والوقت حياً
                elapsed = round(time.time() - start_batch, 1)
                stats.markdown(f"✅ **Success: {success_count}** | ⏱️ **Live Timer:** {elapsed}s")
                
                data = perform_scraping(str(row[0]), str(row[1]), str(row[2]))
                if data:
                    results.append(data)
                    success_count += 1
                
                tbl.table(pd.DataFrame(results))
            
            if results:
                st.write("### Click to Inquiry Details:")
                for r in results:
                    if st.button(f"🔗 Card No: {r['Card Number']}", key=f"link_{r['Card Number']}"):
                        show_inquiry_popup(r['Card Number'])
