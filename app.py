import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

st.set_page_config(page_title="MOHRE Stable Pro", layout="wide")
st.title("HAMADA TRACING SITE - STABLE")

# الحماية وإدارة الجلسة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login") and pwd == "Bilkish":
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# حل جذري لمشكلة Errno 24 (Too many open files)
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # إنشاء مسار فريد لكل جلسة متصفح لتحرير الذاكرة
    user_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_dir}")
    try:
        return uc.Chrome(options=options, headless=True, use_subprocess=False)
    except: return None

def extract_logic(driver, passport, nationality, dob):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_in = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_in)
        dob_in.clear()
        dob_in.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_in)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        
        def gv(lbl):
            try:
                xp = f"//span[contains(text(), '{lbl}')]/following::span[1] | //label[contains(text(), '{lbl}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except: return 'N/A'
            
        return {"Passport": passport, "Card": gv("Card Number"), "Salary": gv("Total Salary"), "Status": "Found"}
    except: return None

# واجهة البحث الجماعي
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # تحسين الواجهة: زر التنسيق يظهر كخيار سريع فوق الجدول
    col1, col2 = st.columns([1, 4])
    if col1.button("🪄 Format Dates"):
        try:
            df['Date of Birth'] = pd.to_datetime(df['Date of Birth']).dt.strftime('%d/%m/%Y')
            st.success("Forced Format: dd/mm/yyyy")
        except: st.error("Check 'Date of Birth' column")

    # إعداد الجدول الاحترافي (AgGrid) مع القائمة الجانبية كما في طلبك
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationPageSize=10)
    gb.configure_side_bar() # لتفعيل قائمة (Filters/Columns) الجانبية
    gb.configure_default_column(editable=True, groupable=True)
    grid_opt = gb.build()

    st.info("💡 Right-click inside table or use Side Bar for Options.")
    AgGrid(df, gridOptions=grid_opt, height=400, theme='alpine')

    if st.button("🚀 Start Search"):
        results = []
        prog = st.progress(0)
        status = st.empty()
        
        driver = get_driver()
        for i, row in df.iterrows():
            # تدوير المتصفح كل 15 عملية لحل مشكلة الذاكرة نهائياً
            if i > 0 and i % 15 == 0:
                driver.quit()
                driver = get_driver()
                
            p, n, d = str(row['Passport Number']), str(row['Nationality']), str(row['Date of Birth'])
            status.text(f"Processing {i+1}/{len(df)}: {p}")
            res = extract_logic(driver, p, n, d)
            results.append(res if res else {"Passport": p, "Status": "Not Found"})
            prog.progress((i + 1) / len(df))
            
        if driver: driver.quit()
        st.dataframe(pd.DataFrame(results))
