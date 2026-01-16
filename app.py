import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode # مكتبة الجداول المتقدمة

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة الجلسة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'df_full' not in st.session_state:
    st.session_state['df_full'] = None

# التحقق من تسجيل الدخول (نفس الكود السابق)
if not st.session_state['authenticated']:
    with st.form("login_form"):
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login") and pwd_input == "Bilkish":
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# --- وظيفة تشغيل المتصفح مع حل مشكلة الذاكرة ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # تعيين مجلد مستخدم مؤقت فريد لمنع خطأ Too many open files
    user_data_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_data_dir}")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# وظيفة استخراج البيانات (نفس منطق الكود الأصلي)
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
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
        
        def gv(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Card Number": gv("Card Number"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    # (البحث الفردي كما هو في كودك الأصلي)
    st.subheader("Single Person Search")
    # ... كود البحث الفردي المختصر ...

with tab2:
    st.subheader("Batch Search with Menu Options")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        if st.session_state.df_full is None:
            st.session_state.df_full = pd.read_excel(uploaded_file)
        
        # إعداد AgGrid لعرض القائمة المنسدلة المطلوبة
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df_full)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_side_bar() # إضافة الفلاتر والقائمة الجانبية
        gb.configure_selection('multiple', use_checkbox=True)
        grid_options = gb.build()

        st.info("💡 Right-click on any cell or use column menu to interact.")
        
        # عرض الجدول
        grid_response = AgGrid(
            st.session_state.df_full,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            height=400,
            theme='balham'
        )
        
        # زر التنسيق سيظهر هنا بشكل أنيق أو ينفذ تلقائياً عند الرغبة
        if st.button("🪄 Apply Date Formatting to All"):
            try:
                st.session_state.df_full['Date of Birth'] = pd.to_datetime(st.session_state.df_full['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("Dates formatted successfully inside the grid!")
                st.rerun()
            except:
                st.error("Format Error: Ensure the column name is 'Date of Birth'")

        if st.button("🚀 Start Processing Checked Rows"):
            # معالجة البيانات المختارة أو الكل
            selected_rows = grid_response['selected_rows']
            df_to_process = pd.DataFrame(selected_rows) if selected_rows else st.session_state.df_full
            
            results = []
            progress_bar = st.progress(0)
            for i, row in df_to_process.iterrows():
                res = extract_data(str(row['Passport Number']), str(row['Nationality']), str(row['Date of Birth']))
                results.append(res if res else {"Passport Number": row['Passport Number'], "Status": "Error"})
                progress_bar.progress((i + 1) / len(df_to_process))
            
            st.table(pd.DataFrame(results))
