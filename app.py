import streamlit as st
import pandas as pd
import time
import os
import requests
from datetime import datetime, timedelta

# حل استباقي لمشكلة نقص distutils في نسخ بايثون الجديدة
try:
    import distutils.version
except ImportError:
    import sys
    from packaging import version
    import types
    m = types.ModuleType('distutils')
    sys.modules['distutils'] = m
    m.version = types.ModuleType('distutils.version')
    sys.modules['distutils.version'] = m.version
    m.version.LooseVersion = version.parse

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Stable Pro", layout="wide")

# القائمة الجانبية (Sidebar)
with st.sidebar:
    st.title("🛠️ الأدوات")
    if st.button("🪄 تنسيق التاريخ (dd/mm/yyyy)"):
        if 'df_data' in st.session_state:
            try:
                st.session_state.df_data['Date of Birth'] = pd.to_datetime(st.session_state.df_data['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("تم التنسيق!")
                st.rerun()
            except: st.error("خطأ في عمود التاريخ")
    st.markdown("---")

st.title("HAMADA TRACING SITE - VERSION 2026")

# الحماية (Password)
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Password", type="password")
    if pwd == "Bilkish":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# دالة تشغيل المتصفح (تمنع خطأ Errno 24)
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # مسار فريد لتحرير الملفات المفتوحة
    options.add_argument(f"--user-data-dir=/tmp/chrome_user_{int(time.time())}")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# دالة البحث (Logic) - كما في الكود القديم
def run_search(driver, passport, nationality, dob):
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
        
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_field)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(10)

        def gv(lbl):
            try:
                xp = f"//span[contains(text(), '{lbl}')]/following::span[1] | //label[contains(text(), '{lbl}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except: return 'N/A'

        return {"Passport": passport, "Card Number": gv("Card Number"), "Salary": gv("Total Salary"), "Status": "Success"}
    except: return {"Passport": passport, "Status": "Error/Timeout"}

# رفع الملف والجدول الاحترافي
uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
if uploaded:
    if 'df_data' not in st.session_state:
        st.session_state.df_data = pd.read_excel(uploaded)
    
    # إعداد AgGrid (القائمة المنسدلة والمينو)
    gb = GridOptionsBuilder.from_dataframe(st.session_state.df_data)
    gb.configure_pagination(paginationPageSize=10)
    gb.configure_side_bar() # القائمة الجانبية داخل الجدول
    gb.configure_default_column(editable=True, filter=True)
    grid_opt = gb.build()

    AgGrid(st.session_state.df_data, gridOptions=grid_opt, theme='alpine', height=400)

    if st.button("🚀 Start Batch Search"):
        prog = st.progress(0)
        results = []
        driver = get_driver()
        for i, row in st.session_state.df_data.iterrows():
            # تدوير المتصفح كل 15 اسم لمنع تعليق الملفات
            if i > 0 and i % 15 == 0:
                driver.quit()
                driver = get_driver()
            
            res = run_search(driver, str(row['Passport Number']), str(row['Nationality']), str(row['Date of Birth']))
            results.append(res)
            prog.progress((i + 1) / len(st.session_state.df_data))
        
        if driver: driver.quit()
        st.dataframe(pd.DataFrame(results))
