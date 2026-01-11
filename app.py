import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# إعداد الصفحة
st.set_page_config(page_title="Test-1 Lab", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قائمة الجنسيات
NATIONS = ["", "Egypt", "India", "Pakistan", "Bangladesh", "Nepal", "Philippines"]

# --- نافذة الاستعلام عن تفاصيل الشركة (المربع المنبثق) ---
@st.dialog("Work Permit Inquiry")
def show_mohre_details(card_no):
    st.info(f"⏳ Please wait... Fetching details for: {card_no}")
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        
        # الدخول لصفحة الاستعلامات
        driver.get("https://inquiry.mohre.gov.ae/")
        
        # اختيار الخدمة ووضع رقم البطاقة
        wait = WebDriverWait(driver, 10)
        select = wait.until(EC.element_to_be_clickable((By.ID, "ddlService")))
        select.click()
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_no)
        
        # الكابتشا
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        st.image(captcha_img.screenshot_as_png, caption="Enter Code")
        
        with st.form("inquiry_form"):
            code = st.text_input("Captcha Code")
            if st.form_submit_button("Get Details"):
                driver.find_element(By.ID, "txtCaptcha").send_keys(code)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(5)
                
                # النتائج
                st.success("✅ Results Found")
                st.markdown(f"""
                - **Establishment Name:** {driver.find_element(By.ID, "lblEstNameEn").text}
                - **Establishment Code:** {driver.find_element(By.ID, "lblEstNo").text}
                - **Employee Name:** {driver.find_element(By.ID, "lblWorkerNameEn").text}
                - **Designation:** {driver.find_element(By.ID, "lblWorkerDesignationEn").text}
                """)
    except: st.error("Inquiry failed. Please try again.")
    finally:
        if driver: driver.quit()

# --- وظيفة السكرابر الأساسية ---
def core_scraper(p, n, d):
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
        time.sleep(7)
        
        def g(l):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{l}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {"Passport": p, "Card Number": g("Card Number"), "Job": g("Job Description"), "Basic": g("Basic Salary"), "Total": g("Total Salary")}
    except: return None
    finally: driver.quit()

# --- الواجهة ---
t1, t2 = st.tabs(["Single Person Search", "Batch Preview"])

with t1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", value="")
    n_in = c2.selectbox("Nationality", NATIONS, index=0)
    d_in = c3.text_input("Date of Birth (DD/MM/YYYY)", placeholder="e.g. 12/01/1982") # حل مشكلة السنين

    if st.button("Start Search"):
        st.session_state.start = time.time()
        with st.spinner("Searching..."):
            res = core_scraper(p_in, n_in, d_in)
            if res:
                # العداد والوقت
                st.success(f"✅ Success: 1 | ⏱️ Live Timer: {round(time.time() - st.session_state.start, 2)}s")
                st.table(pd.DataFrame([res]))
                
                if res["Card Number"] != "N/A":
                    # الربط ببحث الشركة
                    if st.button(f"🔍 Click to fetch Company Info for: {res['Card Number']}"):
                        show_mohre_details(res["Card Number"])
            else: st.error("No records found.")

with t2:
    st.subheader("Batch Processing & Preview")
    up = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up:
        df_view = pd.read_excel(up)
        st.write("### File Preview")
        st.dataframe(df_view, use_container_width=True) # المعاينة
        
        # زر البحث المفقود عاد
        if st.button("🚀 Start Batch Processing"):
            results = []
            bar = st.progress(0)
            for i, row in df_view.iterrows():
                # (منطق البحث للمجموعة يوضع هنا)
                bar.progress((i + 1) / len(df_view))
    else:
        st.info("Please upload a file to view and process data.")
