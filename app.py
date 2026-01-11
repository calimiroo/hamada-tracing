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

# قائمة الجنسيات
NATIONS = ["", "Egypt", "India", "Pakistan", "Bangladesh", "Nepal", "Philippines"]

# --- خدمة الاستعلام عن تفاصيل الشركة (المربع المنبثق) ---
@st.dialog("Company & Employee Detailed Info")
def show_mohre_details(card_number):
    st.info("⏳ Please wait... Fetching data from MOHRE Inquiry Service")
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        
        # 1. الدخول لموقع الاستعلامات
        driver.get("https://inquiry.mohre.gov.ae/")
        
        # 2. اختيار Electronic Work Permit Information
        dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlService")))
        dropdown.click()
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        
        # 3. إدخال رقم البطاقة في Transaction No
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_number)
        
        # 4. طلب كود الصورة
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        st.image(captcha_img.screenshot_as_png, caption="Enter Verification Code Below")
        
        with st.form("captcha_step"):
            v_code = st.text_input("Code")
            if st.form_submit_button("Search Now"):
                driver.find_element(By.ID, "txtCaptcha").send_keys(v_code)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(5)
                
                # 5. جلب النتائج
                res = {
                    "Company Name": driver.find_element(By.ID, "lblEstNameEn").text,
                    "Company Code": driver.find_element(By.ID, "lblEstNo").text,
                    "Person Name": driver.find_element(By.ID, "lblWorkerNameEn").text,
                    "Designation": driver.find_element(By.ID, "lblWorkerDesignationEn").text
                }
                st.success("✅ Inquiry Complete")
                st.json(res)
    except:
        st.error("Error fetching data. Check captcha or card number.")
    finally:
        if driver: driver.quit()

# --- وظيفة البحث الأساسية ---
def perform_search(p, n, d):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(n)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()
        # كتابة التاريخ يدوياً لحل مشكلة السنين
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
tab1, tab2 = st.tabs(["Single Person Search", "Batch Preview"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", value="") # فارغ افتراضياً
    n_in = c2.selectbox("Nationality", NATIONS, index=0)
    d_in = c3.text_input("Date of Birth (DD/MM/YYYY)", placeholder="e.g. 12/01/1982") # حل مشكلة السنين

    if st.button("Start Search"):
        start_time = time.time()
        with st.spinner("Processing..."):
            res = perform_search(p_in, n_in, d_in)
            if res:
                end_time = time.time()
                # إعادة العداد والوقت
                st.success(f"✅ Success: 1 | ⏱️ Live Timer: {round(end_time - start_time, 2)}s")
                st.table(pd.DataFrame([res]))
                
                # ربط رقم البطاقة بلينك البحث المطلوب
                if res["Card Number"] != "N/A":
                    if st.button(f"🔎 Click to fetch Company Info for: {res['Card Number']}"):
                        show_mohre_details(res["Card Number"])
            else: st.error("No record found.")

with tab2:
    st.subheader("Batch Processing & Preview")
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up_file:
        df = pd.read_excel(up_file)
        st.write("### File Preview")
        st.dataframe(df, use_container_width=True) # المعاينة لمنع الصفحة الفاضية
    else:
        # شرح ما تفعله هذه الصفحة
        st.info("Upload your Excel file here to search for multiple records at once automatically.")
