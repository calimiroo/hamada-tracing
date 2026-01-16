import streamlit as st
import pandas as pd
import time
import os
import requests
from datetime import datetime, timedelta

# حل مشكلة Python 3.13 ونقص distutils
try:
    from distutils.version import LooseVersion
except ImportError:
    # إنشاء بديل لمكتبة distutils لتجنب انهيار الموقع في النسخ الجديدة
    import sys
    from packaging import version
    class MockDistutils:
        class version:
            LooseVersion = version.parse
    sys.modules['distutils'] = MockDistutils
    sys.modules['distutils.version'] = MockDistutils.version

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Pro Contract", layout="wide")

# القائمة الجانبية (Sidebar) كما طلبت في الصورة ليكون المنظر احترافياً
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.info("Management Tools")
    
    # خيار تنسيق التاريخ داخل القائمة الجانبية
    if st.button("🪄 Format Dates (dd/mm/yyyy)"):
        if 'df_main' in st.session_state:
            try:
                st.session_state.df_main['Date of Birth'] = pd.to_datetime(st.session_state.df_main['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("Format Applied!")
                st.rerun()
            except: st.error("Date column error")
        else: st.warning("Upload a file first!")

    st.markdown("---")
    st.caption("Version 2.0 - Stable")

st.title("HAMADA TRACING SITE TEST")

# الحماية بكلمة مرور
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Enter Password", type="password")
    if pwd == "Bilkish":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# دالة تشغيل المتصفح مع حل مشكلة [Errno 24] Too many open files
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # إنشاء مسار مؤقت فريد لتحرير الملفات المفتوحة (OS Handles)
    user_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_dir}")
    try:
        return uc.Chrome(options=options, headless=True, use_subprocess=False)
    except Exception as e:
        st.error(f"Failed to start Chrome: {e}")
        return None

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

        return {"Passport": passport, "Card": gv("Card Number"), "Salary": gv("Total Salary"), "Status": "Success"}
    except: return {"Passport": passport, "Status": "Failed"}

# واجهة رفع الملفات والجدول
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    if 'df_main' not in st.session_state:
        st.session_state.df_main = pd.read_excel(uploaded_file)
    
    # إعداد الجدول المتقدم (AgGrid) مع تفعيل القائمة (Menu) كما طلبت
    gb = GridOptionsBuilder.from_dataframe(st.session_state.df_main)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_side_bar() # هذا يضيف القائمة الجانبية داخل الجدول (التي ظهرت في صورتك)
    gb.configure_default_column(editable=True, groupable=True, filter=True)
    grid_options = gb.build()

    st.write("Right-click inside table for context options:")
    grid_response = AgGrid(
        st.session_state.df_main,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        theme='alpine',
        height=400
    )

    if st.button("🚀 Start Batch Search"):
        start_t = time.time()
        prog = st.progress(0)
        status = st.empty()
        res_list = []
        
        driver = get_driver()
        for i, row in st.session_state.df_main.iterrows():
            # تدوير المتصفح كل 15 اسماً لحل مشكلة Errno 24
            if i > 0 and i % 15 == 0:
                driver.quit()
                driver = get_driver()
            
            p, n, d = str(row['Passport Number']), str(row['Nationality']), str(row['Date of Birth'])
            status.info(f"Searching: {p} ({i+1}/{len(st.session_state.df_main)})")
            
            res = extract_logic(driver, p, n, d)
            res_list.append(res)
            prog.progress((i + 1) / len(st.session_state.df_main))
        
        if driver: driver.quit()
        st.success(f"Complete! Time: {str(timedelta(seconds=int(time.time()-start_t)))}")
        st.dataframe(pd.DataFrame(res_list))
