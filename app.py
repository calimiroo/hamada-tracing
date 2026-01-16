import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from datetime import datetime, timedelta
import os
import requests
from st_aggrid import AgGrid, GridOptionsBuilder

# قائمة الجنسيات
countries = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines", "Jordan", "Syria"] # ... بقية القائمة

st.set_page_config(page_title="MOHRE Contract Extractor", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# الحماية بكلمة مرور
password = st.text_input("Enter Password", type="password")
if password != "Bilkish":
    st.error("Incorrect Password")
    st.stop()

# إعداد المتصفح مع حل مشكلة الذاكرة
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # إنشاء مسار مؤقت فريد لتجنب OSError: [Errno 24] Too many open files
    user_data_dir = f"/tmp/chrome_user_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_data_dir}")
    return uc.Chrome(options=options)

def translate_text(text, from_lang='ar', to_lang='en'):
    if not text or text == 'Not Found': return text
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair={from_lang}|{to_lang}"
        response = requests.get(url, timeout=5)
        return response.json()['responseData']['translatedText']
    except: return text

def extract_single(driver, passport, nationality, dob_str):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(2)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(10)
        
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Card Number": get_value("Card Number"), "Card Issue": get_value("Card Issue"),
            "Job Description": translate_text(get_value("Job Description")),
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"),
        }
    except: return None

tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="one_p")
    n_in = c2.selectbox("Nationality", countries, index=5, key="one_n")
    d_in = c3.date_input("Date of Birth", datetime(1990, 1, 1), key="one_d")
    
    if st.button("Search", key="one_btn"):
        drv = get_driver()
        with st.spinner("Searching..."):
            res = extract_single(drv, p_in, n_in, d_in.strftime("%d/%m/%Y"))
            st.table(pd.DataFrame([res]))
        drv.quit()

with tab2:
    st.subheader("Upload Excel for Batch Search")
    uploaded_file = st.file_uploader("Upload data.xlsx", type=["xlsx"])
    
    if uploaded_file:
        if 'df_batch' not in st.session_state:
            st.session_state.df_batch = pd.read_excel(uploaded_file)
        
        # --- زر التنسيق الصغير فوق الجدول ---
        col_format, _ = st.columns([1, 4])
        if col_format.button("🪄 Format Dates (dd/mm/yyyy)"):
            try:
                st.session_state.df_batch['Date of Birth'] = pd.to_datetime(st.session_state.df_batch['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("Dates formatted successfully!")
            except:
                st.error("Error formatting: Ensure column 'Date of Birth' exists.")

        # عرض الجدول مع Pagination
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df_batch)
        gb.configure_pagination(paginationPageSize=10)
        grid_res = AgGrid(st.session_state.df_batch, gridOptions=gb.build(), height=350, use_container_width=True)

        if st.button("Start Batch Search"):
            start_time = time.time()
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            results = []
            found_count = 0
            
            # تشغيل المتصفح الأول
            driver = get_driver()
            
            for i, row in st.session_state.df_batch.iterrows():
                # حل مشكلة الذاكرة: تدوير المتصفح كل 30 اسم
                if i > 0 and i % 30 == 0:
                    driver.quit()
                    driver = get_driver()
                
                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                dob = str(row.get('Date of Birth', ''))

                status_text.text(f"Searching: {p_num} ({i+1}/{len(st.session_state.df_ready)})")
                res = extract_single(driver, p_num, nat, dob)
                
                if res and res.get('Card Number') != 'Not Found':
                    found_count += 1
                
                results.append(res if res else {"Passport Number": p_num, "Status": "Error/Not Found"})
                
                elapsed = time.time() - start_time
                stats_area.markdown(f"✅ **Found:** {found_count} | ⏱️ **Elapsed:** `{str(timedelta(seconds=int(elapsed)))}`")
                progress_bar.progress((i + 1) / len(st.session_state.df_batch))
            
            driver.quit()
            st.success("Batch Complete!")
            st.dataframe(pd.DataFrame(results))
