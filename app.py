import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import os
import requests
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Pro Extractor", layout="wide")
st.title("HAMADA TRACING SITE - STABLE VERSION")

# الحماية بكلمة مرور
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Enter Password", type="password")
    if pwd == "Bilkish":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# إدارة الجلسة لمنع الانهيار
if 'batch_results' not in st.session_state: st.session_state.batch_results = []

# دالة تشغيل المتصفح مع تنظيف الذاكرة
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    user_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_dir}")
    try:
        return uc.Chrome(options=options, headless=True, use_subprocess=False)
    except: return None

# دالة الاستخراج الأساسية
def extract_logic(driver, passport, nationality, dob):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_in = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_in)
        dob_in.clear()
        dob_in.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_in)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(10)

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
    
    # القائمة المنسدلة الاحترافية والتحكم في الجدول
    col_btn, _ = st.columns([1, 5])
    if col_btn.button("🪄 Format Dates to dd/mm/yyyy"):
        df['Date of Birth'] = pd.to_datetime(df['Date of Birth']).dt.strftime('%d/%m/%Y')
        st.success("Format Applied!")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationPageSize=10)
    gb.configure_side_bar() # لتفعيل القائمة المنسدلة الجانبية كما في صورتك
    gb.configure_selection('multiple', use_checkbox=True)
    grid_opt = gb.build()
    
    st.info("Right-click inside the table to use the Menu options.")
    AgGrid(df, gridOptions=grid_opt, height=350, theme='alpine')

    if st.button("🚀 Start Search"):
        start_time = time.time()
        prog = st.progress(0)
        status = st.empty()
        table_view = st.empty()
        
        driver = get_driver()
        for i, row in df.iterrows():
            # تدوير المتصفح كل 20 اسماً لحل مشكلة OSError نهائياً
            if i > 0 and i % 20 == 0:
                driver.quit()
                driver = get_driver()
            
            p, n, d = str(row['Passport Number']), str(row['Nationality']), str(row['Date of Birth'])
            status.info(f"Processing {i+1}/{len(df)}: {p}")
            
            res = extract_logic(driver, p, n, d)
            st.session_state.batch_results.append(res if res else {"Passport": p, "Status": "Not Found"})
            
            elapsed = str(timedelta(seconds=int(time.time() - start_time)))
            prog.progress((i + 1) / len(df))
            table_view.dataframe(pd.DataFrame(st.session_state.batch_results))
        
        if driver: driver.quit()
        st.success(f"Finished in {elapsed}")
