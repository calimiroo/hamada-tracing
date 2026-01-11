import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# نظام أمان للمكتبات
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- قائمة الجنسيات ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# دالة الترجمة
def safe_translate(text):
    if not text or text == "Not Found" or not HAS_TRANSLATOR: return text
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='ar', target='en').translate(text)
    except: pass
    return text

# دالة البحث
def perform_scraping(passport, nationality, dob):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(nationality)
        time.sleep(1.5)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, dob)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        def get_v(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                v = driver.find_element(By.XPATH, xpath).text.strip()
                return v if v else None
            except: return None

        job = get_v("Job Description")
        if not job: return None # إذا لم يجد بيانات المسمى الوظيفي نعتبر السجل غير موجود

        return {
            "Passport": passport, "Nationality": nationality, "DOB": dob,
            "Job Description": safe_translate(job),
            "Card Number": get_v("Card Number"), "Basic Salary": get_v("Basic Salary"), "Total Salary": get_v("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة التطبيق ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    if st.button("🗑️ Clear Inputs", key="clr_s"): st.rerun() # زر مسح الداتا المدخلة
    
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="ps_1")
    n_in = col2.selectbox("Nationality", countries_list, key="na_1")
    d_in = col3.text_input("Date of Birth (DD/MM/YYYY)", key="db_1")

    if st.button("Start Search", key="run_s"):
        if p_in and d_in:
            with st.spinner("Searching..."):
                res = perform_scraping(p_in, n_in, d_in)
                if res:
                    st.success("Result Found!")
                    st.table(pd.DataFrame([res]))
                else: st.error("No data found for this person.")

with tab2:
    st.subheader("Batch Excel Processing")
    if st.button("🗑️ Reset Batch", key="clr_b"): st.rerun() # زر مسح الداتا المدخلة والملف
    
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="file_up")
    
    if up_file:
        df_preview = pd.read_excel(up_file)
        st.write(f"📊 **Total records in file:** {len(df_preview)}")
        
        # عرض الجدول مقسم لـ 10 صفوف في الصفحة
        st.dataframe(df_preview, use_container_width=True, height=400) # Streamlit يدعم التقسم التلقائي داخلياً بفاعلية
        
        if st.button("Start Search", key="run_b"):
            results = []
            found_count = 0
            total = len(df_preview)
            
            pb = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty()
            
            for i, row in df_preview.iterrows():
                data = perform_scraping(str(row[0]), str(row[1]), str(row[2]))
                if data:
                    results.append(data)
                    found_count += 1
                
                # تحديث العداد بصيغة (تم العثور/الإجمالي)
                pb.progress((i + 1) / total)
                status_text.markdown(f"### 🔍 Status: Found {found_count} / {total}")
                
                # تحديث الجدول حياً (يظهر فقط ما تم العثور عليه)
                if results:
                    table_placeholder.dataframe(pd.DataFrame(results), use_container_width=True)

            if results:
                st.success(f"Finished! Found {found_count} matching records.")
                st.download_button("📥 Download Found Data (CSV)", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "MOHRE_Found.csv")
            else:
                st.warning("Finished. No matching records were found in the database.")
