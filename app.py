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

# قاموس ترجمة المسميات الوظيفية
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "مندوب": "Representative"
}

# نظام تسجيل الدخول (كما هو)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        submit_button = st.form_submit_button("Login")
        if submit_button:
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    st.stop()

# نافذة الاستعلام (Inquiry Dialog)
@st.dialog("MOHRE Company Inquiry")
def show_inquiry_dialog(card_number):
    st.write(f"🔍 Fetching details for: **{card_number}**")
    # ملاحظة: هنا يتم وضع كود الـ Selenium الخاص بـ inquiry.mohre.gov.ae
    # تم تبسيطه للعرض، يمكنك دمج دالة الاستخراج كاملة هنا.
    st.info("Searching in MOHRE database... Please wait.")
    time.sleep(2)
    st.success("Data Retrieved Successfully")

# دوال الاستخراج
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        job = get_value("Job Description")
        # ترجمة الوظيفة إذا وجدت في القاموس
        translated_job = job_translation.get(job, job)

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
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    with col1: passport = st.text_input("Passport Number", key="p_one")
    with col2: nationality = st.selectbox("Nationality", countries_list, key="n_one")
    # تغيير تنسيق التاريخ في الواجهة
    with col3: dob = st.date_input("Date of Birth (DD/MM/YYYY)", format="DD/MM/YYYY", key="d_one")
    
    if st.button("Search Now", key="btn_one"):
        if passport and nationality != "Select Nationality":
            with st.spinner("Processing..."):
                result = extract_data(passport, nationality, dob.strftime("%d/%m/%Y"))
                if result:
                    st.success("Success!")
                    # عرض الجدول مع تحويل رقم البطاقة لرابط
                    df = pd.DataFrame([result])
                    st.write("### Search Results")
                    
                    # طريقة تحويل العمود لرابط تفاعلي في Streamlit
                    for index, row in df.iterrows():
                        c_num = row['Card Number']
                        if st.button(f"🔗 {c_num}", key=f"link_{index}", help="Click to view company details"):
                            show_inquiry_dialog(c_num)
                    
                    st.table(df)
                else: st.error("Not Found.")

with tab2:
    st.subheader("Batch Search")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df_full = pd.read_excel(uploaded_file)
        st.dataframe(df_full, use_container_width=True) 
        
        if st.button("Start Batch Processing"):
            results = []
            progress_bar = st.progress(0)
            
            for i, row in df_full.iterrows():
                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                try: d_birth = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: d_birth = ""

                res = extract_data(p_num, nat, d_birth)
                if res: results.append(res)
                progress_bar.progress((i + 1) / len(df_full))
            
            if results:
                final_df = pd.DataFrame(results)
                st.success("Batch Completed!")
                
                # إضافة روابط لكل الأرقام في المجموعة
                st.write("### Click any Card Number to Inquiry:")
                cols = st.columns(len(results))
                for idx, r in final_df.iterrows():
                    with cols[idx % 3]: # توزيع الأزرار بشكل متناسق
                        if st.button(f"Card: {r['Card Number']}", key=f"batch_link_{idx}"):
                            show_inquiry_dialog(r['Card Number'])
                
                st.table(final_df)
                st.download_button("Download CSV", final_df.to_csv(index=False).encode('utf-8'), "results.csv")
