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
            else: st.error("Wrong Password")
    st.stop()

# --- نافذة الاستعلام الثانية (Modal/Dialog) ---
@st.dialog("Work Permit Information")
def show_inquiry(card_no):
    st.markdown(f"### ⏳ Please wait...")
    st.info(f"Fetching details for Card: {card_no} in the background.")
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        
        # الدخول لرابط الاستعلامات
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(2)
        
        # اختيار الخدمة وإدخال الرقم
        select = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlService")))
        select.click()
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_no)
        
        # عرض الكابتشا للمستخدم
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        st.image(captcha_img.screenshot_as_png, caption="Enter Code to Continue")
        
        with st.form("captcha_step"):
            code = st.text_input("Verification Code")
            if st.form_submit_button("Search"):
                driver.find_element(By.ID, "txtCaptcha").send_keys(code)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(4)
                
                # سحب النتائج النهائية
                res = {
                    "Employee Name": driver.find_element(By.ID, "lblWorkerNameEn").text,
                    "Company Name": driver.find_element(By.ID, "lblEstNameEn").text,
                    "Company Code": driver.find_element(By.ID, "lblEstNo").text
                }
                st.success("✅ Data Retrieved Successfully")
                st.json(res) # ستظهر هنا علامة X للإغلاق اليدوي
    except: st.error("Connection Error. Please try again.")
    finally:
        if driver: driver.quit()

# --- وظيفة البحث الأساسية ---
def run_search(p, n, d):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(n)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()
        driver.execute_script(f"arguments[0].value = '{d}';", driver.find_element(By.ID, "txtBirthDate"))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)
        
        def gv(lbl):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{lbl}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {"Passport": p, "Card Number": gv("Card Number"), "Job": gv("Job Description"), "Basic": gv("Basic Salary"), "Total": gv("Total Salary")}
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
t1, t2 = st.tabs(["Single Person Search", "Batch Preview"])

with t1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    # مسح البيانات الافتراضية
    p_in = c1.text_input("Passport Number", value="")
    n_in = c2.selectbox("Nationality", ["", "Egypt", "India", "Pakistan"], index=0)
    d_in = c3.date_input("Date of Birth", value=None, format="DD/MM/YYYY")

    if st.button("Start Search"):
        start_t = time.time()
        with st.spinner("Searching..."):
            res = run_search(p_in, n_in, d_in.strftime("%d/%m/%Y") if d_in else "")
            if res:
                end_t = time.time()
                # إرجاع العداد والوقت
                st.success(f"✅ Success: 1 | ⏱️ Live Timer: {round(end_t - start_t, 2)}s")
                
                # تحويل رقم البطاقة لرابط تفاعلي
                st.write("### Result Preview")
                st.table(pd.DataFrame([res]))
                
                if res["Card Number"] != "N/A":
                    # ربط رقم البطاقة باللينك الجديد
                    if st.button(f"🔗 Click Card No: {res['Card Number']} to fetch Company Details"):
                        show_inquiry(res["Card Number"])
            else: st.error("No Data Found.")

with t2:
    # سيتم تفعيل الـ Batch هنا بنفس المنطق
    st.info("Upload your file to start batch processing.")
