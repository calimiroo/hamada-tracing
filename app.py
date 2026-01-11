import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="Test-1 Lab", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# نظام الدخول
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    with st.form("login"):
        pwd = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Incorrect Password")
    st.stop()

# --- نافذة الاستعلام عن تفاصيل الشركة (المربع المنبثق) ---
@st.dialog("Work Permit Details")
def show_company_details(card_number):
    # رسالة الانتظار المطلوبة
    st.info(f"⏳ Please wait... Fetching data for Card No: {card_number}")
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        
        # الدخول لرابط الاستعلامات
        driver.get("https://inquiry.mohre.gov.ae/")
        
        # اختيار الخدمة من القائمة
        select = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlService")))
        select.click()
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        
        # إدخال رقم البطاقة
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_number)
        
        # عرض الكابتشا للمستخدم
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        st.image(captcha_img.screenshot_as_png, caption="Enter Verification Code")
        
        with st.form("captcha_form"):
            code = st.text_input("Code")
            if st.form_submit_button("Search Details"):
                driver.find_element(By.ID, "txtCaptcha").send_keys(code)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(4)
                
                # استخراج البيانات المطلوبة
                name = driver.find_element(By.ID, "lblWorkerNameEn").text
                est_name = driver.find_element(By.ID, "lblEstNameEn").text
                est_code = driver.find_element(By.ID, "lblEstNo").text
                
                st.success("✅ Information Retrieved")
                st.markdown(f"""
                - **Full Name:** {name}
                - **Establishment:** {est_name}
                - **Company Code:** {est_code}
                """)
    except Exception as e:
        st.error(f"Error fetching details. Please try again.")
    finally:
        if driver: driver.quit()

# --- وظائف البحث الأساسية ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    return uc.Chrome(options=options, use_subprocess=False)

def run_search(passport, nation, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search.send_keys(nation)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script(f"arguments[0].value = '{dob}';", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        
        def val(l):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{l}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {
            "Passport": passport,
            "Card Number": val("Card Number"),
            "Job": val("Job Description"),
            "Basic": val("Basic Salary"),
            "Total": val("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم المحدثة ---
t1, t2 = st.tabs(["Single Person Search", "Batch Preview"])

with t1:
    st.subheader("Single Person Search") # تغيير العنوان للإنجليزية
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport")
    n_in = c2.selectbox("Nationality", ["Egypt", "India", "Pakistan"])
    # تعديل نمط التاريخ ليكون dd/mm/yyyy
    d_in = c3.date_input("Date of Birth", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))

    if st.button("Search"):
        with st.spinner("Searching primary data..."):
            res = run_search(p_in, n_in, d_in.strftime("%d/%m/%Y"))
            if res:
                # عرض النتيجة وربط رقم البطاقة بالدالة
                st.table(pd.DataFrame([res]))
                if res["Card Number"] != "N/A":
                    # جعل رقم البطاقة هو الرابط الوحيد لبدء العملية
                    if st.button(f"Click here to query Company details for: {res['Card Number']}"):
                        show_company_details(res["Card Number"])
            else: st.error("No data found.")
