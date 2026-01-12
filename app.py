import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MOHRE Full System", layout="wide")

# --- قائمة كاملة لجميع الجنسيات ---
ALL_NATIONALITIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", 
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", 
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", 
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", 
    "Cote d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", 
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", 
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", 
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", 
    "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea North", "Korea South", "Kuwait", 
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", 
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", 
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", 
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway", "Oman", "Pakistan", "Palau", 
    "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", 
    "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Samoa", "San Marino", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", 
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", 
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", 
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", 
    "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

def translate_to_en(text):
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='auto', target='en').translate(text)
    except: pass
    return text

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def run_search(passport, nationality, dob):
    driver = get_driver()
    if not driver: return "System Error"
    try:
        # تحويل التاريخ للصيغة المطلوبة
        dob_str = dob.strftime("%d/%m/%Y") if isinstance(dob, (datetime, pd.Timestamp)) else str(dob)

        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(passport))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Nationality Error"
        
        # حقن التاريخ (مفتوح من 1900)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_field, dob_str)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)
        
        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "N/A"

        job = gv("Job Description")
        if job == "N/A" or not job: return "Not Found"

        return {
            "Job": translate_to_en(job),
            "Card": gv("Card Number"),
            "Start": gv("Contract Start"),
            "End": gv("Contract End"),
            "Salary": gv("Total Salary")
        }
    except: return "Format Error"
    finally: driver.quit()

# --- واجهة المستخدم ---
st.title("🛡️ HAMADA TRACING SYSTEM - GLOBAL VERSION")

tab1, tab2 = st.tabs(["🔍 البحث الفردي", "📁 ملف الإكسيل"])

with tab1:
    col1, col2, col3 = st.columns(3)
    p_num = col1.text_input("رقم الجواز")
    # قائمة الجنسيات كاملة
    nat = col2.selectbox("اختر الجنسية", ALL_NATIONALITIES)
    # التقويم يبدأ من 1900
    dob_input = col3.date_input("تاريخ الميلاد", 
                               min_value=datetime(1900, 1, 1), 
                               max_value=datetime.today(),
                               value=datetime(1990, 1, 1))
    
    if st.button("بحث الآن"):
        with st.spinner("جاري جلب البيانات..."):
            res = run_search(p_num, nat, dob_input)
            if isinstance(res, dict): st.table(pd.DataFrame([res]))
            else: st.error(res)

with tab2:
    up_file = st.file_uploader("ارفع الملف", type=["xlsx"])
    if up_file:
        df = pd.read_excel(up_file)
        st.write("📊 معاينة الملف المرفوع:")
        st.dataframe(df)
        
        if st.button("🚀 معالجة الكل"):
            results = []
            m1, m2, m3 = st.columns(3)
            timer_d, count_d, success_d = m1.empty(), m2.empty(), m3.empty()
            pb = st.progress(0)
            table_d = st.empty()
            start_t = time.time()
            success_c = 0

            for i, row in df.iterrows():
                timer_d.metric("⏳ الوقت", f"{round(time.time()-start_t, 1)}s")
                count_d.metric("📊 سجل رقم", f"{i+1}/{len(df)}")
                success_d.metric("✅ نجاح", success_c)
                
                # ترتيب الأعمدة: اسم، جواز، جنسية، تاريخ
                data = run_search(row[1], row[2], row[3])
                entry = {"الاسم": row[0], "الجواز": row[1], "الحالة": "Success" if isinstance(data, dict) else data}
                if isinstance(data, dict):
                    entry.update(data)
                    success_c += 1
                results.append(entry)
                table_d.dataframe(pd.DataFrame(results))
                pb.progress((i+1)/len(df))

            st.success("اكتملت المعالجة")
            st.download_button("تحميل النتيجة", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")
